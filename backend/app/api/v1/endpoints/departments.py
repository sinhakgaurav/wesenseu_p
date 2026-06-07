import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user
from app.db.base import get_db
from app.models.department import Department
from app.models.employee import Employee
from app.models.property import Property
from app.models.catalog import CatalogItem
from app.models.p2_extensions import DepartmentCatalogDuty
from app.schemas.catalog import CatalogItemResponse
from app.schemas.department import DepartmentCreate, DepartmentResponse, DepartmentUpdate
from pydantic import BaseModel


class DepartmentDutiesSet(BaseModel):
    catalog_item_ids: list[uuid.UUID]


router = APIRouter()

WRITE_ROLES = ("super_admin", "property_manager")
READ_ROLES = ("super_admin", "property_manager", "dept_manager", "employee")


def _uuid_eq(a, b) -> bool:
    """Compare UUID-like values (asyncpg UUID vs SQLite string in tests)."""
    if a is None or b is None:
        return False
    return uuid.UUID(str(a)) == uuid.UUID(str(b))


def _resolve_property_filter(
    current_user: Employee,
    property_id: Optional[uuid.UUID],
) -> uuid.UUID:
    if current_user.role == "super_admin":
        if not property_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="property_id is required for super_admin",
            )
        return property_id
    if property_id and not _uuid_eq(property_id, current_user.property_id):
        raise HTTPException(status_code=403, detail="Cannot access another property")
    if not current_user.property_id:
        raise HTTPException(status_code=400, detail="User has no property scope")
    return current_user.property_id


async def _get_department_or_404(
    db: AsyncSession, department_id: uuid.UUID
) -> Department:
    res = await db.execute(select(Department).where(Department.id == department_id))
    dept = res.scalar_one_or_none()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    return dept


def _assert_can_read_dept(current_user: Employee, dept: Department) -> None:
    if current_user.role == "super_admin":
        return
    if not _uuid_eq(current_user.property_id, dept.property_id):
        raise HTTPException(status_code=403, detail="Access denied")


@router.get("/", response_model=List[DepartmentResponse])
async def list_departments(
    property_id: Optional[uuid.UUID] = Query(None),
    include_inactive: bool = Query(False),
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if current_user.role not in READ_ROLES:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    pid = _resolve_property_filter(current_user, property_id)
    q = select(Department).where(Department.property_id == pid)
    if not include_inactive:
        q = q.where(Department.is_active.is_(True))
    q = q.order_by(Department.name).offset(skip).limit(limit)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{department_id}", response_model=DepartmentResponse)
async def get_department(
    department_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if current_user.role not in READ_ROLES:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    dept = await _get_department_or_404(db, department_id)
    _assert_can_read_dept(current_user, dept)
    return dept


@router.post("/", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_department(
    data: DepartmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if current_user.role not in WRITE_ROLES:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    if current_user.role != "super_admin" and not _uuid_eq(data.property_id, current_user.property_id):
        raise HTTPException(status_code=403, detail="Can only create departments for your property")

    prop = await db.get(Property, data.property_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    if data.manager_id:
        mgr = await db.get(Employee, data.manager_id)
        if not mgr or not _uuid_eq(mgr.property_id, data.property_id):
            raise HTTPException(status_code=400, detail="manager_id must belong to this property")

    dept = Department(
        property_id=data.property_id,
        name=data.name,
        description=data.description,
        manager_id=data.manager_id,
        is_active=True,
    )
    db.add(dept)
    await db.commit()
    await db.refresh(dept)
    return dept


@router.patch("/{department_id}", response_model=DepartmentResponse)
async def update_department(
    department_id: uuid.UUID,
    data: DepartmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if current_user.role not in WRITE_ROLES:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    dept = await _get_department_or_404(db, department_id)
    _assert_can_read_dept(current_user, dept)

    if data.manager_id is not None:
        if data.manager_id:
            mgr = await db.get(Employee, data.manager_id)
            if not mgr or not _uuid_eq(mgr.property_id, dept.property_id):
                raise HTTPException(status_code=400, detail="manager_id must belong to this property")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(dept, field, value)
    await db.commit()
    await db.refresh(dept)
    return dept


@router.delete("/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_department(
    department_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    """Soft-deactivate department (keeps FK integrity for historical rows)."""
    if current_user.role not in WRITE_ROLES:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    dept = await _get_department_or_404(db, department_id)
    _assert_can_read_dept(current_user, dept)
    dept.is_active = False
    await db.commit()


@router.get("/{department_id}/duties", response_model=list[CatalogItemResponse])
async def get_department_duties(
    department_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    dept = await _get_department_or_404(db, department_id)
    _assert_can_read_dept(current_user, dept)
    rows = (
        await db.execute(
            select(CatalogItem)
            .join(DepartmentCatalogDuty, DepartmentCatalogDuty.catalog_item_id == CatalogItem.id)
            .where(DepartmentCatalogDuty.department_id == department_id, CatalogItem.is_active == True)
        )
    ).scalars().all()
    return rows


@router.put("/{department_id}/duties", response_model=list[CatalogItemResponse])
async def set_department_duties(
    department_id: uuid.UUID,
    body: DepartmentDutiesSet,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if current_user.role not in WRITE_ROLES:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    dept = await _get_department_or_404(db, department_id)
    _assert_can_read_dept(current_user, dept)
    await db.execute(delete(DepartmentCatalogDuty).where(DepartmentCatalogDuty.department_id == department_id))
    for cid in body.catalog_item_ids:
        item = (await db.execute(select(CatalogItem).where(CatalogItem.id == cid))).scalar_one_or_none()
        if not item or item.kind != "department_duty":
            raise HTTPException(status_code=400, detail=f"Invalid department_duty id: {cid}")
        db.add(DepartmentCatalogDuty(department_id=department_id, catalog_item_id=cid))
    await db.commit()
    return await get_department_duties(department_id, db, current_user)
