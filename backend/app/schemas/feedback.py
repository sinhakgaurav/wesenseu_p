from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal
import uuid


class FeedbackCreate(BaseModel):
    property_id: uuid.UUID
    room_id: Optional[uuid.UUID] = None
    department_id: Optional[uuid.UUID] = None
    guest_name: Optional[str] = None
    guest_phone: Optional[str] = None
    rating: int
    review_text: Optional[str] = None
    source: str = "qr"


class FeedbackResponse(FeedbackCreate):
    id: uuid.UUID
    sentiment_score: Optional[Decimal] = None
    sentiment_label: Optional[str] = None
    is_public: bool
    status: str = "pending"
    created_at: datetime

    class Config:
        from_attributes = True
