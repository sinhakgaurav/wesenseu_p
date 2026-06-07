"""Notify property and department managers."""
from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.department import Department
from app.models.employee import Employee
from app.models.notification import Notification


async def notify_managers(
    db: AsyncSession,
    property_id: uuid.UUID,
    notification_type: str,
    title: str,
    message: str,
    *,
    department_id: Optional[uuid.UUID] = None,
    reference_type: Optional[str] = None,
    reference_id: Optional[uuid.UUID] = None,
) -> list[Notification]:
    """Create in-app notifications for dept manager (if department_id) and property managers."""
    recipient_ids: set[uuid.UUID] = set()

    pm_rows = (
        await db.execute(
            select(Employee.id).where(
                Employee.property_id == property_id,
                Employee.role == "property_manager",
                Employee.status == "active",
            )
        )
    ).all()
    recipient_ids.update(r[0] for r in pm_rows)

    if department_id:
        dept = (await db.execute(select(Department).where(Department.id == department_id))).scalar_one_or_none()
        if dept and dept.manager_id:
            recipient_ids.add(dept.manager_id)
        dm_rows = (
            await db.execute(
                select(Employee.id).where(
                    Employee.property_id == property_id,
                    Employee.department_id == department_id,
                    Employee.role == "dept_manager",
                    Employee.status == "active",
                )
            )
        ).all()
        recipient_ids.update(r[0] for r in dm_rows)
    else:
        dm_rows = (
            await db.execute(
                select(Employee.id).where(
                    Employee.property_id == property_id,
                    Employee.role == "dept_manager",
                    Employee.status == "active",
                )
            )
        ).all()
        recipient_ids.update(r[0] for r in dm_rows)

    created: list[Notification] = []
    for uid in recipient_ids:
        n = Notification(
            user_id=uid,
            property_id=property_id,
            notification_type=notification_type,
            title=title,
            message=message,
            data={
                "reference_type": reference_type,
                "reference_id": str(reference_id) if reference_id else None,
            },
            channels=["in_app"],
            is_read=False,
        )
        db.add(n)
        created.append(n)
    return created
