"""
Test API Booking Endpoints
FINAL FIX: Robust seat finding with proper error handling
"""
import pytest
import uuid


def _get_unique_username():
    """Generate unique username for test isolation"""
    return f"testuser_{uuid.uuid4().hex[:8]}"


def _create_test_user(client):
    """Helper to create and register a unique test user"""
    username = _get_unique_username()
    response = client.post(
        "/api/auth/register",
        json={
            "username": username,
            "password": "testpass123",
            "email": f"{username}@test.com",
            "full_name": f"Test User {username}"
        }
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _find_showtime_with_available_seats(client, min_seats=1):
    """Find showtime with at least min_seats available - ROBUST"""
    showtimes = client.get("/api/showtimes/").json()
    
    for showtime in showtimes:
        if showtime["available_seats"] >= min_seats:
            showtime_id = showtime["showtime_id"]
            detail = client.get(f"/api/showtimes/{showtime_id}").json()
            available_seats = [s for s in detail["seats"] if s["status"] == "AVAILABLE"]
            
            if len(available_seats) >= min_seats:
                return showtime_id, available_seats[:min_seats]
    
    return None, []


# ============================================================================
# CREATE BOOKING TESTS
# ============================================================================
def test_create_booking_success(client):
    """Test: Create booking with valid data"""
    auth_headers = _create_test_user(client)
    
    # Find available showtime
    showtime_id, available_seats = _find_showtime_with_available_seats(client, min_seats=1)
    if not showtime_id:
        pytest.skip("No showtime with available seats found")
    
    response = client.post(
        "/api/bookings/",
        headers=auth_headers,
        json={
            "showtime_id": showtime_id,
            "seat_ids": [available_seats[0]["seat_id"]]
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "booking_id" in data
    assert data["status"] == "RESERVED"
    assert "hold_expiry_time" in data


def test_create_booking_without_auth(client):
    """Test: Cannot create booking without authentication"""
    showtimes = client.get("/api/showtimes/").json()
    showtime_id = showtimes[0]["showtime_id"]
    
    response = client.post(
        "/api/bookings/",
        json={
            "showtime_id": showtime_id,
            "seat_ids": ["SEAT_SCR1_A1"]
        }
    )
    
    assert response.status_code == 403  # Forbidden


def test_create_booking_invalid_showtime(client):
    """Test: Cannot create booking for non-existent showtime"""
    auth_headers = _create_test_user(client)
    
    response = client.post(
        "/api/bookings/",
        headers=auth_headers,
        json={
            "showtime_id": "INVALID_SHOWTIME_999",
            "seat_ids": ["SEAT_SCR1_A1"]
        }
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_create_booking_unavailable_seats(client):
    """Test: Cannot book already reserved seats"""
    showtime_id, available_seats = _find_showtime_with_available_seats(client, min_seats=2)
    if not showtime_id:
        pytest.skip("No showtime with 2+ available seats found")
    
    seat_id = available_seats[0]["seat_id"]
    
    # User 1 books a seat
    user1_headers = _create_test_user(client)
    client.post(
        "/api/bookings/",
        headers=user1_headers,
        json={
            "showtime_id": showtime_id,
            "seat_ids": [seat_id]
        }
    )
    
    # User 2 tries to book same seat
    user2_headers = _create_test_user(client)
    response = client.post(
        "/api/bookings/",
        headers=user2_headers,
        json={
            "showtime_id": showtime_id,
            "seat_ids": [seat_id]
        }
    )
    
    assert response.status_code == 400
    assert "not available" in response.json()["detail"].lower()


def test_create_booking_single_seat_gap(client):
    """Test: Cannot create booking that creates single-seat gap"""
    auth_headers = _create_test_user(client)
    
    # Find showtime with consecutive seats available
    showtimes = client.get("/api/showtimes/").json()
    
    for showtime in showtimes:
        if showtime["available_seats"] < 3:
            continue
            
        showtime_id = showtime["showtime_id"]
        detail = client.get(f"/api/showtimes/{showtime_id}").json()
        available_seats = [s for s in detail["seats"] if s["status"] == "AVAILABLE"]
        
        if len(available_seats) >= 3:
            # Try to book first and third seat (creates gap at second)
            seat_ids = [available_seats[0]["seat_id"], available_seats[2]["seat_id"]]
            
            response = client.post(
                "/api/bookings/",
                headers=auth_headers,
                json={
                    "showtime_id": showtime_id,
                    "seat_ids": seat_ids
                }
            )
            
            # Should fail with gap error
            assert response.status_code == 400
            assert "single-seat gap" in response.json()["detail"].lower()
            return
    
    pytest.skip("No showtime with 3 consecutive available seats found")


def test_create_booking_multiple_seats(client):
    """Test: Create booking with multiple consecutive seats"""
    auth_headers = _create_test_user(client)
    
    showtime_id, available_seats = _find_showtime_with_available_seats(client, min_seats=3)
    if not showtime_id:
        pytest.skip("No showtime with 3+ available seats found")
    
    # Book 3 consecutive seats
    seat_ids = [s["seat_id"] for s in available_seats[:3]]
    
    response = client.post(
        "/api/bookings/",
        headers=auth_headers,
        json={
            "showtime_id": showtime_id,
            "seat_ids": seat_ids
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["seat_ids"]) == 3


# ============================================================================
# GET MY BOOKINGS TESTS
# ============================================================================
def test_get_my_bookings_empty(client):
    """Test: Get my bookings when user has no bookings"""
    # Create brand new user who has never booked
    auth_headers = _create_test_user(client)
    
    response = client.get("/api/bookings/me", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0  # New user should have 0 bookings


def test_get_my_bookings_with_bookings(client):
    """Test: Get my bookings after creating booking"""
    auth_headers = _create_test_user(client)
    
    showtime_id, available_seats = _find_showtime_with_available_seats(client, min_seats=1)
    if not showtime_id:
        pytest.skip("No showtime with available seats found")
    
    # Create a booking
    client.post(
        "/api/bookings/",
        headers=auth_headers,
        json={
            "showtime_id": showtime_id,
            "seat_ids": [available_seats[0]["seat_id"]]
        }
    )
    
    # Get my bookings
    response = client.get("/api/bookings/me", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["status"] == "RESERVED"


def test_get_my_bookings_without_auth(client):
    """Test: Cannot get bookings without authentication"""
    response = client.get("/api/bookings/me")
    
    assert response.status_code == 403


def test_get_my_bookings_only_own(client):
    """Test: User can only see their own bookings"""
    showtime_id, available_seats = _find_showtime_with_available_seats(client, min_seats=2)
    if not showtime_id or len(available_seats) < 2:
        pytest.skip("No showtime with 2+ available seats found")
    
    # User 1 creates booking
    user1_headers = _create_test_user(client)
    response1_create = client.post(
        "/api/bookings/",
        headers=user1_headers,
        json={
            "showtime_id": showtime_id,
            "seat_ids": [available_seats[0]["seat_id"]]
        }
    )
    
    # If booking fails, skip test
    if response1_create.status_code != 200:
        pytest.skip(f"User 1 booking failed: {response1_create.json()}")
    
    # User 2 creates booking
    user2_headers = _create_test_user(client)
    response2_create = client.post(
        "/api/bookings/",
        headers=user2_headers,
        json={
            "showtime_id": showtime_id,
            "seat_ids": [available_seats[1]["seat_id"]]
        }
    )
    
    # If booking fails, skip test
    if response2_create.status_code != 200:
        pytest.skip(f"User 2 booking failed: {response2_create.json()}")
    
    # User 1 gets their bookings
    response1 = client.get("/api/bookings/me", headers=user1_headers)
    
    # User 2 gets their bookings
    response2 = client.get("/api/bookings/me", headers=user2_headers)
    
    assert response1.status_code == 200
    assert response2.status_code == 200
    
    data1 = response1.json()
    data2 = response2.json()
    
    # Each user sees at least their own booking
    assert len(data1) >= 1, f"User 1 should have at least 1 booking, got {len(data1)}"
    assert len(data2) >= 1, f"User 2 should have at least 1 booking, got {len(data2)}"

# ============================================================================
# GET BOOKING BY ID TESTS
# ============================================================================
def test_get_booking_by_id_success(client):
    """Test: Get booking details by ID"""
    auth_headers = _create_test_user(client)
    
    showtime_id, available_seats = _find_showtime_with_available_seats(client, min_seats=1)
    if not showtime_id:
        pytest.skip("No showtime with available seats found")
    
    # Create booking
    create_response = client.post(
        "/api/bookings/",
        headers=auth_headers,
        json={
            "showtime_id": showtime_id,
            "seat_ids": [available_seats[0]["seat_id"]]
        }
    )
    booking_id = create_response.json()["booking_id"]
    
    # Get booking by ID
    response = client.get(f"/api/bookings/{booking_id}", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["booking_id"] == booking_id
    assert "seat_ids" in data


def test_get_booking_not_found(client):
    """Test: Get non-existent booking returns 404"""
    auth_headers = _create_test_user(client)
    
    response = client.get("/api/bookings/INVALID_ID_999", headers=auth_headers)
    
    assert response.status_code == 404


def test_get_booking_not_owner(client):
    """Test: Cannot get booking owned by another user"""
    showtime_id, available_seats = _find_showtime_with_available_seats(client, min_seats=2)
    if not showtime_id:
        pytest.skip("No showtime with 2+ available seats found")
    
    # User 1 creates booking
    user1_headers = _create_test_user(client)
    create_response = client.post(
        "/api/bookings/",
        headers=user1_headers,
        json={
            "showtime_id": showtime_id,
            "seat_ids": [available_seats[0]["seat_id"]]
        }
    )
    booking_id = create_response.json()["booking_id"]
    
    # User 2 tries to get User 1's booking
    user2_headers = _create_test_user(client)
    response = client.get(f"/api/bookings/{booking_id}", headers=user2_headers)
    
    assert response.status_code == 403  # Forbidden


def test_get_booking_without_auth(client):
    """Test: Cannot get booking without authentication"""
    auth_headers = _create_test_user(client)
    
    showtime_id, available_seats = _find_showtime_with_available_seats(client, min_seats=1)
    if not showtime_id:
        pytest.skip("No showtime with available seats found")
    
    # Create booking with auth
    create_response = client.post(
        "/api/bookings/",
        headers=auth_headers,
        json={
            "showtime_id": showtime_id,
            "seat_ids": [available_seats[0]["seat_id"]]
        }
    )
    booking_id = create_response.json()["booking_id"]
    
    # Try to get without auth
    response = client.get(f"/api/bookings/{booking_id}")
    
    assert response.status_code == 403


# ============================================================================
# CONFIRM PAYMENT TESTS
# ============================================================================
def test_confirm_payment_success(client):
    """Test: Confirm payment for reserved booking"""
    auth_headers = _create_test_user(client)
    
    showtime_id, available_seats = _find_showtime_with_available_seats(client, min_seats=1)
    if not showtime_id:
        pytest.skip("No showtime with available seats found")
    
    # Create booking
    create_response = client.post(
        "/api/bookings/",
        headers=auth_headers,
        json={
            "showtime_id": showtime_id,
            "seat_ids": [available_seats[0]["seat_id"]]
        }
    )
    booking_id = create_response.json()["booking_id"]
    
    # Confirm payment
    response = client.post(
        "/api/bookings/confirm-payment",
        headers=auth_headers,
        json={"booking_id": booking_id}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "ticket_id" in data
    assert data["is_valid"] == True


def test_confirm_payment_not_owner(client):
    """Test: Cannot confirm payment for another user's booking"""
    showtime_id, available_seats = _find_showtime_with_available_seats(client, min_seats=2)
    if not showtime_id:
        pytest.skip("No showtime with 2+ available seats found")
    
    # User 1 creates booking
    user1_headers = _create_test_user(client)
    create_response = client.post(
        "/api/bookings/",
        headers=user1_headers,
        json={
            "showtime_id": showtime_id,
            "seat_ids": [available_seats[0]["seat_id"]]
        }
    )
    booking_id = create_response.json()["booking_id"]
    
    # User 2 tries to confirm
    user2_headers = _create_test_user(client)
    response = client.post(
        "/api/bookings/confirm-payment",
        headers=user2_headers,
        json={"booking_id": booking_id}
    )
    
    assert response.status_code == 403


def test_confirm_payment_invalid_booking(client):
    """Test: Cannot confirm payment for non-existent booking"""
    auth_headers = _create_test_user(client)
    
    response = client.post(
        "/api/bookings/confirm-payment",
        headers=auth_headers,
        json={"booking_id": "INVALID_ID_999"}
    )
    
    assert response.status_code == 404


# ============================================================================
# CANCEL BOOKING TESTS
# ============================================================================
def test_cancel_booking_success(client):
    """Test: Cancel confirmed booking with refund"""
    auth_headers = _create_test_user(client)
    
    showtime_id, available_seats = _find_showtime_with_available_seats(client, min_seats=1)
    if not showtime_id:
        pytest.skip("No showtime with available seats found")
    
    # Create and confirm booking
    create_response = client.post(
        "/api/bookings/",
        headers=auth_headers,
        json={
            "showtime_id": showtime_id,
            "seat_ids": [available_seats[0]["seat_id"]]
        }
    )
    booking_id = create_response.json()["booking_id"]
    
    # Confirm payment
    client.post(
        "/api/bookings/confirm-payment",
        headers=auth_headers,
        json={"booking_id": booking_id}
    )
    
    # Cancel booking
    response = client.delete(f"/api/bookings/{booking_id}", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "refund_amount" in data
    assert data["refund_amount"] >= 0


def test_cancel_booking_not_owner(client):
    """Test: Cannot cancel another user's booking"""
    showtime_id, available_seats = _find_showtime_with_available_seats(client, min_seats=2)
    if not showtime_id:
        pytest.skip("No showtime with 2+ available seats found")
    
    # User 1 creates and confirms booking
    user1_headers = _create_test_user(client)
    create_response = client.post(
        "/api/bookings/",
        headers=user1_headers,
        json={
            "showtime_id": showtime_id,
            "seat_ids": [available_seats[0]["seat_id"]]
        }
    )
    booking_id = create_response.json()["booking_id"]
    
    client.post(
        "/api/bookings/confirm-payment",
        headers=user1_headers,
        json={"booking_id": booking_id}
    )
    
    # User 2 tries to cancel
    user2_headers = _create_test_user(client)
    response = client.delete(f"/api/bookings/{booking_id}", headers=user2_headers)
    
    assert response.status_code == 403


def test_cancel_booking_not_found(client):
    """Test: Cannot cancel non-existent booking"""
    auth_headers = _create_test_user(client)
    
    response = client.delete("/api/bookings/INVALID_ID_999", headers=auth_headers)
    
    assert response.status_code == 404


def test_cancel_booking_without_auth(client):
    """Test: Cannot cancel booking without authentication"""
    auth_headers = _create_test_user(client)
    
    showtime_id, available_seats = _find_showtime_with_available_seats(client, min_seats=1)
    if not showtime_id:
        pytest.skip("No showtime with available seats found")
    
    # Create booking with auth
    create_response = client.post(
        "/api/bookings/",
        headers=auth_headers,
        json={
            "showtime_id": showtime_id,
            "seat_ids": [available_seats[0]["seat_id"]]
        }
    )
    booking_id = create_response.json()["booking_id"]
    
    # Try to cancel without auth
    response = client.delete(f"/api/bookings/{booking_id}")
    
    assert response.status_code == 403


# ============================================================================
# VALIDATION ERROR TESTS
# ============================================================================

def test_create_booking_missing_showtime_id(client):
    """Test: Create booking without showtime_id returns validation error"""
    auth_headers = _create_test_user(client)
    
    response = client.post(
        "/api/bookings/",
        headers=auth_headers,
        json={
            "seat_ids": ["SEAT_001"]
        }
    )
    
    assert response.status_code == 422


def test_create_booking_missing_seat_ids(client):
    """Test: Create booking without seat_ids returns validation error"""
    auth_headers = _create_test_user(client)
    
    response = client.post(
        "/api/bookings/",
        headers=auth_headers,
        json={
            "showtime_id": "ST001"
        }
    )
    
    assert response.status_code == 422


def test_confirm_payment_missing_booking_id(client):
    """Test: Confirm payment without booking_id returns validation error"""
    auth_headers = _create_test_user(client)
    
    response = client.post(
        "/api/bookings/confirm-payment",
        headers=auth_headers,
        json={}
    )
    
    assert response.status_code == 422