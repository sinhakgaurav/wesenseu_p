from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from decimal import Decimal
from datetime import datetime
import uuid, random, string

from app.db.base import get_db
from app.db.soft_delete import apply_soft_delete, not_deleted_clause
from app.models.order import Order, OrderItem
from app.models.employee import Employee
from app.schemas.order import OrderCreate, OrderUpdate, OrderResponse
from app.api.v1.deps import get_current_user
from app.services.guest_stay import get_active_stay_for_room

router = APIRouter()


def _order_number() -> str:
    return "ORD" + "".join(random.choices(string.digits, k=6))


@router.get("/", response_model=List[OrderResponse])
async def list_orders(
    property_id: Optional[uuid.UUID] = None,
    room_id: Optional[uuid.UUID] = None,
    status: Optional[str] = None,
    order_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    include_deleted: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    query = select(Order)
    if not include_deleted:
        clause = not_deleted_clause(Order)
        if clause is not None:
            query = query.where(clause)
    prop_id = property_id or current_user.property_id
    if prop_id:
        query = query.where(Order.property_id == prop_id)
    if room_id:
        query = query.where(Order.room_id == room_id)
    if status:
        query = query.where(Order.status == status)
    if order_type:
        query = query.where(Order.order_type == order_type)
    query = query.offset(skip).limit(limit).order_by(Order.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    data: OrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    total = sum(item.quantity * item.unit_price for item in data.items)
    stay = await get_active_stay_for_room(db, data.room_id)
    order = Order(
        order_number=_order_number(),
        property_id=data.property_id,
        room_id=data.room_id,
        guest_stay_id=stay.id if stay else None,
        order_type=data.order_type,
        total_amount=total,
        status="pending",
        notes=data.notes,
        guest_name=data.guest_name or (stay.guest_name if stay else None),
    )
    db.add(order)
    await db.flush()

    for item_data in data.items:
        item = OrderItem(
            order_id=order.id,
            item_name=item_data.item_name,
            quantity=item_data.quantity,
            unit_price=item_data.unit_price,
            total_price=Decimal(str(item_data.quantity)) * item_data.unit_price,
        )
        db.add(item)

    await db.commit()
    await db.refresh(order)
    return order


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.patch("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: uuid.UUID,
    data: OrderUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(order, field, value)

    if data.status == "delivered" and not order.delivered_at:
        order.delivered_at = datetime.utcnow()

    await db.commit()
    await db.refresh(order)
    return order


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_order(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status in ("delivered",):
        raise HTTPException(status_code=400, detail="Cannot cancel a delivered order")
    order.status = "cancelled"
    apply_soft_delete(order)
    await db.commit()
