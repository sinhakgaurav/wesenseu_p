"""
AI Customer Support Chat

POST   /support/conversations                     – start a new conversation
GET    /support/conversations/{id}                – get conversation + messages
POST   /support/conversations/{id}/messages       – send a message (user or agent)
PATCH  /support/conversations/{id}/status         – resolve / escalate
GET    /support/conversations/{id}/messages       – list messages
GET    /support/admin/conversations               – admin: list all conversations
"""
import uuid
import re
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.base import get_db
from app.models.support import SupportConversation, SupportMessage
from app.models.employee import Employee
from app.models.customer import Customer
from app.api.v1.deps import get_current_user, get_current_customer

router = APIRouter()


class StartConversation(BaseModel):
    subject: Optional[str] = None
    session_id: Optional[str] = None  # for anonymous users


class SendMessage(BaseModel):
    content: str
    role: str = "user"  # user | assistant


class ConversationStatusUpdate(BaseModel):
    status: str  # resolved | escalated


# ── AI response logic (rule-based with keywords, extend with LLM) ─────────────

FAQ = {
    "pricing": "We offer Starter (₹4,000/mo), Growth (₹11,999/mo), and Enterprise (₹20,000/mo) plans. Visit /pricing for details.",
    "plan": "We offer Starter (₹4,000/mo), Growth (₹11,999/mo), and Enterprise (₹20,000/mo) plans. Visit /pricing for details.",
    "features": "Monitour includes room management, task assignment, AI verification, CCTV surveillance, ticketing, inventory, and more.",
    "trial": "We offer a 14-day free trial on all plans. Contact us at hello@monitour.in to get started.",
    "demo": "You can book a demo at hello@monitour.in or call +91-9000-000000.",
    "integration": "We integrate with WesenseU AI for room verification and CCTV analysis, plus support REST webhooks and ONVIF cameras.",
    "cancel": "You can cancel your subscription at any time from your account settings. No lock-in.",
    "support": "Our support team is available Mon-Sat 9am-7pm IST. Email: support@monitour.in",
    "contact": "Email: hello@monitour.in | Phone: +91-9000-000000 | Mumbai, India",
    "rooms": "Monitour manages room status lifecycle from check-in to verified clean. AI compares staff photos to benchmark images.",
    "cctv": "Monitour integrates with IP cameras via RTSP/ONVIF. WesenseU AI analyses clips for anomalies like trespassing or hygiene violations.",
    "refund": "We offer a full refund within 7 days of purchase if you're not satisfied. Contact billing@monitour.in.",
    "invoice": "Invoices are auto-generated and emailed monthly. You can also download them from your customer portal.",
    "password": "To reset your password, click 'Forgot Password' on the login page or contact support.",
    "login": "Visit /login or contact your property manager for access credentials.",
    "hospital": "Yes! Monitour supports hospitals, clinics, and healthcare facilities with ICU room tracking and compliance workflows.",
    "hotel": "Monitour is purpose-built for hotels — from housekeeping to guest feedback, we cover the full workflow.",
}

GREETINGS = {"hi", "hello", "hey", "hola", "namaste", "good morning", "good evening", "good afternoon"}


