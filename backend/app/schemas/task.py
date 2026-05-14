from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid


class TaskBase(BaseModel):
    task_type: str
    service_type: Optional[str] = None  # housekeeping, f_b, engineering, front_office
    priority: str = "medium"
    description: Optional[str] = None
    due_time: Optional[datetime] = None
    verification_required: bool = True


class TaskCreate(TaskBase):
    property_id: uuid.UUID
    room_id: Optional[uuid.UUID] = None
    assigned_to: Optional[uuid.UUID] = None
    ticket_id: Optional[uuid.UUID] = None
    auto_assign: bool = False  # assign to longest-idle free employee


class TaskUpdate(BaseModel):
    assigned_to: Optional[uuid.UUID] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None
    due_time: Optional[datetime] = None


class TaskStatusUpdate(BaseModel):
    status: str
    notes: Optional[str] = None


class TaskMediaResponse(BaseModel):
    id: uuid.UUID
    task_id: uuid.UUID
    media_url: str
    media_type: str
    uploaded_by: uuid.UUID
    uploaded_at: datetime

    class Config:
        from_attributes = True


class TaskResponse(TaskBase):
    id: uuid.UUID
    property_id: uuid.UUID
    room_id: Optional[uuid.UUID] = None
    assigned_to: Optional[uuid.UUID] = None
    created_by: Optional[uuid.UUID] = None
    ticket_id: Optional[uuid.UUID] = None
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    sla_due_at: Optional[datetime] = None
    root_cause_category: Optional[str] = None
    sla_breached_at: Optional[datetime] = None
    escalation_count: int
    media: List[TaskMediaResponse] = []
    created_at: datetime

    class Config:
        from_attributes = True
