from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
import uuid


class PropertyBase(BaseModel):
    name: str
    property_type: str
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: str = "India"
    phone: Optional[str] = None
    email: Optional[str] = None
    total_rooms: int = 0
    subscription_plan: str = "starter"
    property_group_id: Optional[uuid.UUID] = None
    parent_property_id: Optional[uuid.UUID] = None


class PropertyCreate(PropertyBase):
    customer_id: Optional[uuid.UUID] = None


class PropertyUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    total_rooms: Optional[int] = None
    subscription_plan: Optional[str] = None
    subscription_status: Optional[str] = None
    customer_id: Optional[uuid.UUID] = None
    property_group_id: Optional[uuid.UUID] = None
    parent_property_id: Optional[uuid.UUID] = None
    is_active: Optional[bool] = None


class PropertyResponse(PropertyBase):
    id: uuid.UUID
    customer_id: Optional[uuid.UUID] = None
    logo_url: Optional[str] = None
    subscription_status: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