def _ai_response(user_message: str) -> str:
    msg = user_message.lower().strip()

    # Greetings
    if any(g in msg for g in GREETINGS):
        return (
            "Hello! I'm the Monitour support assistant. How can I help you today? "
            "You can ask me about pricing, features, integrations, or account help."
        )

    # Keyword lookup
    for keyword, answer in FAQ.items():
        if keyword in msg:
            return answer

    # Fallback
    return (
        "Thank you for reaching out! I'm not sure about that specific question. "
        "Please email us at support@monitour.in or call +91-9000-000000 and our team "
        "will be happy to help. Is there anything else I can assist you with?"
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/conversations", status_code=status.HTTP_201_CREATED)
async def start_conversation(
    data: StartConversation,
    db: AsyncSession = Depends(get_db),
):
    """Start a new support conversation (works for authenticated customers AND anonymous visitors)."""
    conv = SupportConversation(subject=data.subject, session_id=data.session_id)
    db.add(conv)
    await db.flush()  # ensure conv.id is populated

    # Auto-send greeting
    greeting = SupportMessage(
        conversation_id=conv.id,
        role="assistant",
        content=(
            "Hi! I'm Monitour's AI support assistant. "
            "How can I help you today? You can ask about pricing, features, "
            "CCTV setup, room verification, or anything else."
        ),
    )
    db.add(greeting)
    await db.commit()
    return {"conversation_id": str(conv.id), "status": conv.status}


@router.post("/conversations/customer", status_code=status.HTTP_201_CREATED)
async def start_customer_conversation(
    data: StartConversation,
    db: AsyncSession = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    """Start a support conversation as an authenticated customer."""
    conv = SupportConversation(
        customer_id=current_customer.id,
        subject=data.subject,
    )
    db.add(conv)
    await db.flush()  # ensure conv.id is populated

    greeting = SupportMessage(
        conversation_id=conv.id,
        role="assistant",
        content=f"Hi {current_customer.contact_name}! How can I help you today?",
    )
    db.add(greeting)
    await db.commit()
    return {"conversation_id": str(conv.id), "status": conv.status}


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SupportConversation)
        .where(SupportConversation.id == conversation_id)
        .options(selectinload(SupportConversation.messages))
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {
        "id": str(conv.id), "status": conv.status, "subject": conv.subject,
        "created_at": conv.created_at,
        "messages": [
            {"id": str(m.id), "role": m.role, "content": m.content, "created_at": m.created_at}
            for m in conv.messages
        ],
    }


@router.get("/conversations/{conversation_id}/messages")
async def list_messages(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SupportMessage)
        .where(SupportMessage.conversation_id == conversation_id)
        .order_by(SupportMessage.created_at)
    )
    return [
        {"id": str(m.id), "role": m.role, "content": m.content, "created_at": m.created_at}
        for m in result.scalars().all()
    ]


@router.post("/conversations/{conversation_id}/messages")
async def send_message(
    conversation_id: uuid.UUID,
    data: SendMessage,
    db: AsyncSession = Depends(get_db),
):
    """Send a user message and get an immediate AI response."""
    result = await db.execute(
        select(SupportConversation).where(SupportConversation.id == conversation_id)
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if conv.status == "resolved":
        raise HTTPException(status_code=400, detail="Conversation is resolved")

    # Save user message
    user_msg = SupportMessage(
        conversation_id=conversation_id,
        role="user",
        content=data.content,
    )
    db.add(user_msg)

    # Generate AI reply
    ai_text = _ai_response(data.content)
    ai_msg = SupportMessage(
        conversation_id=conversation_id,
        role="assistant",
        content=ai_text,
    )
    db.add(ai_msg)
    conv.updated_at = datetime.utcnow()
    await db.commit()

    return {
        "user_message": {"role": "user", "content": data.content},
        "ai_reply": {"role": "assistant", "content": ai_text},
    }


@router.patch("/conversations/{conversation_id}/status")
async def update_conversation_status(
    conversation_id: uuid.UUID,
    data: ConversationStatusUpdate,
    db: AsyncSession = Depends(get_db),
):
    if data.status not in ("resolved", "escalated", "open"):
        raise HTTPException(status_code=400, detail="status must be resolved, escalated, or open")
    result = await db.execute(
        select(SupportConversation).where(SupportConversation.id == conversation_id)
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    conv.status = data.status
    if data.status == "resolved":
        conv.resolved_at = datetime.utcnow()
    await db.commit()
    return {"status": conv.status}


# ── Admin conversation listing ─────────────────────────────────────────────────

@router.get("/admin/conversations")
async def admin_list_conversations(
    conv_status: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Super admin only")
    q = select(SupportConversation)
    if conv_status:
        q = q.where(SupportConversation.status == conv_status)
    result = await db.execute(q.order_by(SupportConversation.updated_at.desc()).limit(limit))
    return [
        {
            "id": str(c.id), "status": c.status, "subject": c.subject,
            "customer_id": str(c.customer_id) if c.customer_id else None,
            "created_at": c.created_at, "updated_at": c.updated_at,
        }
        for c in result.scalars().all()
    ]
