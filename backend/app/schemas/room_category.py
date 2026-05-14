import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class PropertyRoomCategoryBase(BaseModel):
    code: str = Field(..., max_length=64, description="Stable slug unique per property, e.g. classic_room")
    display_name: str = Field(..., max_length=120)
    description: Optional[str] = None
    sort_order: int = 0


class PropertyRoomCategoryCreate(PropertyRoomCategoryBase):
    property_id: uuid.UUID


class PropertyRoomCategoryUpdate(BaseModel):
    display_name: Optional[str] = Field(None, max_length=120)
    description: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class PropertyRoomCategoryResponse(PropertyRoomCategoryBase):
    id: uuid.UUID
    property_id: uuid.UUID
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
