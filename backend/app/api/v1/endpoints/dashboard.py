from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Optional
from datetime import datetime, date, timedelta
import uuid

from app.db.base import get_db
from app.models.room import Room
from app.models.task import Task
from app.models.ticket import Ticket
from app.models.employee import Employee
from app.models.inventory import InventoryItem
from app.models.surveillance import SurveillanceEvent
from app.schemas.dashboard import DashboardStats, PlatformDashboardStats
from app.api.v1.deps import get_current_user
from app.models.property import Property
from app.models.customer import Customer
from fastapi import HTTPException

router = APIRouter()


async def _stats_for_property(db: AsyncSession, prop_id: uuid.UUID) -> DashboardStats:
    today = datetime.utcnow().date()

    # Room stats
    rooms_result = await db.execute(
        select(Room.room_status, func.count(Room.id))
        .where(Room.property_id == prop_id, Room.is_active == True)
        .group_by(Room.room_status)
    )
    room_counts = dict(rooms_result.all())

    total_rooms = sum(room_counts.values())
    occupied_rooms = room_counts.get("occupied", 0)
    vacant_rooms = room_counts.get("vacant", 0)
    cleaning_pending = room_counts.get("cleaning_pending", 0) + room_counts.get("cleaning_in_progress", 0)
    ready_rooms = room_counts.get("ready", 0)
    maintenance_rooms = room_counts.get("maintenance", 0)

    # Task stats
    tasks_result = await db.execute(
        select(Task.status, func.count(Task.id))
        .where(Task.property_id == prop_id)
        .group_by(Task.status)
    )
    task_counts = dict(tasks_result.all())
    active_tasks = task_counts.get("in_progress", 0) + task_counts.get("assigned", 0)
    pending_tasks = task_counts.get("pending", 0)

    completed_today_result = await db.execute(
        select(func.count(Task.id)).where(
            Task.property_id == prop_id,
            Task.status == "completed",
            func.date(Task.completed_at) == today,
        )
    )
    completed_tasks_today = completed_today_result.scalar() or 0

    overdue_result = await db.execute(
        select(func.count(Task.id)).where(
            Task.property_id == prop_id,
            Task.due_time < datetime.utcnow(),
            Task.status.notin_(["completed", "approved", "cancelled"]),
        )
    )
    overdue_tasks = overdue_result.scalar() or 0

    # Ticket stats
    tickets_result = await db.execute(
        select(Ticket.status, func.count(Ticket.id))
        .where(Ticket.property_id == prop_id)
        .group_by(Ticket.status)
    )
    ticket_counts = dict(tickets_result.all())
    open_tickets = ticket_counts.get("open", 0) + ticket_counts.get("assigned", 0) + ticket_counts.get("in_progress", 0)

    resolved_today_result = await db.execute(
        select(func.count(Ticket.id)).where(
            Ticket.property_id == prop_id,
            Ticket.status.in_(["resolved", "closed"]),
            func.date(Ticket.resolved_at) == today,
        )
    )
    resolved_tickets_today = resolved_today_result.scalar() or 0

    critical_tickets_result = await db.execute(
        select(func.count(Ticket.id)).where(
            Ticket.property_id == prop_id,
            Ticket.priority == "critical",
            Ticket.status.notin_(["resolved", "closed"]),
        )
    )
    critical_tickets = critical_tickets_result.scalar() or 0

    # Employee stats
    emp_result = await db.execute(
        select(func.count(Employee.id)).where(
            Employee.property_id == prop_id,
            Employee.status == "active",
        )
    )
    total_employees = emp_result.scalar() or 0

    available_emp_result = await db.execute(
        select(func.count(Employee.id)).where(
            Employee.property_id == prop_id,
            Employee.status == "active",
            Employee.is_available == True,
        )
    )
    available_employees = available_emp_result.scalar() or 0

    # Inventory alerts
    inventory_items_result = await db.execute(
        select(InventoryItem).where(
            InventoryItem.property_id == prop_id,
            InventoryItem.is_active == True,
        )
    )
    items = inventory_items_result.scalars().all()
    inventory_alerts = sum(1 for item in items if item.current_stock <= item.minimum_stock)

    # Surveillance alerts
    surveillance_result = await db.execute(
        select(func.count(SurveillanceEvent.id)).where(
            SurveillanceEvent.property_id == prop_id,
            SurveillanceEvent.status == "open",
        )
    )
    surveillance_alerts = surveillance_result.scalar() or 0

    room_status_chart = [
        {"status": k, "count": v, "label": k.replace("_", " ").title()}
        for k, v in room_counts.items()
    ]

    task_completion_rate = 0.0
    total_tasks = sum(task_counts.values())
    if total_tasks > 0:
        task_completion_rate = round(
            (task_counts.get("completed", 0) + task_counts.get("approved", 0)) / total_tasks * 100, 1
        )

    return DashboardStats(
        total_rooms=total_rooms or 0,
        occupied_rooms=occupied_rooms,
        vacant_rooms=vacant_rooms,
        cleaning_pending=cleaning_pending,
        ready_rooms=ready_rooms,
        maintenance_rooms=maintenance_rooms,
        active_tasks=active_tasks,
        pending_tasks=pending_tasks,
        completed_tasks_today=completed_tasks_today,
        overdue_tasks=overdue_tasks,
        open_tickets=open_tickets,
        resolved_tickets_today=resolved_tickets_today,
        critical_tickets=critical_tickets,
        total_employees=total_employees,
        available_employees=available_employees,
        employees_on_duty=total_employees - available_employees,
        inventory_alerts=inventory_alerts,
        surveillance_alerts=surveillance_alerts,
        room_status_chart=room_status_chart,
        task_completion_rate=task_completion_rate,
    )


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    property_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    prop_id = property_id or current_user.property_id
    if not prop_id:
        if current_user.role == "super_admin":
            first = (await db.execute(select(Property.id).where(Property.is_active == True).limit(1))).scalar_one_or_none()
            if not first:
                return DashboardStats(
                    total_rooms=0, occupied_rooms=0, vacant_rooms=0, cleaning_pending=0,
                    ready_rooms=0, maintenance_rooms=0, active_tasks=0, pending_tasks=0,
                    completed_tasks_today=0, overdue_tasks=0, open_tickets=0,
                    resolved_tickets_today=0, critical_tickets=0, total_employees=0,
                    available_employees=0, employees_on_duty=0, inventory_alerts=0,
                    surveillance_alerts=0, room_status_chart=[], task_completion_rate=0.0,
                )
            prop_id = first
        else:
            raise HTTPException(status_code=400, detail="property_id is required")
    return await _stats_for_property(db, prop_id)


