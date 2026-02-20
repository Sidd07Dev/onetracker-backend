from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, List
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy.orm import Session

import httpx
import os
from dotenv import load_dotenv
from openai import AsyncOpenAI

from ..config.db import get_db
from .bookings_route import (
    get_10_days_availability,
    create_booking
)
from ..validations.booking_validations import CreateBooking

load_dotenv()

CF_ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID")
CF_API_TOKEN = os.getenv("CF_API_TOKEN")
VECTORIZE_INDEX = os.getenv("VECTORIZE_INDEX_NAME", "onetracker-knowledge")

if not CF_ACCOUNT_ID or not CF_API_TOKEN:
    raise RuntimeError("Missing Cloudflare credentials")

cf_client = AsyncOpenAI(
    api_key=CF_API_TOKEN,
    base_url=f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/v1",
    http_client=httpx.AsyncClient(
        headers={"Authorization": f"Bearer {CF_API_TOKEN}"},
        timeout=60.0
    )
)

DEFAULT_MODEL = "@cf/meta/llama-3.1-8b-instruct-fast"
EMBEDDING_MODEL = "@cf/baai/bge-small-en-v1.5"

chatbot_router = APIRouter()

CANCEL_KEYWORDS = ["cancel", "stop", "exit", "quit"]

sessions: Dict[str, List[dict]] = {}
booking_states: Dict[str, dict] = {}

# -----------------------------
# Schemas
# -----------------------------

class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    session_id: str
    reply: str


# -----------------------------
# Chat Endpoint
# -----------------------------

