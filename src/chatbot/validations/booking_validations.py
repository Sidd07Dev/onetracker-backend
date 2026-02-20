from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class CreateBooking(BaseModel):
    name: str
    business_name: str
    work_email: str
    contact_number: str
    booking_datetime: datetime   # Must include timezone (UTC)
    message: Optional[str] = None
    timezone: str = "UTC"
