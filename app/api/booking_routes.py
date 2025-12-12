from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from app.auth.models import User
from app.domain.aggregates import Booking
from app.domain.entities import BookingItem
from app.domain.value_objects import BookingStatus, BookingStatusEnum
from app.infrastructure.in_memory_repository import repository
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/api/bookings", tags=["Bookings"])


# Request/Response Models
class CreateBookingRequest(BaseModel):
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


# ============================================================================
# CREATE BOOKING
# ============================================================================
@router.post("/", response_model=BookingResponse)
def create_booking(
    request: CreateBookingRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Create new booking with seat reservation.
    Requires authentication - user_id is extracted from JWT token.
    """
    # Get user_id from User object
    user_id = current_user.user_id
    
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
        user_id=user_id,
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
        message=f"Booking successful! Please complete payment within {remaining_minutes} minutes to confirm your booking."
    )


# ============================================================================
# CONFIRM PAYMENT
# ============================================================================
@router.post("/confirm-payment", response_model=TicketResponse)
def confirm_payment(
    request: ConfirmPaymentRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Confirm payment and issue ticket.
    Requires authentication and booking ownership.
    """
    booking = repository.get_booking(request.booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Verify ownership - CONSISTENT ownership check
    if booking.user_id != current_user.user_id:   
        raise HTTPException(status_code=403, detail="Not authorized to access this booking")
    
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
        message="Payment confirmed successfully! Your ticket has been issued."
    )


# ============================================================================
# GET MY BOOKINGS
# ============================================================================
@router.get("/me", response_model=List[BookingResponse])
def get_my_bookings(current_user: User = Depends(get_current_user)):
    """
    Get all bookings for the authenticated user.
    Requires authentication - returns bookings for current user only.
    """
    user_id = current_user.user_id
    
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


# ============================================================================
# GET BOOKING BY ID
# ============================================================================
@router.get("/{booking_id}", response_model=BookingResponse)
def get_booking(
    booking_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get booking details.
    Requires authentication and booking ownership.
    """
    booking = repository.get_booking(booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Verify ownership - CONSISTENT
    if booking.user_id != current_user.user_id:   
        raise HTTPException(status_code=403, detail="Not authorized to access this booking")
    
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


# ============================================================================
# CANCEL BOOKING
# ============================================================================
@router.delete("/{booking_id}")
def cancel_booking(
    booking_id: str,
    current_user: User = Depends(get_current_user)
):
    """Cancel a booking with refund calculation based on cancellation policy"""
    booking = repository.get_booking(booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Ownership check - CONSISTENT
    if booking.user_id != current_user.user_id:   
        raise HTTPException(status_code=403, detail="Not authorized to cancel this booking")
    
    # Get showtime untuk refund calculation
    showtime = repository.get_showtime(booking.showtime_id)
    if not showtime:
        raise HTTPException(status_code=404, detail="Showtime not found")
    
    # Parse showtime datetime dari TimeSlot
    showtime_datetime = datetime.strptime(
        f"{showtime.time_slot._date} {showtime.time_slot._start_time}",
        "%Y-%m-%d %H:%M"
    )
    
    # Cancel booking dengan refund calculation
    try:
        refund_amount = booking.cancel_booking(showtime_datetime)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Release seats back to showtime
    seat_ids = [item.seat_id for item in booking.get_booking_items()]
    showtime.release_seats(seat_ids)
    
    return {
        "message": "Booking cancelled successfully",
        "refund_amount": float(refund_amount),
        "booking_id": booking_id,
        "status": booking.booking_status.value.value
    }