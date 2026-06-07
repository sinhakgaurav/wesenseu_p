from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid

from app.schemas.order import OrderResponse


class GuestStayResponse(BaseModel):
    id: uuid.UUID
    property_id: uuid.UUID
    room_id: uuid.UUID
    guest_name: str
    guest_phone: Optional[str] = None
    status: str
    check_in_at: datetime
    check_out_at: Optional[datetime] = None
    expected_check_out: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class GuestStayFolioResponse(BaseModel):
    stay: GuestStayResponse
    orders: List[OrderResponse] = []
    order_total: float = 0
