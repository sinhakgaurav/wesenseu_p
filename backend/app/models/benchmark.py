import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class RoomCategoryBenchmark(Base):
    """
    Reference / benchmark images stored per room-category per property.
    WesenseU compares the staff's after-service photos against these images.
    """
    __tablename__ = "room_category_benchmarks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("properties.id", ondelete="CASCADE"), nullable=False)
    property_room_category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("property_room_categories.id", ondelete="SET NULL"), nullable=True
    )
    room_category: Mapped[str] = mapped_column(String(50), nullable=False)  # Deluxe, Standard, Suite, ICU …
    image_url: Mapped[str] = mapped_column(Text, nullable=False)
    thumbnail_url: Mapped[str] = mapped_column(Text, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    # Which aspects this benchmark covers
    aspect: Mapped[str] = mapped_column(String(50), default="general")
    # general | bed_making | bathroom | furniture | floor | amenities
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    property: Mapped["Property"] = relationship("Property")
    room_category_ref: Mapped[Optional["PropertyRoomCategory"]] = relationship(
        "PropertyRoomCategory", back_populates="benchmarks", foreign_keys="RoomCategoryBenchmark.property_room_category_id"
    )
    creator: Mapped["Employee"] = relationship("Employee", foreign_keys=[created_by])
