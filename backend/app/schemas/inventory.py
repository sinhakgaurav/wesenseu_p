from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal
import uuid


class InventoryItemBase(BaseModel):
    item_name: str
    category: str
    unit: str = "piece"
    minimum_stock: int = 5
    unit_cost: Optional[Decimal] = None
    vendor_id: Optional[uuid.UUID] = None


class InventoryItemCreate(InventoryItemBase):
    property_id: uuid.UUID
    item_code: Optional[str] = None
    current_stock: int = 0


class InventoryItemUpdate(BaseModel):
    item_name: Optional[str] = None
    category: Optional[str] = None
    unit: Optional[str] = None
    current_stock: Optional[int] = None
    minimum_stock: Optional[int] = None
    unit_cost: Optional[Decimal] = None
    vendor_id: Optional[uuid.UUID] = None
    is_active: Optional[bool] = None


class InventoryItemResponse(InventoryItemBase):
    id: uuid.UUID
    property_id: uuid.UUID
    item_code: Optional[str] = None
    current_stock: int
    is_active: bool
    is_low_stock: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class InventoryTransactionCreate(BaseModel):
    inventory_item_id: uuid.UUID
    transaction_type: str  # IN, OUT
    quantity: int
    reference_type: Optional[str] = None
    reference_id: Optional[uuid.UUID] = None
    notes: Optional[str] = None


class InventoryTransactionResponse(BaseModel):
    id: uuid.UUID
    inventory_item_id: uuid.UUID
    transaction_type: str
    quantity: int
    reference_type: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
