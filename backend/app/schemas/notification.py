from pydantic import BaseModel
from typing import Optional, Any, Dict
from datetime import datetime
import uuid


class NotificationResponse(BaseModel):
    id: uuid.UUID
    notification_type: str
    title: str
    message: str
    data: Optional[Dict[str, Any]] = None
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True
