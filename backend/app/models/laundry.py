import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class LaundryOrder(Base):
    """Guest / room laundry tracking (wash, dry-clean, press)."""
    __tablename__ = "laundry_orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("properties.id"), nullable=False)
    room_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("rooms.id"), nullable=True)
    guest_name: Mapped[str] = mapped_column(String(200), nullable=True)
    guest_phone: Mapped[str] = mapped_column(String(20), nullable=True)
    # received, collected, washing, drying, ironing, ready, delivered, cancelled
    status: Mapped[str] = mapped_column(String(30), default="received")
    priority: Mapped[str] = mapped_column(String(20), default="medium")
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    # [{ "description": "Shirts", "quantity": 2, "service_type": "wash" }, ...]
    items: Mapped[list] = mapped_column(JSONB, default=list)
    assigned_to: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=True)
    expected_ready_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    delivered_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    property: Mapped["Property"] = relationship("Property", back_populates="laundry_orders")
    room: Mapped["Room"] = relationship("Room", back_populates="laundry_orders")
