"""
Super-Admin Panel API

Property approvals:
  GET    /admin/approvals                    – list all pending/all approvals
  GET    /admin/approvals/{id}               – single approval detail
  POST   /admin/approvals/{property_id}      – create approval record for a property
  PATCH  /admin/approvals/{approval_id}      – approve / reject / suspend

Module config:
  GET    /admin/modules/{property_id}        – get all module configs for a property
  PATCH  /admin/modules/{property_id}/{mod}  – enable / disable a module

Platform stats:
  GET    /admin/stats                        – platform-wide counts

User management (cross-property):
  GET    /admin/employees                    – list all employees across all properties
  POST   /admin/employees                    – create employee in any property
  DELETE /admin/employees/{id}              – hard-delete employee (admin)
"""
import uuid
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.models.employee import Employee
from app.models.property import Property
from app.models.property_approval import PropertyApproval
from app.models.module_config import ModuleConfig, AVAILABLE_MODULES
from app.models.customer import Customer
from app.models.room import Room
from app.models.task import Task
from app.models.ticket import Ticket
from app.api.v1.deps import get_current_user
from app.core.security import get_password_hash

router = APIRouter()


def _require_super_admin(current_user: Employee):
    if current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Super admin access required")


# ── Property approvals ─────────────────────────────────────────────────────────

class ApprovalAction(BaseModel):
    status: str  # approved | rejected | under_review | suspended
    notes: Optional[str] = None
    rejection_reason: Optional[str] = None


