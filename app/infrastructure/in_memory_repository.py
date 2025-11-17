from typing import Dict, List, Optional
from datetime import datetime
from decimal import Decimal
from app.domain.aggregates import Booking, Showtime
from app.domain.entities import Seat
from app.domain.value_objects import SeatNumber, TimeSlot


class InMemoryRepository:
    """Simple in-memory storage for demo"""
    
    def __init__(self):
        self.bookings: Dict[str, Booking] = {}
        self.showtimes: Dict[str, Showtime] = {}
        self._initialize_sample_data()
    
    def _initialize_sample_data(self):
        """Initialize with sample showtime and seats"""
        # Create sample showtime
        time_slot = TimeSlot(
            date="2025-11-15",
            start_time="19:00",
            end_time="21:30"
        )
        
        showtime = Showtime(
            showtime_id="ST20251115190001",
            movie_id="MOV_ZOOTOPIA2",
            screen_id="SCR1",
            time_slot=time_slot,
            price_per_seat=Decimal("50000.00"),
            available_seats=10
        )
        
        # Add sample seats (Row A, columns 1-10)
        for col in range(1, 11):
            seat_number = SeatNumber("A", col)
            seat = Seat(
                seat_id=f"SEAT_SCR1_A{col}",
                seat_number=seat_number,
                screen_id="SCR1",
                status="AVAILABLE"
            )
            showtime.add_seat(seat)
        
        self.showtimes[showtime.showtime_id] = showtime
    
    # Booking Repository Methods
    def save_booking(self, booking: Booking) -> None:
        self.bookings[booking.booking_id] = booking
    
    def get_booking(self, booking_id: str) -> Optional[Booking]:
        return self.bookings.get(booking_id)
    
    def get_all_bookings(self) -> List[Booking]:
        return list(self.bookings.values())
    
    # Showtime Repository Methods
    def get_showtime(self, showtime_id: str) -> Optional[Showtime]:
        return self.showtimes.get(showtime_id)
    
    def get_all_showtimes(self) -> List[Showtime]:
        return list(self.showtimes.values())


# Global repository instance
repository = InMemoryRepository()