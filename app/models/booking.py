from sqlalchemy import Column, String, Integer, Date, Time
from app.core.database import Base

class InterviewBooking(Base):
    __tablename__ = "interview_bookings"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    booking_date = Column(Date, nullable=False)
    booking_time = Column(Time, nullable=False)