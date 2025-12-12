"""
Test Value Objects: SeatNumber, TimeSlot, BookingStatus, HoldExpiry
"""
import pytest
from datetime import datetime, timedelta
from app.domain.value_objects import (
    SeatNumber, 
    TimeSlot, 
    BookingStatus, 
    BookingStatusEnum,
    HoldExpiry
)


# ============================================================================
# SEATNUMBER TESTS
# ============================================================================
def test_seat_number_creation():
    """Test: Create valid seat number"""
    seat = SeatNumber("A", 1)
    
    assert seat.row == "A"
    assert seat.column == 1


def test_seat_number_string_representation():
    """Test: Seat number string format"""
    seat = SeatNumber("B", 5)
    
    assert str(seat) == "B5"


def test_seat_number_equality():
    """Test: Two seat numbers with same values are equal"""
    seat1 = SeatNumber("A", 1)
    seat2 = SeatNumber("A", 1)
    
    assert seat1 == seat2


def test_seat_number_inequality():
    """Test: Two seat numbers with different values are not equal"""
    seat1 = SeatNumber("A", 1)
    seat2 = SeatNumber("A", 2)
    seat3 = SeatNumber("B", 1)
    
    assert seat1 != seat2
    assert seat1 != seat3


def test_seat_number_hash():
    """Test: Seat numbers can be used in sets/dicts"""
    seat1 = SeatNumber("A", 1)
    seat2 = SeatNumber("A", 1)
    seat3 = SeatNumber("B", 2)
    
    seat_set = {seat1, seat2, seat3}
    assert len(seat_set) == 2  # seat1 and seat2 are same


def test_seat_number_invalid_row():
    """Test: Invalid row raises ValueError"""
    with pytest.raises(ValueError, match="Invalid seat number"):
        SeatNumber("", 1)


def test_seat_number_invalid_column():
    """Test: Invalid column type raises ValueError"""
    with pytest.raises(ValueError, match="Invalid seat number"):
        SeatNumber("A", "invalid")


# ============================================================================
# TIMESLOT TESTS
# ============================================================================
def test_timeslot_creation():
    """Test: Create valid time slot"""
    slot = TimeSlot(
        date="2025-12-20",
        start_time="19:00",
        end_time="21:30"
    )
    
    assert slot.date == "2025-12-20"
    assert slot.start_time == "19:00"
    assert slot.end_time == "21:30"


def test_timeslot_equality():
    """Test: Two time slots with same values are equal"""
    slot1 = TimeSlot(date="2025-12-20", start_time="19:00", end_time="21:30")
    slot2 = TimeSlot(date="2025-12-20", start_time="19:00", end_time="21:30")
    
    assert slot1 == slot2


def test_timeslot_inequality():
    """Test: Two time slots with different values are not equal"""
    slot1 = TimeSlot(date="2025-12-20", start_time="19:00", end_time="21:30")
    slot2 = TimeSlot(date="2025-12-21", start_time="19:00", end_time="21:30")
    
    assert slot1 != slot2


# ============================================================================
# BOOKINGSTATUS TESTS
# ============================================================================
def test_booking_status_reserved():
    """Test: Create RESERVED status"""
    status = BookingStatus(BookingStatusEnum.RESERVED)
    
    assert status.value == BookingStatusEnum.RESERVED
    assert status.is_reserved() == True
    assert status.is_confirmed() == False


def test_booking_status_confirmed():
    """Test: Create CONFIRMED status"""
    status = BookingStatus(BookingStatusEnum.CONFIRMED)
    
    assert status.value == BookingStatusEnum.CONFIRMED
    assert status.is_confirmed() == True
    assert status.is_reserved() == False


def test_booking_status_cancelled():
    """Test: Create CANCELLED status"""
    status = BookingStatus(BookingStatusEnum.CANCELLED)
    
    assert status.value == BookingStatusEnum.CANCELLED


def test_booking_status_expired():
    """Test: Create EXPIRED status"""
    status = BookingStatus(BookingStatusEnum.EXPIRED)
    
    assert status.value == BookingStatusEnum.EXPIRED


def test_booking_status_equality():
    """Test: Two booking statuses with same value are equal"""
    status1 = BookingStatus(BookingStatusEnum.CONFIRMED)
    status2 = BookingStatus(BookingStatusEnum.CONFIRMED)
    
    assert status1 == status2


def test_booking_status_inequality():
    """Test: Two booking statuses with different values are not equal"""
    status1 = BookingStatus(BookingStatusEnum.RESERVED)
    status2 = BookingStatus(BookingStatusEnum.CONFIRMED)
    
    assert status1 != status2


# ============================================================================
# HOLDEXPIRY TESTS
# ============================================================================
def test_hold_expiry_creation():
    """Test: Create hold expiry"""
    expiry_time = datetime.now() + timedelta(minutes=10)
    hold = HoldExpiry(expiry_time)
    
    assert hold.expiry_time == expiry_time


def test_hold_expiry_not_expired():
    """Test: Hold expiry that hasn't expired yet"""
    future_time = datetime.now() + timedelta(minutes=5)
    hold = HoldExpiry(future_time)
    
    assert hold.is_expired() == False


def test_hold_expiry_expired():
    """Test: Hold expiry that has expired"""
    past_time = datetime.now() - timedelta(minutes=5)
    hold = HoldExpiry(past_time)
    
    assert hold.is_expired() == True


def test_hold_expiry_remaining_time_positive():
    """Test: Remaining time for valid hold"""
    future_time = datetime.now() + timedelta(minutes=5)
    hold = HoldExpiry(future_time)
    
    remaining = hold.get_remaining_time()
    assert remaining > 0
    assert remaining <= 300  # 5 minutes in seconds


def test_hold_expiry_remaining_time_zero():
    """Test: Remaining time for expired hold returns 0"""
    past_time = datetime.now() - timedelta(minutes=5)
    hold = HoldExpiry(past_time)
    
    remaining = hold.get_remaining_time()
    assert remaining == 0