from pydantic import BaseModel, EmailStr
from datetime import date, time

class BookingCreate(BaseModel):
    name: str
    email: EmailStr
    booking_date: date
    booking_time: time

class BookingResponse(BookingCreate):
    id: int

    class Config:
        from_attributes = True