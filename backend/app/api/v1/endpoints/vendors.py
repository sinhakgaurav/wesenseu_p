"""Vendor CRUD for inventory procurement."""
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user
from app.db.base import get_db
from app.models.employee import Employee
from app.models.inventory import Vendor

router = APIRouter()


class VendorCreate(BaseModel):
    property_id: uuid.UUID
    name: str
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None


class VendorUpdate(BaseModel):
    name: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None


class VendorResponse(BaseModel):
    id: uuid.UUID
    property_id: uuid.UUID
    name: str
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


@router.get("/", response_model=List[VendorResponse])
async def list_vendors(
    property_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    prop_id = property_id or current_user.property_id
    q = select(Vendor).where(Vendor.is_active == True)
    if prop_id:
        q = q.where(Vendor.property_id == prop_id)
    return (await db.execute(q.order_by(Vendor.name))).scalars().all()


@router.post("/", response_model=VendorResponse, status_code=status.HTTP_201_CREATED)
async def create_vendor(
    data: VendorCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if current_user.role not in ("super_admin", "property_manager"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    v = Vendor(**data.model_dump())
    db.add(v)
    await db.commit()
    await db.refresh(v)
    return v


@router.patch("/{vendor_id}", response_model=VendorResponse)
async def update_vendor(
    vendor_id: uuid.UUID,
    data: VendorUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    v = (await db.execute(select(Vendor).where(Vendor.id == vendor_id))).scalar_one_or_none()
    if not v:
        raise HTTPException(status_code=404, detail="Vendor not found")
    for k, val in data.model_dump(exclude_unset=True).items():
        setattr(v, k, val)
    await db.commit()
    await db.refresh(v)
    return v


@router.delete("/{vendor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vendor(
    vendor_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    v = (await db.execute(select(Vendor).where(Vendor.id == vendor_id))).scalar_one_or_none()
    if not v:
        raise HTTPException(status_code=404, detail="Vendor not found")
    v.is_active = False
    await db.commit()
