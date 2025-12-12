"""
Test Entities: Seat, BookingItem, Ticket
"""
import pytest
from datetime import datetime
from decimal import Decimal
from app.domain.entities import Seat, BookingItem, Ticket
from app.domain.value_objects import SeatNumber


# ============================================================================
# SEAT TESTS
# ============================================================================
def test_seat_creation():
    """Test: Create a seat"""
    seat_number = SeatNumber("A", 1)
    seat = Seat(
        seat_id="SEAT_001",
        seat_number=seat_number,
        screen_id="SCREEN_1",
        status="AVAILABLE"
    )
    
    assert seat.seat_id == "SEAT_001"
    assert seat.seat_number == seat_number
    assert seat.screen_id == "SCREEN_1"
    assert seat.status == "AVAILABLE"


def test_seat_reserve():
    """Test: Reserve an available seat"""
    seat_number = SeatNumber("A", 1)
    seat = Seat(
        seat_id="SEAT_001",
        seat_number=seat_number,
        screen_id="SCREEN_1",
        status="AVAILABLE"
    )
    
    seat.reserve()
    
    assert seat.status == "RESERVED"


def test_seat_reserve_already_reserved():
    """Test: Cannot reserve a non-available seat"""
    seat_number = SeatNumber("A", 1)
    seat = Seat(
        seat_id="SEAT_001",
        seat_number=seat_number,
        screen_id="SCREEN_1",
        status="RESERVED"
    )
    
    with pytest.raises(ValueError, match="not available"):
        seat.reserve()


def test_seat_confirm():
    """Test: Confirm a reserved seat"""
    seat_number = SeatNumber("A", 1)
    seat = Seat(
        seat_id="SEAT_001",
        seat_number=seat_number,
        screen_id="SCREEN_1",
        status="RESERVED"
    )
    
    seat.confirm()
    
    assert seat.status == "BOOKED"


def test_seat_confirm_not_reserved():
    """Test: Cannot confirm a non-reserved seat"""
    seat_number = SeatNumber("A", 1)
    seat = Seat(
        seat_id="SEAT_001",
        seat_number=seat_number,
        screen_id="SCREEN_1",
        status="AVAILABLE"
    )
    
    with pytest.raises(ValueError, match="not reserved"):
        seat.confirm()


def test_seat_release_from_reserved():
    """Test: Release a reserved seat"""
    seat_number = SeatNumber("A", 1)
    seat = Seat(
        seat_id="SEAT_001",
        seat_number=seat_number,
        screen_id="SCREEN_1",
        status="RESERVED"
    )
    
    seat.release()
    
    assert seat.status == "AVAILABLE"


def test_seat_release_from_booked():
    """Test: Release a booked seat"""
    seat_number = SeatNumber("A", 1)
    seat = Seat(
        seat_id="SEAT_001",
        seat_number=seat_number,
        screen_id="SCREEN_1",
        status="BOOKED"
    )
    
    seat.release()
    
    assert seat.status == "AVAILABLE"


def test_seat_adjust_status():
    """Test: Adjust seat status"""
    seat_number = SeatNumber("A", 1)
    seat = Seat(
        seat_id="SEAT_001",
        seat_number=seat_number,
        screen_id="SCREEN_1",
        status="AVAILABLE"
    )
    
    seat.adjust_status("BLOCKED")
    
    assert seat.status == "BLOCKED"


# ============================================================================
# BOOKINGITEM TESTS
# ============================================================================
def test_booking_item_creation():
    """Test: Create a booking item"""
    item = BookingItem(
        booking_item_id="ITEM_001",
        booking_id="BOOKING_001",
        seat_id="SEAT_001",
        price=Decimal("50000")
    )
    
    assert item.booking_item_id == "ITEM_001"
    assert item.booking_id == "BOOKING_001"
    assert item.seat_id == "SEAT_001"
    assert item.price == Decimal("50000")


def test_booking_item_get_price():
    """Test: Get price from booking item"""
    item = BookingItem(
        booking_item_id="ITEM_001",
        booking_id="BOOKING_001",
        seat_id="SEAT_001",
        price=Decimal("55000")
    )
    
    assert item.get_price() == Decimal("55000")


# ============================================================================
# TICKET TESTS
# ============================================================================
def test_ticket_creation():
    """Test: Create a ticket"""
    issued_at = datetime.now()
    ticket = Ticket(
        ticket_id="TICKET_001",
        booking_id="BOOKING_001",
        qr_code="QR_12345",
        issued_at=issued_at,
        is_valid=True
    )
    
    assert ticket.ticket_id == "TICKET_001"
    assert ticket.booking_id == "BOOKING_001"
    assert ticket.qr_code == "QR_12345"
    assert ticket.issued_at == issued_at
    assert ticket.is_valid == True


def test_ticket_validate_valid():
    """Test: Validate a valid ticket"""
    ticket = Ticket(
        ticket_id="TICKET_001",
        booking_id="BOOKING_001",
        qr_code="QR_12345",
        issued_at=datetime.now(),
        is_valid=True
    )
    
    assert ticket.validate_ticket() == True


def test_ticket_validate_invalid():
    """Test: Validate an invalid ticket"""
    ticket = Ticket(
        ticket_id="TICKET_001",
        booking_id="BOOKING_001",
        qr_code="QR_12345",
        issued_at=datetime.now(),
        is_valid=False
    )
    
    assert ticket.validate_ticket() == False


def test_ticket_invalidate():
    """Test: Invalidate a ticket"""
    ticket = Ticket(
        ticket_id="TICKET_001",
        booking_id="BOOKING_001",
        qr_code="QR_12345",
        issued_at=datetime.now(),
        is_valid=True
    )
    
    ticket.invalidate_ticket()
    
    assert ticket.is_valid == False
    assert ticket.validate_ticket() == False