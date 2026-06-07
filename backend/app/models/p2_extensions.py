"""P2 requirement models: schedules, F&B, dept duties, task inventory rules, room variants."""
import uuid
from datetime import datetime, time
from decimal import Decimal
from typing import Optional

from sqlalchemy import String, DateTime, ForeignKey, Integer, Numeric, Text, Boolean, Time, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DepartmentCatalogDuty(Base):
    __tablename__ = "department_catalog_duties"
    __table_args__ = (UniqueConstraint("department_id", "catalog_item_id", name="uq_dept_catalog_duty"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    department_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("departments.id", ondelete="CASCADE"))
    catalog_item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("catalog_items.id", ondelete="CASCADE"))


class PropertySchedule(Base):
    __tablename__ = "property_schedules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("properties.id", ondelete="CASCADE"))
    department_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)  # 0=Mon .. 6=Sun
    open_time: Mapped[time] = mapped_column(Time, nullable=False)
    close_time: Mapped[time] = mapped_column(Time, nullable=False)
    is_closed: Mapped[bool] = mapped_column(Boolean, default=False)


class EmployeeSchedule(Base):
    __tablename__ = "employee_schedules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), unique=True)
    weekly_off_days: Mapped[list] = mapped_column(JSONB, default=list)  # e.g. [6] for Sunday
    lunch_start: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    lunch_end: Mapped[Optional[time]] = mapped_column(Time, nullable=True)


class PropertyOutlet(Base):
    __tablename__ = "property_outlets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("properties.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    outlet_type: Mapped[str] = mapped_column(String(50), default="restaurant")  # restaurant, kitchen, bar, room_service
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PropertyMenuItem(Base):
    __tablename__ = "property_menu_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    outlet_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("property_outlets.id", ondelete="CASCADE"))
    catalog_item_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("catalog_items.id", ondelete="SET NULL"), nullable=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    photo_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)


class RoomVariant(Base):
    __tablename__ = "room_variants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("properties.id", ondelete="CASCADE"))
    property_room_category_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("property_room_categories.id", ondelete="CASCADE"))
    room_view_catalog_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("catalog_items.id", ondelete="SET NULL"), nullable=True)
    variant_label: Mapped[str] = mapped_column(String(120), nullable=False)
    room_count: Mapped[int] = mapped_column(Integer, default=1)
    price_override: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    floor_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    room_number_prefix: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    start_number: Mapped[int] = mapped_column(Integer, default=101)


class TaskInventoryRule(Base):
    __tablename__ = "task_inventory_rules"
    __table_args__ = (UniqueConstraint("property_id", "task_type", "inventory_item_id", name="uq_task_inv_rule"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("properties.id", ondelete="CASCADE"))
    task_type: Mapped[str] = mapped_column(String(50), nullable=False)
    inventory_item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("inventory_items.id", ondelete="CASCADE"))
    quantity_per_task: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
