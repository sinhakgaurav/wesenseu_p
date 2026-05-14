"""
Resolve benchmark URLs and download staff verification images for WesenseU
multipart submission (WesenseU expects uploaded files, not bare URL form fields).
"""
from __future__ import annotations

import mimetypes
import uuid
from typing import List, Optional, Tuple

import httpx
from sqlalchemy import case, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.benchmark import RoomCategoryBenchmark
from app.models.property_room_category import PropertyRoomCategory

MAX_IMAGE_BYTES = 15 * 1024 * 1024


async def _resolve_category_row(
    db: AsyncSession,
    property_id: uuid.UUID,
    room_category: Optional[str],
    property_room_category_id: Optional[uuid.UUID],
) -> Optional[PropertyRoomCategory]:
    if property_room_category_id:
        res = await db.execute(
            select(PropertyRoomCategory).where(
                PropertyRoomCategory.id == property_room_category_id,
                PropertyRoomCategory.property_id == property_id,
                PropertyRoomCategory.is_active.is_(True),
            )
        )
        row = res.scalar_one_or_none()
        if row:
            return row
    if not room_category:
        return None
    res = await db.execute(
        select(PropertyRoomCategory)
        .where(
            PropertyRoomCategory.property_id == property_id,
            PropertyRoomCategory.is_active.is_(True),
            or_(
                PropertyRoomCategory.code == room_category,
                PropertyRoomCategory.display_name == room_category,
            ),
        )
        .limit(1)
    )
    return res.scalar_one_or_none()


async def resolve_benchmark_image_url(
    db: AsyncSession,
    property_id: uuid.UUID,
    room_category: Optional[str],
    property_room_category_id: Optional[uuid.UUID] = None,
) -> Optional[str]:
    """Pick one active benchmark for property + category (prefer ``general`` aspect)."""
    cat = await _resolve_category_row(db, property_id, room_category, property_room_category_id)
    label = (cat.display_name if cat else None) or room_category
    cat_id = cat.id if cat else None
    if not label and not cat_id:
        return None

    or_parts = []
    if cat_id:
        or_parts.append(RoomCategoryBenchmark.property_room_category_id == cat_id)
    if room_category:
        or_parts.append(RoomCategoryBenchmark.room_category == room_category)
    if label and label != room_category:
        or_parts.append(RoomCategoryBenchmark.room_category == label)
    if not or_parts:
        return None

    stmt = (
        select(RoomCategoryBenchmark)
        .where(
            RoomCategoryBenchmark.property_id == property_id,
            RoomCategoryBenchmark.is_active.is_(True),
            or_(*or_parts),
        )
        .order_by(
            case((RoomCategoryBenchmark.aspect == "general", 0), else_=1),
            RoomCategoryBenchmark.created_at.asc(),
        )
        .limit(1)
    )
    res = await db.execute(stmt)
    row = res.scalar_one_or_none()
    return row.image_url if row else None


async def download_verification_images(
    client: httpx.AsyncClient,
    image_urls: List[str],
) -> List[Tuple[str, bytes, str]]:
    """
    Download each URL into memory for multipart upload.
    Returns list of (filename, content_bytes, content_type).
    """
    parts: List[Tuple[str, bytes, str]] = []
    for i, url in enumerate(image_urls):
        if not url or not str(url).strip():
            continue
        resp = await client.get(url, follow_redirects=True, timeout=120.0)
        resp.raise_for_status()
        data = resp.content
        if len(data) > MAX_IMAGE_BYTES:
            raise ValueError(f"Image {i} exceeds max size ({MAX_IMAGE_BYTES} bytes)")
        ctype = resp.headers.get("content-type", "").split(";")[0].strip().lower()
        if not ctype or ctype == "application/octet-stream":
            path = url.split("?", 1)[0].lower()
            if path.endswith(".png"):
                ctype = "image/png"
            elif path.endswith(".webp"):
                ctype = "image/webp"
            else:
                ctype = "image/jpeg"
        ext = mimetypes.guess_extension(ctype) or ".jpg"
        if ext == ".jpe":
            ext = ".jpg"
        parts.append((f"capture_{i}{ext}", data, ctype))
    if not parts:
        raise ValueError("No verification images could be downloaded")
    return parts
