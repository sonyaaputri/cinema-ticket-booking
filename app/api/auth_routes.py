from fastapi import APIRouter, HTTPException, status
from app.auth.models import User, LoginRequest, Token, RegisterRequest
from app.auth.jwt_handler import create_access_token, verify_password, get_password_hash
from app.infrastructure.in_memory_repository import repository
import uuid

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

@router.post("/register", response_model=Token)
def register(request: RegisterRequest):
    """Register new user"""
    if repository.get_user_by_username(request.username):
        raise HTTPException(400, "Username already exists")
    
    user = User(
        user_id=f"USR{str(uuid.uuid4())[:8].upper()}",
        username=request.username,
        email=request.email,
        full_name=request.full_name,
        password_hash=get_password_hash(request.password)
    )
    repository.add_user(user)
    
    access_token = create_access_token(
    data={"user_id": user.user_id, "username": user.username})
    return {"access_token": access_token, "token_type": "bearer"}