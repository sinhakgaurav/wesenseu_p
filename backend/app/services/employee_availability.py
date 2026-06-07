"""Employee availability: leave, weekly off, lunch break."""
from __future__ import annotations

import uuid
from datetime import date, datetime, time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee import Attendance, Employee
from app.models.p2_extensions import EmployeeSchedule


async def is_employee_unavailable_today(db: AsyncSession, emp: Employee, now: datetime | None = None) -> bool:
    now = now or datetime.utcnow()
    today = now.date()

    att = (
        await db.execute(
            select(Attendance).where(
                Attendance.employee_id == emp.id,
                Attendance.date == today,
            )
        )
    ).scalar_one_or_none()
    if att and att.status in ("leave", "absent", "weekly_off"):
        return True

    sched = (
        await db.execute(select(EmployeeSchedule).where(EmployeeSchedule.employee_id == emp.id))
    ).scalar_one_or_none()
    if sched and sched.weekly_off_days:
        # Python weekday: Mon=0; store same convention
        if now.weekday() in sched.weekly_off_days:
            return True
        if sched.lunch_start and sched.lunch_end:
            t = now.time()
            if sched.lunch_start <= t <= sched.lunch_end:
                return True

    return False
