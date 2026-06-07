from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import List, Optional
import uuid

from app.db.base import get_db
from app.models.guest_stay import GuestStay
from app.models.order import Order
from app.models.employee import Employee
from app.schemas.guest_stay import GuestStayResponse, GuestStayFolioResponse
from app.api.v1.deps import get_current_user

router = APIRouter()


@router.get("/", response_model=List[GuestStayResponse])
async def list_guest_stays(
    property_id: Optional[uuid.UUID] = None,
    room_id: Optional[uuid.UUID] = None,
    status: Optional[str] = "active",
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    q = select(GuestStay)
    prop_id = property_id or current_user.property_id
    if prop_id:
        q = q.where(GuestStay.property_id == prop_id)
    if room_id:
        q = q.where(GuestStay.room_id == room_id)
    if status:
        q = q.where(GuestStay.status == status)
    q = q.order_by(GuestStay.check_in_at.desc()).offset(skip).limit(limit)
    return (await db.execute(q)).scalars().all()


@router.get("/{stay_id}", response_model=GuestStayResponse)
async def get_guest_stay(
    stay_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    stay = (await db.execute(select(GuestStay).where(GuestStay.id == stay_id))).scalar_one_or_none()
    if not stay:
        raise HTTPException(status_code=404, detail="Guest stay not found")
    return stay


@router.get("/{stay_id}/folio", response_model=GuestStayFolioResponse)
async def guest_stay_folio(
    stay_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    """Orders and tickets scoped to this stay only (not previous guests in the same room)."""
    stay = (await db.execute(select(GuestStay).where(GuestStay.id == stay_id))).scalar_one_or_none()
    if not stay:
        raise HTTPException(status_code=404, detail="Guest stay not found")

    orders = (
        await db.execute(
            select(Order)
            .where(Order.guest_stay_id == stay_id)
            .options(selectinload(Order.items))
            .order_by(Order.created_at)
        )
    ).scalars().all()

    total_r = await db.execute(
        select(func.coalesce(func.sum(Order.total_amount), 0)).where(Order.guest_stay_id == stay_id)
    )
    order_total = float(total_r.scalar() or 0)

    return GuestStayFolioResponse(
        stay=GuestStayResponse.model_validate(stay),
        orders=orders,
        order_total=order_total,
    )
