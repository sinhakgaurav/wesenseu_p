from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
import uuid


class CustomerCreate(BaseModel):
    company_name: str
    contact_name: str
    email: EmailStr
    password: str
    phone: Optional[str] = None
    address: Optional[str] = None
    subscription_plan: str = "starter"


class CustomerUpdate(BaseModel):
    company_name: Optional[str] = None
    contact_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    logo_url: Optional[str] = None
    subscription_plan: Optional[str] = None
    subscription_status: Optional[str] = None
    is_active: Optional[bool] = None


class CustomerResponse(BaseModel):
    id: uuid.UUID
    company_name: str
    contact_name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    logo_url: Optional[str] = None
    subscription_plan: str
    subscription_status: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class CustomerLoginRequest(BaseModel):
    email: EmailStr
    password: str


class CustomerLoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    customer: CustomerResponse


# ── Dashboard aggregates ──────────────────────────────────────────────────────

class PropertySummary(BaseModel):
    property_id: uuid.UUID
    property_name: str
    property_type: str
    city: Optional[str] = None
    total_rooms: int
    occupied_rooms: int
    rooms_being_cleaned: int
    rooms_ready: int
    open_tickets: int
    tasks_today: int
    verifications_today: int
    avg_verification_score: Optional[float] = None
    last_verification_at: Optional[datetime] = None


class VerificationSummaryItem(BaseModel):
    verification_id: uuid.UUID
    property_name: str
    room_number: str
    task_type: str
    score: Optional[float] = None
    status: str
    defects_count: int
    created_at: datetime


class CustomerDashboard(BaseModel):
    customer_id: uuid.UUID
    company_name: str
    total_properties: int
    total_rooms: int
    active_tickets: int
    verifications_today: int
    avg_score_today: Optional[float] = None
    properties: List[PropertySummary]
    recent_verifications: List[VerificationSummaryItem]
