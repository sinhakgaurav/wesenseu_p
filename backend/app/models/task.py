from typing import Optional
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("properties.id"), nullable=False)
    room_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("rooms.id"), nullable=True)
    assigned_to: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=True)
    ticket_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tickets.id"), nullable=True)
    task_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # cleaning, maintenance, delivery, sanitization, inspection, laundry, other
    service_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # housekeeping, f_b, engineering
    priority: Mapped[str] = mapped_column(String(20), default="medium")  # low, medium, high, critical
    status: Mapped[str] = mapped_column(String(30), default="pending")
    # pending, assigned, in_progress, verification_pending, approved, rejected, rework_required, completed, cancelled
    description: Mapped[str] = mapped_column(Text, nullable=True)
    due_time: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    sla_due_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    root_cause_category: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    sla_breached_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    verification_required: Mapped[bool] = mapped_column(default=True)
    escalation_count: Mapped[int] = mapped_column(default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    room: Mapped["Room"] = relationship("Room", back_populates="tasks")
    assigned_employee: Mapped["Employee"] = relationship("Employee", back_populates="assigned_tasks", foreign_keys=[assigned_to])
    creator: Mapped["Employee"] = relationship("Employee", back_populates="created_tasks", foreign_keys=[created_by])
    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="tasks")
    media: Mapped[list["TaskMedia"]] = relationship("TaskMedia", back_populates="task", cascade="all, delete-orphan")
    verification: Mapped["RoomVerification"] = relationship("RoomVerification", back_populates="task", uselist=False)


class TaskMedia(Base):
    __tablename__ = "task_media"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False)
    media_url: Mapped[str] = mapped_column(Text, nullable=False)
    media_type: Mapped[str] = mapped_column(String(20), nullable=False)  # photo, video
    file_size: Mapped[int] = mapped_column(default=0)
    uploaded_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    task: Mapped["Task"] = relationship("Task", back_populates="media")
