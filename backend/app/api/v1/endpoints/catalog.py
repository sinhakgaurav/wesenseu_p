from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import uuid
import re

from app.db.base import get_db
from app.models.catalog import CatalogItem, PropertyCatalogSelection, RoomCategoryAmenity, CATALOG_KINDS
from app.models.employee import Employee
from app.models.property_room_category import PropertyRoomCategory
from app.schemas.catalog import (
    CatalogItemCreate,
    CatalogItemUpdate,
    CatalogItemResponse,
    PropertyCatalogSetRequest,
    RoomCategoryAmenitySetRequest,
)
from app.api.v1.deps import get_current_user

router = APIRouter()


def _slug_code(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return (s[:64] or "item")


@router.get("/kinds", response_model=list[str])
async def list_catalog_kinds():
    return list(CATALOG_KINDS)


@router.get("/items", response_model=List[CatalogItemResponse])
async def list_catalog_items(
    kind: str = Query(..., description="amenity | property_feature | room_view | department_duty | dish"),
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if kind not in CATALOG_KINDS:
        raise HTTPException(status_code=400, detail=f"kind must be one of {CATALOG_KINDS}")
    q = select(CatalogItem).where(CatalogItem.kind == kind)
    if not include_inactive:
        q = q.where(CatalogItem.is_active == True)
    q = q.order_by(CatalogItem.display_name)
    return (await db.execute(q)).scalars().all()


@router.post("/items", response_model=CatalogItemResponse, status_code=status.HTTP_201_CREATED)
async def create_catalog_item(
    data: CatalogItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if data.kind not in CATALOG_KINDS:
        raise HTTPException(status_code=400, detail=f"kind must be one of {CATALOG_KINDS}")
    code = data.code or _slug_code(data.display_name)
    dup = (
        await db.execute(select(CatalogItem).where(CatalogItem.kind == data.kind, CatalogItem.code == code))
    ).scalar_one_or_none()
    if dup:
        raise HTTPException(status_code=409, detail="Catalog item already exists")
    row = CatalogItem(
        kind=data.kind,
        code=code,
        display_name=data.display_name,
        description=data.description,
        is_system=False,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


@router.patch("/items/{item_id}", response_model=CatalogItemResponse)
async def update_catalog_item(
    item_id: uuid.UUID,
    data: CatalogItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if current_user.role not in ("super_admin", "property_manager"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    row = (await db.execute(select(CatalogItem).where(CatalogItem.id == item_id))).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Catalog item not found")
    for k, val in data.model_dump(exclude_unset=True).items():
        setattr(row, k, val)
    await db.commit()
    await db.refresh(row)
    return row


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_catalog_item(
    item_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if current_user.role not in ("super_admin", "property_manager"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    row = (await db.execute(select(CatalogItem).where(CatalogItem.id == item_id))).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Catalog item not found")
    if row.is_system:
        raise HTTPException(status_code=400, detail="Cannot delete system catalog items")
    row.is_active = False
    await db.commit()


@router.get("/properties/{property_id}/features", response_model=List[CatalogItemResponse])
async def get_property_features(
    property_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    rows = (
        await db.execute(
            select(CatalogItem)
            .join(PropertyCatalogSelection, PropertyCatalogSelection.catalog_item_id == CatalogItem.id)
            .where(
                PropertyCatalogSelection.property_id == property_id,
                CatalogItem.kind == "property_feature",
                CatalogItem.is_active == True,
            )
        )
    ).scalars().all()
    return rows


@router.put("/properties/{property_id}/features", response_model=List[CatalogItemResponse])
async def set_property_features(
    property_id: uuid.UUID,
    body: PropertyCatalogSetRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if current_user.role not in ("super_admin", "property_manager"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    await db.execute(
        delete(PropertyCatalogSelection).where(PropertyCatalogSelection.property_id == property_id)
    )
    for cid in body.catalog_item_ids:
        item = (await db.execute(select(CatalogItem).where(CatalogItem.id == cid))).scalar_one_or_none()
        if not item or item.kind != "property_feature":
            raise HTTPException(status_code=400, detail=f"Invalid property_feature catalog id: {cid}")
        db.add(PropertyCatalogSelection(property_id=property_id, catalog_item_id=cid))
    await db.commit()
    return await get_property_features(property_id, db, current_user)


@router.get("/room-categories/{category_id}/amenities", response_model=List[CatalogItemResponse])
async def get_room_category_amenities(
    category_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    cat = (
        await db.execute(select(PropertyRoomCategory).where(PropertyRoomCategory.id == category_id))
    ).scalar_one_or_none()
    if not cat:
        raise HTTPException(status_code=404, detail="Room category not found")
    rows = (
        await db.execute(
            select(CatalogItem)
            .join(RoomCategoryAmenity, RoomCategoryAmenity.catalog_item_id == CatalogItem.id)
            .where(RoomCategoryAmenity.property_room_category_id == category_id)
        )
    ).scalars().all()
    return rows


@router.put("/room-categories/{category_id}/amenities", response_model=List[CatalogItemResponse])
async def set_room_category_amenities(
    category_id: uuid.UUID,
    body: RoomCategoryAmenitySetRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    cat = (
        await db.execute(select(PropertyRoomCategory).where(PropertyRoomCategory.id == category_id))
    ).scalar_one_or_none()
    if not cat:
        raise HTTPException(status_code=404, detail="Room category not found")
    await db.execute(delete(RoomCategoryAmenity).where(RoomCategoryAmenity.property_room_category_id == category_id))
    for cid in body.catalog_item_ids:
        item = (await db.execute(select(CatalogItem).where(CatalogItem.id == cid))).scalar_one_or_none()
        if not item or item.kind != "amenity":
            raise HTTPException(status_code=400, detail=f"Invalid amenity catalog id: {cid}")
        db.add(RoomCategoryAmenity(property_room_category_id=category_id, catalog_item_id=cid))
    await db.commit()
    rows = (
        await db.execute(
            select(CatalogItem)
            .join(RoomCategoryAmenity, RoomCategoryAmenity.catalog_item_id == CatalogItem.id)
            .where(RoomCategoryAmenity.property_room_category_id == category_id)
        )
    ).scalars().all()
    return rows
