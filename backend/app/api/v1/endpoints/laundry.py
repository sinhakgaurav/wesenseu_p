"""CRUD for guest laundry orders."""
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.models.employee import Employee
from app.models.laundry import LaundryOrder
from app.models.room import Room
from app.api.v1.deps import get_current_user

router = APIRouter()


class LaundryItem(BaseModel):
    description: str
    quantity: int = 1
    service_type: str = "wash"  # wash | dry_clean | press | repair


class LaundryOrderCreate(BaseModel):
    property_id: uuid.UUID
    room_id: Optional[uuid.UUID] = None
    guest_name: Optional[str] = None
    guest_phone: Optional[str] = None
    priority: str = "medium"
    notes: Optional[str] = None
    items: List[LaundryItem] = Field(default_factory=list)
    expected_ready_at: Optional[datetime] = None


class LaundryOrderUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    notes: Optional[str] = None
    items: Optional[List[LaundryItem]] = None
    assigned_to: Optional[uuid.UUID] = None
    expected_ready_at: Optional[datetime] = None


def _dump(o: LaundryOrder) -> dict:
    return {
        "id": str(o.id),
        "property_id": str(o.property_id),
        "room_id": str(o.room_id) if o.room_id else None,
        "guest_name": o.guest_name,
        "guest_phone": o.guest_phone,
        "status": o.status,
        "priority": o.priority,
        "notes": o.notes,
        "items": o.items or [],
        "assigned_to": str(o.assigned_to) if o.assigned_to else None,
        "expected_ready_at": o.expected_ready_at,
        "delivered_at": o.delivered_at,
        "created_at": o.created_at,
        "updated_at": o.updated_at,
    }


@router.get("")
async def list_laundry(
    property_id: Optional[uuid.UUID] = None,
    status_filter: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    prop_id = property_id or current_user.property_id
    q = select(LaundryOrder).where(LaundryOrder.is_active == True)
    if prop_id:
        q = q.where(LaundryOrder.property_id == prop_id)
    if status_filter:
        q = q.where(LaundryOrder.status == status_filter)
    q = q.order_by(LaundryOrder.created_at.desc()).offset(skip).limit(limit)
    rows = (await db.execute(q)).scalars().all()
    return [_dump(r) for r in rows]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_laundry(
    data: LaundryOrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if data.room_id:
        rr = await db.execute(select(Room).where(Room.id == data.room_id))
        room = rr.scalar_one_or_none()
        if not room or room.property_id != data.property_id:
            raise HTTPException(status_code=400, detail="Invalid room for property")
    order = LaundryOrder(
        property_id=data.property_id,
        room_id=data.room_id,
        guest_name=data.guest_name,
        guest_phone=data.guest_phone,
        priority=data.priority,
        notes=data.notes,
        items=[i.model_dump() for i in data.items],
        expected_ready_at=data.expected_ready_at,
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)
    return _dump(order)


@router.get("/{order_id}")
async def get_laundry(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    o = (await db.execute(select(LaundryOrder).where(LaundryOrder.id == order_id))).scalar_one_or_none()
    if not o:
        raise HTTPException(status_code=404, detail="Order not found")
    return _dump(o)


@router.patch("/{order_id}")
async def update_laundry(
    order_id: uuid.UUID,
    data: LaundryOrderUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if current_user.role not in ("super_admin", "property_manager", "dept_manager", "employee"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    o = (await db.execute(select(LaundryOrder).where(LaundryOrder.id == order_id))).scalar_one_or_none()
    if not o:
        raise HTTPException(status_code=404, detail="Order not found")
    payload = data.model_dump(exclude_unset=True)
    if "items" in payload and data.items is not None:
        o.items = [i.model_dump() for i in data.items]
        del payload["items"]
    for k, v in payload.items():
        setattr(o, k, v)
    if data.status == "delivered":
        o.delivered_at = datetime.utcnow()
    await db.commit()
    await db.refresh(o)
    return _dump(o)


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_laundry(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if current_user.role not in ("super_admin", "property_manager"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    o = (await db.execute(select(LaundryOrder).where(LaundryOrder.id == order_id))).scalar_one_or_none()
    if not o:
        raise HTTPException(status_code=404, detail="Order not found")
    o.is_active = False
    await db.commit()
