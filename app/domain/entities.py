from datetime import datetime
from decimal import Decimal
from app.domain.value_objects import SeatNumber


class Seat:
    """Entity"""
    def __init__(
        self,
        seat_id: str,
        seat_number: SeatNumber,
        screen_id: str,
        status: str = "AVAILABLE"
    ):
        self.seat_id = seat_id
        self.seat_number = seat_number
        self.screen_id = screen_id
        self.status = status  # AVAILABLE, RESERVED, BOOKED, BLOCKED
    
    def reserve(self) -> None:
        if self.status != "AVAILABLE":
            raise ValueError(f"Seat {self.seat_number} is not available")
        self.status = "RESERVED"
    
    def confirm(self) -> None:
        if self.status != "RESERVED":
            raise ValueError(f"Seat {self.seat_number} is not reserved")
        self.status = "BOOKED"
    
    def release(self) -> None:
        if self.status in ["RESERVED", "BOOKED"]:
            self.status = "AVAILABLE"
    
    def adjust_status(self, new_status: str) -> None:
        self.status = new_status


class BookingItem:
    """Entity - Member of Booking Aggregate"""
    def __init__(
        self,
        booking_item_id: str,
        booking_id: str,
        seat_id: str,
        price: Decimal
    ):
        self.booking_item_id = booking_item_id
        self.booking_id = booking_id
        self.seat_id = seat_id
        self.price = price
    
    def get_price(self) -> Decimal:
        return self.price


class Ticket:
    """Entity"""
    def __init__(
        self,
        ticket_id: str,
        booking_id: str,
        qr_code: str,
        issued_at: datetime,
        is_valid: bool = True
    ):
        self.ticket_id = ticket_id
        self.booking_id = booking_id
        self.qr_code = qr_code
        self.issued_at = issued_at
        self.is_valid = is_valid
    
    def validate_ticket(self) -> bool:
        return self.is_valid
    
    def invalidate_ticket(self) -> None:
        self.is_valid = False