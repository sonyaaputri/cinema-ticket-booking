from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from app.infrastructure.in_memory_repository import repository

router = APIRouter(prefix="/api/showtimes", tags=["Showtimes"])


class SeatResponse(BaseModel):
    seat_id: str
    seat_number: str
    status: str


class ShowtimeResponse(BaseModel):
    showtime_id: str
    movie_id: str
    screen_id: str
    date: str
    start_time: str
    end_time: str
    price_per_seat: str
    available_seats: int


class ShowtimeDetailResponse(ShowtimeResponse):
    seats: List[SeatResponse]


@router.get("/", response_model=List[ShowtimeResponse])
def get_all_showtimes():
    """Get all available showtimes"""
    
    showtimes = repository.get_all_showtimes()
    
    return [
        ShowtimeResponse(
            showtime_id=st.showtime_id,
            movie_id=st.movie_id,
            screen_id=st.screen_id,
            date=st.time_slot.date,
            start_time=st.time_slot.start_time,
            end_time=st.time_slot.end_time,
            price_per_seat=str(st.price_per_seat),
            available_seats=st.available_seats
        )
        for st in showtimes
    ]


@router.get("/{showtime_id}", response_model=ShowtimeDetailResponse)
def get_showtime_detail(showtime_id: str):
    """Get showtime details with seat availability"""
    
    showtime = repository.get_showtime(showtime_id)
    if not showtime:
        raise HTTPException(status_code=404, detail="Showtime not found")
    
    seats = [
        SeatResponse(
            seat_id=seat.seat_id,
            seat_number=str(seat.seat_number),
            status=seat.status
        )
        for seat in showtime.get_seats()
    ]
    
    return ShowtimeDetailResponse(
        showtime_id=showtime.showtime_id,
        movie_id=showtime.movie_id,
        screen_id=showtime.screen_id,
        date=showtime.time_slot.date,
        start_time=showtime.time_slot.start_time,
        end_time=showtime.time_slot.end_time,
        price_per_seat=str(showtime.price_per_seat),
        available_seats=showtime.available_seats,
        seats=seats
    )