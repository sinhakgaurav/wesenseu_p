from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
import uuid

from app.db.base import get_db
from app.models.room import Room, RoomAuditLog
from app.models.task import Task
from app.models.employee import Employee
from app.models.property_room_category import PropertyRoomCategory
from app.schemas.room import RoomCreate, RoomUpdate, RoomResponse, RoomStatusUpdate, GuestCheckInRequest
from app.api.v1.deps import get_current_user

router = APIRouter()


async def _resolve_room_category_label(
    db: AsyncSession,
    property_id: uuid.UUID,
    property_room_category_id: Optional[uuid.UUID],
    fallback_label: str,
) -> tuple[Optional[uuid.UUID], str]:
    if not property_room_category_id:
        return None, fallback_label
    row = (
        await db.execute(
            select(PropertyRoomCategory).where(
                PropertyRoomCategory.id == property_room_category_id,
                PropertyRoomCategory.property_id == property_id,
                PropertyRoomCategory.is_active == True,
            )
        )
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=400, detail="Invalid or inactive property_room_category_id for this property")
    return property_room_category_id, row.display_name


@router.get("/", response_model=List[RoomResponse])
async def list_rooms(
    property_id: Optional[uuid.UUID] = None,
    room_status: Optional[str] = None,
    room_category: Optional[str] = None,
    property_room_category_id: Optional[uuid.UUID] = None,
    floor_number: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    query = select(Room).where(Room.is_active == True)
    prop_id = property_id or current_user.property_id
    if prop_id:
        query = query.where(Room.property_id == prop_id)

    if room_status:
        query = query.where(Room.room_status == room_status)
    if room_category:
        query = query.where(Room.room_category == room_category)
    if property_room_category_id:
        query = query.where(Room.property_room_category_id == property_room_category_id)
    if floor_number is not None:
        query = query.where(Room.floor_number == floor_number)

    query = query.offset(skip).limit(limit).order_by(Room.room_number)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/guest-stays", response_model=List[RoomResponse])
async def list_guest_stays(
    property_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    """Rooms currently occupied with guest details (front desk / housekeeping)."""
    prop_id = property_id or current_user.property_id
    q = select(Room).where(
        Room.is_active == True,
        Room.occupancy_status == "occupied",
    )
    if prop_id:
        q = q.where(Room.property_id == prop_id)
    q = q.order_by(Room.room_number)
    result = await db.execute(q)
    return result.scalars().all()


@router.post("/", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
async def create_room(
    data: RoomCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    pl = data.model_dump()
    prc_id = pl.get("property_room_category_id")
    label = (pl.get("room_category") or "").strip()
    prc_id, label = await _resolve_room_category_label(db, pl["property_id"], prc_id, label)
    if not label:
        raise HTTPException(status_code=400, detail="room_category or property_room_category_id is required")
    pl["room_category"] = label
    pl["property_room_category_id"] = prc_id
    room = Room(**pl)
    db.add(room)
    await db.commit()
    await db.refresh(room)
    return room


@router.post("/{room_id}/guest-check-in", response_model=RoomResponse)
async def guest_check_in(
    room_id: uuid.UUID,
    data: GuestCheckInRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if current_user.role not in ("super_admin", "property_manager", "dept_manager", "employee"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    result = await db.execute(select(Room).where(Room.id == room_id))
    room = result.scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    from datetime import datetime
    old_status = room.room_status
    room.guest_name = data.guest_name
    room.guest_phone = data.guest_phone
    room.expected_check_out = data.expected_check_out
    room.check_in_time = datetime.utcnow()
    room.check_out_time = None
    room.room_status = "occupied"
    room.occupancy_status = "occupied"
    if data.notes:
        room.notes = (room.notes or "") + ("\n" if room.notes else "") + data.notes
    audit = RoomAuditLog(
        room_id=room_id,
        action="guest_check_in",
        old_status=old_status,
        new_status="occupied",
        performed_by=current_user.id,
        notes=f"Guest: {data.guest_name}",
    )
    db.add(audit)
    await db.commit()
    await db.refresh(room)
    return room


@router.get("/{room_id}", response_model=RoomResponse)
async def get_room(
    room_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    result = await db.execute(select(Room).where(Room.id == room_id))
    room = result.scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room


@router.patch("/{room_id}", response_model=RoomResponse)
async def update_room(
    room_id: uuid.UUID,
    data: RoomUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    result = await db.execute(select(Room).where(Room.id == room_id))
    room = result.scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    payload = data.model_dump(exclude_unset=True)
    if "property_room_category_id" in payload:
        prc_id = payload.get("property_room_category_id")
        if prc_id:
            prc_id, cat_label = await _resolve_room_category_label(
                db, room.property_id, prc_id, room.room_category
            )
            payload["property_room_category_id"] = prc_id
            payload["room_category"] = cat_label
        else:
            payload["property_room_category_id"] = None

    for field, value in payload.items():
        setattr(room, field, value)

    await db.commit()
    await db.refresh(room)
    return room


@router.post("/{room_id}/status", response_model=RoomResponse)
async def update_room_status(
    room_id: uuid.UUID,
    data: RoomStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    result = await db.execute(select(Room).where(Room.id == room_id))
    room = result.scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    old_status = room.room_status

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(room, field, value)

    if data.room_status in ("occupied",):
        room.occupancy_status = "occupied"
    elif data.room_status in ("vacant", "cleaning_pending", "cleaning_in_progress", "ready", "maintenance"):
        room.occupancy_status = "vacant"

    audit = RoomAuditLog(
        room_id=room_id,
        action="status_change",
        old_status=old_status,
        new_status=data.room_status,
        performed_by=current_user.id,
        notes=data.notes,
    )
    db.add(audit)

    if data.room_status == "cleaning_pending":
        task = Task(
            property_id=room.property_id,
            room_id=room_id,
            created_by=current_user.id,
            task_type="cleaning",
            priority="high",
            description=f"Clean room {room.room_number} after checkout",
            status="pending",
        )
        db.add(task)

    await db.commit()
    await db.refresh(room)
    return room


@router.post("/{room_id}/checkout", response_model=RoomResponse)
async def checkout_room(
    room_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    result = await db.execute(select(Room).where(Room.id == room_id))
    room = result.scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    from datetime import datetime
    room.room_status = "cleaning_pending"
    room.occupancy_status = "vacant"
    room.check_out_time = datetime.utcnow()
    room.guest_name = None
    room.guest_phone = None
    room.expected_check_out = None

    task = Task(
        property_id=room.property_id,
        room_id=room_id,
        created_by=current_user.id,
        task_type="cleaning",
        priority="high",
        description=f"Clean room {room.room_number} after guest checkout",
        status="pending",
    )
    db.add(task)
    await db.commit()
    await db.refresh(room)
    return room


@router.get("/{room_id}/by-qr", response_model=RoomResponse)
async def get_room_by_qr(room_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Room).where(Room.id == room_id, Room.is_active == True))
    room = result.scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room


@router.delete("/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_room(
    room_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if current_user.role not in ("super_admin", "property_manager"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    result = await db.execute(select(Room).where(Room.id == room_id))
    room = result.scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    room.is_active = False
    await db.commit()
