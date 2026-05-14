from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from typing import Optional
from datetime import datetime, date, timedelta
import uuid

from app.db.base import get_db
from app.models.room import Room
from app.models.task import Task
from app.models.ticket import Ticket
from app.models.employee import Employee
from app.models.inventory import InventoryItem, InventoryTransaction
from app.models.order import Order
from app.models.department import Department
from app.schemas.reports import (
    OccupancyReport, TaskReport, TicketReport, FullReport,
    OccupancyDataPoint, TaskPerformancePoint, TicketTrendPoint,
    DepartmentPerformance, InventoryConsumption, RevenuePoint,
)
from app.api.v1.deps import get_current_user

router = APIRouter()


def _date_range(days: int = 30, end: Optional[date] = None):
    end = end or date.today()
    start = end - timedelta(days=days - 1)
    return start, end


@router.get("/occupancy", response_model=OccupancyReport)
async def occupancy_report(
    property_id: Optional[uuid.UUID] = None,
    days: int = Query(30, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    prop_id = property_id or current_user.property_id
    start, end = _date_range(days)

    rooms_result = await db.execute(
        select(Room.room_status, func.count(Room.id))
        .where(Room.property_id == prop_id, Room.is_active == True)
        .group_by(Room.room_status)
    )
    status_counts = dict(rooms_result.all())
    total = sum(status_counts.values()) or 1
    cleaning = status_counts.get("cleaning_pending", 0) + status_counts.get("cleaning_in_progress", 0)
    maintenance = status_counts.get("maintenance", 0)

    data = []
    occ_rates = []
    for i in range(days):
        d = start + timedelta(days=i)
        day_start = datetime.combine(d, datetime.min.time())
        day_end = datetime.combine(d, datetime.max.time())
        # Guest stays overlapping this calendar day (check-in / check-out driven)
        guest_occ_r = await db.execute(
            select(func.count(Room.id)).where(
                Room.property_id == prop_id,
                Room.is_active == True,
                Room.check_in_time.isnot(None),
                Room.check_in_time <= day_end,
                or_(Room.check_out_time.is_(None), Room.check_out_time >= day_start),
            )
        )
        occ = int(guest_occ_r.scalar() or 0)
        vacant = max(0, total - occ - cleaning - maintenance)
        rate = round(occ / total * 100, 1) if total else 0.0
        occ_rates.append(rate)
        data.append(OccupancyDataPoint(
            date=d.isoformat(),
            occupied=occ,
            vacant=vacant,
            cleaning=cleaning,
            maintenance=maintenance,
            occupancy_rate=rate,
        ))

    avg_rate = round(sum(occ_rates) / len(occ_rates), 1) if occ_rates else 0.0
    peak = max(data, key=lambda x: x.occupancy_rate) if data else None

    return OccupancyReport(
        period=f"{start.isoformat()} to {end.isoformat()}",
        data=data,
        avg_occupancy_rate=avg_rate,
        peak_occupancy_date=peak.date if peak else None,
    )


@router.get("/tasks", response_model=TaskReport)
async def task_report(
    property_id: Optional[uuid.UUID] = None,
    days: int = Query(30, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    prop_id = property_id or current_user.property_id
    start, end = _date_range(days)
    start_dt = datetime.combine(start, datetime.min.time())
    end_dt = datetime.combine(end, datetime.max.time())

    completed_result = await db.execute(
        select(func.date(Task.completed_at).label("d"), func.count(Task.id))
        .where(
            Task.property_id == prop_id,
            Task.status.in_(["completed", "approved"]),
            Task.completed_at.between(start_dt, end_dt),
        )
        .group_by(func.date(Task.completed_at))
    )
    completed_by_day = {}
    for r in completed_result.all():
        k = r[0].isoformat() if hasattr(r[0], "isoformat") else str(r[0])
        completed_by_day[k] = r[1]

    overdue_result = await db.execute(
        select(func.count(Task.id)).where(
            Task.property_id == prop_id,
            Task.due_time < datetime.utcnow(),
            Task.status.notin_(["completed", "approved", "cancelled"]),
        )
    )
    total_overdue = overdue_result.scalar() or 0

    pending_result = await db.execute(
        select(func.count(Task.id)).where(
            Task.property_id == prop_id,
            Task.status == "pending",
        )
    )
    total_pending = pending_result.scalar() or 0

    avg_time_result = await db.execute(
        select(func.avg(func.extract("epoch", Task.completed_at - Task.created_at) / 60))
        .where(
            Task.property_id == prop_id,
            Task.status.in_(["completed", "approved"]),
            Task.completed_at.isnot(None),
            Task.completed_at.between(start_dt, end_dt),
        )
    )
    avg_minutes = float(avg_time_result.scalar() or 0)

    data = []
    for i in range(days):
        d = start + timedelta(days=i)
        ds = d.isoformat()
        data.append(TaskPerformancePoint(
            date=ds,
            completed=int(completed_by_day.get(ds, 0)),
            pending=int(total_pending),
            overdue=int(total_overdue),
            avg_completion_minutes=avg_minutes,
        ))

    return TaskReport(
        period=f"{start.isoformat()} to {end.isoformat()}",
        data=data,
        total_completed=sum(completed_by_day.values()),
        total_overdue=total_overdue,
        avg_completion_minutes=round(avg_minutes, 1),
    )


@router.get("/tickets", response_model=TicketReport)
async def ticket_report(
    property_id: Optional[uuid.UUID] = None,
    days: int = Query(30, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    prop_id = property_id or current_user.property_id
    start, end = _date_range(days)
    start_dt = datetime.combine(start, datetime.min.time())
    end_dt = datetime.combine(end, datetime.max.time())

    opened_result = await db.execute(
        select(func.date(Ticket.created_at).label("d"), func.count(Ticket.id))
        .where(
            Ticket.property_id == prop_id,
            Ticket.created_at.between(start_dt, end_dt),
        )
        .group_by(func.date(Ticket.created_at))
    )
    def _day_key(val) -> str:
        if val is None:
            return ""
        return val.isoformat() if hasattr(val, "isoformat") else str(val)

    opened_by_day = {_day_key(r[0]): r[1] for r in opened_result.all()}

    resolved_result = await db.execute(
        select(func.date(Ticket.resolved_at).label("d"), func.count(Ticket.id))
        .where(
            Ticket.property_id == prop_id,
            Ticket.resolved_at.between(start_dt, end_dt),
        )
        .group_by(func.date(Ticket.resolved_at))
    )
    resolved_by_day = {_day_key(r[0]): r[1] for r in resolved_result.all()}

    breach_result = await db.execute(
        select(func.date(Ticket.created_at).label("d"), func.count(Ticket.id))
        .where(
            Ticket.property_id == prop_id,
            Ticket.sla_breached == True,
            Ticket.created_at.between(start_dt, end_dt),
        )
        .group_by(func.date(Ticket.created_at))
    )
    breach_by_day = {_day_key(r[0]): r[1] for r in breach_result.all()}

    breached_result = await db.execute(
        select(func.count(Ticket.id)).where(
            Ticket.property_id == prop_id,
            Ticket.sla_breached == True,
            Ticket.created_at.between(start_dt, end_dt),
        )
    )
    total_breached = breached_result.scalar() or 0

    total_opened = sum(opened_by_day.values())
    total_resolved = sum(resolved_by_day.values())
    sla_rate = round(total_breached / max(total_opened, 1) * 100, 1)

    data = []
    for i in range(days):
        d = start + timedelta(days=i)
        dk = d.isoformat()
        data.append(
            TicketTrendPoint(
                date=dk,
                opened=int(opened_by_day.get(dk, 0)),
                resolved=int(resolved_by_day.get(dk, 0)),
                sla_breached=int(breach_by_day.get(dk, 0)),
            )
        )

    return TicketReport(
        period=f"{start.isoformat()} to {end.isoformat()}",
        data=data,
        total_opened=total_opened,
        total_resolved=total_resolved,
        sla_breach_rate=sla_rate,
    )


@router.get("/departments", response_model=list)
async def department_performance(
    property_id: Optional[uuid.UUID] = None,
    days: int = Query(30, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    prop_id = property_id or current_user.property_id
    start_dt = datetime.utcnow() - timedelta(days=days)

    dept_result = await db.execute(
        select(Department).where(Department.property_id == prop_id)
    )
    departments = dept_result.scalars().all()

    perf = []
    for dept in departments:
        emp_count_r = await db.execute(
            select(func.count(Employee.id)).where(
                Employee.department_id == dept.id,
                Employee.status == "active",
            )
        )
        emp_count = emp_count_r.scalar() or 0

        tasks_r = await db.execute(
            select(func.count(Task.id)).where(
                Task.property_id == prop_id,
                Task.status.in_(["completed", "approved"]),
                Task.completed_at >= start_dt,
            )
        )
        tasks_done = tasks_r.scalar() or 0

        avg_r = await db.execute(
            select(func.avg(func.extract("epoch", Task.completed_at - Task.created_at) / 60))
            .where(
                Task.property_id == prop_id,
                Task.status.in_(["completed", "approved"]),
                Task.completed_at >= start_dt,
                Task.completed_at.isnot(None),
            )
        )
        avg_min = float(avg_r.scalar() or 0)

        tickets_r = await db.execute(
            select(func.count(Ticket.id)).where(
                Ticket.property_id == prop_id,
                Ticket.department_id == dept.id,
                Ticket.status.in_(["resolved", "closed"]),
                Ticket.resolved_at >= start_dt,
            )
        )
        tickets_done = tickets_r.scalar() or 0

        perf.append({
            "department": dept.name,
            "tasks_completed": tasks_done,
            "avg_completion_time": round(avg_min, 1),
            "tickets_resolved": tickets_done,
            "employee_count": emp_count,
        })

    return perf


@router.get("/inventory-consumption", response_model=list)
async def inventory_consumption(
    property_id: Optional[uuid.UUID] = None,
    days: int = Query(30, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    prop_id = property_id or current_user.property_id
    start_dt = datetime.utcnow() - timedelta(days=days)

    result = await db.execute(
        select(
            InventoryItem.item_name,
            InventoryItem.category,
            InventoryItem.unit,
            InventoryItem.unit_cost,
            func.sum(InventoryTransaction.quantity).label("consumed"),
        )
        .join(InventoryTransaction, InventoryItem.id == InventoryTransaction.inventory_item_id)
        .where(
            InventoryItem.property_id == prop_id,
            InventoryTransaction.transaction_type == "OUT",
            InventoryTransaction.created_at >= start_dt,
        )
        .group_by(InventoryItem.id)
        .order_by(func.sum(InventoryTransaction.quantity).desc())
        .limit(20)
    )
    rows = result.all()

    return [
        {
            "item_name": r.item_name,
            "category": r.category,
            "consumed": int(r.consumed or 0),
            "unit": r.unit,
            "cost": round(float(r.unit_cost or 0) * int(r.consumed or 0), 2),
        }
        for r in rows
    ]


@router.get("/revenue", response_model=list)
async def revenue_report(
    property_id: Optional[uuid.UUID] = None,
    days: int = Query(30, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    prop_id = property_id or current_user.property_id
    start, end = _date_range(days)
    start_dt = datetime.combine(start, datetime.min.time())
    end_dt = datetime.combine(end, datetime.max.time())

    result = await db.execute(
        select(
            func.date(Order.created_at).label("d"),
            func.sum(Order.total_amount).label("revenue"),
            func.count(Order.id).label("count"),
        )
        .where(
            Order.property_id == prop_id,
            Order.status == "delivered",
            Order.created_at.between(start_dt, end_dt),
        )
        .group_by(func.date(Order.created_at))
        .order_by(func.date(Order.created_at))
    )
    def _rev_day_key(val) -> str:
        return val.isoformat() if hasattr(val, "isoformat") else str(val)

    by_day = {_rev_day_key(r[0]): (float(r[1] or 0), int(r[2])) for r in result.all()}

    return [
        {
            "date": (start + timedelta(days=i)).isoformat(),
            "orders_revenue": by_day.get((start + timedelta(days=i)).isoformat(), (0, 0))[0],
            "order_count": by_day.get((start + timedelta(days=i)).isoformat(), (0, 0))[1],
        }
        for i in range(days)
    ]
