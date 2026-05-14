import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, DateTime, ForeignKey, Numeric, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("properties.id"), nullable=False)
    room_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("rooms.id"), nullable=True)
    department_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True)
    guest_name: Mapped[str] = mapped_column(String(200), nullable=True)
    guest_phone: Mapped[str] = mapped_column(String(20), nullable=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5
    review_text: Mapped[str] = mapped_column(Text, nullable=True)
    sentiment_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=True)
    sentiment_label: Mapped[str] = mapped_column(String(20), nullable=True)  # positive, neutral, negative
    source: Mapped[str] = mapped_column(String(30), default="qr")  # qr, app, manual
    is_public: Mapped[bool] = mapped_column(default=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    # pending | reviewed | flagged | resolved
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    room: Mapped["Room"] = relationship("Room", back_populates="feedback")
    department: Mapped["Department"] = relationship("Department", back_populates="feedback")
