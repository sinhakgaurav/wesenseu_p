from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid


class RoomBase(BaseModel):
    room_number: str
    room_category: Optional[str] = None
    property_room_category_id: Optional[uuid.UUID] = None
    floor_number: Optional[int] = None
    notes: Optional[str] = None


class RoomCreate(RoomBase):
    property_id: uuid.UUID


class RoomUpdate(BaseModel):
    room_number: Optional[str] = None
    room_category: Optional[str] = None
    property_room_category_id: Optional[uuid.UUID] = None
    floor_number: Optional[int] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class RoomStatusUpdate(BaseModel):
    room_status: str
    guest_name: Optional[str] = None
    guest_phone: Optional[str] = None
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None
    expected_check_out: Optional[datetime] = None
    notes: Optional[str] = None


class GuestCheckInRequest(BaseModel):
    guest_name: str
    guest_phone: Optional[str] = None
    expected_check_out: Optional[datetime] = None
    notes: Optional[str] = None


class RoomResponse(RoomBase):
    id: uuid.UUID
    property_id: uuid.UUID
    room_status: str
    occupancy_status: str
    guest_name: Optional[str] = None
    guest_phone: Optional[str] = None
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None
    expected_check_out: Optional[datetime] = None
    last_cleaned_at: Optional[datetime] = None
    qr_code_url: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
