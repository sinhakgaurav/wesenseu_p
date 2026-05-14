from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from datetime import datetime, timedelta
import uuid
import random
import string

from app.db.base import get_db
from app.models.ticket import Ticket, TicketComment
from app.models.employee import Employee
from app.schemas.ticket import TicketCreate, TicketUpdate, TicketResponse, TicketCommentCreate
from app.api.v1.deps import get_current_user

router = APIRouter()


def generate_ticket_number() -> str:
    return "TK" + "".join(random.choices(string.digits, k=6))


SLA_HOURS = {
    "critical": 1,
    "high": 4,
    "medium": 12,
    "low": 24,
}


@router.get("/", response_model=List[TicketResponse])
async def list_tickets(
    property_id: Optional[uuid.UUID] = None,
    department_id: Optional[uuid.UUID] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    ticket_type: Optional[str] = None,
    room_id: Optional[uuid.UUID] = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    query = select(Ticket)
    prop_id = property_id or current_user.property_id
    if prop_id:
        query = query.where(Ticket.property_id == prop_id)

    if department_id:
        query = query.where(Ticket.department_id == department_id)
    if status:
        query = query.where(Ticket.status == status)
    if priority:
        query = query.where(Ticket.priority == priority)
    if ticket_type:
        query = query.where(Ticket.ticket_type == ticket_type)
    if room_id:
        query = query.where(Ticket.room_id == room_id)

    query = query.offset(skip).limit(limit).order_by(Ticket.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    data: TicketCreate,
    db: AsyncSession = Depends(get_db),
):
    sla_hours = SLA_HOURS.get(data.priority, 24)
    ticket = Ticket(
        **data.model_dump(),
        ticket_number=generate_ticket_number(),
        sla_deadline=datetime.utcnow() + timedelta(hours=sla_hours),
    )
    db.add(ticket)
    await db.commit()
    await db.refresh(ticket)
    return ticket


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@router.patch("/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_id: uuid.UUID,
    data: TicketUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(ticket, field, value)

    if data.status in ("resolved", "closed") and not ticket.resolved_at:
        ticket.resolved_at = datetime.utcnow()

    await db.commit()
    await db.refresh(ticket)
    return ticket


@router.post("/{ticket_id}/comments", response_model=TicketResponse)
async def add_ticket_comment(
    ticket_id: uuid.UUID,
    data: TicketCommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    comment = TicketComment(
        ticket_id=ticket_id,
        author_id=current_user.id,
        author_name=current_user.full_name,
        comment=data.comment,
        is_internal=data.is_internal,
    )
    db.add(comment)
    await db.commit()
    await db.refresh(ticket)
    return ticket


@router.delete("/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ticket(
    ticket_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if current_user.role not in ("super_admin", "property_manager"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    ticket.status = "closed"
    await db.commit()


@router.post("/guest", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
async def create_guest_ticket(
    data: TicketCreate,
    db: AsyncSession = Depends(get_db),
):
    """Public endpoint for guest ticket creation via QR code."""
    sla_hours = SLA_HOURS.get(data.priority, 12)
    ticket = Ticket(
        **data.model_dump(),
        ticket_number=generate_ticket_number(),
        sla_deadline=datetime.utcnow() + timedelta(hours=sla_hours),
        created_by_guest=True,
    )
    db.add(ticket)
    await db.commit()
    await db.refresh(ticket)
    return ticket
