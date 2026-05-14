"""Portfolio / owner grouping: multiple properties (and nested groups) under one customer."""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PropertyGroup(Base):
    __tablename__ = "property_groups"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    parent_group_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("property_groups.id", ondelete="SET NULL"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    customer: Mapped[Optional["Customer"]] = relationship("Customer", back_populates="property_groups")
    parent: Mapped[Optional["PropertyGroup"]] = relationship(
        "PropertyGroup", remote_side="PropertyGroup.id", foreign_keys=[parent_group_id], back_populates="child_groups"
    )
    child_groups: Mapped[list["PropertyGroup"]] = relationship(
        "PropertyGroup", back_populates="parent", foreign_keys=[parent_group_id]
    )
    properties: Mapped[list["Property"]] = relationship("Property", back_populates="property_group")
