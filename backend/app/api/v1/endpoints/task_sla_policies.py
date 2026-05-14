"""Admin CRUD for task SLA policies (task_type + service_type → SLA + root-cause bucket)."""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.models.employee import Employee
from app.models.task_sla import TaskSlaPolicy
from app.api.v1.deps import get_current_user

router = APIRouter()


class TaskSlaPolicyCreate(BaseModel):
    property_id: uuid.UUID
    task_type: str
    service_type: str = "*"
    sla_minutes: int
    root_cause_category: str


class TaskSlaPolicyUpdate(BaseModel):
    task_type: Optional[str] = None
    service_type: Optional[str] = None
    sla_minutes: Optional[int] = None
    root_cause_category: Optional[str] = None
    is_active: Optional[bool] = None


def _dump(p: TaskSlaPolicy) -> dict:
    return {
        "id": str(p.id),
        "property_id": str(p.property_id),
        "task_type": p.task_type,
        "service_type": p.service_type,
        "sla_minutes": p.sla_minutes,
        "root_cause_category": p.root_cause_category,
        "is_active": p.is_active,
    }


@router.get("")
async def list_policies(
    property_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    prop_id = property_id or current_user.property_id
    q = select(TaskSlaPolicy).where(TaskSlaPolicy.is_active == True)
    if prop_id:
        q = q.where(TaskSlaPolicy.property_id == prop_id)
    rows = (await db.execute(q)).scalars().all()
    return [_dump(r) for r in rows]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_policy(
    data: TaskSlaPolicyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if current_user.role not in ("super_admin", "property_manager"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    p = TaskSlaPolicy(**data.model_dump())
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return _dump(p)


@router.patch("/{policy_id}")
async def update_policy(
    policy_id: uuid.UUID,
    data: TaskSlaPolicyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if current_user.role not in ("super_admin", "property_manager"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    p = (await db.execute(select(TaskSlaPolicy).where(TaskSlaPolicy.id == policy_id))).scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Policy not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(p, k, v)
    await db.commit()
    return _dump(p)


@router.delete("/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_policy(
    policy_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if current_user.role not in ("super_admin", "property_manager"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    p = (await db.execute(select(TaskSlaPolicy).where(TaskSlaPolicy.id == policy_id))).scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Policy not found")
    p.is_active = False
    await db.commit()
