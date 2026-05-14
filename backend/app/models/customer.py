import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Customer(Base):
    """
    A B2B client (e.g. a hotel chain owner) who can own multiple Properties.
    Separate from Employee — customers log in to a read-only analytics dashboard.
    """
    __tablename__ = "customers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_name: Mapped[str] = mapped_column(String(200), nullable=False)
    contact_name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(500), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=True)
    address: Mapped[str] = mapped_column(Text, nullable=True)
    logo_url: Mapped[str] = mapped_column(Text, nullable=True)

    subscription_plan: Mapped[str] = mapped_column(String(50), default="starter")
    # starter | growth | enterprise
    subscription_status: Mapped[str] = mapped_column(String(20), default="active")
    # active | suspended | cancelled

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    properties: Mapped[list["Property"]] = relationship("Property", back_populates="customer")
    property_groups: Mapped[list["PropertyGroup"]] = relationship("PropertyGroup", back_populates="customer")
