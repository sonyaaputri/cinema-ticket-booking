from datetime import datetime, timedelta
from decimal import Decimal
from typing import List
from app.domain.entities import Seat, BookingItem, Ticket
from app.domain.value_objects import (
    SeatNumber, TimeSlot, BookingStatus, 
    HoldExpiry, BookingStatusEnum
)


class Showtime:
    """Aggregate Root - Showtime Aggregate"""
    def __init__(
        self,
        showtime_id: str,
        movie_id: str,
        screen_id: str,
        time_slot: TimeSlot,
        price_per_seat: Decimal,
        available_seats: int
    ):
        self.showtime_id = showtime_id
        self.movie_id = movie_id
        self.screen_id = screen_id
        self.time_slot = time_slot
        self.price_per_seat = price_per_seat
        self.available_seats = available_seats
        self._seats: List[Seat] = []
    
    def add_seat(self, seat: Seat) -> None:
        """Add seat to showtime"""
        self._seats.append(seat)
    
    def get_seats(self) -> List[Seat]:
        return self._seats.copy()
    
    def check_seat_availability(self, seat_ids: List[str]) -> bool:
        """Check if requested seats are available"""
        for seat_id in seat_ids:
            seat = next((s for s in self._seats if s.seat_id == seat_id), None)
            if not seat or seat.status != "AVAILABLE":
                return False
        return True
    
    def validate_no_single_seat_gap(self, seat_ids: List[str]) -> bool:
        """
        Prevent single-seat gap business rule
        Returns True if booking is valid (no single gaps created)
        """
        # Simplified validation - in real system, check adjacent seats
        return True
    
    def reserve_seats(self, seat_ids: List[str]) -> None:
        """Reserve seats for booking"""
        if not self.check_seat_availability(seat_ids):
            raise ValueError("One or more seats are not available")
        
        if not self.validate_no_single_seat_gap(seat_ids):
            raise ValueError("Booking would create single-seat gap")
        
        for seat_id in seat_ids:
            seat = next((s for s in self._seats if s.seat_id == seat_id), None)
            if seat:
                seat.reserve()
        
        self.available_seats -= len(seat_ids)
    
    def confirm_seats(self, seat_ids: List[str]) -> None:
        """Confirm reserved seats"""
        for seat_id in seat_ids:
            seat = next((s for s in self._seats if s.seat_id == seat_id), None)
            if seat:
                seat.confirm()
    
    def release_seats(self, seat_ids: List[str]) -> None:
        """Release reserved seats back to available"""
        for seat_id in seat_ids:
            seat = next((s for s in self._seats if s.seat_id == seat_id), None)
            if seat:
                seat.release()
        
        self.available_seats += len(seat_ids)


class Booking:
    """Aggregate Root - Booking Aggregate"""
    HOLD_TIMEOUT_MINUTES = 10
    
    def __init__(
        self,
        booking_id: str,
        user_id: str,
        showtime_id: str,
        created_at: datetime,
        total_price: Decimal
    ):
        self.booking_id = booking_id
        self.user_id = user_id
        self.showtime_id = showtime_id
        self.created_at = created_at
        self.total_price = total_price
        
        # Composed Value Objects
        self.booking_status = BookingStatus(BookingStatusEnum.RESERVED)
        expiry_time = created_at + timedelta(minutes=self.HOLD_TIMEOUT_MINUTES)
        self.hold_expiry = HoldExpiry(expiry_time)
        
        # Booking Items collection
        self._booking_items: List[BookingItem] = []
    
    def add_booking_item(self, item: BookingItem) -> None:
        """Add booking item to aggregate"""
        self._booking_items.append(item)
    
    def get_booking_items(self) -> List[BookingItem]:
        return self._booking_items.copy()
    
    def calculate_total_price(self) -> Decimal:
        """Calculate total from booking items"""
        return sum(item.get_price() for item in self._booking_items)
    
    def confirm_payment(self) -> None:
        """Confirm booking after successful payment"""
        if not self.booking_status.is_reserved():
            raise ValueError("Can only confirm reserved bookings")
        
        if self.hold_expiry.is_expired():
            raise ValueError("Booking hold has expired")
        
        self.booking_status = BookingStatus(BookingStatusEnum.CONFIRMED)
    
    def cancel_booking(self) -> Decimal:
        """
        Cancel booking with refund calculation
        Returns refund amount based on cancellation policy
        """
        if self.booking_status.is_confirmed():
            # Calculate refund based on time until showtime
            # Simplified: return full amount for now
            refund_amount = self.total_price
            self.booking_status = BookingStatus(BookingStatusEnum.CANCELLED)
            return refund_amount
        
        raise ValueError("Can only cancel confirmed bookings")
    
    def check_hold_expiry(self) -> bool:
        """Check if hold has expired"""
        if self.hold_expiry.is_expired() and self.booking_status.is_reserved():
            self.booking_status = BookingStatus(BookingStatusEnum.EXPIRED)
            return True
        return False
    
    def issue_ticket(self) -> Ticket:
        """Issue ticket after confirmation"""
        if not self.booking_status.is_confirmed():
            raise ValueError("Can only issue ticket for confirmed bookings")
        
        ticket_id = f"TKT_{self.booking_id}"
        qr_code = f"QR_{self.booking_id}_{datetime.now().timestamp()}"
        
        return Ticket(
            ticket_id=ticket_id,
            booking_id=self.booking_id,
            qr_code=qr_code,
            issued_at=datetime.now()
        )