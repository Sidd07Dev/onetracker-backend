import logging
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from ..config.db import get_db
from ..utils.cache_utils import CacheUtils
from ..utils.security_utils import verify_api_key
from ..utils.uuid_generator import get_uuid
from ..utils.api_response import ApiResponse
from ..utils.email_utils import send_booking_email
from src.chatbot.models.booking import Bookings
from ..validations.booking_validations import CreateBooking


logger = logging.getLogger(__name__)

booking_router = APIRouter(
    dependencies=[Depends(verify_api_key)]
)

AVAILABLE_HOURS = [2, 3, 4, 5]


def get_utc_now():
    return datetime.now(timezone.utc)


@booking_router.get("/")
async def get_all_bookings(db: Session = Depends(get_db)):
    try:
        logger.info("Request received: Get all bookings")

        cache_key = "bookings"
        cached = await CacheUtils.get(cache_key)

        if cached:
            logger.info("Bookings returned from cache")
            return ApiResponse().success_response(
                message="Bookings fetched successfully",
                data=cached
            )

        logger.info("Cache miss. Fetching bookings from DB")

        bookings = db.execute(
            select(Bookings)
            .order_by(Bookings.booking_datetime.desc())
        ).scalars().all()

        booking_data = jsonable_encoder(bookings)

        await CacheUtils.set(cache_key, booking_data)

        logger.info("Bookings fetched and cached successfully")

        return ApiResponse().success_response(
            message="Bookings fetched successfully",
            data=booking_data
        )

    except Exception as e:
        logger.error("Error in get_all_bookings", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
@booking_router.get("/paginated")
def get_bookings_paginated(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    try:
        logger.info(f"Request: Paginated bookings | page={page} | limit={limit}")

        offset = (page - 1) * limit

        total_count = db.execute(
            select(func.count()).select_from(Bookings)
        ).scalar()

        bookings = db.execute(
            select(Bookings)
            .order_by(Bookings.booking_datetime.desc())
            .offset(offset)
            .limit(limit)
        ).scalars().all()

        return ApiResponse().success_response(
            message="Paginated bookings fetched successfully",
            data={
                "page": page,
                "limit": limit,
                "total": total_count,
                "records": bookings
            }
        )

    except Exception:
        logger.error("Error in paginated bookings", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
@booking_router.get("/availability")
async def get_10_days_availability(db: Session = Depends(get_db)):
    try:
        logger.info("Request: Get availability")

        cache_key = "availability"
        cached = await CacheUtils.get(cache_key)

        if cached:
            logger.info("Availability returned from cache")
            return ApiResponse().success_response(
                message="Availability fetched successfully",
                data=cached
            )

        utc_now = get_utc_now()
        start_date = utc_now.date() + timedelta(days=1)

        availability = []

        for i in range(10):
            current_date = start_date + timedelta(days=i)
            day_slots = []

            for hour in AVAILABLE_HOURS:
                slot_datetime = datetime(
                    current_date.year,
                    current_date.month,
                    current_date.day,
                    hour,
                    0,
                    tzinfo=timezone.utc
                )

                if slot_datetime <= utc_now:
                    continue

                existing = db.execute(
                    select(Bookings).where(
                        Bookings.booking_datetime == slot_datetime
                    )
                ).scalar_one_or_none()

                if not existing:
                    day_slots.append(slot_datetime.isoformat())

            availability.append({
                "date": current_date.isoformat(),
                "available_slots": day_slots
            })

        await CacheUtils.set(cache_key, availability)

        logger.info("Availability fetched from DB and cached")

        return ApiResponse().success_response(
            message="Availability fetched successfully",
            data=availability
        )

    except Exception:
        logger.error("Error in availability endpoint", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")


@booking_router.get("/{booking_id}")
def get_booking_by_id(booking_id: str, db: Session = Depends(get_db)):
    try:
        logger.info(f"Request: Get booking by ID | id={booking_id}")

        booking = db.get(Bookings, booking_id)

        if not booking:
            logger.warning("Booking not found")
            raise HTTPException(status_code=404, detail="Booking not found")

        return ApiResponse().success_response(
            message="Booking fetched successfully",
            data=booking
        )

    except HTTPException:
        raise

    except Exception:
        logger.error("Error in get_booking_by_id", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")



@booking_router.post("/", status_code=201)
async def create_booking(payload: CreateBooking, db: Session = Depends(get_db)):
    try:
        logger.info(f"Booking attempt by {payload.work_email}")

        utc_now = get_utc_now()

        if payload.booking_datetime.tzinfo is None:
            logger.warning("Booking rejected: timezone missing")
            raise HTTPException(status_code=400, detail="Timezone required")

        if payload.booking_datetime <= utc_now:
            logger.warning("Booking rejected: past date")
            raise HTTPException(status_code=400, detail="Past booking not allowed")

        if payload.booking_datetime.hour not in AVAILABLE_HOURS:
            logger.warning("Booking rejected: invalid hour slot")
            raise HTTPException(status_code=400, detail="Invalid time slot")

        existing = db.execute(
            select(Bookings).where(
                Bookings.booking_datetime == payload.booking_datetime
            )
        ).scalar_one_or_none()

        if existing:
            logger.warning("Booking conflict detected")
            raise HTTPException(status_code=409, detail="Slot already booked")

        booking = Bookings(
            id=get_uuid(),
            name=payload.name,
            business_name=payload.business_name,
            work_email=payload.work_email,
            contact_number=payload.contact_number,
            booking_datetime=payload.booking_datetime,
            message=payload.message,
            timezone=payload.timezone
        )

        db.add(booking)
        db.commit()
        db.refresh(booking)

        logger.info(f"Booking created successfully | ID: {booking.id}")

        await CacheUtils.delete("availability")
        logger.info("Availability cache invalidated")

        send_booking_email(booking)
        logger.info("Booking confirmation email sent")

        return ApiResponse().success_response(
            message="Booking created successfully",
            data=booking
        )

    except HTTPException as http_error:
        db.rollback()
        raise http_error

    except Exception:
        db.rollback()
        logger.error("Unexpected error in create_booking", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")

@booking_router.delete("/{booking_id}")
def delete_booking(booking_id: str, db: Session = Depends(get_db)):
    try:
        logger.info(f"Delete request | id={booking_id}")

        booking = db.get(Bookings, booking_id)

        if not booking:
            logger.warning("Delete failed: booking not found")
            raise HTTPException(status_code=404, detail="Booking not found")

        db.delete(booking)
        db.commit()

        logger.info(f"Booking deleted | id={booking_id}")

        return ApiResponse().success_response(
            message="Booking deleted successfully"
        )

    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        logger.error("Error in delete_booking", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")
