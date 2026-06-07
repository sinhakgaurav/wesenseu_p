from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime
import uuid


class OnboardingSessionCreate(BaseModel):
    customer_id: Optional[uuid.UUID] = None
    property_id: Optional[uuid.UUID] = None


class OnboardingStepUpdate(BaseModel):
    current_step: Optional[str] = None
    step_index: Optional[int] = None
    payload_patch: Optional[dict[str, Any]] = None
    customer_id: Optional[uuid.UUID] = None
    property_id: Optional[uuid.UUID] = None
    status: Optional[str] = None


class OnboardingSessionResponse(BaseModel):
    id: uuid.UUID
    customer_id: Optional[uuid.UUID] = None
    property_id: Optional[uuid.UUID] = None
    current_step: str
    step_index: int
    payload: dict
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
