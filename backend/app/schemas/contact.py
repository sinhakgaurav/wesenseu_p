from pydantic import BaseModel, Field
from typing import Optional
from typing import Optional
from datetime import datetime
import uuid


class ContactCreate(BaseModel):
    contact_type: str = Field(..., pattern="^(phone|email)$")
    value: str
    label: Optional[str] = None
    is_primary: bool = False


class ContactUpdate(BaseModel):
    contact_type: Optional[str] = Field(None, pattern="^(phone|email)$")
    value: Optional[str] = None
    label: Optional[str] = None
    is_primary: Optional[bool] = None


class ContactUpdate(BaseModel):
    contact_type: Optional[str] = Field(None, pattern="^(phone|email)$")
    value: Optional[str] = None
    label: Optional[str] = None
    is_primary: Optional[bool] = None


class ContactResponse(BaseModel):
    id: uuid.UUID
    contact_type: str
    value: str
    label: Optional[str] = None
    is_primary: bool
    created_at: datetime

    class Config:
        from_attributes = True
