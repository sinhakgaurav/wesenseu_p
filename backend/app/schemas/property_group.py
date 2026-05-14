import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class PropertyGroupBase(BaseModel):
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    parent_group_id: Optional[uuid.UUID] = None


class PropertyGroupCreate(PropertyGroupBase):
    customer_id: Optional[uuid.UUID] = None


class PropertyGroupUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    parent_group_id: Optional[uuid.UUID] = None
    is_active: Optional[bool] = None


class PropertyGroupResponse(PropertyGroupBase):
    id: uuid.UUID
    customer_id: Optional[uuid.UUID] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
