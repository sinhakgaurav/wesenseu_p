import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Property(Base):
    __tablename__ = "properties"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Owner (B2B customer) — nullable so properties can exist without a customer account
    customer_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id", ondelete="SET NULL"), nullable=True
    )
    # Portfolio grouping (e.g. all hotels under one owner)
    property_group_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("property_groups.id", ondelete="SET NULL"), nullable=True
    )
    # Optional sub-property / wing / annex under a parent property
    parent_property_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("properties.id", ondelete="SET NULL"), nullable=True
    )

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    property_type: Mapped[str] = mapped_column(String(50), nullable=False)  # Hotel, Hospital, Resort, etc.
    address: Mapped[str] = mapped_column(Text, nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=True)
    state: Mapped[str] = mapped_column(String(100), nullable=True)
    country: Mapped[str] = mapped_column(String(100), default="India")
    phone: Mapped[str] = mapped_column(String(20), nullable=True)
    email: Mapped[str] = mapped_column(String(200), nullable=True)
    logo_url: Mapped[str] = mapped_column(Text, nullable=True)
    total_rooms: Mapped[int] = mapped_column(default=0)
    subscription_plan: Mapped[str] = mapped_column(String(50), default="starter")  # starter, growth, enterprise
    subscription_status: Mapped[str] = mapped_column(String(20), default="active")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    customer: Mapped[Optional["Customer"]] = relationship("Customer", back_populates="properties")
    property_group: Mapped[Optional["PropertyGroup"]] = relationship("PropertyGroup", back_populates="properties")
    parent_property: Mapped[Optional["Property"]] = relationship(
        "Property",
        remote_side="Property.id",
        foreign_keys=[parent_property_id],
        back_populates="child_properties",
    )
    child_properties: Mapped[list["Property"]] = relationship(
        "Property",
        back_populates="parent_property",
        foreign_keys="Property.parent_property_id",
    )
    room_categories: Mapped[list["PropertyRoomCategory"]] = relationship(
        "PropertyRoomCategory", back_populates="property", cascade="all, delete-orphan"
    )
    departments: Mapped[list["Department"]] = relationship("Department", back_populates="property", cascade="all, delete-orphan")
    employees: Mapped[list["Employee"]] = relationship("Employee", back_populates="property")
    rooms: Mapped[list["Room"]] = relationship("Room", back_populates="property")
    inventory_items: Mapped[list["InventoryItem"]] = relationship("InventoryItem", back_populates="property")
    tickets: Mapped[list["Ticket"]] = relationship("Ticket", back_populates="property")
    surveillance_events: Mapped[list["SurveillanceEvent"]] = relationship("SurveillanceEvent", back_populates="property")
    laundry_orders: Mapped[list["LaundryOrder"]] = relationship("LaundryOrder", back_populates="property")
    task_sla_policies: Mapped[list["TaskSlaPolicy"]] = relationship("TaskSlaPolicy", back_populates="property")
