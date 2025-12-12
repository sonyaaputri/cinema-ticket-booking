"""
Test API Authentication Endpoints
FIXED to work with global repository
"""
import pytest
from app.auth.models import User
from app.auth.jwt_handler import get_password_hash
from app.infrastructure.in_memory_repository import repository


# ============================================================================
# LOGIN ENDPOINT TESTS
# ============================================================================
def test_login_success_with_demo_user(client):
    """Test: Login with demo user credentials"""
    response = client.post(
        "/api/auth/login",
        json={
            "username": "user1",
            "password": "password123"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client):
    """Test: Login with incorrect password"""
    response = client.post(
        "/api/auth/login",
        json={
            "username": "user1",
            "password": "wrongpassword"
        }
    )
    
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]


def test_login_user_not_found(client):
    """Test: Login with non-existent username"""
    response = client.post(
        "/api/auth/login",
        json={
            "username": "nonexistentuser99999",
            "password": "somepass"
        }
    )
    
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]


def test_login_missing_username(client):
    """Test: Login without username"""
    response = client.post(
        "/api/auth/login",
        json={
            "password": "testpass"
        }
    )
    
    assert response.status_code == 422  # Validation error


def test_login_missing_password(client):
    """Test: Login without password"""
    response = client.post(
        "/api/auth/login",
        json={
            "username": "testuser"
        }
    )
    
    assert response.status_code == 422  # Validation error


# ============================================================================
# REGISTER ENDPOINT TESTS
# ============================================================================
def test_register_success(client):
    """Test: Register new user successfully"""
    import uuid
    unique_username = f"newuser_{uuid.uuid4().hex[:8]}"
    
    response = client.post(
        "/api/auth/register",
        json={
            "username": unique_username,
            "password": "newpass123",
            "email": "new@example.com",
            "full_name": "New User"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_register_duplicate_username(client):
    """Test: Cannot register with existing username"""
    # Register first time
    import uuid
    username = f"dupuser_{uuid.uuid4().hex[:8]}"
    
    client.post(
        "/api/auth/register",
        json={
            "username": username,
            "password": "pass123",
            "email": "dup1@example.com",
            "full_name": "Dup User 1"
        }
    )
    
    # Try to register again with same username
    response = client.post(
        "/api/auth/register",
        json={
            "username": username,
            "password": "pass456",
            "email": "dup2@example.com",
            "full_name": "Dup User 2"
        }
    )
    
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"].lower()


def test_register_missing_fields(client):
    """Test: Register with missing required fields"""
    response = client.post(
        "/api/auth/register",
        json={
            "username": "newuser"
            # Missing password, email, full_name
        }
    )
    
    assert response.status_code == 422  # Validation error


def test_register_token_can_be_used_immediately(client):
    """Test: Token from registration can be used for authenticated requests"""
    import uuid
    username = f"instantuser_{uuid.uuid4().hex[:8]}"
    
    # Register
    register_response = client.post(
        "/api/auth/register",
        json={
            "username": username,
            "password": "pass123",
            "email": "instant@example.com",
            "full_name": "Instant User"
        }
    )
    
    assert register_response.status_code == 200
    token = register_response.json()["access_token"]
    
    # Use token to access protected endpoint
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/bookings/me", headers=headers)
    
    # Should work (even if empty list)
    assert response.status_code == 200


# ============================================================================
# AUTHENTICATION TOKEN TESTS
# ============================================================================
def test_protected_endpoint_without_token(client):
    """Test: Accessing protected endpoint without token fails"""
    response = client.get("/api/bookings/me")
    
    assert response.status_code == 403  # Forbidden (no auth header)


def test_protected_endpoint_with_invalid_token(client):
    """Test: Accessing protected endpoint with invalid token"""
    headers = {"Authorization": "Bearer invalid_token_12345"}
    response = client.get("/api/bookings/me", headers=headers)
    
    assert response.status_code == 401  # Unauthorized


def test_protected_endpoint_with_valid_token(client, auth_headers):
    """Test: Accessing protected endpoint with valid token"""
    response = client.get("/api/bookings/me", headers=auth_headers)
    
    assert response.status_code == 200


def test_token_contains_user_info(client, test_user_token):
    """Test: Token contains user_id and username"""
    from app.auth.jwt_handler import decode_access_token
    
    token_data = decode_access_token(test_user_token)
    
    assert token_data is not None
    assert token_data.user_id == "TEST_USER_001"
    assert token_data.username == "testuser_pytest"


# ============================================================================
# LOGIN AND REGISTER CONSISTENCY TESTS
# ============================================================================
def test_login_register_token_consistency(client):
    """Test: Tokens from login and register have same structure"""
    import uuid
    username = f"consistuser_{uuid.uuid4().hex[:8]}"
    
    # Register
    register_response = client.post(
        "/api/auth/register",
        json={
            "username": username,
            "password": "pass123",
            "email": "consist@example.com",
            "full_name": "Consistent User"
        }
    )
    register_token = register_response.json()["access_token"]
    
    # Login with same user
    login_response = client.post(
        "/api/auth/login",
        json={
            "username": username,
            "password": "pass123"
        }
    )
    login_token = login_response.json()["access_token"]
    
    # Decode both tokens
    from app.auth.jwt_handler import decode_access_token
    
    register_data = decode_access_token(register_token)
    login_data = decode_access_token(login_token)
    
    # Both should have same user info
    assert register_data.username == login_data.username
    assert register_data.user_id == login_data.user_id