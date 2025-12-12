# Cinema Ticket Booking System

Production-ready FastAPI microservice for cinema ticket booking with Domain-Driven Design (DDD) architecture.

**Final Project** - II3160 Teknologi Sistem Terintegrasi  
**Sonya Putri Fadilah / 18223138**  
Institut Teknologi Bandung

---

---

## Quick Start

### Docker usage

```bash
docker compose up --build
docker compose run test
```

* App: http://localhost:8000
* Docs: http://localhost:8000/docs

### Local development

```bash
git clone https://github.com/sonyaaputri/cinema-ticket-booking.git
cd cinema-ticket-booking
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
pytest tests/ -v --cov=app --cov-report=term-missing
```

---

## Project Overview

### Architecture

```
cinema-ticket-booking/
├── app/
│   ├── main.py                      # FastAPI application entry point
│   ├── auth/                        # Authentication module
│   │   ├── models.py                # User, Token models
│   │   ├── jwt_handler.py           # JWT token management
│   │   └── dependencies.py          # Auth dependencies
│   ├── domain/                      # Domain layer (DDD)
│   │   ├── value_objects.py         # Immutable value objects
│   │   ├── entities.py              # Entities with identity
│   │   └── aggregates.py            # Booking & Showtime aggregates
│   ├── api/                         # API layer
│   │   ├── auth_routes.py           # Authentication endpoints
│   │   ├── booking_routes.py        # Booking endpoints
│   │   └── showtime_routes.py       # Showtime endpoints
│   └── infrastructure/              # Infrastructure layer
│       └── in_memory_repository.py  # Data storage
├── tests/                           # Comprehensive test suite (95% coverage)
├── Dockerfile                       # Docker configuration
├── docker-compose.yaml              # Container orchestration
└── requirements.txt                 # Python dependencies
```

### Key Features

* **Domain-Driven Design**: Clean architecture with separated layers
* **JWT Authentication**: Secure token-based auth with registration
* **Seat Reservation**: 10-minute hold with automatic release
* **Concurrent Booking Prevention**: First-come-first-served
* **Comprehensive Testing**: 95%+ coverage
* **Docker Ready**: Full containerization
* **CI Pipeline**: Automated testing and linting

### Technology Stack

* **Python 3.10+**
* **FastAPI** - Modern web framework
* **Uvicorn** - ASGI server
* **python-jose** - JWT tokens
* **passlib** - Password hashing
* **pytest** - Testing with coverage

---

## API Documentation

### Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/auth/register` | No | Register new user |
| `POST` | `/api/auth/login` | No | Login and get JWT token |
| `GET` | `/api/showtimes/` | No | List all showtimes |
| `GET` | `/api/showtimes/{id}` | No | Get showtime details |
| `POST` | `/api/bookings/` | Yes | Create booking |
| `GET` | `/api/bookings/me` | Yes | Get user bookings |
| `GET` | `/api/bookings/{id}` | Yes | Get booking details |
| `POST` | `/api/bookings/confirm-payment` | Yes | Confirm payment |
| `DELETE` | `/api/bookings/{id}` | Yes | Cancel booking |

---
## Error Handling

Standard HTTP status codes:

| Status Code | Description |
|-------------|-------------|
| `200 OK` | Request successful |
| `201 Created` | Resource created successfully |
| `400 Bad Request` | Business rule violation or invalid input |
| `401 Unauthorized` | Token invalid, expired, or missing |
| `403 Forbidden` | User lacks permission for resource |
| `404 Not Found` | Resource not found |
| `409 Conflict` | Resource conflict (duplicate booking, etc.) |
| `422 Unprocessable Entity` | Validation error |
| `500 Internal Server Error` | Unexpected server error |

---

## Authentication

System uses JWT tokens. All booking endpoints require authentication.

### Register

```bash
POST /api/auth/register

{
  "username": "johndoe",
  "password": "securepass123",
  "full_name": "John Doe",
  "email": "john@example.com"
}
```

### Login

```bash
POST /api/auth/login

{
  "username": "johndoe",
  "password": "securepass123"
}

Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Using Token

```bash
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Token expires after 60 minutes.

---

## Booking Flow

```
1. Register → POST /api/auth/register

2. Login → POST /api/auth/login
   → Get access_token

3. Browse Showtimes → GET /api/showtimes/

4. Create Booking → POST /api/bookings/
   Status: RESERVED (10 min hold)

5. Confirm Payment → POST /api/bookings/confirm-payment
   Status: CONFIRMED, Ticket: ISSUED

6. View Bookings → GET /api/bookings/me

7. (Optional) Cancel → DELETE /api/bookings/{id}
   Refund based on cancellation policy
```

---

## Business Rules

All business rules fully implemented:

* **Seat Hold Timeout**: Seats reserved for 10 minutes, auto-release if unpaid
* **Concurrent Booking Prevention**: First-come-first-served, prevents double-booking
* **Single-Seat Gap Prevention**: Validates selections to avoid isolated seats
* **Cancellation Policy**: 
  - 24+ hours before: 100% refund
  - 12-24 hours before: 50% refund
  - Less than 12 hours: No refund
* **JWT Authentication**: Secure token-based auth with 60-min expiry
* **Booking Ownership**: Users can only access their own bookings

---

## Testing

### Test Coverage: 95%+

```
tests/
├── test_auth.py              # Authentication & registration
├── test_booking.py           # Booking operations
├── test_showtime.py          # Showtime endpoints
├── test_payment.py           # Payment confirmation
├── test_cancellation.py      # Cancellation policy
├── test_business_rules.py    # Business logic
├── test_integration.py       # End-to-end workflows
└── conftest.py               # Test fixtures
```

### Run Tests

```bash
# All tests with coverage
pytest tests/ -v --cov=app --cov-report=term-missing

# Specific test files
pytest tests/test_auth.py -v
pytest tests/test_booking.py -v

# HTML coverage report
pytest tests/ --cov=app --cov-report=html

# Run with verbose output
pytest tests/ -vv --cov=app
```

---

## Docker Usage

```bash
# Build and start
docker compose up --build

# Run tests
docker compose run test

# Stop services
docker compose down
```

Container features:
* Multi-stage build
* Health checks
* Hot reload for dev
* CORS enabled

---

## Development

### Code Quality

```bash
# Linting
ruff check app/ tests/

# Formatting
black app/ tests/

# Import sorting
isort app/ tests/

# Type checking
mypy app/
```

### CI Pipeline

GitHub Actions runs on every push/PR:
* Tests with 95%+ coverage requirement
* Code quality checks (ruff, black, isort, mypy)
* Security scanning (bandit, safety)
* Docker build and integration tests

---

**License:** Academic Project - Institut Teknologi Bandung © 2025
