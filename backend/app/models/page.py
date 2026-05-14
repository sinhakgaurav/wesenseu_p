import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Page(Base):
    """
    CMS pages for the public-facing website (About, Contact, Terms, Privacy, Blogs, custom).
    Content is stored as structured JSON blocks for flexible rendering.
    """
    __tablename__ = "pages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    page_type: Mapped[str] = mapped_column(String(50), default="custom")
    # about | contact | pricing | terms | privacy | blog | faq | custom
    meta_title: Mapped[str] = mapped_column(String(200), nullable=True)
    meta_description: Mapped[str] = mapped_column(Text, nullable=True)
    # Hero section
    hero_heading: Mapped[str] = mapped_column(String(300), nullable=True)
    hero_subheading: Mapped[str] = mapped_column(Text, nullable=True)
    hero_image_url: Mapped[str] = mapped_column(Text, nullable=True)
    # Structured content blocks: [{type: "text"|"image"|"cta"|"cards", ...}]
    content_blocks: Mapped[list] = mapped_column(JSONB, default=list)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    published_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
