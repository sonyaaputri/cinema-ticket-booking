from fastapi import FastAPI
from app.api import booking_routes, showtime_routes, auth_routes

app = FastAPI(
    title="Cinema Ticket Booking System",
    description="Final Project II3160 - Teknologi Sistem Terintegrasi - With JWT Authentication",
    version="2.0.0"
)

# Include routers
app.include_router(auth_routes.router)
app.include_router(booking_routes.router)
app.include_router(showtime_routes.router)


@app.get("/")
def root():
    return {
        "message": "Cinema Ticket Booking System API - v2.0 with JWT Authentication",
        "student": "Sonya Putri Fadilah - 18223138",
        "docs": "/docs",
        "authentication": "Required for booking operations. Use /api/auth/login to get access token."
    }


@app.get("/health")
def health_check():
    return {"status": "healthy", "version": "2.0.0"}
