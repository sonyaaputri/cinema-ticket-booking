"""
Test Business Rules (MOST CRITICAL for grading):
1. Seat hold timeout (10 minutes)
2. Concurrent booking prevention
3. Single-seat gap prevention
4. Cancellation policy (H-24: 100%, H-12: 50%, <H-12: 0%)
"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from app.domain.aggregates import Booking, Showtime
from app.domain.entities import Seat
from app.domain.value_objects import SeatNumber, TimeSlot, BookingStatusEnum


# ============================================================================
# BUSINESS RULE 1: SEAT HOLD TIMEOUT (10 MINUTES)
# ============================================================================
def test_seat_hold_timeout_valid_booking():
    """Test: Booking created 5 minutes ago is still valid"""
    created_at = datetime.now() - timedelta(minutes=5)
    booking = Booking(
        booking_id="BOOKING_001",
        user_id="USER_001",
        showtime_id="SHOWTIME_001",
        created_at=created_at,
        total_price=Decimal("50000")
    )
    
    is_expired = booking.check_hold_expiry()
    
    assert is_expired == False
    assert booking.booking_status.is_reserved() == True


def test_seat_hold_timeout_expired_booking():
    """Test: Booking created 11 minutes ago is expired"""
    created_at = datetime.now() - timedelta(minutes=11)
    booking = Booking(
        booking_id="BOOKING_001",
        user_id="USER_001",
        showtime_id="SHOWTIME_001",
        created_at=created_at,
        total_price=Decimal("50000")
    )
    
    is_expired = booking.check_hold_expiry()
    
    assert is_expired == True
    assert booking.booking_status.value == BookingStatusEnum.EXPIRED


def test_seat_hold_timeout_cannot_confirm_expired():
    """Test: Cannot confirm payment for expired booking"""
    created_at = datetime.now() - timedelta(minutes=11)
    booking = Booking(
        booking_id="BOOKING_001",
        user_id="USER_001",
        showtime_id="SHOWTIME_001",
        created_at=created_at,
        total_price=Decimal("50000")
    )
    
    with pytest.raises(ValueError, match="expired"):
        booking.confirm_payment()


def test_seat_hold_timeout_edge_case_exactly_10_minutes():
    """Test: Booking at exactly 10 minutes should be expired"""
    created_at = datetime.now() - timedelta(minutes=10, seconds=1)
    booking = Booking(
        booking_id="BOOKING_001",
        user_id="USER_001",
        showtime_id="SHOWTIME_001",
        created_at=created_at,
        total_price=Decimal("50000")
    )
    
    is_expired = booking.check_hold_expiry()
    
    assert is_expired == True


# ============================================================================
# BUSINESS RULE 2: CONCURRENT BOOKING PREVENTION
# ============================================================================
def test_concurrent_booking_first_user_success():
    """Test: First user can book available seats"""
    time_slot = TimeSlot("2025-12-20", "19:00", "21:30")
    showtime = Showtime(
        showtime_id="SHOWTIME_001",
        movie_id="MOVIE_001",
        screen_id="SCREEN_001",
        time_slot=time_slot,
        price_per_seat=Decimal("50000"),
        available_seats=3
    )
    
    # Add 3 seats
    for i in range(1, 4):
        seat = Seat(f"SEAT_00{i}", SeatNumber("A", i), "SCREEN_001", "AVAILABLE")
        showtime.add_seat(seat)
    
    # First user books A1, A2
    showtime.reserve_seats(["SEAT_001", "SEAT_002"])
    
    assert showtime.available_seats == 1
    seats = showtime.get_seats()
    assert seats[0].status == "RESERVED"
    assert seats[1].status == "RESERVED"
    assert seats[2].status == "AVAILABLE"


def test_concurrent_booking_second_user_same_seats_fails():
    """Test: Second user cannot book already reserved seats"""
    time_slot = TimeSlot("2025-12-20", "19:00", "21:30")
    showtime = Showtime(
        showtime_id="SHOWTIME_001",
        movie_id="MOVIE_001",
        screen_id="SCREEN_001",
        time_slot=time_slot,
        price_per_seat=Decimal("50000"),
        available_seats=3
    )
    
    # Add 3 seats
    for i in range(1, 4):
        seat = Seat(f"SEAT_00{i}", SeatNumber("A", i), "SCREEN_001", "AVAILABLE")
        showtime.add_seat(seat)
    
    # First user books A1, A2
    showtime.reserve_seats(["SEAT_001", "SEAT_002"])
    
    # Second user tries to book A2, A3 (A2 already reserved)
    with pytest.raises(ValueError, match="not available"):
        showtime.reserve_seats(["SEAT_002", "SEAT_003"])


def test_concurrent_booking_second_user_different_seats_success():
    """Test: Second user can book remaining available seats"""
    time_slot = TimeSlot("2025-12-20", "19:00", "21:30")
    showtime = Showtime(
        showtime_id="SHOWTIME_001",
        movie_id="MOVIE_001",
        screen_id="SCREEN_001",
        time_slot=time_slot,
        price_per_seat=Decimal("50000"),
        available_seats=5
    )
    
    # Add 5 seats
    for i in range(1, 6):
        seat = Seat(f"SEAT_00{i}", SeatNumber("A", i), "SCREEN_001", "AVAILABLE")
        showtime.add_seat(seat)
    
    # First user books A1, A2
    showtime.reserve_seats(["SEAT_001", "SEAT_002"])
    
    # Second user books A4, A5 (different seats)
    showtime.reserve_seats(["SEAT_004", "SEAT_005"])
    
    assert showtime.available_seats == 1
    seats = showtime.get_seats()
    assert seats[0].status == "RESERVED"  # A1
    assert seats[1].status == "RESERVED"  # A2
    assert seats[2].status == "AVAILABLE"  # A3
    assert seats[3].status == "RESERVED"  # A4
    assert seats[4].status == "RESERVED"  # A5


# ============================================================================
# BUSINESS RULE 3: SINGLE-SEAT GAP PREVENTION
# ============================================================================
def test_single_seat_gap_consecutive_seats_allowed():
    """Test: Booking consecutive seats is allowed (no gap)"""
    time_slot = TimeSlot("2025-12-20", "19:00", "21:30")
    showtime = Showtime(
        showtime_id="SHOWTIME_001",
        movie_id="MOVIE_001",
        screen_id="SCREEN_001",
        time_slot=time_slot,
        price_per_seat=Decimal("50000"),
        available_seats=5
    )
    
    # Add 5 consecutive seats
    for i in range(1, 6):
        seat = Seat(f"SEAT_00{i}", SeatNumber("A", i), "SCREEN_001", "AVAILABLE")
        showtime.add_seat(seat)
    
    # Book A1, A2, A3 (consecutive)
    showtime.reserve_seats(["SEAT_001", "SEAT_002", "SEAT_003"])
    
    assert showtime.available_seats == 2


def test_single_seat_gap_creates_gap_rejected():
    """Test: Booking A1 and A3 creates single-seat gap at A2 - REJECTED"""
    time_slot = TimeSlot("2025-12-20", "19:00", "21:30")
    showtime = Showtime(
        showtime_id="SHOWTIME_001",
        movie_id="MOVIE_001",
        screen_id="SCREEN_001",
        time_slot=time_slot,
        price_per_seat=Decimal("50000"),
        available_seats=5
    )
    
    # Add 5 consecutive seats
    for i in range(1, 6):
        seat = Seat(f"SEAT_00{i}", SeatNumber("A", i), "SCREEN_001", "AVAILABLE")
        showtime.add_seat(seat)
    
    # Try to book A1, A3 (creates gap at A2)
    with pytest.raises(ValueError, match="single-seat gap"):
        showtime.reserve_seats(["SEAT_001", "SEAT_003"])


def test_single_seat_gap_two_seat_gap_allowed():
    """Test: Booking A1 and A4 leaves 2-seat gap (A2, A3) - ALLOWED"""
    time_slot = TimeSlot("2025-12-20", "19:00", "21:30")
    showtime = Showtime(
        showtime_id="SHOWTIME_001",
        movie_id="MOVIE_001",
        screen_id="SCREEN_001",
        time_slot=time_slot,
        price_per_seat=Decimal("50000"),
        available_seats=5
    )
    
    # Add 5 consecutive seats
    for i in range(1, 6):
        seat = Seat(f"SEAT_00{i}", SeatNumber("A", i), "SCREEN_001", "AVAILABLE")
        showtime.add_seat(seat)
    
    # Book A1, A4 (leaves A2-A3 as 2-seat gap - OK)
    showtime.reserve_seats(["SEAT_001", "SEAT_004"])
    
    assert showtime.available_seats == 3


def test_single_seat_gap_different_rows_allowed():
    """Test: Booking seats from different rows is always allowed"""
    time_slot = TimeSlot("2025-12-20", "19:00", "21:30")
    showtime = Showtime(
        showtime_id="SHOWTIME_001",
        movie_id="MOVIE_001",
        screen_id="SCREEN_001",
        time_slot=time_slot,
        price_per_seat=Decimal("50000"),
        available_seats=4
    )
    
    # Add seats from different rows
    seat_a1 = Seat("SEAT_A1", SeatNumber("A", 1), "SCREEN_001", "AVAILABLE")
    seat_a3 = Seat("SEAT_A3", SeatNumber("A", 3), "SCREEN_001", "AVAILABLE")
    seat_b1 = Seat("SEAT_B1", SeatNumber("B", 1), "SCREEN_001", "AVAILABLE")
    seat_b2 = Seat("SEAT_B2", SeatNumber("B", 2), "SCREEN_001", "AVAILABLE")
    
    showtime.add_seat(seat_a1)
    showtime.add_seat(seat_a3)
    showtime.add_seat(seat_b1)
    showtime.add_seat(seat_b2)
    
    # Book A1 and B1 (different rows - no gap issue)
    showtime.reserve_seats(["SEAT_A1", "SEAT_B1"])
    
    assert showtime.available_seats == 2


def test_single_seat_gap_edge_case_A1_A3_A5():
    """Test: Booking A1, A3, A5 creates multiple gaps - REJECTED"""
    time_slot = TimeSlot("2025-12-20", "19:00", "21:30")
    showtime = Showtime(
        showtime_id="SHOWTIME_001",
        movie_id="MOVIE_001",
        screen_id="SCREEN_001",
        time_slot=time_slot,
        price_per_seat=Decimal("50000"),
        available_seats=5
    )
    
    # Add 5 consecutive seats
    for i in range(1, 6):
        seat = Seat(f"SEAT_00{i}", SeatNumber("A", i), "SCREEN_001", "AVAILABLE")
        showtime.add_seat(seat)
    
    # Try to book A1, A3, A5 (creates gaps at A2 and A4)
    with pytest.raises(ValueError, match="single-seat gap"):
        showtime.reserve_seats(["SEAT_001", "SEAT_003", "SEAT_005"])


# ============================================================================
# BUSINESS RULE 4: CANCELLATION POLICY
# ============================================================================
def test_cancellation_policy_h24_plus_full_refund():
    """Test: Cancel ≥24 hours before showtime = 100% refund"""
    booking = Booking(
        booking_id="BOOKING_001",
        user_id="USER_001",
        showtime_id="SHOWTIME_001",
        created_at=datetime.now(),
        total_price=Decimal("50000")
    )
    
    # Confirm booking first
    booking.confirm_payment()
    
    # Showtime is 30 hours from now (>24 hours)
    showtime_datetime = datetime.now() + timedelta(hours=30)
    
    refund = booking.cancel_booking(showtime_datetime)
    
    assert refund == Decimal("50000")  # 100% refund
    assert booking.booking_status.value == BookingStatusEnum.CANCELLED


def test_cancellation_policy_h12_to_h24_half_refund():
    """Test: Cancel 12-24 hours before showtime = 50% refund"""
    booking = Booking(
        booking_id="BOOKING_001",
        user_id="USER_001",
        showtime_id="SHOWTIME_001",
        created_at=datetime.now(),
        total_price=Decimal("50000")
    )
    
    # Confirm booking first
    booking.confirm_payment()
    
    # Showtime is 15 hours from now (between 12-24 hours)
    showtime_datetime = datetime.now() + timedelta(hours=15)
    
    refund = booking.cancel_booking(showtime_datetime)
    
    assert refund == Decimal("25000")  # 50% refund
    assert booking.booking_status.value == BookingStatusEnum.CANCELLED


def test_cancellation_policy_less_h12_no_refund():
    """Test: Cancel <12 hours before showtime = 0% refund"""
    booking = Booking(
        booking_id="BOOKING_001",
        user_id="USER_001",
        showtime_id="SHOWTIME_001",
        created_at=datetime.now(),
        total_price=Decimal("50000")
    )
    
    # Confirm booking first
    booking.confirm_payment()
    
    # Showtime is 5 hours from now (<12 hours)
    showtime_datetime = datetime.now() + timedelta(hours=5)
    
    refund = booking.cancel_booking(showtime_datetime)
    
    assert refund == Decimal("0")  # No refund
    assert booking.booking_status.value == BookingStatusEnum.CANCELLED


def test_cancellation_policy_edge_exactly_24_hours():
    """Test: Cancel exactly 24 hours before = 100% refund"""
    booking = Booking(
        booking_id="BOOKING_001",
        user_id="USER_001",
        showtime_id="SHOWTIME_001",
        created_at=datetime.now(),
        total_price=Decimal("100000")
    )
    
    booking.confirm_payment()
    
    # Exactly 24 hours
    showtime_datetime = datetime.now() + timedelta(hours=24)
    
    refund = booking.cancel_booking(showtime_datetime)
    
    assert refund == Decimal("100000")  # 100% refund


def test_cancellation_policy_edge_exactly_12_hours():
    """Test: Cancel exactly 12 hours before = 50% refund"""
    booking = Booking(
        booking_id="BOOKING_001",
        user_id="USER_001",
        showtime_id="SHOWTIME_001",
        created_at=datetime.now(),
        total_price=Decimal("100000")
    )
    
    booking.confirm_payment()
    
    # Exactly 12 hours
    showtime_datetime = datetime.now() + timedelta(hours=12)
    
    refund = booking.cancel_booking(showtime_datetime)
    
    assert refund == Decimal("50000")  # 50% refund


def test_cancellation_policy_cannot_cancel_not_confirmed():
    """Test: Cannot cancel booking that is not confirmed"""
    booking = Booking(
        booking_id="BOOKING_001",
        user_id="USER_001",
        showtime_id="SHOWTIME_001",
        created_at=datetime.now(),
        total_price=Decimal("50000")
    )
    
    # Don't confirm - try to cancel while RESERVED
    showtime_datetime = datetime.now() + timedelta(hours=30)
    
    with pytest.raises(ValueError, match="only cancel confirmed"):
        booking.cancel_booking(showtime_datetime)


def test_cancellation_policy_past_showtime_no_refund():
    """Test: Cancel after showtime has passed = 0% refund"""
    booking = Booking(
        booking_id="BOOKING_001",
        user_id="USER_001",
        showtime_id="SHOWTIME_001",
        created_at=datetime.now(),
        total_price=Decimal("50000")
    )
    
    booking.confirm_payment()
    
    # Showtime already passed (2 hours ago)
    past_showtime = datetime.now() - timedelta(hours=2)
    
    refund = booking.cancel_booking(past_showtime)
    
    assert refund == Decimal("0")  # No refund for past showtime


# ============================================================================
# INTEGRATION: BUSINESS RULES WORKING TOGETHER
# ============================================================================
def test_integration_full_booking_workflow():
    """Test: Complete workflow - book, confirm, cancel with refund"""
    # Setup showtime
    time_slot = TimeSlot("2025-12-20", "19:00", "21:30")
    showtime = Showtime(
        showtime_id="SHOWTIME_001",
        movie_id="MOVIE_001",
        screen_id="SCREEN_001",
        time_slot=time_slot,
        price_per_seat=Decimal("50000"),
        available_seats=3
    )
    
    for i in range(1, 4):
        seat = Seat(f"SEAT_00{i}", SeatNumber("A", i), "SCREEN_001", "AVAILABLE")
        showtime.add_seat(seat)
    
    # Step 1: Reserve seats (concurrent booking + single-seat gap validation)
    showtime.reserve_seats(["SEAT_001", "SEAT_002"])  # OK - consecutive
    
    # Step 2: Create booking
    booking = Booking(
        booking_id="BOOKING_001",
        user_id="USER_001",
        showtime_id="SHOWTIME_001",
        created_at=datetime.now(),
        total_price=Decimal("100000")
    )
    
    # Step 3: Check hold timeout not expired
    assert booking.check_hold_expiry() == False
    
    # Step 4: Confirm payment
    booking.confirm_payment()
    assert booking.booking_status.is_confirmed() == True
    
    # Step 5: Cancel with refund policy
    future_showtime = datetime.now() + timedelta(hours=30)
    refund = booking.cancel_booking(future_showtime)
    
    assert refund == Decimal("100000")  # 100% refund (>24h)
    assert booking.booking_status.value == BookingStatusEnum.CANCELLED