@router.get("/approvals")
async def list_approvals(
    status_filter: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    _require_super_admin(current_user)
    q = select(PropertyApproval)
    if status_filter:
        q = q.where(PropertyApproval.status == status_filter)
    result = await db.execute(q.order_by(PropertyApproval.created_at.desc()).limit(limit))
    approvals = result.scalars().all()

    out = []
    for a in approvals:
        prop = (await db.execute(select(Property).where(Property.id == a.property_id))).scalar_one_or_none()
        out.append({
            "id": str(a.id), "property_id": str(a.property_id),
            "property_name": prop.name if prop else None,
            "status": a.status, "notes": a.notes,
            "rejection_reason": a.rejection_reason,
            "requested_plan": a.requested_plan,
            "reviewed_at": a.reviewed_at, "created_at": a.created_at,
        })
    return out


@router.get("/approvals/{approval_id}")
async def get_approval(
    approval_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    _require_super_admin(current_user)
    result = await db.execute(select(PropertyApproval).where(PropertyApproval.id == approval_id))
    a = result.scalar_one_or_none()
    if not a:
        raise HTTPException(status_code=404, detail="Approval record not found")
    return {
        "id": str(a.id), "property_id": str(a.property_id),
        "status": a.status, "notes": a.notes,
        "rejection_reason": a.rejection_reason,
        "requested_plan": a.requested_plan,
        "reviewed_by": str(a.reviewed_by) if a.reviewed_by else None,
        "reviewed_at": a.reviewed_at, "created_at": a.created_at,
    }


@router.post("/approvals/{property_id}", status_code=status.HTTP_201_CREATED)
async def create_approval(
    property_id: uuid.UUID,
    requested_plan: str = "starter",
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    """Manually create an approval record (normally auto-created on property creation)."""
    _require_super_admin(current_user)
    existing = (await db.execute(
        select(PropertyApproval).where(PropertyApproval.property_id == property_id)
    )).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Approval record already exists for this property")
    rec = PropertyApproval(property_id=property_id, requested_plan=requested_plan)
    db.add(rec)
    await db.commit()
    await db.refresh(rec)
    return {"id": str(rec.id), "status": rec.status}


@router.patch("/approvals/{approval_id}")
async def action_on_approval(
    approval_id: uuid.UUID,
    data: ApprovalAction,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    _require_super_admin(current_user)
    if data.status not in ("approved", "rejected", "under_review", "suspended"):
        raise HTTPException(status_code=400, detail="Invalid status")

    result = await db.execute(select(PropertyApproval).where(PropertyApproval.id == approval_id))
    a = result.scalar_one_or_none()
    if not a:
        raise HTTPException(status_code=404, detail="Approval record not found")

    a.status = data.status
    a.notes = data.notes or a.notes
    a.rejection_reason = data.rejection_reason or a.rejection_reason
    a.reviewed_by = current_user.id
    a.reviewed_at = datetime.utcnow()

    # Mirror status onto Property
    prop = (await db.execute(select(Property).where(Property.id == a.property_id))).scalar_one_or_none()
    if prop:
        if data.status == "approved":
            prop.subscription_status = "active"
            prop.is_active = True
        elif data.status in ("rejected", "suspended"):
            prop.subscription_status = data.status
            if data.status == "suspended":
                prop.is_active = False

    await db.commit()
    return {"message": f"Property {data.status}", "approval_id": str(a.id)}


# ── Module configuration ───────────────────────────────────────────────────────

@router.get("/modules/{property_id}")
async def get_module_configs(
    property_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    _require_super_admin(current_user)
    result = await db.execute(
        select(ModuleConfig).where(ModuleConfig.property_id == property_id)
    )
    configs = {c.module_name: c for c in result.scalars().all()}
    return [
        {
            "module_name": mod,
            "is_enabled": configs[mod].is_enabled if mod in configs else True,
            "config": configs[mod].config if mod in configs else {},
        }
        for mod in AVAILABLE_MODULES
    ]


class ModuleToggle(BaseModel):
    is_enabled: bool
    config: Optional[dict] = None


@router.patch("/modules/{property_id}/{module_name}")
async def toggle_module(
    property_id: uuid.UUID,
    module_name: str,
    data: ModuleToggle,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    _require_super_admin(current_user)
    if module_name not in AVAILABLE_MODULES:
        raise HTTPException(status_code=400, detail=f"Unknown module '{module_name}'")

    result = await db.execute(
        select(ModuleConfig).where(
            ModuleConfig.property_id == property_id,
            ModuleConfig.module_name == module_name,
        )
    )
    cfg = result.scalar_one_or_none()
    if cfg:
        cfg.is_enabled = data.is_enabled
        if data.config is not None:
            cfg.config = data.config
        cfg.updated_by = current_user.id
    else:
        cfg = ModuleConfig(
            property_id=property_id,
            module_name=module_name,
            is_enabled=data.is_enabled,
            config=data.config or {},
            updated_by=current_user.id,
        )
        db.add(cfg)
    await db.commit()
    return {"module_name": module_name, "is_enabled": data.is_enabled}


# ── Platform stats ─────────────────────────────────────────────────────────────

@router.get("/stats")
async def platform_stats(
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    _require_super_admin(current_user)
    total_properties = (await db.execute(select(func.count(Property.id)))).scalar()
    active_properties = (await db.execute(
        select(func.count(Property.id)).where(Property.is_active == True)
    )).scalar()
    pending_approvals = (await db.execute(
        select(func.count(PropertyApproval.id)).where(PropertyApproval.status == "pending")
    )).scalar()
    total_customers = (await db.execute(select(func.count(Customer.id)))).scalar()
    total_employees = (await db.execute(select(func.count(Employee.id)))).scalar()
    total_rooms = (await db.execute(select(func.count(Room.id)))).scalar()
    open_tasks = (await db.execute(
        select(func.count(Task.id)).where(Task.status.notin_(["approved", "rejected"]))
    )).scalar()
    open_tickets = (await db.execute(
        select(func.count(Ticket.id)).where(Ticket.status.notin_(["resolved", "closed"]))
    )).scalar()

    return {
        "total_properties": total_properties,
        "active_properties": active_properties,
        "pending_approvals": pending_approvals,
        "total_customers": total_customers,
        "total_employees": total_employees,
        "total_rooms": total_rooms,
        "open_tasks": open_tasks,
        "open_tickets": open_tickets,
    }


# ── Cross-property employee management ────────────────────────────────────────

class EmployeeAdminCreate(BaseModel):
    property_id: Optional[uuid.UUID] = None
    employee_code: str
    full_name: str
    email: str
    password: str
    role: str
    phone: Optional[str] = None


@router.get("/employees")
async def list_all_employees(
    property_id: Optional[uuid.UUID] = None,
    role: Optional[str] = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    _require_super_admin(current_user)
    q = select(Employee)
    if property_id:
        q = q.where(Employee.property_id == property_id)
    if role:
        q = q.where(Employee.role == role)
    result = await db.execute(q.order_by(Employee.full_name).limit(limit))
    emps = result.scalars().all()
    return [
        {
            "id": str(e.id), "property_id": str(e.property_id) if e.property_id else None,
            "employee_code": e.employee_code, "full_name": e.full_name,
            "email": e.email, "role": e.role, "status": e.status,
        }
        for e in emps
    ]


@router.post("/employees", status_code=status.HTTP_201_CREATED)
async def admin_create_employee(
    data: EmployeeAdminCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    _require_super_admin(current_user)
    emp = Employee(
        property_id=data.property_id,
        employee_code=data.employee_code,
        full_name=data.full_name,
        email=data.email,
        hashed_password=get_password_hash(data.password),
        role=data.role,
        phone=data.phone,
        status="active",
    )
    db.add(emp)
    await db.commit()
    await db.refresh(emp)
    return {"id": str(emp.id), "email": emp.email, "role": emp.role}


@router.delete("/employees/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_employee(
    employee_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    _require_super_admin(current_user)
    result = await db.execute(select(Employee).where(Employee.id == employee_id))
    emp = result.scalar_one_or_none()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    if emp.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    await db.delete(emp)
    await db.commit()
