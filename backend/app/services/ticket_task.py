"""Create operational tasks from guest/staff tickets."""
from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task
from app.models.ticket import Ticket
from app.services.task_assignment import pick_longest_idle_free_employee
from app.services.task_sla import resolve_sla_for_task

# ticket_type -> (task_type, service_type, verification_required)
TICKET_TASK_MAP: dict[str, tuple[str, Optional[str], bool]] = {
    "housekeeping": ("cleaning", "housekeeping", True),
    "maintenance": ("maintenance", "engineering", False),
    "complaint": ("other", "front_office", False),
    "service_request": ("other", "front_office", False),
    "feedback": ("other", "front_office", False),
    "emergency": ("other", None, False),
    "food": ("delivery", "f_b", False),
}


async def create_task_for_ticket(db: AsyncSession, ticket: Ticket, *, auto_assign: bool = True) -> Task:
    task_type, service_type, verification_required = TICKET_TASK_MAP.get(
        ticket.ticket_type, ("other", None, False)
    )
    task = Task(
        property_id=ticket.property_id,
        room_id=ticket.room_id,
        ticket_id=ticket.id,
        task_type=task_type,
        service_type=service_type,
        priority=ticket.priority,
        description=ticket.description or ticket.title,
        verification_required=verification_required,
        status="pending",
    )
    sla_due, _, _ = await resolve_sla_for_task(db, task.property_id, task.task_type, task.service_type)
    if sla_due:
        task.sla_due_at = sla_due
        task.due_time = sla_due

    if auto_assign:
        emp = await pick_longest_idle_free_employee(db, ticket.property_id)
        if emp:
            task.assigned_to = emp.id
            task.status = "assigned"

    db.add(task)
    return task
