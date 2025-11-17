from datetime import datetime
from enum import Enum


class BookingStatusEnum(str, Enum):
    RESERVED = "RESERVED"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class SeatNumber:
    """Value Object - Immutable"""
    def __init__(self, row: str, column: int):
        if not row or not isinstance(column, int):
            raise ValueError("Invalid seat number")
        self._row = row
        self._column = column
    
    @property
    def row(self) -> str:
        return self._row
    
    @property
    def column(self) -> int:
        return self._column
    
    def __str__(self) -> str:
        return f"{self._row}{self._column}"
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, SeatNumber):
            return False
        return self._row == other._row and self._column == other._column
    
    def __hash__(self):
        return hash((self._row, self._column))


class TimeSlot:
    """Value Object - Immutable"""
    def __init__(self, date: str, start_time: str, end_time: str):
        self._date = date
        self._start_time = start_time
        self._end_time = end_time
    
    @property
    def date(self) -> str:
        return self._date
    
    @property
    def start_time(self) -> str:
        return self._start_time
    
    @property
    def end_time(self) -> str:
        return self._end_time
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, TimeSlot):
            return False
        return (self._date == other._date and 
                self._start_time == other._start_time and
                self._end_time == other._end_time)


class BookingStatus:
    """Value Object - Immutable"""
    def __init__(self, value: BookingStatusEnum):
        self._value = value
    
    @property
    def value(self) -> BookingStatusEnum:
        return self._value
    
    def is_reserved(self) -> bool:
        return self._value == BookingStatusEnum.RESERVED
    
    def is_confirmed(self) -> bool:
        return self._value == BookingStatusEnum.CONFIRMED
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, BookingStatus):
            return False
        return self._value == other._value


class HoldExpiry:
    """Value Object - Immutable"""
    def __init__(self, expiry_time: datetime):
        self._expiry_time = expiry_time
    
    @property
    def expiry_time(self) -> datetime:
        return self._expiry_time
    
    def is_expired(self) -> bool:
        return datetime.now() > self._expiry_time
    
    def get_remaining_time(self) -> float:
        """Returns remaining time in seconds"""
        delta = self._expiry_time - datetime.now()
        return max(0, delta.total_seconds())