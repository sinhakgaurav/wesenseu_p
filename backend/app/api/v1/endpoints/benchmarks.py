"""
Room Category Benchmark Images

GET    /benchmarks                        – list benchmarks for a property/category
POST   /benchmarks                        – upload a benchmark image
GET    /benchmarks/{id}                   – get single benchmark
PATCH  /benchmarks/{id}                   – update benchmark metadata
DELETE /benchmarks/{id}                   – remove benchmark
GET    /benchmarks/categories             – list room categories with benchmark counts
"""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user
from app.db.base import get_db
from app.models.benchmark import RoomCategoryBenchmark
from app.models.employee import Employee
from app.models.property_room_category import PropertyRoomCategory
from app.services.storage import upload_file

router = APIRouter()


class BenchmarkUpdate(BaseModel):
    description: Optional[str] = None
    aspect: Optional[str] = None
    is_active: Optional[bool] = None
    property_room_category_id: Optional[uuid.UUID] = None


@router.get("/categories")
async def list_categories_with_benchmarks(
    property_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    """Return each managed room category plus benchmark counts; legacy string-only rows included."""
    prop_id = property_id or current_user.property_id
    if not prop_id:
        raise HTTPException(status_code=400, detail="property_id is required")

    q = (
        select(
            PropertyRoomCategory.id,
            PropertyRoomCategory.code,
            PropertyRoomCategory.display_name,
            func.count(RoomCategoryBenchmark.id).label("cnt"),
        )
        .outerjoin(
            RoomCategoryBenchmark,
            (RoomCategoryBenchmark.property_room_category_id == PropertyRoomCategory.id)
            & (RoomCategoryBenchmark.is_active.is_(True)),
        )
        .where(PropertyRoomCategory.property_id == prop_id, PropertyRoomCategory.is_active == True)
        .group_by(PropertyRoomCategory.id, PropertyRoomCategory.code, PropertyRoomCategory.display_name)
        .order_by(PropertyRoomCategory.sort_order, PropertyRoomCategory.display_name)
    )
    managed = [
        {
            "property_room_category_id": str(i),
            "code": c,
            "display_name": d,
            "benchmark_count": int(n or 0),
        }
        for i, c, d, n in (await db.execute(q)).all()
    ]

    legacy_q = (
        select(RoomCategoryBenchmark.room_category, func.count(RoomCategoryBenchmark.id))
        .where(
            RoomCategoryBenchmark.property_id == prop_id,
            RoomCategoryBenchmark.is_active == True,
            RoomCategoryBenchmark.property_room_category_id.is_(None),
        )
        .group_by(RoomCategoryBenchmark.room_category)
    )
    legacy_rows = {r: c for r, c in (await db.execute(legacy_q)).all()}

    managed_names = {m["display_name"] for m in managed}
    legacy = []
    for room_category, cnt in legacy_rows.items():
        if room_category in managed_names:
            continue
        legacy.append({"property_room_category_id": None, "code": None, "room_category": room_category, "benchmark_count": int(cnt)})

    return {"managed": managed, "legacy_string_only": legacy}


@router.get("")
async def list_benchmarks(
    property_id: Optional[uuid.UUID] = None,
    room_category: Optional[str] = None,
    property_room_category_id: Optional[uuid.UUID] = None,
    aspect: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    prop_id = property_id or current_user.property_id
    q = select(RoomCategoryBenchmark).where(RoomCategoryBenchmark.is_active == True)
    if prop_id:
        q = q.where(RoomCategoryBenchmark.property_id == prop_id)
    if room_category:
        q = q.where(RoomCategoryBenchmark.room_category == room_category)
    if property_room_category_id:
        q = q.where(RoomCategoryBenchmark.property_room_category_id == property_room_category_id)
    if aspect:
        q = q.where(RoomCategoryBenchmark.aspect == aspect)
    result = await db.execute(q.order_by(RoomCategoryBenchmark.room_category, RoomCategoryBenchmark.created_at))
    benchmarks = result.scalars().all()
    return [
        {
            "id": str(b.id),
            "property_id": str(b.property_id),
            "property_room_category_id": str(b.property_room_category_id) if b.property_room_category_id else None,
            "room_category": b.room_category,
            "aspect": b.aspect,
            "image_url": b.image_url,
            "thumbnail_url": b.thumbnail_url,
            "description": b.description,
            "is_active": b.is_active,
            "created_at": b.created_at,
        }
        for b in benchmarks
    ]


@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_benchmark(
    property_id: uuid.UUID = Form(...),
    room_category: Optional[str] = Form(None),
    property_room_category_id: Optional[uuid.UUID] = Form(None),
    aspect: str = Form("general"),
    description: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if current_user.role not in ("super_admin", "property_manager"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    cat_label = room_category
    prc_id = property_room_category_id
    if prc_id:
        cat_row = (
            await db.execute(
                select(PropertyRoomCategory).where(
                    PropertyRoomCategory.id == prc_id,
                    PropertyRoomCategory.property_id == property_id,
                    PropertyRoomCategory.is_active == True,
                )
            )
        ).scalar_one_or_none()
        if not cat_row:
            raise HTTPException(status_code=400, detail="property_room_category_id does not belong to this property")
        cat_label = cat_row.display_name
    if not cat_label or not str(cat_label).strip():
        raise HTTPException(status_code=400, detail="Provide room_category or property_room_category_id")

    image_url = await upload_file(
        file, folder=f"benchmarks/{property_id}/{cat_label.replace(' ', '_')}/{aspect}"
    )

    benchmark = RoomCategoryBenchmark(
        property_id=property_id,
        property_room_category_id=prc_id,
        room_category=cat_label.strip(),
        aspect=aspect,
        description=description,
        image_url=image_url,
        created_by=current_user.id,
    )
    db.add(benchmark)
    await db.commit()
    await db.refresh(benchmark)
    return {
        "id": str(benchmark.id),
        "room_category": benchmark.room_category,
        "property_room_category_id": str(benchmark.property_room_category_id) if benchmark.property_room_category_id else None,
        "image_url": benchmark.image_url,
        "message": "Benchmark image uploaded",
    }


@router.get("/{benchmark_id}")
async def get_benchmark(
    benchmark_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    result = await db.execute(select(RoomCategoryBenchmark).where(RoomCategoryBenchmark.id == benchmark_id))
    b = result.scalar_one_or_none()
    if not b:
        raise HTTPException(status_code=404, detail="Benchmark not found")
    return {
        "id": str(b.id),
        "property_id": str(b.property_id),
        "property_room_category_id": str(b.property_room_category_id) if b.property_room_category_id else None,
        "room_category": b.room_category,
        "aspect": b.aspect,
        "image_url": b.image_url,
        "description": b.description,
        "is_active": b.is_active,
        "created_at": b.created_at,
    }


@router.patch("/{benchmark_id}")
async def update_benchmark(
    benchmark_id: uuid.UUID,
    data: BenchmarkUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if current_user.role not in ("super_admin", "property_manager"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    result = await db.execute(select(RoomCategoryBenchmark).where(RoomCategoryBenchmark.id == benchmark_id))
    b = result.scalar_one_or_none()
    if not b:
        raise HTTPException(status_code=404, detail="Benchmark not found")
    payload = data.model_dump(exclude_unset=True)
    new_prc = payload.pop("property_room_category_id", None)
    for field, value in payload.items():
        setattr(b, field, value)
    if new_prc is not None:
        if new_prc:
            cat_row = (
                await db.execute(
                    select(PropertyRoomCategory).where(
                        PropertyRoomCategory.id == new_prc,
                        PropertyRoomCategory.property_id == b.property_id,
                    )
                )
            ).scalar_one_or_none()
            if not cat_row:
                raise HTTPException(status_code=400, detail="Invalid property_room_category_id for this property")
            b.property_room_category_id = new_prc
            b.room_category = cat_row.display_name
        else:
            b.property_room_category_id = None
    await db.commit()
    return {"message": "Benchmark updated"}


@router.delete("/{benchmark_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_benchmark(
    benchmark_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if current_user.role not in ("super_admin", "property_manager"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    result = await db.execute(select(RoomCategoryBenchmark).where(RoomCategoryBenchmark.id == benchmark_id))
    b = result.scalar_one_or_none()
    if not b:
        raise HTTPException(status_code=404, detail="Benchmark not found")
    b.is_active = False
    await db.commit()
