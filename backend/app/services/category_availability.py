"""Category availability pool for front desk / booking."""
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.guest_stay import GuestStay
from app.models.property_room_category import PropertyRoomCategory
from app.models.room import Room

AVAILABLE_STATUSES = ("vacant", "ready", "clean")


async def category_availability(
    db: AsyncSession,
    property_id: uuid.UUID,
    *,
    on_date: Optional[date] = None,
) -> list[dict]:
    """Per category: total rooms vs available (not occupied by active stay)."""
    on_date = on_date or date.today()
    day_start = datetime.combine(on_date, datetime.min.time())
    day_end = datetime.combine(on_date, datetime.max.time())

    categories = (
        await db.execute(
            select(PropertyRoomCategory).where(
                PropertyRoomCategory.property_id == property_id,
                PropertyRoomCategory.is_active == True,
            )
        )
    ).scalars().all()

    result = []
    for cat in categories:
        total_r = await db.execute(
            select(func.count(Room.id)).where(
                Room.property_id == property_id,
                Room.is_active == True,
                Room.property_room_category_id == cat.id,
            )
        )
        total = int(total_r.scalar() or 0)

        occupied_r = await db.execute(
            select(func.count(Room.id)).where(
                Room.property_id == property_id,
                Room.is_active == True,
                Room.property_room_category_id == cat.id,
                or_(
                    Room.occupancy_status == "occupied",
                    Room.room_status.in_(("occupied", "cleaning_in_progress", "cleaning_pending", "maintenance")),
                ),
            )
        )
        occupied = int(occupied_r.scalar() or 0)

        stay_overlap_r = await db.execute(
            select(func.count(func.distinct(GuestStay.room_id))).where(
                GuestStay.property_id == property_id,
                GuestStay.room_id.isnot(None),
                GuestStay.status == "active",
                GuestStay.check_in_at <= day_end,
                or_(GuestStay.check_out_at.is_(None), GuestStay.check_out_at >= day_start),
            )
        )
        _ = stay_overlap_r  # guest_stays refine future booking windows

        available = max(0, total - occupied)
        result.append(
            {
                "category_id": str(cat.id),
                "code": cat.code,
                "display_name": cat.display_name,
                "base_price": float(cat.base_price) if cat.base_price else None,
                "total_rooms": total,
                "available_rooms": available,
                "occupied_rooms": occupied,
            }
        )
    return result
