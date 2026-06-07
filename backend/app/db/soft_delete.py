"""Shared soft-delete helpers (is_active + deleted_at)."""
from datetime import datetime
from typing import Any, Optional, TypeVar

from sqlalchemy import Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import ColumnElement

T = TypeVar("T")


class SoftDeleteMixin:
    """Add to models that support soft delete."""

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


def apply_soft_delete(record: Any) -> None:
    """Mark row inactive; set deleted_at when the column exists."""
    if hasattr(record, "is_active"):
        record.is_active = False
    if hasattr(record, "deleted_at"):
        record.deleted_at = datetime.utcnow()


def restore_soft_deleted(record: Any) -> None:
    if hasattr(record, "is_active"):
        record.is_active = True
    if hasattr(record, "deleted_at"):
        record.deleted_at = None


def not_deleted_clause(model: type) -> Optional[ColumnElement[bool]]:
    """SQLAlchemy filter: active rows only (when model has soft-delete columns)."""
    parts: list[ColumnElement[bool]] = []
    if hasattr(model, "is_active"):
        parts.append(model.is_active.is_(True))
    if hasattr(model, "deleted_at"):
        parts.append(model.deleted_at.is_(None))
    if not parts:
        return None
    from sqlalchemy import and_

    return and_(*parts)
