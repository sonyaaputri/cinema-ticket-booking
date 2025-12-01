from pydantic import BaseModel
from typing import Optional


class User(BaseModel):
    """User model for authentication"""
    user_id: str
    username: str
    full_name: str
    password_hash: str


class Token(BaseModel):
    """Token response model"""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Token payload data"""
    user_id: str
    username: str


class LoginRequest(BaseModel):
    """Login request model"""
    username: str
    password: str
