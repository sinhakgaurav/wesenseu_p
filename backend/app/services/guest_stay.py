"""Guest stay lifecycle helpers."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.guest_stay import GuestStay
from app.models.room import Room


async def get_active_stay_for_room(db: AsyncSession, room_id: uuid.UUID) -> Optional[GuestStay]:
    return (
        await db.execute(
            select(GuestStay).where(
                GuestStay.room_id == room_id,
                GuestStay.status == "active",
            )
        )
    ).scalar_one_or_none()


async def open_guest_stay(
    db: AsyncSession,
    room: Room,
    guest_name: str,
    guest_phone: Optional[str],
    expected_check_out: Optional[datetime],
    notes: Optional[str] = None,
) -> GuestStay:
    existing = await get_active_stay_for_room(db, room.id)
    if existing:
        raise ValueError("Room already has an active guest stay")

    stay = GuestStay(
        property_id=room.property_id,
        room_id=room.id,
        guest_name=guest_name,
        guest_phone=guest_phone,
        expected_check_out=expected_check_out,
        notes=notes,
        status="active",
        check_in_at=datetime.utcnow(),
    )
    db.add(stay)
    await db.flush()
    return stay


async def close_active_stay(db: AsyncSession, room_id: uuid.UUID) -> Optional[GuestStay]:
    stay = await get_active_stay_for_room(db, room_id)
    if not stay:
        return None
    stay.status = "closed"
    stay.check_out_at = datetime.utcnow()
    await db.flush()
    return stay
