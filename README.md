# Cinema Ticket Booking System API

API backend untuk sistem pemesanan tiket bioskop berbasis Domain-Driven Design (DDD) dengan JWT Authentication.

**Proyek Akhir** - II3160 Teknologi Sistem Terintegrasi  
**Nama / NIM:** Sonya Putri Fadilah / 18223138  
**Milestone:** M5 - Implementasi Lanjutan (JWT Authentication)

---

## Stack Teknologi

* **Python 3.10+**
* **FastAPI** - Modern web framework untuk building APIs
* **Pydantic** - Data validation menggunakan Python type hints
* **Uvicorn** - ASGI server untuk menjalankan FastAPI
* **python-jose** - JWT token generation dan validation
* **passlib** - Password hashing dengan bcrypt

---

## Quick Start

### Installation
```bash
# Clone repository
git clone https://github.com/sonyaaputri/cinema-ticket-booking.git
cd cinema-ticket-booking

# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn app.main:app --reload
```

### Access API Documentation

Server akan berjalan di `http://localhost:8000`

* **Swagger UI (Interactive):** http://localhost:8000/docs
* **ReDoc (Documentation):** http://localhost:8000/redoc

---

## Authentication (M5)

Sistem menggunakan JWT (JSON Web Token) untuk autentikasi. Semua endpoint booking memerlukan authentication.

### Demo Users

Gunakan salah satu demo user berikut untuk testing:

| Username | Password | User ID | Full Name |
|----------|----------|---------|-----------|
| `user1` | `password123` | USR001 | John Doe |
| `user2` | `password456` | USR002 | Jane Smith |
| `testuser` | `test123` | USR003 | Test User |

### Login Flow

1. **Login untuk mendapatkan token:**
   ```bash
   POST /api/auth/login
   Content-Type: application/json

   {
     "username": "user1",
     "password": "password123"
   }
   ```

   **Response:**
   ```json
   {
     "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
     "token_type": "bearer"
   }
   ```

2. **Gunakan token untuk endpoint protected:**
   ```
   Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```

3. **Token berlaku selama 60 menit** (1 jam)

---

## Endpoints API

### Authentication

| Method | Endpoint | Auth Required | Deskripsi |
|--------|----------|---------------|-----------|
| `POST` | `/api/auth/login` | Tidak | Login dan mendapatkan JWT access token |

### Showtimes (Public)

| Method | Endpoint | Auth Required | Deskripsi |
|--------|----------|---------------|-----------|
| `GET` | `/api/showtimes/` | Tidak | Mendapatkan daftar semua jadwal tayang |
| `GET` | `/api/showtimes/{showtime_id}` | Tidak | Mendapatkan detail jadwal tayang beserta ketersediaan kursi |

### Bookings (Protected)

| Method | Endpoint | Auth Required | Deskripsi |
|--------|----------|---------------|-----------|
| `POST` | `/api/bookings/` | Ya | Membuat booking baru (reserve kursi) - user_id dari token |
| `GET` | `/api/bookings/me` | Ya | Mendapatkan semua booking dari user yang sedang login |
| `GET` | `/api/bookings/{booking_id}` | Ya | Mendapatkan detail booking (verifikasi ownership) |
| `POST` | `/api/bookings/confirm-payment` | Ya | Konfirmasi pembayaran dan terbitkan tiket |
| `DELETE` | `/api/bookings/{booking_id}` | Ya | Membatalkan booking dengan refund (verifikasi ownership) |

---

## Error Handling

API menggunakan HTTP status code yang sesuai:

| Status Code | Deskripsi |
|-------------|-----------|
| `200 OK` | Request berhasil |
| `400 Bad Request` | Business rule violation (seat not available, booking expired, dll) |
| `401 Unauthorized` | Token tidak valid, expired, atau tidak ada token |
| `403 Forbidden` | User tidak memiliki akses ke resource (ownership violation) |
| `404 Not Found` | Resource tidak ditemukan (booking_id/showtime_id invalid) |
| `422 Unprocessable Entity` | Input validation error (format JSON salah) |

Setiap error response menyertakan pesan yang jelas untuk debugging.

---

## Alur Pemesanan Tiket (dengan Authentication)

