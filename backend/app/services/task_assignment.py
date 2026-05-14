"""Assign tasks to the employee who has been idle longest among those currently free."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee import Employee
from app.models.task import Task

BUSY_STATUSES = ("assigned", "in_progress", "verification_pending")


async def pick_longest_idle_free_employee(
    db: AsyncSession,
    property_id: uuid.UUID,
    department_id: Optional[uuid.UUID] = None,
) -> Optional[Employee]:
    """
    Free = no tasks in BUSY_STATUSES for this property.
    Idle score = time since last completed/approved task (larger = longer idle).
    Employees with no completions are treated as maximally idle.
    """
    q = select(Employee).where(
        Employee.property_id == property_id,
        Employee.status == "active",
        Employee.role == "employee",
    )
    if department_id:
        q = q.where(Employee.department_id == department_id)
    emps = (await db.execute(q)).scalars().all()
    if not emps:
        return None

    best: Optional[Employee] = None
    best_idle_seconds: float = -1.0
    now = datetime.utcnow()

    for emp in emps:
        busy = (
            await db.execute(
                select(func.count())
                .select_from(Task)
                .where(
                    Task.assigned_to == emp.id,
                    Task.property_id == property_id,
                    Task.status.in_(BUSY_STATUSES),
                )
            )
        ).scalar_one()
        if busy and int(busy) > 0:
            continue

        last_done = (
            await db.execute(
                select(func.max(Task.completed_at))
                .where(
                    Task.assigned_to == emp.id,
                    Task.property_id == property_id,
                    Task.status.in_(("completed", "approved")),
                )
            )
        ).scalar_one_or_none()

        if last_done is None:
            idle = 1e12
        else:
            idle = (now - last_done).total_seconds()

        if idle > best_idle_seconds:
            best_idle_seconds = idle
            best = emp

    return best