@router.get("/platform", response_model=PlatformDashboardStats)
async def get_platform_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    """Aggregated stats across all properties (super_admin)."""
    if current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Super admin only")

    total_properties = (await db.execute(select(func.count(Property.id)))).scalar() or 0
    active_properties = (
        await db.execute(select(func.count(Property.id)).where(Property.is_active == True))
    ).scalar() or 0
    total_customers = (await db.execute(select(func.count(Customer.id)))).scalar() or 0
    total_rooms = (
        await db.execute(select(func.count(Room.id)).where(Room.is_active == True))
    ).scalar() or 0
    open_tasks = (
        await db.execute(
            select(func.count(Task.id)).where(Task.status.notin_(["approved", "rejected", "cancelled", "completed"]))
        )
    ).scalar() or 0
    open_tickets = (
        await db.execute(
            select(func.count(Ticket.id)).where(Ticket.status.notin_(["resolved", "closed"]))
        )
    ).scalar() or 0
    total_employees = (await db.execute(select(func.count(Employee.id)))).scalar() or 0

    props = (await db.execute(select(Property).where(Property.is_active == True).order_by(Property.name))).scalars().all()
    property_summaries = []
    for p in props:
        s = await _stats_for_property(db, p.id)
        property_summaries.append({
            "property_id": str(p.id),
            "property_name": p.name,
            "city": p.city,
            "total_rooms": s.total_rooms,
            "open_tasks": s.active_tasks + s.pending_tasks,
            "open_tickets": s.open_tickets,
            "occupancy_pct": round((s.occupied_rooms / s.total_rooms * 100), 1) if s.total_rooms else 0,
        })

    return PlatformDashboardStats(
        total_properties=total_properties,
        active_properties=active_properties,
        total_customers=total_customers,
        total_rooms=total_rooms,
        open_tasks=open_tasks,
        open_tickets=open_tickets,
        total_employees=total_employees,
        properties=property_summaries,
    )
