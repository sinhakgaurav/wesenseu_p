import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user
from app.db.base import get_db
from app.models.employee import Employee
from app.models.property import Property
from app.models.property_group import PropertyGroup
from app.schemas.property_group import (
    PropertyGroupCreate,
    PropertyGroupResponse,
    PropertyGroupUpdate,
)

router = APIRouter()


async def _property_for_employee(db: AsyncSession, user: Employee) -> Optional[Property]:
    if not user.property_id:
        return None
    return (
        await db.execute(select(Property).where(Property.id == user.property_id))
    ).scalar_one_or_none()


def _assert_group_manage(user: Employee):
    if user.role not in ("super_admin", "property_manager"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")


@router.get("/", response_model=List[PropertyGroupResponse])
async def list_property_groups(
    customer_id: Optional[uuid.UUID] = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    q = select(PropertyGroup).where(PropertyGroup.is_active == True)
    if current_user.role == "super_admin":
        if customer_id:
            q = q.where(PropertyGroup.customer_id == customer_id)
    else:
        prop = await _property_for_employee(db, current_user)
        if not prop or not prop.customer_id:
            return []
        q = q.where(PropertyGroup.customer_id == prop.customer_id)
    q = q.offset(skip).limit(limit).order_by(PropertyGroup.name)
    return (await db.execute(q)).scalars().all()


@router.post("/", response_model=PropertyGroupResponse, status_code=status.HTTP_201_CREATED)
async def create_property_group(
    data: PropertyGroupCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    _assert_group_manage(current_user)
    payload = data.model_dump()
    if current_user.role != "super_admin":
        prop = await _property_for_employee(db, current_user)
        if not prop or not prop.customer_id:
            raise HTTPException(status_code=400, detail="Property has no customer owner; cannot create a group")
        payload["customer_id"] = prop.customer_id
    row = PropertyGroup(**payload)
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


@router.get("/{group_id}", response_model=PropertyGroupResponse)
async def get_property_group(
    group_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    row = (await db.execute(select(PropertyGroup).where(PropertyGroup.id == group_id))).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Property group not found")
    if current_user.role != "super_admin":
        prop = await _property_for_employee(db, current_user)
        if not prop or row.customer_id != prop.customer_id:
            raise HTTPException(status_code=403, detail="Access denied")
    return row


@router.patch("/{group_id}", response_model=PropertyGroupResponse)
async def update_property_group(
    group_id: uuid.UUID,
    data: PropertyGroupUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    _assert_group_manage(current_user)
    row = (await db.execute(select(PropertyGroup).where(PropertyGroup.id == group_id))).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Property group not found")
    if current_user.role != "super_admin":
        prop = await _property_for_employee(db, current_user)
        if not prop or row.customer_id != prop.customer_id:
            raise HTTPException(status_code=403, detail="Access denied")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    await db.commit()
    await db.refresh(row)
    return row


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_property_group(
    group_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    _assert_group_manage(current_user)
    row = (await db.execute(select(PropertyGroup).where(PropertyGroup.id == group_id))).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Property group not found")
    if current_user.role != "super_admin":
        prop = await _property_for_employee(db, current_user)
        if not prop or row.customer_id != prop.customer_id:
            raise HTTPException(status_code=403, detail="Access denied")
    row.is_active = False
    await db.commit()
