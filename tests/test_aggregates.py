"""
Test Aggregates: Booking and Showtime
"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from app.domain.aggregates import Booking, Showtime
from app.domain.entities import Seat, BookingItem
from app.domain.value_objects import (
    SeatNumber, TimeSlot, BookingStatus, 
    BookingStatusEnum, HoldExpiry
)


# ============================================================================
# BOOKING AGGREGATE TESTS
# ============================================================================
def test_booking_creation():
    """Test: Create a booking"""
    created_at = datetime.now()
    booking = Booking(
        booking_id="BOOKING_001",
        user_id="USER_001",
        showtime_id="SHOWTIME_001",
        created_at=created_at,
        total_price=Decimal("100000")
    )
    
    assert booking.booking_id == "BOOKING_001"
    assert booking.user_id == "USER_001"
    assert booking.showtime_id == "SHOWTIME_001"
    assert booking.created_at == created_at
    assert booking.total_price == Decimal("100000")
    assert booking.booking_status.is_reserved() == True


def test_booking_initial_status_reserved():
    """Test: New booking starts with RESERVED status"""
    booking = Booking(
        booking_id="BOOKING_001",
        user_id="USER_001",
        showtime_id="SHOWTIME_001",
        created_at=datetime.now(),
        total_price=Decimal("50000")
    )
    
    assert booking.booking_status.value == BookingStatusEnum.RESERVED


def test_booking_hold_expiry_set():
    """Test: Hold expiry is set to 10 minutes after creation"""
    created_at = datetime.now()
    booking = Booking(
        booking_id="BOOKING_001",
        user_id="USER_001",
        showtime_id="SHOWTIME_001",
        created_at=created_at,
        total_price=Decimal("50000")
    )
    
    expected_expiry = created_at + timedelta(minutes=10)
    assert booking.hold_expiry.expiry_time == expected_expiry


def test_booking_add_item():
    """Test: Add booking item to booking"""
    booking = Booking(
        booking_id="BOOKING_001",
        user_id="USER_001",
        showtime_id="SHOWTIME_001",
        created_at=datetime.now(),
        total_price=Decimal("50000")
    )
    
    item = BookingItem(
        booking_item_id="ITEM_001",
        booking_id="BOOKING_001",
        seat_id="SEAT_001",
        price=Decimal("50000")
    )
    
    booking.add_booking_item(item)
    
    items = booking.get_booking_items()
    assert len(items) == 1
    assert items[0].booking_item_id == "ITEM_001"


def test_booking_calculate_total_price():
    """Test: Calculate total price from booking items"""
    booking = Booking(
        booking_id="BOOKING_001",
        user_id="USER_001",
        showtime_id="SHOWTIME_001",
        created_at=datetime.now(),
        total_price=Decimal("0")
    )
    
    item1 = BookingItem("ITEM_001", "BOOKING_001", "SEAT_001", Decimal("50000"))
    item2 = BookingItem("ITEM_002", "BOOKING_001", "SEAT_002", Decimal("50000"))
    
    booking.add_booking_item(item1)
    booking.add_booking_item(item2)
    
    total = booking.calculate_total_price()
    assert total == Decimal("100000")


def test_booking_confirm_payment_success():
    """Test: Confirm payment for reserved booking"""
    booking = Booking(
        booking_id="BOOKING_001",
        user_id="USER_001",
        showtime_id="SHOWTIME_001",
        created_at=datetime.now(),
        total_price=Decimal("50000")
    )
    
    booking.confirm_payment()
    
    assert booking.booking_status.is_confirmed() == True


def test_booking_confirm_payment_not_reserved():
    """Test: Cannot confirm payment if not reserved"""
    booking = Booking(
        booking_id="BOOKING_001",
        user_id="USER_001",
        showtime_id="SHOWTIME_001",
        created_at=datetime.now(),
        total_price=Decimal("50000")
    )
    
    # Force to CANCELLED
    booking.booking_status = BookingStatus(BookingStatusEnum.CANCELLED)
    
    with pytest.raises(ValueError, match="only confirm reserved"):
        booking.confirm_payment()


def test_booking_confirm_payment_expired():
    """Test: Cannot confirm payment if booking expired"""
    past_time = datetime.now() - timedelta(minutes=15)
    booking = Booking(
        booking_id="BOOKING_001",
        user_id="USER_001",
        showtime_id="SHOWTIME_001",
        created_at=past_time,
        total_price=Decimal("50000")
    )
    
    with pytest.raises(ValueError, match="expired"):
        booking.confirm_payment()


def test_booking_check_hold_expiry_not_expired():
    """Test: Check hold expiry for valid booking"""
    booking = Booking(
        booking_id="BOOKING_001",
        user_id="USER_001",
        showtime_id="SHOWTIME_001",
        created_at=datetime.now(),
        total_price=Decimal("50000")
    )
    
    is_expired = booking.check_hold_expiry()
    
    assert is_expired == False
    assert booking.booking_status.is_reserved() == True


def test_booking_check_hold_expiry_expired():
    """Test: Check hold expiry for expired booking"""
    past_time = datetime.now() - timedelta(minutes=15)
    booking = Booking(
        booking_id="BOOKING_001",
        user_id="USER_001",
        showtime_id="SHOWTIME_001",
        created_at=past_time,
        total_price=Decimal("50000")
    )
    
    is_expired = booking.check_hold_expiry()
    
    assert is_expired == True
    assert booking.booking_status.value == BookingStatusEnum.EXPIRED


def test_booking_issue_ticket_success():
    """Test: Issue ticket for confirmed booking"""
    booking = Booking(
        booking_id="BOOKING_001",
        user_id="USER_001",
        showtime_id="SHOWTIME_001",
        created_at=datetime.now(),
        total_price=Decimal("50000")
    )
    
    booking.confirm_payment()
    ticket = booking.issue_ticket()
    
    assert ticket.ticket_id == "TKT_BOOKING_001"
    assert ticket.booking_id == "BOOKING_001"
    assert ticket.qr_code.startswith("QR_BOOKING_001")
    assert ticket.is_valid == True


def test_booking_issue_ticket_not_confirmed():
    """Test: Cannot issue ticket if booking not confirmed"""
    booking = Booking(
        booking_id="BOOKING_001",
        user_id="USER_001",
        showtime_id="SHOWTIME_001",
        created_at=datetime.now(),
        total_price=Decimal("50000")
    )
    
    with pytest.raises(ValueError, match="confirmed bookings"):
        booking.issue_ticket()


# ============================================================================
# SHOWTIME AGGREGATE TESTS
# ============================================================================
def test_showtime_creation():
    """Test: Create a showtime"""
    time_slot = TimeSlot(
        date="2025-12-20",
        start_time="19:00",
        end_time="21:30"
    )
    
    showtime = Showtime(
        showtime_id="SHOWTIME_001",
        movie_id="MOVIE_001",
        screen_id="SCREEN_001",
        time_slot=time_slot,
        price_per_seat=Decimal("50000"),
        available_seats=10
    )
    
    assert showtime.showtime_id == "SHOWTIME_001"
    assert showtime.movie_id == "MOVIE_001"
    assert showtime.screen_id == "SCREEN_001"
    assert showtime.time_slot == time_slot
    assert showtime.price_per_seat == Decimal("50000")
    assert showtime.available_seats == 10


def test_showtime_add_seat():
    """Test: Add seat to showtime"""
    time_slot = TimeSlot("2025-12-20", "19:00", "21:30")
    showtime = Showtime(
        showtime_id="SHOWTIME_001",
        movie_id="MOVIE_001",
        screen_id="SCREEN_001",
        time_slot=time_slot,
        price_per_seat=Decimal("50000"),
        available_seats=10
    )
    
    seat_number = SeatNumber("A", 1)
    seat = Seat("SEAT_001", seat_number, "SCREEN_001", "AVAILABLE")
    
    showtime.add_seat(seat)
    
    seats = showtime.get_seats()
    assert len(seats) == 1
    assert seats[0].seat_id == "SEAT_001"


def test_showtime_check_seat_availability_all_available():
    """Test: Check availability when all seats are available"""
    time_slot = TimeSlot("2025-12-20", "19:00", "21:30")
    showtime = Showtime(
        showtime_id="SHOWTIME_001",
        movie_id="MOVIE_001",
        screen_id="SCREEN_001",
        time_slot=time_slot,
        price_per_seat=Decimal("50000"),
        available_seats=3
    )
    
    # Add 3 available seats
    for i in range(1, 4):
        seat_number = SeatNumber("A", i)
        seat = Seat(f"SEAT_00{i}", seat_number, "SCREEN_001", "AVAILABLE")
        showtime.add_seat(seat)
    
    is_available = showtime.check_seat_availability(["SEAT_001", "SEAT_002"])
    
    assert is_available == True


def test_showtime_check_seat_availability_some_unavailable():
    """Test: Check availability when some seats are not available"""
    time_slot = TimeSlot("2025-12-20", "19:00", "21:30")
    showtime = Showtime(
        showtime_id="SHOWTIME_001",
        movie_id="MOVIE_001",
        screen_id="SCREEN_001",
        time_slot=time_slot,
        price_per_seat=Decimal("50000"),
        available_seats=3
    )
    
    # Add seats, one reserved
    seat1 = Seat("SEAT_001", SeatNumber("A", 1), "SCREEN_001", "AVAILABLE")
    seat2 = Seat("SEAT_002", SeatNumber("A", 2), "SCREEN_001", "RESERVED")
    showtime.add_seat(seat1)
    showtime.add_seat(seat2)
    
    is_available = showtime.check_seat_availability(["SEAT_001", "SEAT_002"])
    
    assert is_available == False


def test_showtime_reserve_seats_success():
    """Test: Reserve available seats"""
    time_slot = TimeSlot("2025-12-20", "19:00", "21:30")
    showtime = Showtime(
        showtime_id="SHOWTIME_001",
        movie_id="MOVIE_001",
        screen_id="SCREEN_001",
        time_slot=time_slot,
        price_per_seat=Decimal("50000"),
        available_seats=3
    )
    
    # Add 3 consecutive seats
    for i in range(1, 4):
        seat_number = SeatNumber("A", i)
        seat = Seat(f"SEAT_00{i}", seat_number, "SCREEN_001", "AVAILABLE")
        showtime.add_seat(seat)
    
    showtime.reserve_seats(["SEAT_001", "SEAT_002"])
    
    assert showtime.available_seats == 1
    seats = showtime.get_seats()
    assert seats[0].status == "RESERVED"
    assert seats[1].status == "RESERVED"


def test_showtime_reserve_seats_unavailable():
    """Test: Cannot reserve unavailable seats"""
    time_slot = TimeSlot("2025-12-20", "19:00", "21:30")
    showtime = Showtime(
        showtime_id="SHOWTIME_001",
        movie_id="MOVIE_001",
        screen_id="SCREEN_001",
        time_slot=time_slot,
        price_per_seat=Decimal("50000"),
        available_seats=2
    )
    
    seat1 = Seat("SEAT_001", SeatNumber("A", 1), "SCREEN_001", "RESERVED")
    showtime.add_seat(seat1)
    
    with pytest.raises(ValueError, match="not available"):
        showtime.reserve_seats(["SEAT_001"])


def test_showtime_confirm_seats():
    """Test: Confirm reserved seats"""
    time_slot = TimeSlot("2025-12-20", "19:00", "21:30")
    showtime = Showtime(
        showtime_id="SHOWTIME_001",
        movie_id="MOVIE_001",
        screen_id="SCREEN_001",
        time_slot=time_slot,
        price_per_seat=Decimal("50000"),
        available_seats=2
    )
    
    seat1 = Seat("SEAT_001", SeatNumber("A", 1), "SCREEN_001", "RESERVED")
    showtime.add_seat(seat1)
    
    showtime.confirm_seats(["SEAT_001"])
    
    seats = showtime.get_seats()
    assert seats[0].status == "BOOKED"


def test_showtime_release_seats():
    """Test: Release reserved seats"""
    time_slot = TimeSlot("2025-12-20", "19:00", "21:30")
    showtime = Showtime(
        showtime_id="SHOWTIME_001",
        movie_id="MOVIE_001",
        screen_id="SCREEN_001",
        time_slot=time_slot,
        price_per_seat=Decimal("50000"),
        available_seats=0
    )
    
    seat1 = Seat("SEAT_001", SeatNumber("A", 1), "SCREEN_001", "RESERVED")
    seat2 = Seat("SEAT_002", SeatNumber("A", 2), "SCREEN_001", "RESERVED")
    showtime.add_seat(seat1)
    showtime.add_seat(seat2)
    
    showtime.release_seats(["SEAT_001", "SEAT_002"])
    
    assert showtime.available_seats == 2
    seats = showtime.get_seats()
    assert seats[0].status == "AVAILABLE"
    assert seats[1].status == "AVAILABLE"