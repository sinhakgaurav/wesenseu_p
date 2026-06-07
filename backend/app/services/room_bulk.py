"""Bulk room creation from category variants."""
from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.property_room_category import PropertyRoomCategory
from app.models.room import Room


async def resolve_category_label(
    db: AsyncSession,
    property_id: uuid.UUID,
    property_room_category_id: uuid.UUID,
) -> str:
    row = (
        await db.execute(
            select(PropertyRoomCategory).where(
                PropertyRoomCategory.id == property_room_category_id,
                PropertyRoomCategory.property_id == property_id,
                PropertyRoomCategory.is_active == True,
            )
        )
    ).scalar_one_or_none()
    return row.display_name if row else "Standard"


async def bulk_create_rooms(
    db: AsyncSession,
    *,
    property_id: uuid.UUID,
    property_room_category_id: uuid.UUID,
    count: int,
    start_number: int = 101,
    room_number_prefix: str = "",
    floor_number: Optional[int] = None,
    room_view_catalog_id: Optional[uuid.UUID] = None,
) -> list[Room]:
    label = await resolve_category_label(db, property_id, property_room_category_id)
    created: list[Room] = []
    for i in range(count):
        num = start_number + i
        room_number = f"{room_number_prefix}{num}"
        exists = (
            await db.execute(
                select(Room.id).where(Room.property_id == property_id, Room.room_number == room_number)
            )
        ).scalar_one_or_none()
        if exists:
            continue
        room = Room(
            property_id=property_id,
            room_number=room_number,
            room_category=label,
            property_room_category_id=property_room_category_id,
            floor_number=floor_number,
            room_view_catalog_id=room_view_catalog_id,
        )
        db.add(room)
        created.append(room)
    return created
