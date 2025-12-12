"""
Pytest configuration and fixtures.
FIXED to work with global repository instance.
"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from fastapi.testclient import TestClient

from app.main import app
from app.domain.aggregates import Booking, Showtime
from app.domain.entities import Seat, BookingItem, Ticket
from app.domain.value_objects import (
    SeatNumber, TimeSlot, BookingStatus, 
    HoldExpiry, BookingStatusEnum
)
from app.auth.models import User
from app.infrastructure.in_memory_repository import repository  # Use global repository
from app.auth.jwt_handler import get_password_hash, create_access_token


# ============================================================================
# API CLIENT FIXTURE
# ============================================================================
@pytest.fixture
def client():
    """FastAPI test client for API endpoint testing"""
    return TestClient(app)


# ============================================================================
# USER FIXTURES
# ============================================================================
@pytest.fixture
def test_user():
    """Create a test user and add to repository"""
    user = User(
        user_id="TEST_USER_001",
        username="testuser_pytest",
        full_name="Test User Pytest",
        password_hash=get_password_hash("testpass123")
    )
    # Add to global repository
    repository.add_user(user)
    return user


@pytest.fixture
def test_user_2():
    """Create a second test user for ownership tests"""
    user = User(
        user_id="TEST_USER_002",
        username="testuser2_pytest",
        full_name="Test User Two Pytest",
        password_hash=get_password_hash("testpass456")
    )
    # Add to global repository
    repository.add_user(user)
    return user


@pytest.fixture
def test_user_token(test_user):
    """Generate JWT token for test user"""
    return create_access_token(
        data={"user_id": test_user.user_id, "username": test_user.username}
    )


@pytest.fixture
def test_user_2_token(test_user_2):
    """Generate JWT token for second test user"""
    return create_access_token(
        data={"user_id": test_user_2.user_id, "username": test_user_2.username}
    )


@pytest.fixture
def auth_headers(test_user_token):
    """Authorization headers with bearer token for test user"""
    return {"Authorization": f"Bearer {test_user_token}"}


@pytest.fixture
def auth_headers_2(test_user_2_token):
    """Authorization headers for second test user"""
    return {"Authorization": f"Bearer {test_user_2_token}"}


# ============================================================================
# DATE/TIME FIXTURES
# ============================================================================
@pytest.fixture
def future_date():
    """Date 7 days in the future"""
    return (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")


@pytest.fixture
def showtime_datetime_h24_plus():
    """Showtime datetime 30 hours in the future (for 100% refund test)"""
    return datetime.now() + timedelta(hours=30)


@pytest.fixture
def showtime_datetime_h12_to_h24():
    """Showtime datetime 15 hours in the future (for 50% refund test)"""
    return datetime.now() + timedelta(hours=15)


@pytest.fixture
def showtime_datetime_less_h12():
    """Showtime datetime 5 hours in the future (for 0% refund test)"""
    return datetime.now() + timedelta(hours=5)


@pytest.fixture
def expired_datetime():
    """Datetime in the past (for expired booking test)"""
    return datetime.now() - timedelta(minutes=15)


# ============================================================================
# SHOWTIME FIXTURES
# ============================================================================
@pytest.fixture
def test_showtime(future_date):
    """Create a test showtime with 10 seats"""
    time_slot = TimeSlot(
        date=future_date,
        start_time="19:00",
        end_time="21:30"
    )
    
    showtime = Showtime(
        showtime_id="TEST_SHOWTIME_001",
        movie_id="TEST_MOVIE",
        screen_id="TEST_SCREEN",
        time_slot=time_slot,
        price_per_seat=Decimal("50000"),
        available_seats=10
    )
    
    # Add 10 seats (Row A, columns 1-10)
    for col in range(1, 11):
        seat_number = SeatNumber("A", col)
        seat = Seat(
            seat_id=f"TEST_SEAT_A{col}",
            seat_number=seat_number,
            screen_id="TEST_SCREEN",
            status="AVAILABLE"
        )
        showtime.add_seat(seat)
    
    return showtime


@pytest.fixture
def test_showtime_with_reserved_seats(test_showtime):
    """Showtime with some seats already reserved (A1, A2)"""
    test_showtime.reserve_seats(["TEST_SEAT_A1", "TEST_SEAT_A2"])
    return test_showtime


# ============================================================================
# BOOKING FIXTURES
# ============================================================================
@pytest.fixture
def test_booking(test_user):
    """Create a test booking in RESERVED status"""
    booking = Booking(
        booking_id="TEST_BOOKING_001",
        user_id=test_user.user_id,
        showtime_id="TEST_SHOWTIME_001",
        created_at=datetime.now(),
        total_price=Decimal("50000")
    )
    
    # Add booking item
    item = BookingItem(
        booking_item_id="TEST_ITEM_001",
        booking_id=booking.booking_id,
        seat_id="TEST_SEAT_A1",
        price=Decimal("50000")
    )
    booking.add_booking_item(item)
    
    return booking


@pytest.fixture
def confirmed_booking(test_booking):
    """Create a confirmed booking"""
    test_booking.confirm_payment()
    return test_booking


@pytest.fixture
def expired_booking(test_user):
    """Create an expired booking (created 15 minutes ago)"""
    past_time = datetime.now() - timedelta(minutes=15)
    booking = Booking(
        booking_id="TEST_BOOKING_EXPIRED",
        user_id=test_user.user_id,
        showtime_id="TEST_SHOWTIME_001",
        created_at=past_time,
        total_price=Decimal("50000")
    )
    
    item = BookingItem(
        booking_item_id="TEST_ITEM_EXPIRED",
        booking_id=booking.booking_id,
        seat_id="TEST_SEAT_A1",
        price=Decimal("50000")
    )
    booking.add_booking_item(item)
    
    # Force check expiry
    booking.check_hold_expiry()
    
    return booking


# ============================================================================
# SEAT FIXTURES
# ============================================================================
@pytest.fixture
def test_seat():
    """Create a test seat"""
    seat_number = SeatNumber("A", 1)
    return Seat(
        seat_id="TEST_SEAT_A1",
        seat_number=seat_number,
        screen_id="TEST_SCREEN",
        status="AVAILABLE"
    )


@pytest.fixture
def reserved_seat():
    """Create a reserved seat"""
    seat_number = SeatNumber("A", 1)
    seat = Seat(
        seat_id="TEST_SEAT_A1",
        seat_number=seat_number,
        screen_id="TEST_SCREEN",
        status="AVAILABLE"
    )
    seat.reserve()
    return seat


# ============================================================================
# VALUE OBJECT FIXTURES
# ============================================================================
@pytest.fixture
def test_seat_number():
    """Create a test seat number"""
    return SeatNumber("A", 1)


@pytest.fixture
def test_time_slot(future_date):
    """Create a test time slot"""
    return TimeSlot(
        date=future_date,
        start_time="19:00",
        end_time="21:30"
    )


@pytest.fixture
def test_booking_status_reserved():
    """Create a RESERVED booking status"""
    return BookingStatus(BookingStatusEnum.RESERVED)


@pytest.fixture
def test_booking_status_confirmed():
    """Create a CONFIRMED booking status"""
    return BookingStatus(BookingStatusEnum.CONFIRMED)


@pytest.fixture
def test_hold_expiry_valid():
    """Create a valid (not expired) hold expiry"""
    expiry_time = datetime.now() + timedelta(minutes=5)
    return HoldExpiry(expiry_time)


@pytest.fixture
def test_hold_expiry_expired():
    """Create an expired hold expiry"""
    expiry_time = datetime.now() - timedelta(minutes=5)
    return HoldExpiry(expiry_time)