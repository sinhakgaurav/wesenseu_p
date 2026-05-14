"""Resolve SLA due time and root-cause category from TaskSlaPolicy."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional, Tuple
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task_sla import TaskSlaPolicy


async def resolve_sla_for_task(
    db: AsyncSession,
    property_id: uuid.UUID,
    task_type: str,
    service_type: Optional[str],
) -> Tuple[Optional[datetime], Optional[str], Optional[int]]:
    """
    Returns (sla_due_at from now, root_cause_category, sla_minutes) or (None, None, None) if no policy.
    """
    policies = (
        await db.execute(
            select(TaskSlaPolicy).where(
                TaskSlaPolicy.property_id == property_id,
                TaskSlaPolicy.task_type == task_type,
                TaskSlaPolicy.is_active == True,
            )
        )
    ).scalars().all()
    if not policies:
        return None, None, None

    st = ((service_type or "").strip() or "*")
    exact = next((p for p in policies if p.service_type == st), None)
    chosen = exact or next((p for p in policies if p.service_type in ("*", "")), None)
    if not chosen:
        return None, None, None

    due = datetime.utcnow() + timedelta(minutes=chosen.sla_minutes)
    return due, chosen.root_cause_category, chosen.sla_minutes


async def refresh_task_sla_breach(db: AsyncSession, task) -> None:
    """If past SLA and not terminal, set sla_breached_at and root_cause_category from policy."""
    if not task.sla_due_at or task.sla_breached_at:
        return
    if task.status in ("completed", "approved", "cancelled"):
        return
    if datetime.utcnow() < task.sla_due_at:
        return
    _, rcc, _ = await resolve_sla_for_task(db, task.property_id, task.task_type, task.service_type)
    task.sla_breached_at = datetime.utcnow()
    if rcc and not task.root_cause_category:
        task.root_cause_category = rcc
