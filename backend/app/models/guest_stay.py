"""Guest stay sessions — scope orders/tickets/bills to one check-in (no cross-guest leakage on same room)."""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class GuestStay(Base):
    __tablename__ = "guest_stays"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("properties.id", ondelete="CASCADE"), nullable=False)
    room_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False)
    guest_name: Mapped[str] = mapped_column(String(200), nullable=False)
    guest_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")  # active | closed
    check_in_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    check_out_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    expected_check_out: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    room: Mapped["Room"] = relationship("Room", back_populates="guest_stays")
    orders: Mapped[list["Order"]] = relationship("Order", back_populates="guest_stay")
    tickets: Mapped[list["Ticket"]] = relationship("Ticket", back_populates="guest_stay")
