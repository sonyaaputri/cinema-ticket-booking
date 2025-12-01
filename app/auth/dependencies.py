from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from app.auth.jwt_handler import decode_access_token
from app.auth.models import TokenData

# Security scheme
security = HTTPBearer()


def get_current_user(token: str = Depends(security)) -> dict:
    """
    Dependency to get the current authenticated user from JWT token.
    
    Args:
        token: HTTP Bearer token from security scheme
        
    Returns:
        dict: User information (user_id, username)
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    # Extract token string from HTTPAuthorizationCredentials
    token_str = token.credentials if hasattr(token, 'credentials') else token
    
    token_data = decode_access_token(token_str)
    
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return {
        "user_id": token_data.user_id,
        "username": token_data.username
    }


def verify_booking_ownership(booking_user_id: str, current_user: dict) -> None:
    """
    Verify that the current user owns the booking.
    
    Args:
        booking_user_id: User ID from the booking
        current_user: Current authenticated user
        
    Raises:
        HTTPException: If user does not own the booking
    """
    if booking_user_id != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this booking"
        )
