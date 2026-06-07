from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid


class CatalogItemUpdate(BaseModel):
    display_name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class CatalogItemCreate(BaseModel):
    kind: str
    code: Optional[str] = Field(None, min_length=1, max_length=64)
    display_name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None


class CatalogItemResponse(BaseModel):
    id: uuid.UUID
    kind: str
    code: str
    display_name: str
    description: Optional[str] = None
    is_system: bool
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class PropertyCatalogSetRequest(BaseModel):
    catalog_item_ids: list[uuid.UUID]


class RoomCategoryAmenitySetRequest(BaseModel):
    catalog_item_ids: list[uuid.UUID]
