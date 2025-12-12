from typing import Dict, List, Optional
from datetime import datetime, timedelta
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
        self.users: Dict[str, User] = {}
        self._initialize_sample_data()
    
    def _initialize_sample_data(self):
        """Initialize with sample showtime, seats, and demo users"""
        # Initialize demo users first
        self._initialize_demo_users()
        
        # Calculate future dates (7, 14, 21 days from now)
        today = datetime.now()
        date_1_week = (today + timedelta(days=7)).strftime("%Y-%m-%d")
        date_2_weeks = (today + timedelta(days=14)).strftime("%Y-%m-%d")
        date_3_weeks = (today + timedelta(days=21)).strftime("%Y-%m-%d")
        
        # ========================================================================
        # SHOWTIME 1 - Avengers: Endgame (1 week from now)
        # ========================================================================
        time_slot_1 = TimeSlot(
            date=date_1_week,
            start_time="19:00",
            end_time="22:00"
        )
        
        showtime_1 = Showtime(
            showtime_id="ST20251220190001",
            movie_id="MOV_AVENGERS",
            screen_id="SCR1",
            time_slot=time_slot_1,
            price_per_seat=Decimal("50000.00"),
            available_seats=10
        )
        
        # Add seats to showtime 1 (Row A, columns 1-10)
        for col in range(1, 11):
            seat_number = SeatNumber("A", col)
            seat = Seat(
                seat_id=f"SEAT_SCR1_A{col}",
                seat_number=seat_number,
                screen_id="SCR1",
                status="AVAILABLE"
            )
            showtime_1.add_seat(seat)
        
        # ========================================================================
        # SHOWTIME 2 - The Dark Knight (2 weeks from now)
        # ========================================================================
        time_slot_2 = TimeSlot(
            date=date_2_weeks,
            start_time="19:00",
            end_time="21:30"
        )
        
        showtime_2 = Showtime(
            showtime_id="ST20251227140002",
            movie_id="MOV_DARK_KNIGHT",
            screen_id="SCR2",
            time_slot=time_slot_2,
            price_per_seat=Decimal("55000.00"),
            available_seats=8
        )
        
        # Add seats to showtime 2 (Row B, columns 1-8)
        for col in range(1, 9):
            seat_number = SeatNumber("B", col)
            seat = Seat(
                seat_id=f"SEAT_SCR2_B{col}",
                seat_number=seat_number,
                screen_id="SCR2",
                status="AVAILABLE"
            )
            showtime_2.add_seat(seat)
        
        # ========================================================================
        # SHOWTIME 3 - Inception (3 weeks from now)
        # ========================================================================
        time_slot_3 = TimeSlot(
            date=date_3_weeks,
            start_time="20:00",
            end_time="22:30"
        )
        
        showtime_3 = Showtime(
            showtime_id="ST20260103200003",
            movie_id="MOV_INCEPTION",
            screen_id="SCR1",
            time_slot=time_slot_3,
            price_per_seat=Decimal("60000.00"),
            available_seats=10
        )
        
        # Add seats to showtime 3 (Row C, columns 1-10)
        for col in range(1, 11):
            seat_number = SeatNumber("C", col)
            seat = Seat(
                seat_id=f"SEAT_SCR1_C{col}",
                seat_number=seat_number,
                screen_id="SCR1",
                status="AVAILABLE"
            )
            showtime_3.add_seat(seat)
        
        # Store showtimes
        self.showtimes = {
            "ST20251220190001": showtime_1,
            "ST20251227140002": showtime_2,
            "ST20260103200003": showtime_3
        }
    
    def _initialize_demo_users(self):
        """Initialize demo users for testing"""
        demo_users_data = [
            {
                "user_id": "USR001",
                "username": "user1",
                "email": "user1@example.com",
                "password": "password123",
                "full_name": "John Doe"
            },
            {
                "user_id": "USR002",
                "username": "user2",
                "email": "user2@example.com",
                "password": "password456",
                "full_name": "Jane Smith"
            },
            {
                "user_id": "USR003",
                "username": "testuser",
                "email": "testuser@example.com",
                "password": "test123",
                "full_name": "Test User"
            }
        ]
        
        for user_data in demo_users_data:
            user = User(
                user_id=user_data["user_id"],
                username=user_data["username"],
                email=user_data["email"],
                password_hash=get_password_hash(user_data["password"]),
                full_name=user_data["full_name"]
            )
            self.users[user.user_id] = user
    
    # ========================================================================
    # BOOKING REPOSITORY METHODS
    # ========================================================================
    def save_booking(self, booking: Booking) -> None:
        """Save or update booking"""
        self.bookings[booking.booking_id] = booking
    
    def get_booking(self, booking_id: str) -> Optional[Booking]:
        """Get booking by ID"""
        return self.bookings.get(booking_id)
    
    def get_all_bookings(self) -> List[Booking]:
        """Get all bookings"""
        return list(self.bookings.values())
    
    # ========================================================================
    # SHOWTIME REPOSITORY METHODS
    # ========================================================================
    def get_showtime(self, showtime_id: str) -> Optional[Showtime]:
        """Get showtime by ID"""
        return self.showtimes.get(showtime_id)
    
    def get_all_showtimes(self) -> List[Showtime]:
        """Get all showtimes"""
        return list(self.showtimes.values())
    
    # ========================================================================
    # USER REPOSITORY METHODS
    # ========================================================================
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        for user in self.users.values():
            if user.username == username:
                return user
        return None
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by user_id"""
        return self.users.get(user_id)
    
    def add_user(self, user: User) -> User:
        """Add new user to repository"""
        self.users[user.user_id] = user
        return user


# Global repository instance
repository = InMemoryRepository()