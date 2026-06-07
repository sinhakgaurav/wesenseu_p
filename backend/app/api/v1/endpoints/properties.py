from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
import uuid

from app.db.base import get_db
from app.models.property import Property
from app.models.employee import Employee
from app.schemas.property import PropertyCreate, PropertyUpdate, PropertyResponse
from app.schemas.p2 import PropertyScheduleSet
from app.models.p2_extensions import PropertySchedule
from sqlalchemy import delete
from app.api.v1.deps import get_current_user

router = APIRouter()

# Roles allowed to manage (create/update) properties
PROPERTY_ADMIN_ROLES = ("super_admin",)
# Roles that see only their own property
SCOPED_ROLES = ("property_manager", "dept_manager", "employee")


def _assert_property_access(current_user: Employee, prop: Property):
    """Raise 403 if user is not allowed to access this specific property."""
    if current_user.role in PROPERTY_ADMIN_ROLES:
        return
    if current_user.property_id != prop.id:
        raise HTTPException(status_code=403, detail="Access to this property is not allowed")


@router.get("/", response_model=List[PropertyResponse])
async def list_properties(
    customer_id: Optional[uuid.UUID] = Query(None),
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    query = select(Property).where(Property.is_active == True)

    if current_user.role == "super_admin":
        if customer_id:
            query = query.where(Property.customer_id == customer_id)
    else:
        # Non-admin employees only see their own property
        query = query.where(Property.id == current_user.property_id)

    query = query.offset(skip).limit(limit).order_by(Property.name)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=PropertyResponse, status_code=status.HTTP_201_CREATED)
async def create_property(
    data: PropertyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if current_user.role not in PROPERTY_ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Only super_admin can create properties")
    prop = Property(**data.model_dump())
    db.add(prop)
    await db.commit()
    await db.refresh(prop)
    return prop


@router.get("/{property_id}", response_model=PropertyResponse)
async def get_property(
    property_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    result = await db.execute(select(Property).where(Property.id == property_id))
    prop = result.scalar_one_or_none()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    _assert_property_access(current_user, prop)
    return prop


@router.patch("/{property_id}", response_model=PropertyResponse)
async def update_property(
    property_id: uuid.UUID,
    data: PropertyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if current_user.role not in PROPERTY_ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Only super_admin can update properties")

    result = await db.execute(select(Property).where(Property.id == property_id))
    prop = result.scalar_one_or_none()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(prop, field, value)

    await db.commit()
    await db.refresh(prop)
    return prop


@router.delete("/{property_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_property(
    property_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if current_user.role not in PROPERTY_ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Only super_admin can delete properties")
    result = await db.execute(select(Property).where(Property.id == property_id))
    prop = result.scalar_one_or_none()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    prop.is_active = False
    prop.subscription_status = "suspended"
    await db.commit()


@router.get("/{property_id}/schedules")
async def get_property_schedules(
    property_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    result = await db.execute(select(Property).where(Property.id == property_id))
    prop = result.scalar_one_or_none()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    _assert_property_access(current_user, prop)
    rows = (
        await db.execute(select(PropertySchedule).where(PropertySchedule.property_id == property_id))
    ).scalars().all()
    return [
        {
            "day_of_week": r.day_of_week,
            "open_time": r.open_time.isoformat(),
            "close_time": r.close_time.isoformat(),
            "department_id": str(r.department_id) if r.department_id else None,
            "is_closed": r.is_closed,
        }
        for r in rows
    ]


@router.put("/{property_id}/schedules")
async def set_property_schedules(
    property_id: uuid.UUID,
    body: PropertyScheduleSet,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if current_user.role not in ("super_admin", "property_manager"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    result = await db.execute(select(Property).where(Property.id == property_id))
    prop = result.scalar_one_or_none()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    await db.execute(delete(PropertySchedule).where(PropertySchedule.property_id == property_id))
    for entry in body.schedules:
        db.add(
            PropertySchedule(
                property_id=property_id,
                department_id=entry.department_id,
                day_of_week=entry.day_of_week,
                open_time=entry.open_time,
                close_time=entry.close_time,
                is_closed=entry.is_closed,
            )
        )
    await db.commit()
    return await get_property_schedules(property_id, db, current_user)
