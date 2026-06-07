"""F&B outlets and property menus."""
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user
from app.db.base import get_db
from app.models.employee import Employee
from app.models.p2_extensions import PropertyOutlet, PropertyMenuItem
from app.schemas.p2 import OutletCreate, OutletUpdate, MenuItemCreate, MenuItemUpdate

router = APIRouter()


@router.get("/properties/{property_id}/outlets")
async def list_outlets(
    property_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    rows = (
        await db.execute(
            select(PropertyOutlet).where(
                PropertyOutlet.property_id == property_id,
                PropertyOutlet.is_active == True,
            )
        )
    ).scalars().all()
    return [
        {
            "id": str(o.id),
            "name": o.name,
            "outlet_type": o.outlet_type,
        }
        for o in rows
    ]


@router.post("/properties/{property_id}/outlets", status_code=status.HTTP_201_CREATED)
async def create_outlet(
    property_id: uuid.UUID,
    data: OutletCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if current_user.role not in ("super_admin", "property_manager"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    outlet = PropertyOutlet(property_id=property_id, name=data.name, outlet_type=data.outlet_type)
    db.add(outlet)
    await db.commit()
    await db.refresh(outlet)
    return {"id": str(outlet.id), "name": outlet.name, "outlet_type": outlet.outlet_type}


@router.patch("/outlets/{outlet_id}")
async def update_outlet(
    outlet_id: uuid.UUID,
    data: OutletUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if current_user.role not in ("super_admin", "property_manager"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    outlet = (
        await db.execute(select(PropertyOutlet).where(PropertyOutlet.id == outlet_id))
    ).scalar_one_or_none()
    if not outlet:
        raise HTTPException(status_code=404, detail="Outlet not found")
    for k, val in data.model_dump(exclude_unset=True).items():
        setattr(outlet, k, val)
    await db.commit()
    await db.refresh(outlet)
    return {"id": str(outlet.id), "name": outlet.name, "outlet_type": outlet.outlet_type, "is_active": outlet.is_active}


@router.delete("/outlets/{outlet_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_outlet(
    outlet_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if current_user.role not in ("super_admin", "property_manager"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    outlet = (
        await db.execute(select(PropertyOutlet).where(PropertyOutlet.id == outlet_id))
    ).scalar_one_or_none()
    if not outlet:
        raise HTTPException(status_code=404, detail="Outlet not found")
    outlet.is_active = False
    await db.commit()


@router.get("/outlets/{outlet_id}/menu")
async def list_menu(
    outlet_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    rows = (
        await db.execute(
            select(PropertyMenuItem).where(
                PropertyMenuItem.outlet_id == outlet_id,
                PropertyMenuItem.is_available == True,
            )
        )
    ).scalars().all()
    return [
        {
            "id": str(m.id),
            "name": m.name,
            "price": float(m.price),
            "catalog_item_id": str(m.catalog_item_id) if m.catalog_item_id else None,
            "photo_url": m.photo_url,
        }
        for m in rows
    ]


@router.post("/outlets/{outlet_id}/menu", status_code=status.HTTP_201_CREATED)
async def add_menu_item(
    outlet_id: uuid.UUID,
    data: MenuItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if current_user.role not in ("super_admin", "property_manager"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    item = PropertyMenuItem(
        outlet_id=outlet_id,
        name=data.name,
        price=data.price,
        catalog_item_id=data.catalog_item_id,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return {"id": str(item.id), "name": item.name, "price": float(item.price)}


@router.patch("/menu/{menu_item_id}")
async def update_menu_item(
    menu_item_id: uuid.UUID,
    data: MenuItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if current_user.role not in ("super_admin", "property_manager"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    item = (
        await db.execute(select(PropertyMenuItem).where(PropertyMenuItem.id == menu_item_id))
    ).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")
    for k, val in data.model_dump(exclude_unset=True).items():
        setattr(item, k, val)
    await db.commit()
    await db.refresh(item)
    return {
        "id": str(item.id),
        "name": item.name,
        "price": float(item.price),
        "is_available": item.is_available,
    }


@router.delete("/menu/{menu_item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_menu_item(
    menu_item_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if current_user.role not in ("super_admin", "property_manager"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    item = (
        await db.execute(select(PropertyMenuItem).where(PropertyMenuItem.id == menu_item_id))
    ).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")
    item.is_available = False
    await db.commit()
