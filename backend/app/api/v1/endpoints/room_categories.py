import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user
from app.constants.benchmark_aspects import SUGGESTED_BENCHMARK_ASPECTS
from app.services.category_availability import category_availability
from app.db.base import get_db
from app.models.benchmark import RoomCategoryBenchmark
from app.models.employee import Employee
from app.models.property import Property
from app.models.property_room_category import PropertyRoomCategory
from app.schemas.room_category import (
    PropertyRoomCategoryCreate,
    PropertyRoomCategoryResponse,
    PropertyRoomCategoryUpdate,
)

router = APIRouter()


async def _get_property_for_user(
    db: AsyncSession, current_user: Employee, property_id: Optional[uuid.UUID]
) -> Property:
    pid = property_id or current_user.property_id
    if not pid:
        raise HTTPException(status_code=400, detail="property_id is required")
    prop = (await db.execute(select(Property).where(Property.id == pid))).scalar_one_or_none()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    if current_user.role != "super_admin" and current_user.property_id != prop.id:
        raise HTTPException(status_code=403, detail="Access to this property is not allowed")
    return prop


def _assert_category_manage(user: Employee):
    if user.role not in ("super_admin", "property_manager"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")


@router.get("/suggested-aspects")
async def suggested_benchmark_aspects():
    """Common aspect / view-type labels for benchmark uploads (free-text ``aspect`` is still allowed)."""
    return {"aspects": SUGGESTED_BENCHMARK_ASPECTS}


@router.get("/", response_model=List[PropertyRoomCategoryResponse])
async def list_room_categories(
    property_id: Optional[uuid.UUID] = Query(None),
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    prop = await _get_property_for_user(db, current_user, property_id)
    q = select(PropertyRoomCategory).where(PropertyRoomCategory.property_id == prop.id)
    if not include_inactive:
        q = q.where(PropertyRoomCategory.is_active == True)
    q = q.order_by(PropertyRoomCategory.sort_order, PropertyRoomCategory.display_name)
    return (await db.execute(q)).scalars().all()


@router.post("/", response_model=PropertyRoomCategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_room_category(
    data: PropertyRoomCategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    _assert_category_manage(current_user)
    await _get_property_for_user(db, current_user, data.property_id)
    dup = (
        await db.execute(
            select(PropertyRoomCategory).where(
                PropertyRoomCategory.property_id == data.property_id,
                PropertyRoomCategory.code == data.code,
            )
        )
    ).scalar_one_or_none()
    if dup:
        raise HTTPException(status_code=409, detail="A category with this code already exists for the property")
    row = PropertyRoomCategory(**data.model_dump())
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


@router.get("/{category_id}/benchmark-summary")
async def room_category_benchmark_summary(
    category_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    row = (
        await db.execute(select(PropertyRoomCategory).where(PropertyRoomCategory.id == category_id))
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Room category not found")
    await _get_property_for_user(db, current_user, row.property_id)
    q = (
        select(RoomCategoryBenchmark.aspect, func.count(RoomCategoryBenchmark.id))
        .where(
            RoomCategoryBenchmark.is_active == True,
            RoomCategoryBenchmark.property_id == row.property_id,
            RoomCategoryBenchmark.property_room_category_id == row.id,
        )
        .group_by(RoomCategoryBenchmark.aspect)
    )
    rows = (await db.execute(q)).all()
    return {"category_id": str(row.id), "aspects": [{"aspect": a, "count": c} for a, c in rows]}


@router.get("/{category_id}", response_model=PropertyRoomCategoryResponse)
async def get_room_category(
    category_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    row = (
        await db.execute(select(PropertyRoomCategory).where(PropertyRoomCategory.id == category_id))
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Room category not found")
    await _get_property_for_user(db, current_user, row.property_id)
    return row


@router.patch("/{category_id}", response_model=PropertyRoomCategoryResponse)
async def update_room_category(
    category_id: uuid.UUID,
    data: PropertyRoomCategoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    _assert_category_manage(current_user)
    row = (
        await db.execute(select(PropertyRoomCategory).where(PropertyRoomCategory.id == category_id))
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Room category not found")
    await _get_property_for_user(db, current_user, row.property_id)
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    await db.commit()
    await db.refresh(row)
    return row


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_room_category(
    category_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    _assert_category_manage(current_user)
    row = (
        await db.execute(select(PropertyRoomCategory).where(PropertyRoomCategory.id == category_id))
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Room category not found")
    await _get_property_for_user(db, current_user, row.property_id)
    row.is_active = False
    await db.commit()


@router.get("/availability")
async def room_category_availability(
    property_id: Optional[uuid.UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    prop = await _get_property_for_user(db, current_user, property_id)
    return await category_availability(db, prop.id)
