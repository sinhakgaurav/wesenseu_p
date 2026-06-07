from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid


class TicketCommentCreate(BaseModel):
    comment: str
    is_internal: bool = False


class TicketCommentResponse(BaseModel):
    id: uuid.UUID
    ticket_id: uuid.UUID
    author_name: Optional[str] = None
    comment: str
    is_internal: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TicketBase(BaseModel):
    title: str
    ticket_type: str
    priority: str = "medium"
    description: Optional[str] = None


class TicketCreate(TicketBase):
    property_id: uuid.UUID
    room_id: Optional[uuid.UUID] = None
    department_id: Optional[uuid.UUID] = None
    guest_name: Optional[str] = None
    guest_phone: Optional[str] = None
    created_by_guest: bool = True


class TicketUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    department_id: Optional[uuid.UUID] = None
    assigned_to: Optional[uuid.UUID] = None
    resolution_notes: Optional[str] = None
    rating: Optional[int] = None


class TicketResponse(TicketBase):
    id: uuid.UUID
    ticket_number: str
    property_id: uuid.UUID
    room_id: Optional[uuid.UUID] = None
    guest_stay_id: Optional[uuid.UUID] = None
    department_id: Optional[uuid.UUID] = None
    assigned_to: Optional[uuid.UUID] = None
    status: str
    guest_name: Optional[str] = None
    guest_phone: Optional[str] = None
    created_by_guest: bool
    resolution_notes: Optional[str] = None
    sla_deadline: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    escalation_count: int
    rating: Optional[int] = None
    comments: List[TicketCommentResponse] = []
    created_at: datetime

    class Config:
        from_attributes = True