```
0. Customer login terlebih dahulu
   POST /api/auth/login
   → Mendapatkan access_token
   → Simpan token untuk request selanjutnya

1. Customer melihat jadwal tayang (tanpa auth)
   GET /api/showtimes/

2. Customer melihat ketersediaan kursi (tanpa auth)
   GET /api/showtimes/{showtime_id}

3. Customer membuat booking dengan token (kursi di-reserve 10 menit)
   POST /api/bookings/
   Header: Authorization: Bearer {token}
   Status: RESERVED
   Seat Status: RESERVED
   Note: user_id otomatis dari token, tidak perlu input manual

4. Customer melakukan pembayaran dengan token
   POST /api/bookings/confirm-payment
   Header: Authorization: Bearer {token}
   Status: CONFIRMED
   Seat Status: BOOKED
   Ticket: ISSUED

5. Customer melihat semua booking miliknya
   GET /api/bookings/me
   Header: Authorization: Bearer {token}
   → Return list semua booking user

6. (Opsional) Customer membatalkan booking
   DELETE /api/bookings/{booking_id}
   Header: Authorization: Bearer {token}
   Status: CANCELLED
   Seat Status: AVAILABLE
   Refund: PROCESSED
```

---

## Testing di Swagger UI

1. Buka http://localhost:8000/docs
2. Scroll ke endpoint **POST /api/auth/login**
3. Klik "Try it out" dan login dengan demo user (contoh: user1 / password123)
4. Copy `access_token` dari response
5. Klik tombol **"Authorize"** (ikon gembok) di kanan atas
6. Paste token di field "Value" (jangan tambahkan "Bearer" manual)
7. Klik "Authorize" lalu "Close"
8. Sekarang semua endpoint protected bisa diakses!

---

## Struktur Project

```
cinema-ticket-booking/
├── app/
│   ├── __init__.py
│   ├── main.py                      # Entry point aplikasi dengan auth routes
│   ├── auth/                        # Authentication Module (M5)
│   │   ├── __init__.py
│   │   ├── models.py                # User, Token, LoginRequest models
│   │   ├── jwt_handler.py           # JWT token creation & validation
│   │   └── dependencies.py          # Auth dependencies (get_current_user)
│   ├── domain/                      # Domain Layer (DDD)
│   │   ├── __init__.py
│   │   ├── value_objects.py         # Value Objects (Immutable)
│   │   ├── entities.py              # Entities (dengan identity)
│   │   └── aggregates.py            # Aggregates (Booking, Showtime)
│   ├── api/                         # API Layer
│   │   ├── __init__.py
│   │   ├── auth_routes.py           # Authentication endpoints (M5)
│   │   ├── booking_routes.py        # Booking endpoints (updated with auth)
│   │   └── showtime_routes.py       # Showtime endpoints (public)
│   └── infrastructure/              # Infrastructure Layer
│       ├── __init__.py
│       └── in_memory_repository.py  # Data storage (updated with users)
├── requirements.txt                 # Python dependencies
├── .gitignore                       # Git ignore rules
└── README.md                        # Dokumentasi project
```

---

## Business Rules yang Diimplementasikan

### Fully Implemented 
- **Seat Hold Timeout:** Kursi di-hold selama 10 menit sejak booking dibuat
- **Concurrent Booking Prevention:** First-come-first-served untuk seat availability
- **JWT Authentication:** Token-based security untuk semua booking operations
- **Booking Ownership Verification:** User hanya bisa akses booking milik sendiri

### Simplified Implementation 
- **Single-Seat Gap Prevention:** Menggunakan stub validation (return True)
- **Cancellation Policy:** Full refund untuk semua cancellation (belum implement H-24/H-12 logic)
- **External Context Integration:** Payment Context dan Pricing Context masih mocked

---

## Notes

- **In-Memory Storage:** Data akan hilang ketika server restart (untuk demo purposes)
- **Demo Users Only:** Tidak ada endpoint registration, gunakan demo users yang sudah disediakan
- **JWT Secret Key:** Hard-coded untuk development (production harus pakai environment variable)
- **Token Expiry:** 60 menit, setelah itu perlu login ulang

---

## Development Timeline

- **M1:** Domain Analysis - Identifikasi subdomain dan business capabilities
- **M2:** Context Mapping - Definisi bounded context dan context map
- **M3:** Tactical Design - Class diagram dan ubiquitous language
- **M4:** Initial Implementation - Basic API dengan DDD architecture
- **M5:** Extended Implementation - JWT Authentication dan protected endpoints ← **Current**
- **M6:** Finalization - Laporan akhir dan video demo (Coming Soon)

---

**License:** Academic Project - Institut Teknologi Bandung © 2025