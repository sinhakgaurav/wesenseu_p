from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
import uuid

from app.db.base import get_db
from app.models.employee import Employee
from app.models.department import Department
from app.core.security import get_password_hash
from app.schemas.employee import EmployeeCreate, EmployeeUpdate, EmployeeResponse
from app.schemas.p2 import ImportResult
from app.api.v1.deps import get_current_user

router = APIRouter()


def generate_employee_code(prefix: str = "EMP") -> str:
    import random
    import string
    return prefix + "".join(random.choices(string.digits, k=5))


@router.get("/", response_model=List[EmployeeResponse])
async def list_employees(
    property_id: Optional[uuid.UUID] = None,
    department_id: Optional[uuid.UUID] = None,
    status: Optional[str] = None,
    role: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    query = select(Employee)
    if property_id:
        query = query.where(Employee.property_id == property_id)
    elif current_user.role != "super_admin":
        query = query.where(Employee.property_id == current_user.property_id)

    if department_id:
        query = query.where(Employee.department_id == department_id)
    if status:
        query = query.where(Employee.status == status)
    if role:
        query = query.where(Employee.role == role)

    query = query.offset(skip).limit(limit).order_by(Employee.full_name)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
async def create_employee(
    data: EmployeeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    result = await db.execute(select(Employee).where(Employee.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    employee = Employee(
        **{k: v for k, v in data.model_dump().items() if k != "password"},
        employee_code=generate_employee_code(),
        hashed_password=get_password_hash(data.password),
    )
    db.add(employee)
    await db.commit()
    await db.refresh(employee)
    return employee


@router.get("/{employee_id}", response_model=EmployeeResponse)
async def get_employee(
    employee_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    result = await db.execute(select(Employee).where(Employee.id == employee_id))
    employee = result.scalar_one_or_none()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee


@router.patch("/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    employee_id: uuid.UUID,
    data: EmployeeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    result = await db.execute(select(Employee).where(Employee.id == employee_id))
    employee = result.scalar_one_or_none()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(employee, field, value)

    await db.commit()
    await db.refresh(employee)
    return employee


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_employee(
    employee_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    result = await db.execute(select(Employee).where(Employee.id == employee_id))
    employee = result.scalar_one_or_none()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    employee.status = "inactive"
    await db.commit()


@router.get("/available/list", response_model=List[EmployeeResponse])
async def get_available_employees(
    property_id: Optional[uuid.UUID] = None,
    department_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    prop_id = property_id or current_user.property_id
    query = select(Employee).where(
        Employee.property_id == prop_id,
        Employee.is_available == True,
        Employee.status == "active",
    )
    if department_id:
        query = query.where(Employee.department_id == department_id)

    result = await db.execute(query)
    return result.scalars().all()


@router.post("/import", response_model=ImportResult)
async def import_employees_csv(
    file: UploadFile = File(...),
    property_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if current_user.role not in ("super_admin", "property_manager"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    import csv
    import io

    prop_id = property_id or current_user.property_id
    if not prop_id:
        raise HTTPException(status_code=400, detail="property_id required")
    content = (await file.read()).decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(content))
    created = updated = 0
    errors: list[str] = []
    for i, row in enumerate(reader, start=2):
        email = (row.get("email") or "").strip().lower()
        full_name = (row.get("full_name") or row.get("name") or "").strip()
        if not email or not full_name:
            errors.append(f"Row {i}: missing email or full_name")
            continue
        dept_id = None
        dept_name = (row.get("department_name") or row.get("department") or "").strip()
        if dept_name:
            dept = (
                await db.execute(
                    select(Department).where(
                        Department.property_id == prop_id,
                        Department.name == dept_name,
                        Department.is_active == True,
                    )
                )
            ).scalar_one_or_none()
            if dept:
                dept_id = dept.id
        existing = (await db.execute(select(Employee).where(Employee.email == email))).scalar_one_or_none()
        password = (row.get("password") or "ChangeMe@123").strip()
        role = (row.get("role") or "employee").strip()
        if existing:
            existing.full_name = full_name
            existing.department_id = dept_id or existing.department_id
            existing.role = role
            updated += 1
        else:
            db.add(
                Employee(
                    property_id=prop_id,
                    department_id=dept_id,
                    employee_code=generate_employee_code(),
                    full_name=full_name,
                    email=email,
                    phone=(row.get("phone") or "").strip() or None,
                    role=role,
                    shift_type=(row.get("shift_type") or "").strip() or None,
                    hashed_password=get_password_hash(password),
                    status="active",
                )
            )
            created += 1
    await db.commit()
    return ImportResult(created=created, updated=updated, errors=errors)
