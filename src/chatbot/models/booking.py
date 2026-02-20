from sqlalchemy import Column, String, DateTime, Text,UUID
from ..config.base import Base

class Bookings(Base):
    __tablename__ = "bookings"

    id = Column(UUID, primary_key=True, index=True)
    name = Column(String, nullable=False)
    business_name = Column(String, nullable=False)
    work_email = Column(String, nullable=False)
    contact_number = Column(String, nullable=False)

    #  Store UTC datetime only
    booking_datetime = Column(DateTime(timezone=True), nullable=False, index=True)

    message = Column(Text, nullable=True)

    timezone = Column(String, nullable=False, default = "UTC")
   