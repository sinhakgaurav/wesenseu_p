from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
import uuid

from app.db.base import get_db
from app.models.inventory import InventoryItem, InventoryTransaction, Vendor
from app.models.employee import Employee
from app.schemas.inventory import (
    InventoryItemCreate, InventoryItemUpdate, InventoryItemResponse,
    InventoryTransactionCreate, InventoryTransactionResponse
)
from app.api.v1.deps import get_current_user

router = APIRouter()


@router.get("/items", response_model=List[InventoryItemResponse])
async def list_inventory(
    property_id: Optional[uuid.UUID] = None,
    category: Optional[str] = None,
    low_stock_only: bool = False,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    query = select(InventoryItem).where(InventoryItem.is_active == True)
    prop_id = property_id or current_user.property_id
    if prop_id:
        query = query.where(InventoryItem.property_id == prop_id)
    if category:
        query = query.where(InventoryItem.category == category)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()

    response = []
    for item in items:
        item_dict = {
            "id": item.id,
            "property_id": item.property_id,
            "item_name": item.item_name,
            "item_code": item.item_code,
            "category": item.category,
            "unit": item.unit,
            "current_stock": item.current_stock,
            "minimum_stock": item.minimum_stock,
            "unit_cost": item.unit_cost,
            "vendor_id": item.vendor_id,
            "is_active": item.is_active,
            "is_low_stock": item.current_stock <= item.minimum_stock,
            "created_at": item.created_at,
        }
        if low_stock_only and not item_dict["is_low_stock"]:
            continue
        response.append(InventoryItemResponse(**item_dict))

    return response


@router.post("/items", response_model=InventoryItemResponse, status_code=status.HTTP_201_CREATED)
async def create_inventory_item(
    data: InventoryItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    item = InventoryItem(**data.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return InventoryItemResponse(
        **{k: getattr(item, k) for k in InventoryItemResponse.model_fields if hasattr(item, k)},
        is_low_stock=item.current_stock <= item.minimum_stock,
    )


@router.patch("/items/{item_id}", response_model=InventoryItemResponse)
async def update_inventory_item(
    item_id: uuid.UUID,
    data: InventoryItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    result = await db.execute(select(InventoryItem).where(InventoryItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(item, field, value)

    await db.commit()
    await db.refresh(item)
    return InventoryItemResponse(
        **{k: getattr(item, k) for k in InventoryItemResponse.model_fields if hasattr(item, k)},
        is_low_stock=item.current_stock <= item.minimum_stock,
    )


@router.get("/items/{item_id}", response_model=InventoryItemResponse)
async def get_inventory_item(
    item_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    result = await db.execute(select(InventoryItem).where(InventoryItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    return InventoryItemResponse(
        **{k: getattr(item, k) for k in InventoryItemResponse.model_fields if hasattr(item, k)},
        is_low_stock=item.current_stock <= item.minimum_stock,
    )


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_inventory_item(
    item_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if current_user.role not in ("super_admin", "property_manager", "dept_manager"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    result = await db.execute(select(InventoryItem).where(InventoryItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    item.is_active = False
    await db.commit()


@router.post("/transactions", response_model=InventoryTransactionResponse, status_code=status.HTTP_201_CREATED)
async def record_transaction(
    data: InventoryTransactionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    result = await db.execute(select(InventoryItem).where(InventoryItem.id == data.inventory_item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")

    if data.transaction_type == "OUT" and item.current_stock < data.quantity:
        raise HTTPException(status_code=400, detail="Insufficient stock")

    if data.transaction_type == "IN":
        item.current_stock += data.quantity
    else:
        item.current_stock -= data.quantity

    transaction = InventoryTransaction(
        **data.model_dump(),
        performed_by=current_user.id,
    )
    db.add(transaction)
    await db.commit()
    await db.refresh(transaction)
    return transaction


@router.get("/transactions", response_model=List[InventoryTransactionResponse])
async def list_transactions(
    inventory_item_id: Optional[uuid.UUID] = None,
    transaction_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    query = select(InventoryTransaction)
    if inventory_item_id:
        query = query.where(InventoryTransaction.inventory_item_id == inventory_item_id)
    if transaction_type:
        query = query.where(InventoryTransaction.transaction_type == transaction_type)

    query = query.offset(skip).limit(limit).order_by(InventoryTransaction.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()
