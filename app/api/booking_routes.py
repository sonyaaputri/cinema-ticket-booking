from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from app.domain.aggregates import Booking
from app.domain.entities import BookingItem
from app.infrastructure.in_memory_repository import repository

router = APIRouter(prefix="/api/bookings", tags=["Bookings"])


# Request/Response Models
class CreateBookingRequest(BaseModel):
    user_id: str
    showtime_id: str
    seat_ids: List[str]


class BookingResponse(BaseModel):
    booking_id: str
    user_id: str
    showtime_id: str
    total_price: str
    status: str
    hold_expiry_time: str
    created_at: str
    seat_ids: List[str]
    message: Optional[str] = None


class ConfirmPaymentRequest(BaseModel):
    booking_id: str


class TicketResponse(BaseModel):
    ticket_id: str
    booking_id: str
    qr_code: str
    issued_at: str
    is_valid: bool
    message: str


class CancelResponse(BaseModel):
    message: str
    refund_amount: str
    booking_id: str


@router.post("/", response_model=BookingResponse)
def create_booking(request: CreateBookingRequest):
    """Create new booking with seat reservation"""
    
    # Get showtime
    showtime = repository.get_showtime(request.showtime_id)
    if not showtime:
        raise HTTPException(status_code=404, detail="Showtime not found")
    
    # Check seat availability
    if not showtime.check_seat_availability(request.seat_ids):
        raise HTTPException(
            status_code=400, 
            detail="One or more seats not available. Please choose different seats."
        )
    
    # Reserve seats in showtime
    try:
        showtime.reserve_seats(request.seat_ids)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Create booking
    booking_id = f"BK{datetime.now().strftime('%Y%m%d%H%M%S')}"
    total_price = showtime.price_per_seat * len(request.seat_ids)
    
    booking = Booking(
        booking_id=booking_id,
        user_id=request.user_id,
        showtime_id=request.showtime_id,
        created_at=datetime.now(),
        total_price=total_price
    )
    
    # Add booking items
    for seat_id in request.seat_ids:
        item_id = f"{booking_id}_{seat_id}"
        item = BookingItem(
            booking_item_id=item_id,
            booking_id=booking_id,
            seat_id=seat_id,
            price=showtime.price_per_seat
        )
        booking.add_booking_item(item)
    
    # Save booking
    repository.save_booking(booking)
    
    # Calculate remaining time
    remaining_seconds = int(booking.hold_expiry.get_remaining_time())
    remaining_minutes = remaining_seconds // 60
    
    return BookingResponse(
        booking_id=booking.booking_id,
        user_id=booking.user_id,
        showtime_id=booking.showtime_id,
        total_price=str(booking.total_price),
        status=booking.booking_status.value.value,
        hold_expiry_time=booking.hold_expiry.expiry_time.isoformat(),
        created_at=booking.created_at.isoformat(),
        seat_ids=request.seat_ids,
        message=f"Booking successful! Please complete payment within {remaining_minutes} minutes to confirm your booking. Your seats are temporarily reserved."
    )


@router.post("/confirm-payment", response_model=TicketResponse)
def confirm_payment(request: ConfirmPaymentRequest):
    """Confirm payment and issue ticket"""
    
    booking = repository.get_booking(request.booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Check if expired
    if booking.check_hold_expiry():
        raise HTTPException(
            status_code=400, 
            detail="Booking has expired. Please create a new booking."
        )
    
    # Confirm booking
    try:
        booking.confirm_payment()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Confirm seats in showtime
    showtime = repository.get_showtime(booking.showtime_id)
    if showtime:
        seat_ids = [item.seat_id for item in booking.get_booking_items()]
        showtime.confirm_seats(seat_ids)
    
    # Issue ticket
    ticket = booking.issue_ticket()
    
    return TicketResponse(
        ticket_id=ticket.ticket_id,
        booking_id=ticket.booking_id,
        qr_code=ticket.qr_code,
        issued_at=ticket.issued_at.isoformat(),
        is_valid=ticket.is_valid,
        message="Payment confirmed successfully! Your ticket has been issued. Please save your QR code for check-in."
    )


@router.get("/{booking_id}", response_model=BookingResponse)
def get_booking(booking_id: str):
    """Get booking details"""
    
    booking = repository.get_booking(booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    seat_ids = [item.seat_id for item in booking.get_booking_items()]
    
    # Generate message based on status
    status = booking.booking_status.value.value
    if status == "RESERVED":
        remaining_seconds = int(booking.hold_expiry.get_remaining_time())
        if remaining_seconds > 0:
            remaining_minutes = remaining_seconds // 60
            message = f"Booking is reserved. Please complete payment within {remaining_minutes} minutes."
        else:
            message = "Booking has expired."
    elif status == "CONFIRMED":
        message = "Booking is confirmed. Ticket has been issued."
    elif status == "CANCELLED":
        message = "Booking has been cancelled."
    elif status == "EXPIRED":
        message = "Booking has expired."
    else:
        message = None
    
    return BookingResponse(
        booking_id=booking.booking_id,
        user_id=booking.user_id,
        showtime_id=booking.showtime_id,
        total_price=str(booking.total_price),
        status=status,
        hold_expiry_time=booking.hold_expiry.expiry_time.isoformat(),
        created_at=booking.created_at.isoformat(),
        seat_ids=seat_ids,
        message=message
    )


@router.delete("/{booking_id}", response_model=CancelResponse)
def cancel_booking(booking_id: str):
    """Cancel booking with refund"""
    
    booking = repository.get_booking(booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    try:
        refund_amount = booking.cancel_booking()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Release seats in showtime - BUG FIX!
    showtime = repository.get_showtime(booking.showtime_id)
    if showtime:
        seat_ids = [item.seat_id for item in booking.get_booking_items()]
        showtime.release_seats(seat_ids)
    
    return CancelResponse(
        message="Booking cancelled successfully. Refund will be processed according to cancellation policy.",
        refund_amount=str(refund_amount),
        booking_id=booking_id
    )


@router.get("/user/{user_id}", response_model=List[BookingResponse])
def get_user_bookings(user_id: str):
    """Get all bookings for a specific user"""
    
    all_bookings = repository.get_all_bookings()
    user_bookings = [b for b in all_bookings if b.user_id == user_id]
    
    if not user_bookings:
        return []
    
    result = []
    for booking in user_bookings:
        seat_ids = [item.seat_id for item in booking.get_booking_items()]
        
        status = booking.booking_status.value.value
        if status == "RESERVED":
            remaining_seconds = int(booking.hold_expiry.get_remaining_time())
            if remaining_seconds > 0:
                remaining_minutes = remaining_seconds // 60
                message = f"Reserved. Pay within {remaining_minutes} minutes."
            else:
                message = "Expired."
        elif status == "CONFIRMED":
            message = "Confirmed. Ticket issued."
        elif status == "CANCELLED":
            message = "Cancelled."
        elif status == "EXPIRED":
            message = "Expired."
        else:
            message = None
        
        result.append(BookingResponse(
            booking_id=booking.booking_id,
            user_id=booking.user_id,
            showtime_id=booking.showtime_id,
            total_price=str(booking.total_price),
            status=status,
            hold_expiry_time=booking.hold_expiry.expiry_time.isoformat(),
            created_at=booking.created_at.isoformat(),
            seat_ids=seat_ids,
            message=message
        ))
    
    return result