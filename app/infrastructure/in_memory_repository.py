from typing import Dict, List, Optional
from datetime import datetime
from decimal import Decimal
from app.domain.aggregates import Booking, Showtime
from app.domain.entities import Seat
from app.domain.value_objects import SeatNumber, TimeSlot
from app.auth.models import User
from app.auth.jwt_handler import get_password_hash


class InMemoryRepository:
    """Simple in-memory storage for demo"""
    
    def __init__(self):
        self.bookings: Dict[str, Booking] = {}
        self.showtimes: Dict[str, Showtime] = {}
        self.users: Dict[str, User] = {}  # username -> User
        self._initialize_sample_data()
    
    def _initialize_sample_data(self):
        """Initialize with sample showtime, seats, and demo users"""
        # Initialize demo users
        self._initialize_demo_users()
        
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
    
    def _initialize_demo_users(self):
        """Initialize demo users for testing"""
        demo_users = [
            {
                "user_id": "USR001",
                "username": "user1",
                "password": "password123",
                "full_name": "John Doe"
            },
            {
                "user_id": "USR002",
                "username": "user2",
                "password": "password456",
                "full_name": "Jane Smith"
            },
            {
                "user_id": "USR003",
                "username": "testuser",
                "password": "test123",
                "full_name": "Test User"
            }
        ]
        
        for user_data in demo_users:
            user = User(
                user_id=user_data["user_id"],
                username=user_data["username"],
                password_hash=get_password_hash(user_data["password"]),
                full_name=user_data["full_name"]
            )
            self.users[user.username] = user
    
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
    
    # User Repository Methods
    def get_user_by_username(self, username: str) -> Optional[User]:
        return self.users.get(username)
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        for user in self.users.values():
            if user.user_id == user_id:
                return user
        return None


# Global repository instance
repository = InMemoryRepository()
