from fastapi import APIRouter, HTTPException, status
from app.auth.models import LoginRequest, Token
from app.auth.jwt_handler import verify_password, create_access_token
from app.infrastructure.in_memory_repository import repository

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/login", response_model=Token)
def login(request: LoginRequest):
    """
    Authenticate user and return JWT access token.
    
    Demo users:
    - username: user1, password: password123
    - username: user2, password: password456
    - username: testuser, password: test123
    """
    # Get user from repository
    user = repository.get_user_by_username(request.username)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token = create_access_token(
        data={"user_id": user.user_id, "username": user.username}
    )
    
    return Token(access_token=access_token, token_type="bearer")
