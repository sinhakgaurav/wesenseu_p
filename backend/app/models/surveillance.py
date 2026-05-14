import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class SurveillanceCamera(Base):
    __tablename__ = "surveillance_cameras"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("properties.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    location: Mapped[str] = mapped_column(String(200), nullable=True)
    stream_url: Mapped[str] = mapped_column(Text, nullable=True)
    camera_type: Mapped[str] = mapped_column(String(50), default="ip")  # ip, analog, ptz
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    ai_monitoring_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    # Per-camera checklist: [{ "scenario_code", "enabled", "threshold_seconds" }, ...]
    scenario_rules: Mapped[list] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    events: Mapped[list["SurveillanceEvent"]] = relationship("SurveillanceEvent", back_populates="camera")


class SurveillanceEvent(Base):
    __tablename__ = "surveillance_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("properties.id"), nullable=False)
    camera_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("surveillance_cameras.id"), nullable=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    scenario_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    detection_mode: Mapped[str] = mapped_column(String(20), default="instant")  # instant | duration
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    threshold_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    root_cause_hint: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # trespassing, unauthorized_access, employee_absence, bell_desk_unavailable,
    # kitchen_hygiene_violation, garbage_overflow, corridor_obstruction, cleanliness_issue
    severity: Mapped[str] = mapped_column(String(20), default="medium")  # low, medium, high, critical
    description: Mapped[str] = mapped_column(Text, nullable=True)
    event_snapshot: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="open")  # open, acknowledged, resolved
    ai_confidence: Mapped[Optional[float]] = mapped_column(nullable=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    property: Mapped["Property"] = relationship("Property", back_populates="surveillance_events")
    camera: Mapped["SurveillanceCamera"] = relationship("SurveillanceCamera", back_populates="events")
