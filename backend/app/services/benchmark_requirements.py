"""How many staff photos are required before a cleaning task can enter verification."""
from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.benchmark import RoomCategoryBenchmark
from app.models.room import Room
from app.models.task import Task, TaskMedia


async def required_benchmark_aspect_count(
    db: AsyncSession,
    property_id: uuid.UUID,
    room: Optional[Room],
) -> tuple[int, list[str]]:
    """
    Returns (required_photo_count, list of aspect labels).
    Count = distinct active benchmark aspects for the room's category.
    """
    if not room:
        return 0, []

    or_parts = []
    if room.property_room_category_id:
        or_parts.append(RoomCategoryBenchmark.property_room_category_id == room.property_room_category_id)
    if room.room_category:
        or_parts.append(RoomCategoryBenchmark.room_category == room.room_category)

    if not or_parts:
        return 0, []

    q = (
        select(RoomCategoryBenchmark.aspect)
        .where(
            RoomCategoryBenchmark.property_id == property_id,
            RoomCategoryBenchmark.is_active == True,
            or_(*or_parts),
        )
        .distinct()
    )
    aspects = [row[0] for row in (await db.execute(q)).all() if row[0]]
    return len(aspects), aspects


async def count_task_photos(db: AsyncSession, task_id: uuid.UUID) -> int:
    r = await db.execute(
        select(func.count())
        .select_from(TaskMedia)
        .where(TaskMedia.task_id == task_id, TaskMedia.media_type == "photo")
    )
    return int(r.scalar() or 0)


async def validate_cleaning_task_photos(db: AsyncSession, task: Task) -> Optional[str]:
    """Return error message if photos insufficient; None if OK or not applicable."""
    if not task.verification_required or task.task_type != "cleaning":
        return None
    room = None
    if task.room_id:
        room = (await db.execute(select(Room).where(Room.id == task.room_id))).scalar_one_or_none()
    required, aspects = await required_benchmark_aspect_count(db, task.property_id, room)
    if required == 0:
        return None
    have = await count_task_photos(db, task.id)
    if have < required:
        return (
            f"Upload at least {required} room photo(s) matching benchmark aspects "
            f"({', '.join(aspects)}). Currently {have} photo(s)."
        )
    return None
