from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime, timedelta
import uuid
import random
import string

from app.db.base import get_db
from app.db.soft_delete import apply_soft_delete, not_deleted_clause, restore_soft_deleted
from app.models.ticket import Ticket, TicketComment
from app.models.employee import Employee
from app.models.department import Department
from app.models.room import Room
from app.constants.ticket_department import TICKET_TYPE_DEPARTMENT
from app.services.guest_stay import get_active_stay_for_room
from app.services.ticket_task import create_task_for_ticket
from app.services.notify_managers import notify_managers
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
    include_deleted: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    query = select(Ticket).options(selectinload(Ticket.comments))
    if not include_deleted:
        clause = not_deleted_clause(Ticket)
        if clause is not None:
            query = query.where(clause)
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
    await db.flush()
    await create_task_for_ticket(db, ticket)
    await notify_managers(
        db,
        ticket.property_id,
        "ticket_created",
        f"Ticket {ticket.ticket_number}",
        ticket.title,
        department_id=ticket.department_id,
        reference_type="ticket",
        reference_id=ticket.id,
    )
    await db.commit()
    await db.refresh(ticket)
    return ticket


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    result = await db.execute(
        select(Ticket).options(selectinload(Ticket.comments)).where(Ticket.id == ticket_id)
    )
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
    apply_soft_delete(ticket)
    ticket.status = "closed"
    await db.commit()


@router.post("/{ticket_id}/restore", response_model=TicketResponse)
async def restore_ticket(
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
    restore_soft_deleted(ticket)
    await db.commit()
    await db.refresh(ticket)
    return ticket


@router.post("/guest", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
async def create_guest_ticket(
    data: TicketCreate,
    db: AsyncSession = Depends(get_db),
):
    """Public endpoint for guest ticket creation via QR code."""
    sla_hours = SLA_HOURS.get(data.priority, 12)
    payload = data.model_dump()
    department_id = payload.get("department_id")
    if not department_id and data.room_id:
        dept_name = TICKET_TYPE_DEPARTMENT.get(data.ticket_type)
        if dept_name:
            room = (await db.execute(select(Room).where(Room.id == data.room_id))).scalar_one_or_none()
            if room:
                dept = (
                    await db.execute(
                        select(Department).where(
                            Department.property_id == room.property_id,
                            Department.name == dept_name,
                            Department.is_active == True,
                        )
                    )
                ).scalar_one_or_none()
                if dept:
                    department_id = dept.id
        payload["department_id"] = department_id

    guest_stay_id = None
    if data.room_id:
        stay = await get_active_stay_for_room(db, data.room_id)
        if stay:
            guest_stay_id = stay.id
            if not payload.get("guest_name"):
                payload["guest_name"] = stay.guest_name
            if not payload.get("guest_phone"):
                payload["guest_phone"] = stay.guest_phone

    ticket = Ticket(
        **payload,
        guest_stay_id=guest_stay_id,
        ticket_number=generate_ticket_number(),
        sla_deadline=datetime.utcnow() + timedelta(hours=sla_hours),
        created_by_guest=True,
    )
    db.add(ticket)
    await db.flush()
    await create_task_for_ticket(db, ticket)
    await notify_managers(
        db,
        ticket.property_id,
        "ticket_created",
        f"Ticket {ticket.ticket_number}",
        ticket.title,
        department_id=ticket.department_id,
        reference_type="ticket",
        reference_id=ticket.id,
    )
    await db.commit()
    await db.refresh(ticket)
    return ticket
