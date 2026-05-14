import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DepartmentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    manager_id: Optional[uuid.UUID] = None


class DepartmentCreate(DepartmentBase):
    property_id: uuid.UUID


class DepartmentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    manager_id: Optional[uuid.UUID] = None
    is_active: Optional[bool] = None


class DepartmentResponse(BaseModel):
    id: uuid.UUID
    property_id: uuid.UUID
    name: str
    description: Optional[str] = None
    manager_id: Optional[uuid.UUID] = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
