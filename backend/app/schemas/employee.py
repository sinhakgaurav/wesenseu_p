from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, date
from decimal import Decimal
import uuid


class EmployeeBase(BaseModel):
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    role: str
    department_id: Optional[uuid.UUID] = None
    shift_type: Optional[str] = None
    joining_date: Optional[date] = None
    salary: Optional[Decimal] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    status: str = "active"


class EmployeeCreate(EmployeeBase):
    password: str
    property_id: uuid.UUID


class EmployeeUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    department_id: Optional[uuid.UUID] = None
    shift_type: Optional[str] = None
    salary: Optional[Decimal] = None
    status: Optional[str] = None
    is_available: Optional[bool] = None


class EmployeeResponse(EmployeeBase):
    id: uuid.UUID
    employee_code: str
    property_id: uuid.UUID
    avatar_url: Optional[str] = None
    is_available: bool
    last_login: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
