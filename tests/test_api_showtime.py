"""
Test API Showtime Endpoints
FIXED to match actual API response structure (no time_slot nested object)
"""
import pytest


# ============================================================================
# GET ALL SHOWTIMES TESTS
# ============================================================================
def test_get_all_showtimes_success(client):
    """Test: Get all available showtimes"""
    response = client.get("/api/showtimes/")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0  # Should have demo showtimes


def test_get_all_showtimes_structure(client):
    """Test: Showtime response has correct structure (FIXED: no time_slot)"""
    response = client.get("/api/showtimes/")
    
    data = response.json()
    first_showtime = data[0]
    
    assert "showtime_id" in first_showtime
    assert "movie_id" in first_showtime
    assert "screen_id" in first_showtime
    # FIXED: No time_slot nested object, fields are flat
    assert "date" in first_showtime
    assert "start_time" in first_showtime
    assert "end_time" in first_showtime
    assert "price_per_seat" in first_showtime
    assert "available_seats" in first_showtime


def test_get_all_showtimes_no_auth_required(client):
    """Test: Getting showtimes does not require authentication"""
    response = client.get("/api/showtimes/")
    
    assert response.status_code == 200


# ============================================================================
# GET SHOWTIME BY ID TESTS
# ============================================================================
def test_get_showtime_by_id_success(client):
    """Test: Get specific showtime by ID"""
    # First get all showtimes to get a valid ID
    all_response = client.get("/api/showtimes/")
    showtime_id = all_response.json()[0]["showtime_id"]
    
    # Get specific showtime
    response = client.get(f"/api/showtimes/{showtime_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["showtime_id"] == showtime_id


def test_get_showtime_by_id_not_found(client):
    """Test: Get non-existent showtime returns 404"""
    response = client.get("/api/showtimes/INVALID_ID")
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_showtime_by_id_seats_info(client):
    """Test: Showtime detail response includes seats information"""
    all_response = client.get("/api/showtimes/")
    showtime_id = all_response.json()[0]["showtime_id"]
    
    response = client.get(f"/api/showtimes/{showtime_id}")
    
    data = response.json()
    assert "seats" in data
    assert isinstance(data["seats"], list)
    assert len(data["seats"]) > 0


def test_get_showtime_seat_structure(client):
    """Test: Seat information has correct structure"""
    all_response = client.get("/api/showtimes/")
    showtime_id = all_response.json()[0]["showtime_id"]
    
    response = client.get(f"/api/showtimes/{showtime_id}")
    
    data = response.json()
    first_seat = data["seats"][0]
    
    assert "seat_id" in first_seat
    assert "seat_number" in first_seat
    assert "status" in first_seat


def test_get_showtime_no_auth_required(client):
    """Test: Getting showtime by ID does not require authentication"""
    all_response = client.get("/api/showtimes/")
    showtime_id = all_response.json()[0]["showtime_id"]
    
    # Should work without authentication
    response = client.get(f"/api/showtimes/{showtime_id}")
    
    assert response.status_code == 200


# ============================================================================
# SHOWTIME SEAT AVAILABILITY TESTS
# ============================================================================
def test_showtime_seat_availability_all_available(client):
    """Test: Showtimes have available seats"""
    response = client.get("/api/showtimes/")
    
    data = response.json()
    # At least one showtime should have available seats
    assert any(s["available_seats"] > 0 for s in data)


def test_showtime_seat_availability_after_booking(client, auth_headers):
    """Test: Available seats decrease after booking"""
    # Get showtime with available seats
    all_response = client.get("/api/showtimes/")
    showtimes = all_response.json()
    
    # Find showtime with available seats
    showtime = next(s for s in showtimes if s["available_seats"] > 2)
    initial_available = showtime["available_seats"]
    showtime_id = showtime["showtime_id"]
    
    # Get seat details
    detail_response = client.get(f"/api/showtimes/{showtime_id}")
    seats = detail_response.json()["seats"]
    available_seat = next(s for s in seats if s["status"] == "AVAILABLE")
    
    # Create booking (reserve 1 seat)
    client.post(
        "/api/bookings/",
        headers=auth_headers,
        json={
            "showtime_id": showtime_id,
            "seat_ids": [available_seat["seat_id"]]
        }
    )
    
    # Check available seats decreased
    updated_response = client.get(f"/api/showtimes/{showtime_id}")
    updated_showtime = updated_response.json()
    
    assert updated_showtime["available_seats"] == initial_available - 1


def test_showtime_seat_status_after_booking(client, auth_headers):
    """Test: Seat status changes to RESERVED after booking"""
    all_response = client.get("/api/showtimes/")
    showtimes = all_response.json()
    
    # Find showtime with available seats
    showtime = next(s for s in showtimes if s["available_seats"] > 2)
    showtime_id = showtime["showtime_id"]
    
    # Get seat details
    detail_response = client.get(f"/api/showtimes/{showtime_id}")
    seats = detail_response.json()["seats"]
    available_seat = next(s for s in seats if s["status"] == "AVAILABLE")
    seat_id = available_seat["seat_id"]
    
    # Check initial status is AVAILABLE
    assert available_seat["status"] == "AVAILABLE"
    
    # Create booking
    client.post(
        "/api/bookings/",
        headers=auth_headers,
        json={
            "showtime_id": showtime_id,
            "seat_ids": [seat_id]
        }
    )
    
    # Check status changed to RESERVED
    updated_response = client.get(f"/api/showtimes/{showtime_id}")
    updated_seats = updated_response.json()["seats"]
    updated_seat = next(s for s in updated_seats if s["seat_id"] == seat_id)
    
    assert updated_seat["status"] == "RESERVED"


def test_showtime_seat_status_after_cancel(client, auth_headers):
    """Test: Seat status returns to AVAILABLE after cancellation"""
    all_response = client.get("/api/showtimes/")
    showtimes = all_response.json()
    
    # Find showtime with available seats
    showtime = next(s for s in showtimes if s["available_seats"] > 2)
    showtime_id = showtime["showtime_id"]
    
    # Get seat details
    detail_response = client.get(f"/api/showtimes/{showtime_id}")
    seats = detail_response.json()["seats"]
    available_seat = next(s for s in seats if s["status"] == "AVAILABLE")
    seat_id = available_seat["seat_id"]
    
    # Create and confirm booking
    create_response = client.post(
        "/api/bookings/",
        headers=auth_headers,
        json={
            "showtime_id": showtime_id,
            "seat_ids": [seat_id]
        }
    )
    booking_id = create_response.json()["booking_id"]
    
    client.post(
        "/api/bookings/confirm-payment",
        headers=auth_headers,
        json={"booking_id": booking_id}
    )
    
    # Cancel booking
    client.delete(f"/api/bookings/{booking_id}", headers=auth_headers)
    
    # Check seat is AVAILABLE again
    updated_response = client.get(f"/api/showtimes/{showtime_id}")
    updated_seats = updated_response.json()["seats"]
    updated_seat = next(s for s in updated_seats if s["seat_id"] == seat_id)
    
    assert updated_seat["status"] == "AVAILABLE"


# ============================================================================
# SHOWTIME DATA VALIDATION TESTS
# ============================================================================
def test_showtime_price_is_string(client):
    """Test: Price per seat is returned as string"""
    response = client.get("/api/showtimes/")
    
    data = response.json()
    price = data[0]["price_per_seat"]
    
    assert isinstance(price, str)
    # Should be convertible to Decimal
    from decimal import Decimal
    Decimal(price)  # Should not raise exception


def test_showtime_available_seats_is_integer(client):
    """Test: Available seats is integer"""
    response = client.get("/api/showtimes/")
    
    data = response.json()
    available_seats = data[0]["available_seats"]
    
    assert isinstance(available_seats, int)
    assert available_seats >= 0


def test_showtime_date_format(client):
    """Test: Date is in correct format (YYYY-MM-DD)"""
    response = client.get("/api/showtimes/")
    
    data = response.json()
    date = data[0]["date"]  # FIXED: direct field, not time_slot.date
    
    # Should match YYYY-MM-DD format
    import re
    assert re.match(r'^\d{4}-\d{2}-\d{2}$', date)


def test_showtime_time_format(client):
    """Test: Time is in correct format (HH:MM)"""
    response = client.get("/api/showtimes/")
    
    data = response.json()
    start_time = data[0]["start_time"]  # FIXED: direct field
    end_time = data[0]["end_time"]  # FIXED: direct field
    
    # Should match HH:MM format
    import re
    assert re.match(r'^\d{2}:\d{2}$', start_time)
    assert re.match(r'^\d{2}:\d{2}$', end_time)


# ============================================================================
# MULTIPLE SHOWTIMES TESTS
# ============================================================================
def test_multiple_showtimes_available(client):
    """Test: Multiple showtimes are available"""
    response = client.get("/api/showtimes/")
    
    data = response.json()
    # Demo data should have at least 2-3 showtimes
    assert len(data) >= 2


def test_showtimes_have_unique_ids(client):
    """Test: Each showtime has unique ID"""
    response = client.get("/api/showtimes/")
    
    data = response.json()
    showtime_ids = [s["showtime_id"] for s in data]
    
    # All IDs should be unique
    assert len(showtime_ids) == len(set(showtime_ids))


def test_showtimes_different_screens(client):
    """Test: Showtimes can be for different screens"""
    response = client.get("/api/showtimes/")
    
    data = response.json()
    screen_ids = [s["screen_id"] for s in data]
    
    # Should have at least 1 screen (could have multiple)
    assert len(set(screen_ids)) >= 1


def test_get_all_showtimes_response_fields_not_null(client):
    """Test: All required fields are not null"""
    response = client.get("/api/showtimes/")
    
    data = response.json()
    first_showtime = data[0]
    
    assert first_showtime["showtime_id"] is not None
    assert first_showtime["movie_id"] is not None
    assert first_showtime["screen_id"] is not None
    assert first_showtime["date"] is not None
    assert first_showtime["start_time"] is not None
    assert first_showtime["end_time"] is not None
    assert first_showtime["price_per_seat"] is not None
    assert first_showtime["available_seats"] is not None