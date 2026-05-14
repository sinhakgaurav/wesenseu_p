from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date
import uuid


class AttendanceCheckIn(BaseModel):
    notes: Optional[str] = None


class AttendanceCheckOut(BaseModel):
    notes: Optional[str] = None


class AttendanceResponse(BaseModel):
    id: uuid.UUID
    employee_id: uuid.UUID
    property_id: uuid.UUID
    date: date
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    status: str
    notes: Optional[str] = None
    hours_worked: Optional[float] = None

    class Config:
        from_attributes = True


class AttendanceSummary(BaseModel):
    employee_id: uuid.UUID
    employee_name: str
    present_days: int
    absent_days: int
    half_days: int
    leave_days: int
    total_hours: float
    avg_check_in: Optional[str] = None
