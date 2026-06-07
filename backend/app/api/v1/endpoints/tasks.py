from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime
import uuid

from app.db.base import get_db
from app.db.soft_delete import apply_soft_delete, not_deleted_clause, restore_soft_deleted
from app.models.task import Task, TaskMedia
from app.models.employee import Employee
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse, TaskStatusUpdate
from app.api.v1.deps import get_current_user
from app.services.storage import upload_file
from app.services.task_sla import resolve_sla_for_task, refresh_task_sla_breach
from app.services.task_assignment import pick_longest_idle_free_employee
from app.services.benchmark_requirements import (
    count_task_photos,
    required_benchmark_aspect_count,
    validate_cleaning_task_photos,
)
from app.services.inventory_task import deduct_inventory_for_task
from app.services.notify_managers import notify_managers
from app.models.room import Room

router = APIRouter()


@router.get("/", response_model=List[TaskResponse])
async def list_tasks(
    property_id: Optional[uuid.UUID] = None,
    assigned_to: Optional[uuid.UUID] = None,
    room_id: Optional[uuid.UUID] = None,
    status: Optional[str] = None,
    task_type: Optional[str] = None,
    priority: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    refresh_sla: bool = Query(False, description="If true, evaluate SLA breach flags for returned tasks"),
    include_deleted: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    query = select(Task)
    if not include_deleted:
        clause = not_deleted_clause(Task)
        if clause is not None:
            query = query.where(clause)
    prop_id = property_id or current_user.property_id
    if prop_id:
        query = query.where(Task.property_id == prop_id)

    if current_user.role == "employee":
        query = query.where(Task.assigned_to == current_user.id)
    elif assigned_to:
        query = query.where(Task.assigned_to == assigned_to)

    if room_id:
        query = query.where(Task.room_id == room_id)
    if status:
        query = query.where(Task.status == status)
    if task_type:
        query = query.where(Task.task_type == task_type)
    if priority:
        query = query.where(Task.priority == priority)

    query = query.options(selectinload(Task.media)).offset(skip).limit(limit).order_by(Task.created_at.desc())
    result = await db.execute(query)
    tasks = result.scalars().all()
    if refresh_sla:
        for t in tasks:
            await refresh_task_sla_breach(db, t)
        await db.commit()
        result = await db.execute(query)
        tasks = result.scalars().all()
    return tasks


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    data: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    payload = data.model_dump(exclude={"auto_assign"})
    if payload.get("service_type") in ("", None):
        payload["service_type"] = None
    task = Task(**payload, created_by=current_user.id)
    if data.assigned_to:
        task.status = "assigned"

    sla_due, _, _ = await resolve_sla_for_task(
        db, task.property_id, task.task_type, task.service_type
    )
    if sla_due:
        task.sla_due_at = sla_due
        if task.due_time is None:
            task.due_time = sla_due

    if data.auto_assign and not task.assigned_to:
        emp = await pick_longest_idle_free_employee(db, task.property_id)
        if emp:
            task.assigned_to = emp.id
            task.status = "assigned"

    db.add(task)
    await db.commit()
    result2 = await db.execute(select(Task).where(Task.id == task.id).options(selectinload(Task.media)))
    return result2.scalar_one()


@router.post("/{task_id}/auto-assign", response_model=TaskResponse)
async def auto_assign_task(
    task_id: uuid.UUID,
    department_id: Optional[uuid.UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if current_user.role not in ("super_admin", "property_manager", "dept_manager"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    result = await db.execute(select(Task).where(Task.id == task_id).options(selectinload(Task.media)))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    emp = await pick_longest_idle_free_employee(db, task.property_id, department_id)
    if not emp:
        raise HTTPException(status_code=400, detail="No free employee found for auto-assignment")
    task.assigned_to = emp.id
    if task.status == "pending":
        task.status = "assigned"
    await db.commit()
    result2 = await db.execute(select(Task).where(Task.id == task.id).options(selectinload(Task.media)))
    return result2.scalar_one()


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    result = await db.execute(select(Task).where(Task.id == task_id).options(selectinload(Task.media)))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    await refresh_task_sla_breach(db, task)
    await db.commit()
    result2 = await db.execute(select(Task).where(Task.id == task_id).options(selectinload(Task.media)))
    return result2.scalar_one()


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: uuid.UUID,
    data: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(task, field, value)

    await db.commit()
    result2 = await db.execute(select(Task).where(Task.id == task.id).options(selectinload(Task.media)))
    return result2.scalar_one()


@router.post("/{task_id}/status", response_model=TaskResponse)
async def update_task_status(
    task_id: uuid.UUID,
    data: TaskStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    result = await db.execute(select(Task).where(Task.id == task_id).options(selectinload(Task.media)))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    old_status = task.status
    if data.status in ("verification_pending", "completed", "approved"):
        err = await validate_cleaning_task_photos(db, task)
        if err:
            raise HTTPException(status_code=400, detail=err)
    task.status = data.status

    if data.status == "in_progress" and not task.started_at:
        task.started_at = datetime.utcnow()
    elif data.status in ("completed", "approved"):
        task.completed_at = datetime.utcnow()
        if old_status not in ("completed", "approved"):
            await deduct_inventory_for_task(db, task, current_user.id)

        if task.room_id and data.status == "approved":
            room_result = await db.execute(select(Room).where(Room.id == task.room_id))
            room = room_result.scalar_one_or_none()
            if room and task.task_type == "cleaning":
                room.room_status = "ready"
                room.last_cleaned_at = datetime.utcnow()

    await db.commit()
    result2 = await db.execute(select(Task).where(Task.id == task.id).options(selectinload(Task.media)))
    return result2.scalar_one()


@router.post("/{task_id}/upload-media", response_model=TaskResponse)
async def upload_task_media(
    task_id: uuid.UUID,
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    for file in files:
        media_type = "video" if file.content_type and "video" in file.content_type else "photo"
        url = await upload_file(file, folder=f"tasks/{task_id}")
        media = TaskMedia(
            task_id=task_id,
            media_url=url,
            media_type=media_type,
            uploaded_by=current_user.id,
        )
        db.add(media)

    if task.status == "in_progress":
        err = await validate_cleaning_task_photos(db, task)
        if not err:
            task.status = "verification_pending"

    await db.commit()
    result2 = await db.execute(select(Task).where(Task.id == task.id).options(selectinload(Task.media)))
    return result2.scalar_one()


@router.get("/{task_id}/benchmark-requirements")
async def get_benchmark_requirements(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    room = None
    if task.room_id:
        room = (await db.execute(select(Room).where(Room.id == task.room_id))).scalar_one_or_none()
    required, aspects = await required_benchmark_aspect_count(db, task.property_id, room)
    photos = await count_task_photos(db, task.id)
    return {
        "task_id": str(task.id),
        "verification_required": task.verification_required,
        "task_type": task.task_type,
        "required_photo_count": required,
        "aspects": aspects,
        "current_photo_count": photos,
        "satisfied": photos >= required if required > 0 else True,
    }


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if current_user.role not in ("super_admin", "property_manager"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    apply_soft_delete(task)
    task.status = "cancelled"
    await db.commit()


@router.post("/{task_id}/restore", response_model=TaskResponse)
async def restore_task(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if current_user.role not in ("super_admin", "property_manager"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    result = await db.execute(select(Task).where(Task.id == task_id).options(selectinload(Task.media)))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    restore_soft_deleted(task)
    await db.commit()
    await db.refresh(task)
    return task


@router.post("/{task_id}/assign/{employee_id}", response_model=TaskResponse)
async def assign_task(
    task_id: uuid.UUID,
    employee_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    result = await db.execute(select(Task).where(Task.id == task_id).options(selectinload(Task.media)))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.assigned_to = employee_id
    task.status = "assigned"
    await notify_managers(
        db,
        task.property_id,
        "task_assigned",
        "Task assigned",
        f"{task.task_type} task assigned to staff",
        reference_type="task",
        reference_id=task.id,
    )

    await db.commit()
    result2 = await db.execute(select(Task).where(Task.id == task.id).options(selectinload(Task.media)))
    return result2.scalar_one()
