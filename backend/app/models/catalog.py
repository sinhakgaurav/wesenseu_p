"""Global reusable catalog entries (amenities, property features, room views, duties, dishes)."""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

CATALOG_KINDS = (
    "amenity",
    "property_feature",
    "room_view",
    "department_duty",
    "dish",
)


class CatalogItem(Base):
    __tablename__ = "catalog_items"
    __table_args__ = (UniqueConstraint("kind", "code", name="uq_catalog_items_kind_code"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    kind: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PropertyCatalogSelection(Base):
    """Property-level feature flags (kitchen, restaurant, star rating, etc.)."""

    __tablename__ = "property_catalog_selections"
    __table_args__ = (UniqueConstraint("property_id", "catalog_item_id", name="uq_property_catalog_selection"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("properties.id", ondelete="CASCADE"), nullable=False)
    catalog_item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("catalog_items.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class RoomCategoryAmenity(Base):
    __tablename__ = "room_category_amenities"
    __table_args__ = (
        UniqueConstraint("property_room_category_id", "catalog_item_id", name="uq_room_category_amenity"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_room_category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("property_room_categories.id", ondelete="CASCADE"), nullable=False
    )
    catalog_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("catalog_items.id", ondelete="CASCADE"), nullable=False
    )
