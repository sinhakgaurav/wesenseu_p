from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from datetime import datetime, date, timedelta
import uuid

from app.db.base import get_db
from app.models.employee import Employee, Attendance
from app.schemas.attendance import (
    AttendanceCheckIn, AttendanceCheckOut,
    AttendanceResponse, AttendanceSummary,
)
from app.schemas.p2 import AttendanceRecordCreate, EmployeeScheduleUpdate, ImportResult
from app.models.p2_extensions import EmployeeSchedule
from app.api.v1.deps import get_current_user

router = APIRouter()


@router.post("/check-in", response_model=AttendanceResponse)
async def check_in(
    data: AttendanceCheckIn,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    today = date.today()
    existing = await db.execute(
        select(Attendance).where(
            Attendance.employee_id == current_user.id,
            Attendance.date == today,
        )
    )
    record = existing.scalar_one_or_none()

    if record and record.check_in:
        raise HTTPException(status_code=400, detail="Already checked in today")

    if not record:
        record = Attendance(
            employee_id=current_user.id,
            property_id=current_user.property_id,
            date=today,
            check_in=datetime.utcnow(),
            status="present",
            notes=data.notes,
        )
        db.add(record)
    else:
        record.check_in = datetime.utcnow()

    current_user.is_available = False
    await db.commit()
    await db.refresh(record)
    return _with_hours(record)


@router.post("/check-out", response_model=AttendanceResponse)
async def check_out(
    data: AttendanceCheckOut,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    today = date.today()
    result = await db.execute(
        select(Attendance).where(
            Attendance.employee_id == current_user.id,
            Attendance.date == today,
        )
    )
    record = result.scalar_one_or_none()

    if not record or not record.check_in:
        raise HTTPException(status_code=400, detail="No check-in found for today")
    if record.check_out:
        raise HTTPException(status_code=400, detail="Already checked out today")

    record.check_out = datetime.utcnow()
    if data.notes:
        record.notes = data.notes

    current_user.is_available = True
    await db.commit()
    await db.refresh(record)
    return _with_hours(record)


@router.get("/today", response_model=AttendanceResponse)
async def get_today_attendance(
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    result = await db.execute(
        select(Attendance).where(
            Attendance.employee_id == current_user.id,
            Attendance.date == date.today(),
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="No attendance record for today")
    return _with_hours(record)


@router.get("/history", response_model=List[AttendanceResponse])
async def attendance_history(
    employee_id: Optional[uuid.UUID] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 30,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    target_id = employee_id or current_user.id
    # non-admins can only see their own
    if current_user.role == "employee":
        target_id = current_user.id

    query = select(Attendance).where(Attendance.employee_id == target_id)
    if from_date:
        query = query.where(Attendance.date >= from_date)
    if to_date:
        query = query.where(Attendance.date <= to_date)

    query = query.offset(skip).limit(limit).order_by(Attendance.date.desc())
    result = await db.execute(query)
    return [_with_hours(r) for r in result.scalars().all()]


@router.get("/summary", response_model=List[AttendanceSummary])
async def attendance_summary(
    property_id: Optional[uuid.UUID] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    now = datetime.utcnow()
    m = month or now.month
    y = year or now.year
    start = date(y, m, 1)
    if m == 12:
        end = date(y + 1, 1, 1) - timedelta(days=1)
    else:
        end = date(y, m + 1, 1) - timedelta(days=1)

    prop_id = property_id or current_user.property_id
    emp_result = await db.execute(
        select(Employee).where(
            Employee.property_id == prop_id,
            Employee.status == "active",
        )
    )
    employees = emp_result.scalars().all()

    summaries = []
    for emp in employees:
        att_result = await db.execute(
            select(Attendance).where(
                Attendance.employee_id == emp.id,
                Attendance.date >= start,
                Attendance.date <= end,
            )
        )
        records = att_result.scalars().all()

        total_hours = 0.0
        for r in records:
            if r.check_in and r.check_out:
                diff = (r.check_out - r.check_in).total_seconds() / 3600
                total_hours += diff

        summaries.append(AttendanceSummary(
            employee_id=emp.id,
            employee_name=emp.full_name,
            present_days=sum(1 for r in records if r.status == "present"),
            absent_days=sum(1 for r in records if r.status == "absent"),
            half_days=sum(1 for r in records if r.status == "half_day"),
            leave_days=sum(1 for r in records if r.status == "leave"),
            total_hours=round(total_hours, 1),
        ))

    return summaries


@router.post("/records", response_model=AttendanceResponse)
async def manager_set_attendance(
    data: AttendanceRecordCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if current_user.role not in ("super_admin", "property_manager", "dept_manager"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    emp = (await db.execute(select(Employee).where(Employee.id == data.employee_id))).scalar_one_or_none()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    record = (
        await db.execute(
            select(Attendance).where(Attendance.employee_id == data.employee_id, Attendance.date == data.record_date)
        )
    ).scalar_one_or_none()
    if not record:
        record = Attendance(
            employee_id=data.employee_id,
            property_id=emp.property_id,
            date=data.record_date,
            status=data.status,
            notes=data.notes,
        )
        db.add(record)
    else:
        record.status = data.status
        if data.notes:
            record.notes = data.notes
    await db.commit()
    await db.refresh(record)
    return _with_hours(record)


@router.put("/employees/{employee_id}/schedule")
async def set_employee_schedule(
    employee_id: uuid.UUID,
    data: EmployeeScheduleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if current_user.role not in ("super_admin", "property_manager", "dept_manager"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    sched = (
        await db.execute(select(EmployeeSchedule).where(EmployeeSchedule.employee_id == employee_id))
    ).scalar_one_or_none()
    if not sched:
        sched = EmployeeSchedule(employee_id=employee_id)
        db.add(sched)
    sched.weekly_off_days = data.weekly_off_days
    sched.lunch_start = data.lunch_start
    sched.lunch_end = data.lunch_end
    await db.commit()
    return {"employee_id": str(employee_id), "weekly_off_days": sched.weekly_off_days}


@router.post("/import", response_model=ImportResult)
async def import_attendance_csv(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    """Manager confirmation import: employee_code,date,status"""
    if current_user.role not in ("super_admin", "property_manager", "dept_manager"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    import csv
    import io

    content = (await file.read()).decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(content))
    created = updated = 0
    errors: list[str] = []
    for i, row in enumerate(reader, start=2):
        code = (row.get("employee_code") or row.get("code") or "").strip()
        date_str = (row.get("date") or "").strip()
        status_val = (row.get("status") or "present").strip().lower()
        if not code or not date_str:
            errors.append(f"Row {i}: missing employee_code or date")
            continue
        emp = (
            await db.execute(select(Employee).where(Employee.employee_code == code))
        ).scalar_one_or_none()
        if not emp:
            errors.append(f"Row {i}: unknown employee_code {code}")
            continue
        try:
            rec_date = date.fromisoformat(date_str)
        except ValueError:
            errors.append(f"Row {i}: invalid date {date_str}")
            continue
        existing = (
            await db.execute(
                select(Attendance).where(Attendance.employee_id == emp.id, Attendance.date == rec_date)
            )
        ).scalar_one_or_none()
        if existing:
            existing.status = status_val
            updated += 1
        else:
            db.add(
                Attendance(
                    employee_id=emp.id,
                    property_id=emp.property_id,
                    date=rec_date,
                    status=status_val,
                )
            )
            created += 1
    await db.commit()
    return ImportResult(created=created, updated=updated, errors=errors)


def _with_hours(record: Attendance) -> AttendanceResponse:
    hours = None
    if record.check_in and record.check_out:
        hours = round((record.check_out - record.check_in).total_seconds() / 3600, 2)
    return AttendanceResponse(
        id=record.id,
        employee_id=record.employee_id,
        property_id=record.property_id,
        date=record.date,
        check_in=record.check_in,
        check_out=record.check_out,
        status=record.status,
        notes=record.notes,
        hours_worked=hours,
    )
