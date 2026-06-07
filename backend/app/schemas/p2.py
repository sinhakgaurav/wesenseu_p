from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, time
from decimal import Decimal
import uuid


class BulkRoomCreate(BaseModel):
    property_id: uuid.UUID
    property_room_category_id: uuid.UUID
    floor_number: Optional[int] = None
    room_number_prefix: str = ""
    start_number: int = 101
    count: int = Field(..., ge=1, le=500)
    room_view_catalog_id: Optional[uuid.UUID] = None


class RoomVariantCreate(BaseModel):
    property_id: uuid.UUID
    property_room_category_id: uuid.UUID
    variant_label: str
    room_count: int = Field(..., ge=1, le=500)
    price_override: Optional[Decimal] = None
    floor_number: Optional[int] = None
    room_number_prefix: Optional[str] = None
    start_number: int = 101
    room_view_catalog_id: Optional[uuid.UUID] = None
    create_rooms: bool = True


class AttendanceRecordCreate(BaseModel):
    employee_id: uuid.UUID
    record_date: date
    status: str = Field(..., pattern="^(present|absent|half_day|leave|weekly_off)$")
    notes: Optional[str] = None


class EmployeeScheduleUpdate(BaseModel):
    weekly_off_days: List[int] = Field(default_factory=list)
    lunch_start: Optional[time] = None
    lunch_end: Optional[time] = None


class PropertyScheduleEntry(BaseModel):
    day_of_week: int = Field(..., ge=0, le=6)
    open_time: time
    close_time: time
    department_id: Optional[uuid.UUID] = None
    is_closed: bool = False


class PropertyScheduleSet(BaseModel):
    schedules: List[PropertyScheduleEntry]


class OutletUpdate(BaseModel):
    name: Optional[str] = None
    outlet_type: Optional[str] = None
    is_active: Optional[bool] = None


class OutletCreate(BaseModel):
    property_id: uuid.UUID
    name: str
    outlet_type: str = "restaurant"


class MenuItemCreate(BaseModel):
    name: str
    price: Decimal
    catalog_item_id: Optional[uuid.UUID] = None


class MenuItemUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[Decimal] = None
    is_available: Optional[bool] = None


class TaskInventoryRuleCreate(BaseModel):
    property_id: uuid.UUID
    task_type: str
    inventory_item_id: uuid.UUID
    quantity_per_task: int = 1


class ImportResult(BaseModel):
    created: int = 0
    updated: int = 0
    errors: List[str] = Field(default_factory=list)
