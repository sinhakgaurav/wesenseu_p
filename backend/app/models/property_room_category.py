"""Configurable room types per property (replaces ad-hoc strings). Benchmarks attach per category + aspect."""
import uuid
from datetime import datetime
from typing import Optional

from decimal import Decimal

from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, Integer, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PropertyRoomCategory(Base):
    __tablename__ = "property_room_categories"
    __table_args__ = (UniqueConstraint("property_id", "code", name="uq_property_room_category_property_code"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("properties.id", ondelete="CASCADE"), nullable=False)
    code: Mapped[str] = mapped_column(String(64), nullable=False)  # machine slug, e.g. classic, deluxe
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)  # e.g. Classic Room
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    base_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    property: Mapped["Property"] = relationship("Property", back_populates="room_categories")
    benchmarks: Mapped[list["RoomCategoryBenchmark"]] = relationship(
        "RoomCategoryBenchmark", back_populates="room_category_ref", foreign_keys="RoomCategoryBenchmark.property_room_category_id"
    )
