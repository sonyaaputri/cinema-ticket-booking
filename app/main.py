from fastapi import FastAPI
from app.api import booking_routes, showtime_routes

app = FastAPI(
    title="Cinema Ticket Booking System",
    description="Final Project II3160 - Teknologi Sistem Terintegrasi",
    version="1.0.0"
)

# Include routers
app.include_router(booking_routes.router)
app.include_router(showtime_routes.router)


@app.get("/")
def root():
    return {
        "message": "Cinema Ticket Booking System API",
        "student": "Sonya Putri Fadilah - 18223138",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}