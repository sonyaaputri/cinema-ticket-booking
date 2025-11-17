# Cinema Ticket Booking System API

API backend untuk sistem pemesanan tiket bioskop berbasis Domain-Driven Design (DDD).

**Proyek Akhir** - II3160 Teknologi Sistem Terintegrasi  
**Nama / NIM:** Sonya Putri Fadilah / 18223138

---

## Stack Teknologi

* **Python 3.10+**
* **FastAPI** - Modern web framework untuk building APIs
* **Pydantic** - Data validation menggunakan Python type hints
* **Uvicorn** - ASGI server untuk menjalankan FastAPI

---

## Quick Start

### Installation
```bash
# Clone repository
git clone https://github.com/[your-username]/cinema-ticket-booking.git
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

## Endpoints API

### Showtimes

| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| `GET` | `/api/showtimes/` | Mendapatkan daftar semua jadwal tayang |
| `GET` | `/api/showtimes/{showtime_id}` | Mendapatkan detail jadwal tayang beserta ketersediaan kursi |

### Bookings

| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| `POST` | `/api/bookings/` | Membuat booking baru (reserve kursi) |
| `GET` | `/api/bookings/{booking_id}` | Mendapatkan detail booking |
| `GET` | `/api/bookings/user/{user_id}` | Mendapatkan semua booking dari user tertentu |
| `POST` | `/api/bookings/confirm-payment` | Konfirmasi pembayaran dan terbitkan tiket |
| `DELETE` | `/api/bookings/{booking_id}` | Membatalkan booking dengan refund |

---

## Error Handling

API menggunakan HTTP status code yang sesuai:

| Status Code | Deskripsi |
|-------------|-----------|
| `200 OK` | Request berhasil |
| `400 Bad Request` | Business rule violation (seat not available, booking expired, dll) |
| `404 Not Found` | Resource tidak ditemukan (booking_id/showtime_id invalid) |
| `422 Unprocessable Entity` | Input validation error (format JSON salah) |

Setiap error response menyertakan pesan yang jelas untuk debugging.

---

## Alur Pemesanan Tiket
```
1. Customer melihat jadwal tayang
   GET /api/showtimes/

2. Customer melihat ketersediaan kursi
   GET /api/showtimes/{showtime_id}

3. Customer membuat booking (kursi di-reserve 10 menit)
   POST /api/bookings/
   Status: RESERVED
   Seat Status: RESERVED

4. Customer melakukan pembayaran
   POST /api/bookings/confirm-payment
   Status: CONFIRMED
   Seat Status: BOOKED
   Ticket: ISSUED

5. (Opsional) Customer membatalkan booking
   DELETE /api/bookings/{booking_id}
   Status: CANCELLED
   Seat Status: AVAILABLE
   Refund: PROCESSED
```

---

## Struktur Project
```
cinema-ticket-booking/
├── app/
│   ├── __init__.py
│   ├── main.py                      # Entry point aplikasi
│   ├── domain/                      # Domain Layer (DDD)
│   │   ├── __init__.py
│   │   ├── value_objects.py         # Value Objects (Immutable)
│   │   ├── entities.py              # Entities (dengan identity)
│   │   └── aggregates.py            # Aggregates (Booking, Showtime)
│   ├── api/                         # API Layer
│   │   ├── __init__.py
│   │   ├── booking_routes.py        # Booking endpoints
│   │   └── showtime_routes.py       # Showtime endpoints
│   └── infrastructure/              # Infrastructure Layer
│       ├── __init__.py
│       └── in_memory_repository.py  # Data storage (in-memory)
├── requirements.txt                 # Python dependencies
├── .gitignore                       # Git ignore rules
└── README.md                        # Dokumentasi project
```

---

**License:** Academic Project - Institut Teknologi Bandung © 2025