@chatbot_router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, db: Session = Depends(get_db)):

    user_input = req.message.strip()
    user_message_lower = user_input.lower()

    if req.session_id not in sessions:
        sessions[req.session_id] = []
        booking_states[req.session_id] = {}

    state = booking_states[req.session_id]

    # -----------------------------------
    # Cancel Booking
    # -----------------------------------
    if any(word in user_message_lower for word in CANCEL_KEYWORDS):
        booking_states.pop(req.session_id, None)
        sessions.pop(req.session_id, None)
        return ChatResponse(
            session_id=req.session_id,
            reply="Booking session cancelled."
        )

    # -----------------------------------
    # Start Booking
    # -----------------------------------
    if "demo" in user_message_lower and not state:
        state["step"] = "collect_timezone"
        return ChatResponse(
            session_id=req.session_id,
            reply="Please provide your timezone (Example: Asia/Kolkata)"
        )

    # -----------------------------------
    # BOOKING FLOW (AI BLOCKED)
    # -----------------------------------
    if state:
        step = state.get("step")

        # 1️⃣ Collect Timezone
        if step == "collect_timezone":
            try:
                ZoneInfo(user_input)
                state["timezone"] = user_input
                state["step"] = "choose_slot"

                availability_response = await get_10_days_availability(db)
                availability_data = availability_response["data"]

                state["availability"] = availability_data

                all_slots = [
                    slot
                    for day in availability_data
                    for slot in day["available_slots"]
                ]

                if not all_slots:
                    booking_states.pop(req.session_id, None)
                    return ChatResponse(
                        session_id=req.session_id,
                        reply="No slots available in next 10 days."
                    )

                formatted = "\n".join(all_slots)

                return ChatResponse(
                    session_id=req.session_id,
                    reply=f"Available slots:\n{formatted}\n\nPlease select one slot."
                )

            except Exception:
                return ChatResponse(
                    session_id=req.session_id,
                    reply="Invalid timezone."
                )

        # 2️⃣ Choose Slot
        elif step == "choose_slot":
            selected_slot = user_input.strip()

            valid_slots = [
                slot
                for day in state.get("availability", [])
                for slot in day["available_slots"]
            ]

            if selected_slot not in valid_slots:
                return ChatResponse(
                    session_id=req.session_id,
                    reply="Invalid or unavailable slot."
                )

            state["booking_datetime"] = selected_slot
            state["step"] = "collect_name"

            return ChatResponse(
                session_id=req.session_id,
                reply="Please provide your full name."
            )

        # 3️⃣ Collect Name
        elif step == "collect_name":
            state["name"] = user_input
            state["step"] = "collect_email"
            return ChatResponse(
                session_id=req.session_id,
                reply="Please provide your work email."
            )

        # 4️⃣ Collect Email
        elif step == "collect_email":
            if "@" not in user_input:
                return ChatResponse(
                    session_id=req.session_id,
                    reply="Please enter a valid email address."
                )

            state["work_email"] = user_input
            state["step"] = "collect_business"
            return ChatResponse(
                session_id=req.session_id,
                reply="Please provide your business name."
            )

        # 5️⃣ Collect Business
        elif step == "collect_business":
            state["business_name"] = user_input
            state["step"] = "collect_contact"
            return ChatResponse(
                session_id=req.session_id,
                reply="Please provide your contact number."
            )
 
        # 6️⃣ Collect Contact
        elif step == "collect_contact":
            if not user_input.isdigit():
                return ChatResponse(
                    session_id=req.session_id,
                    reply="Contact number should contain digits only."
                )

            state["contact_number"] = user_input
            state["step"] = "collect_message"
            return ChatResponse(
                session_id=req.session_id,
                reply="Any additional message?"
            )

        # 7️⃣ Final Booking
        elif step == "collect_message":
            state["message"] = user_input

            try:
                booking_payload = CreateBooking(
                    name=state["name"],
                    business_name=state["business_name"],
                    work_email=state["work_email"],
                    contact_number=state["contact_number"],
                    booking_datetime=datetime.fromisoformat(
                        state["booking_datetime"]
                    ),
                    message=state["message"],
                    timezone=state["timezone"]
                )

                await create_booking(booking_payload, db)

                booking_states.pop(req.session_id, None)

                return ChatResponse(
                    session_id=req.session_id,
                    reply="🎉 Demo booked successfully! Confirmation email sent."
                )

            except HTTPException as e:
                booking_states.pop(req.session_id, None)
                return ChatResponse(
                    session_id=req.session_id,
                    reply=f"Booking failed: {e.detail}"
                )

            except Exception:
                booking_states.pop(req.session_id, None)
                return ChatResponse(
                    session_id=req.session_id,
                    reply="Something went wrong while booking."
                )

    # -----------------------------------
    # AI RAG SECTION (ONLY IF NOT BOOKING)
    # -----------------------------------

    conversation = sessions[req.session_id]
    conversation.append({"role": "user", "content": user_input})

    try:
        embed_resp = await cf_client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=[user_input]
        )
        query_vector = embed_resp.data[0].embedding
    except Exception:
        query_vector = None

    contexts_str = ""

    if query_vector:
        try:
            async with httpx.AsyncClient() as http:
                vec_url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/vectorize/v2/indexes/{VECTORIZE_INDEX}/query"

                vec_resp = await http.post(
                    vec_url,
                    json={
                        "vector": query_vector,
                        "topK": 5,
                        "returnMetadata": "all"
                    },
                    headers={
                        "Authorization": f"Bearer {CF_API_TOKEN}",
                        "Content-Type": "application/json"
                    }
                )

                matches = vec_resp.json()["result"]["matches"]
                relevant = [m for m in matches if m.get("score", 0) >= 0.68]

                contexts_str = "\n\n".join(
                    m["metadata"].get("text", "")[:500]
                    for m in relevant
                )
        except Exception:
            pass

    system_content = f"""
You are OneTracker AI assistant.
Only answer OneTracker related queries.
Use documentation context only if relevant.
If unsure, say so politely.

Context:
{contexts_str if contexts_str else "No relevant documentation found."}

Never simulate bookings.
"""

    try:
        completion = await cf_client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": system_content},
                *conversation[-12:]
            ],
            temperature=0.7,
            max_tokens=600
        )

        reply = completion.choices[0].message.content.strip()

    except Exception:
        reply = "AI is currently unavailable."

    conversation.append({"role": "assistant", "content": reply})
    sessions[req.session_id] = conversation

    return ChatResponse(session_id=req.session_id, reply=reply)
