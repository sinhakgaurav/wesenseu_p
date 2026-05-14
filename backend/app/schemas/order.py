from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
import uuid


class OrderItemCreate(BaseModel):
    item_name: str
    quantity: int = 1
    unit_price: Decimal


class OrderItemResponse(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    item_name: str
    quantity: int
    unit_price: Decimal
    total_price: Decimal

    class Config:
        from_attributes = True


class OrderCreate(BaseModel):
    property_id: uuid.UUID
    room_id: uuid.UUID
    order_type: str  # food, service, amenity, extra_bed
    notes: Optional[str] = None
    guest_name: Optional[str] = None
    items: List[OrderItemCreate] = []


class OrderUpdate(BaseModel):
    status: Optional[str] = None
    assigned_to: Optional[uuid.UUID] = None
    notes: Optional[str] = None
    delivered_at: Optional[datetime] = None


class OrderResponse(BaseModel):
    id: uuid.UUID
    order_number: str
    property_id: uuid.UUID
    room_id: uuid.UUID
    order_type: str
    total_amount: Decimal
    status: str
    notes: Optional[str] = None
    guest_name: Optional[str] = None
    assigned_to: Optional[uuid.UUID] = None
    delivered_at: Optional[datetime] = None
    created_at: datetime
    items: List[OrderItemResponse] = []

    class Config:
        from_attributes = True
