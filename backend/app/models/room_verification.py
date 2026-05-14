import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, DateTime, ForeignKey, Numeric, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class RoomVerification(Base):
    __tablename__ = "room_verifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False)

    # Queue / async tracking
    queue_status: Mapped[str] = mapped_column(String(20), default="queued")
    # queued | dispatched | processing | completed | failed
    wesenseu_job_id: Mapped[str] = mapped_column(String(200), nullable=True)
    # Image URLs submitted to WesenseU
    submitted_image_urls: Mapped[list] = mapped_column(JSONB, nullable=True)

    # Result fields (populated by callback)
    verification_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=True)
    cleanliness_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=True)
    organization_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=True)
    amenities_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=True)
    check_results: Mapped[dict] = mapped_column(JSONB, nullable=True)

    status: Mapped[str] = mapped_column(String(20), default="pending")
    # pending | approved | needs_review | rejected | manual_override
    defects_found: Mapped[dict] = mapped_column(JSONB, nullable=True)
    ai_response: Mapped[dict] = mapped_column(JSONB, nullable=True)

    verified_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    verified_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    task: Mapped["Task"] = relationship("Task", back_populates="verification")
