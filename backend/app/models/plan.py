import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, DateTime, Boolean, Integer, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class Plan(Base):
    """
    Subscription plans shown on the public pricing page and managed via admin panel.
    """
    __tablename__ = "plans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    # starter | growth | enterprise | custom
    slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    tagline: Mapped[str] = mapped_column(String(200), nullable=True)
    price_monthly: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=True)
    price_yearly: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="INR")
    room_limit: Mapped[int] = mapped_column(Integer, nullable=True)   # None = unlimited
    employee_limit: Mapped[int] = mapped_column(Integer, nullable=True)
    # JSON list of feature strings shown on pricing page
    features: Mapped[list] = mapped_column(JSONB, default=list)
    # JSON map of module keys → bool / settings for module_config defaults
    module_defaults: Mapped[dict] = mapped_column(JSONB, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_popular: Mapped[bool] = mapped_column(Boolean, default=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    cta_text: Mapped[str] = mapped_column(String(50), default="Get Started")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
