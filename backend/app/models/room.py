import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("properties.id"), nullable=False)
    room_number: Mapped[str] = mapped_column(String(20), nullable=False)
    room_category: Mapped[str] = mapped_column(String(50), nullable=False)  # Deluxe, Standard, Suite, ICU, VIP, etc.
    floor_number: Mapped[int] = mapped_column(Integer, nullable=True)
    room_status: Mapped[str] = mapped_column(String(30), default="vacant")
    # vacant, occupied, cleaning_pending, cleaning_in_progress, ready, maintenance, inspection_pending, blocked
    occupancy_status: Mapped[str] = mapped_column(String(20), default="vacant")  # occupied, vacant
    guest_name: Mapped[str] = mapped_column(String(200), nullable=True)
    guest_phone: Mapped[str] = mapped_column(String(20), nullable=True)
    check_in_time: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    check_out_time: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    expected_check_out: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    last_cleaned_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    qr_code_url: Mapped[str] = mapped_column(Text, nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    property: Mapped["Property"] = relationship("Property", back_populates="rooms")
    room_category_definition: Mapped[Optional["PropertyRoomCategory"]] = relationship(
        "PropertyRoomCategory", foreign_keys="Room.property_room_category_id"
    )
    tasks: Mapped[list["Task"]] = relationship("Task", back_populates="room")
    tickets: Mapped[list["Ticket"]] = relationship("Ticket", back_populates="room")
    orders: Mapped[list["Order"]] = relationship("Order", back_populates="room")
    feedback: Mapped[list["Feedback"]] = relationship("Feedback", back_populates="room")
    audit_logs: Mapped[list["RoomAuditLog"]] = relationship("RoomAuditLog", back_populates="room")
    laundry_orders: Mapped[list["LaundryOrder"]] = relationship("LaundryOrder", back_populates="room")


class RoomAuditLog(Base):
    __tablename__ = "room_audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("rooms.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    old_status: Mapped[str] = mapped_column(String(30), nullable=True)
    new_status: Mapped[str] = mapped_column(String(30), nullable=True)
    performed_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    room: Mapped["Room"] = relationship("Room", back_populates="audit_logs")
