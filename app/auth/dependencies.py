from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.auth.jwt_handler import decode_access_token
from app.auth.models import User
from app.infrastructure.in_memory_repository import repository

# Security scheme
security = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """
    Dependency to get the current authenticated user from JWT token.
    
    Args:
        credentials: HTTP Bearer token credentials
        
    Returns:
        User: Complete User object from repository
        
    Raises:
        HTTPException: If token is invalid, expired, or user not found
    """
    # Extract token string from HTTPAuthorizationCredentials
    token_str = credentials.credentials
    
    # Decode and verify token
    token_data = decode_access_token(token_str)
    
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get User object from repository using username from token
    user = repository.get_user_by_username(token_data.username)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user  # Return User object, bukan dict!


def verify_booking_ownership(booking_user_id: str, current_user: User) -> None:
    """
    Verify that the current user owns the booking.
    
    Args:
        booking_user_id: User ID from the booking
        current_user: Current authenticated User object
        
    Raises:
        HTTPException: If user does not own the booking
    """
    if booking_user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this booking"
        )