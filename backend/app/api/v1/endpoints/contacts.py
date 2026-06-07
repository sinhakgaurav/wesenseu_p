from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import uuid

from app.db.base import get_db
from app.db.soft_delete import apply_soft_delete, not_deleted_clause, restore_soft_deleted
from app.models.contact import CustomerContact, PropertyContact
from app.models.employee import Employee
from app.schemas.contact import ContactCreate, ContactUpdate, ContactResponse
from app.api.v1.deps import get_current_user

router = APIRouter()


@router.get("/customers/{customer_id}", response_model=List[ContactResponse])
async def list_customer_contacts(
    customer_id: uuid.UUID,
    include_deleted: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    q = select(CustomerContact).where(CustomerContact.customer_id == customer_id)
    if not include_deleted:
        clause = not_deleted_clause(CustomerContact)
        if clause is not None:
            q = q.where(clause)
    rows = (await db.execute(q)).scalars().all()
    return rows


@router.post("/customers/{customer_id}", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def add_customer_contact(
    customer_id: uuid.UUID,
    data: ContactCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if current_user.role not in ("super_admin", "property_manager"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    row = CustomerContact(customer_id=customer_id, **data.model_dump())
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


@router.delete("/customers/{customer_id}/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer_contact(
    customer_id: uuid.UUID,
    contact_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    row = (
        await db.execute(
            select(CustomerContact).where(
                CustomerContact.id == contact_id,
                CustomerContact.customer_id == customer_id,
            )
        )
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Contact not found")
    apply_soft_delete(row)
    await db.commit()


@router.post("/customers/{customer_id}/{contact_id}/restore", response_model=ContactResponse)
async def restore_customer_contact(
    customer_id: uuid.UUID,
    contact_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if current_user.role not in ("super_admin", "property_manager"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    row = (
        await db.execute(
            select(CustomerContact).where(
                CustomerContact.id == contact_id,
                CustomerContact.customer_id == customer_id,
            )
        )
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Contact not found")
    restore_soft_deleted(row)
    await db.commit()
    await db.refresh(row)
    return row


@router.get("/properties/{property_id}", response_model=List[ContactResponse])
async def list_property_contacts(
    property_id: uuid.UUID,
    include_deleted: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    q = select(PropertyContact).where(PropertyContact.property_id == property_id)
    if not include_deleted:
        clause = not_deleted_clause(PropertyContact)
        if clause is not None:
            q = q.where(clause)
    rows = (await db.execute(q)).scalars().all()
    return rows


@router.post("/properties/{property_id}", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def add_property_contact(
    property_id: uuid.UUID,
    data: ContactCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if current_user.role not in ("super_admin", "property_manager"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    row = PropertyContact(property_id=property_id, **data.model_dump())
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


@router.patch("/properties/{property_id}/{contact_id}", response_model=ContactResponse)
async def update_property_contact(
    property_id: uuid.UUID,
    contact_id: uuid.UUID,
    data: ContactUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if current_user.role not in ("super_admin", "property_manager"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    row = (
        await db.execute(
            select(PropertyContact).where(
                PropertyContact.id == contact_id,
                PropertyContact.property_id == property_id,
            )
        )
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Contact not found")
    for k, val in data.model_dump(exclude_unset=True).items():
        setattr(row, k, val)
    await db.commit()
    await db.refresh(row)
    return row


@router.delete("/properties/{property_id}/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_property_contact(
    property_id: uuid.UUID,
    contact_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    row = (
        await db.execute(
            select(PropertyContact).where(
                PropertyContact.id == contact_id,
                PropertyContact.property_id == property_id,
            )
        )
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Contact not found")
    apply_soft_delete(row)
    await db.commit()


@router.post("/properties/{property_id}/{contact_id}/restore", response_model=ContactResponse)
async def restore_property_contact(
    property_id: uuid.UUID,
    contact_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if current_user.role not in ("super_admin", "property_manager"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    row = (
        await db.execute(
            select(PropertyContact).where(
                PropertyContact.id == contact_id,
                PropertyContact.property_id == property_id,
            )
        )
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Contact not found")
    restore_soft_deleted(row)
    await db.commit()
    await db.refresh(row)
    return row
