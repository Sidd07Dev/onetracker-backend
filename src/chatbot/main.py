from fastapi import FastAPI,Depends,Request
from fastapi.middleware.cors import CORSMiddleware

import uvicorn
import logging
import time
from sqlalchemy.orm import Session

from .routes.bookings_route import booking_router
from .routes.chatbot_route import chatbot_router
from .config.db import engine,get_db
from . import models
from src.chatbot.config.base import Base
from .config.logging import setup_logging



setup_logging()

logger = logging.getLogger(__name__)


app = FastAPI(
     title="OneTracker",
    description="This is the backend of OneTracker and intigrating the chatbot .",
    version="1.0.0"
)

origins = [
    "http://localhost:8080",
    "http://192.168.1.79:8080",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,          # allowed frontend origins
    allow_credentials=True,
    allow_methods=["*"],            # allow all HTTP methods
    allow_headers=["*"],            # allow all headers
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    response = await call_next(request)

    process_time = round((time.time() - start_time) * 1000, 2)

    logger.info(
        f"{request.method} {request.url.path} "
        f"Status: {response.status_code} "
        f"Time: {process_time}ms"
    )

    return response


@app.get("/")
def health_check(db:Session = Depends(get_db)):
     if not db:
           return {
          "status":False,
          "message":"Database connect nehi hua hai....."
     }
     return {
          "status":True,
          "message":"Server alive",
     }
     
app.include_router(booking_router,prefix ="/api/v1/booking",tags = ["Bookings"])
app.include_router(chatbot_router,prefix ="/api/v1/chatbot",tags = ["ChatBot"])


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    logger.info(f"Tables created: {list(Base.metadata.tables.keys())}")

def start():
    try:
         uvicorn.run("src.chatbot.main:app",host = "127.0.0.1", port =8000,reload = True)

    except Exception as e:
        logger.error("Error starting server", exc_info=True)
