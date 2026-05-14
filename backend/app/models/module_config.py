import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

AVAILABLE_MODULES = [
    "rooms", "tasks", "tickets", "inventory", "orders",
    "attendance", "feedback", "surveillance", "verification",
    "reports", "notifications", "support_chat",
]


class ModuleConfig(Base):
    """
    Feature-flag table: controls which modules are active per property.
    Super-admin manages this; checked at runtime by the API.
    """
    __tablename__ = "module_configs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("properties.id", ondelete="CASCADE"), nullable=False
    )
    module_name: Mapped[str] = mapped_column(String(50), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    # Module-specific settings (e.g. {"max_cameras": 5})
    config: Mapped[dict] = mapped_column(JSONB, default=dict)
    updated_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    property: Mapped["Property"] = relationship("Property")

    __table_args__ = (
        # One row per module per property
        __import__("sqlalchemy").UniqueConstraint("property_id", "module_name", name="uq_module_config_property_module"),
    )
