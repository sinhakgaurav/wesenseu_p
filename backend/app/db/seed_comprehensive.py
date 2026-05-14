"""Idempotent demo dataset for dashboards, reports, and charts (metrics from real rows)."""
from __future__ import annotations

import asyncio
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select

from app.db.base import AsyncSessionLocal
from app.models.employee import Attendance, Employee
from app.models.feedback import Feedback
from app.models.inventory import InventoryItem, InventoryTransaction, Vendor
from app.models.laundry import LaundryOrder
from app.models.module_config import AVAILABLE_MODULES, ModuleConfig
from app.models.notification import Notification
from app.models.order import Order, OrderItem
from app.models.property import Property
from app.models.room import Room
from app.models.room_verification import RoomVerification
from app.models.surveillance import SurveillanceCamera, SurveillanceEvent
from app.models.support import SupportConversation, SupportMessage
from app.models.task import Task, TaskMedia
from app.models.ticket import Ticket, TicketComment

DEMO_TAG = "[monitour_demo_dataset]"
MARKER_TITLE = "MONITOUR_DEMO_DATASET_V1"


def _tnum() -> str:
    return f"TKT-{uuid.uuid4().hex[:10].upper()}"


def _onum() -> str:
    return f"ORD-{uuid.uuid4().hex[:10].upper()}"


async def run_comprehensive_seed() -> None:
    async with AsyncSessionLocal() as db:
        prop = (
            await db.execute(select(Property).where(Property.is_active == True).order_by(Property.name).limit(1))
        ).scalar_one_or_none()
        if not prop:
            print("[seed_comprehensive] No active property; skipping.")
            return

        marker = (
            await db.execute(
                select(Notification.id).where(
                    Notification.property_id == prop.id,
                    Notification.title == MARKER_TITLE,
                )
            )
        ).scalar_one_or_none()
        if marker:
            print("[seed_comprehensive] Demo dataset already applied; skipping.")
            return

        rooms = (
            await db.execute(select(Room).where(Room.property_id == prop.id, Room.is_active == True))
        ).scalars().all()
        if len(rooms) < 5:
            print("[seed_comprehensive] Not enough rooms; skipping.")
            return

        emps = (
            await db.execute(
                select(Employee).where(Employee.property_id == prop.id, Employee.status == "active").limit(20)
            )
        ).scalars().all()
        mgr = next((e for e in emps if e.role == "property_manager"), emps[0] if emps else None)
        staff = next((e for e in emps if e.role == "employee"), emps[-1] if emps else None)
        hk_dept_emp = next((e for e in emps if e.role in ("employee", "dept_manager")), staff)
        if not mgr or not staff:
            print("[seed_comprehensive] Missing employees; skipping.")
            return

        dept_id = hk_dept_emp.department_id or staff.department_id or mgr.department_id
        now = datetime.utcnow()

        # --- Module toggles (all modules on for demos) ---
        for mod in AVAILABLE_MODULES:
            row = (
                await db.execute(
                    select(ModuleConfig).where(ModuleConfig.property_id == prop.id, ModuleConfig.module_name == mod)
                )
            ).scalar_one_or_none()
            if not row:
                db.add(
                    ModuleConfig(
                        id=uuid.uuid4(),
                        property_id=prop.id,
                        module_name=mod,
                        is_enabled=True,
                        config={},
                        updated_by=mgr.id,
                    )
                )
        await db.flush()

        # --- Vendors ---
        for vname, phone in [("FreshLinens Co.", "+91-8001112222"), ("Hospitality Supplies Ltd", "+91-8003334444")]:
            exists = (
                await db.execute(select(Vendor.id).where(Vendor.property_id == prop.id, Vendor.name == vname))
            ).scalar_one_or_none()
            if not exists:
                db.add(
                    Vendor(
                        id=uuid.uuid4(),
                        property_id=prop.id,
                        name=vname,
                        contact_person="Demo Vendor",
                        phone=phone,
                        email="vendor@example.com",
                    )
                )
        await db.flush()

        vendors = (await db.execute(select(Vendor).where(Vendor.property_id == prop.id))).scalars().all()
        vendor_id = vendors[0].id if vendors else None

        # --- Staff availability mix (dashboard) ---
        for i, emp in enumerate(emps):
            if emp.role == "employee":
                emp.is_available = i % 3 != 0

        # --- Guest stay history (occupancy report uses check-in / check-out overlap) ---
        for i, room in enumerate(rooms[:12]):
            cin = now - timedelta(days=26 - i)
            cout = cin + timedelta(days=1 + (i % 4))
            room.check_in_time = cin
            room.check_out_time = cout
            room.guest_name = f"Past Guest {i}"
            room.occupancy_status = "vacant"
            room.room_status = "ready" if i % 2 == 0 else "vacant"
        for room in rooms[12:17]:
            room.check_in_time = now - timedelta(days=1 + (rooms.index(room) % 3))
            room.check_out_time = None
            room.guest_name = "In-house Guest"
            room.occupancy_status = "occupied"
            room.room_status = "occupied"
        tail = rooms[17:] if len(rooms) > 17 else []
        for j, room in enumerate(tail[:3]):
            room.room_status = "cleaning_pending" if j % 2 == 0 else "maintenance"
            room.occupancy_status = "vacant"

        # --- Tickets (time distribution + SLA breach sample) ---
        for day in range(22):
            ttype = "housekeeping" if day % 3 == 0 else "maintenance"
            prio = ["low", "medium", "high"][day % 3]
            status = ["open", "assigned", "in_progress", "resolved", "closed"][day % 5]
            created_at = now - timedelta(days=day)
            resolved_at = created_at + timedelta(hours=10) if status in ("resolved", "closed") else None
            breach = day == 7
            room = rooms[day % len(rooms)]
            t = Ticket(
                id=uuid.uuid4(),
                ticket_number=_tnum(),
                property_id=prop.id,
                room_id=room.id,
                department_id=dept_id,
                assigned_to=mgr.id if status != "open" else None,
                ticket_type=ttype,
                priority=prio,
                status=status,
                title=f"Demo ticket {day + 1}",
                description=f"Auto ticket for reporting. {DEMO_TAG}",
                created_by_guest=day % 2 == 0,
                guest_name="Walk-in" if day % 2 == 0 else None,
                sla_deadline=created_at + timedelta(hours=8),
                sla_breached=breach,
                resolved_at=resolved_at,
                created_at=created_at,
            )
            db.add(t)
            if status in ("resolved", "closed"):
                await db.flush()
                db.add(
                    TicketComment(
                        id=uuid.uuid4(),
                        ticket_id=t.id,
                        author_id=mgr.id,
                        author_name=mgr.full_name,
                        comment="Closed as part of demo dataset.",
                        is_internal=False,
                    )
                )

        # --- Tasks (completed per day for /reports/tasks) ---
        for day in range(18):
            room = rooms[(day + 3) % len(rooms)]
            created_at = now - timedelta(days=day + 2)
            completed_at = now - timedelta(days=day) if day % 4 != 0 else None
            st = "completed" if completed_at else ["pending", "assigned", "in_progress"][day % 3]
            tsk = Task(
                id=uuid.uuid4(),
                property_id=prop.id,
                room_id=room.id,
                assigned_to=hk_dept_emp.id,
                created_by=mgr.id,
                task_type="cleaning",
                service_type="housekeeping",
                priority="medium",
                status=st,
                description=f"Demo housekeeping task. {DEMO_TAG}",
                due_time=created_at + timedelta(hours=4),
                verification_required=True,
                created_at=created_at,
                completed_at=completed_at,
                started_at=created_at + timedelta(minutes=30) if completed_at else None,
            )
            db.add(tsk)
            if completed_at:
                await db.flush()
                db.add(
                    TaskMedia(
                        id=uuid.uuid4(),
                        task_id=tsk.id,
                        media_url="https://placehold.co/800x600/png?text=Task+photo",
                        media_type="photo",
                        file_size=12000,
                        uploaded_by=hk_dept_emp.id,
                    )
                )
                ver = RoomVerification(
                    id=uuid.uuid4(),
                    task_id=tsk.id,
                    queue_status="completed",
                    verification_score=Decimal("88.50"),
                    cleanliness_score=Decimal("90.00"),
                    organization_score=Decimal("85.00"),
                    amenities_score=Decimal("86.00"),
                    status="approved",
                    verified_by=mgr.id,
                    verified_at=completed_at,
                    submitted_image_urls=["https://placehold.co/800x600/png?text=Verify"],
                )
                db.add(ver)

        # --- Orders (delivered revenue curve) ---
        for day in range(16):
            room = rooms[day % len(rooms)]
            created_at = now - timedelta(days=day, hours=4)
            amt = Decimal("450.00") + Decimal(day * 35)
            o = Order(
                id=uuid.uuid4(),
                order_number=_onum(),
                room_id=room.id,
                property_id=prop.id,
                order_type=["food", "service", "amenity"][day % 3],
                total_amount=amt,
                status="delivered",
                guest_name=f"Order guest {day}",
                assigned_to=staff.id,
                delivered_at=created_at + timedelta(hours=2),
                created_at=created_at,
            )
            db.add(o)
            await db.flush()
            db.add(
                OrderItem(
                    id=uuid.uuid4(),
                    order_id=o.id,
                    item_name="Demo platter",
                    quantity=1 + (day % 3),
                    unit_price=Decimal("150.00"),
                    total_price=Decimal("150.00") * (1 + (day % 3)),
                )
            )

        # --- Inventory OUT / IN transactions (consumption report) ---
        items = (await db.execute(select(InventoryItem).where(InventoryItem.property_id == prop.id))).scalars().all()
        for idx, item in enumerate(items[:10]):
            for j in range(4):
                ts = now - timedelta(days=idx + j * 3)
                qty_out = 3 + (j % 4)
                db.add(
                    InventoryTransaction(
                        id=uuid.uuid4(),
                        inventory_item_id=item.id,
                        transaction_type="OUT",
                        quantity=qty_out,
                        reference_type="manual",
                        notes=f"Demo consumption. {DEMO_TAG}",
                        performed_by=staff.id,
                        created_at=ts,
                    )
                )
                item.current_stock = max(0, (item.current_stock or 0) - qty_out)
            db.add(
                InventoryTransaction(
                    id=uuid.uuid4(),
                    inventory_item_id=item.id,
                    transaction_type="IN",
                    quantity=20,
                    reference_type="manual",
                    notes=f"Demo restock. {DEMO_TAG}",
                    performed_by=mgr.id,
                    created_at=now - timedelta(days=1),
                )
            )
            item.current_stock = (item.current_stock or 0) + 20
            if vendor_id:
                item.vendor_id = vendor_id

        # --- More operational rows ---
        for i in range(8):
            room = rooms[i % len(rooms)]
            db.add(
                Feedback(
                    id=uuid.uuid4(),
                    property_id=prop.id,
                    room_id=room.id,
                    department_id=dept_id,
                    guest_name=f"Chart Guest {i}",
                    rating=2 + (i % 4),
                    review_text=f"Feedback for charts. {DEMO_TAG}",
                    sentiment_label=["positive", "neutral", "negative"][i % 3],
                    source="qr",
                    status=["pending", "reviewed", "resolved"][i % 3],
                )
            )

        for emp in emps[:5]:
            if not emp.property_id:
                continue
            for day_offset in range(14):
                d = date.today() - timedelta(days=day_offset)
                db.add(
                    Attendance(
                        id=uuid.uuid4(),
                        employee_id=emp.id,
                        property_id=prop.id,
                        date=d,
                        check_in=datetime.combine(d, datetime.min.time()) + timedelta(hours=8 + (day_offset % 2)),
                        check_out=datetime.combine(d, datetime.min.time()) + timedelta(hours=16),
                        status="present" if day_offset % 6 != 5 else "half_day",
                    )
                )

        cam = (
            await db.execute(select(SurveillanceCamera).where(SurveillanceCamera.property_id == prop.id).limit(1))
        ).scalar_one_or_none()
        if not cam:
            cam = SurveillanceCamera(
                id=uuid.uuid4(),
                property_id=prop.id,
                name="Lobby Cam (demo)",
                location="Lobby",
                stream_url="rtsp://demo/monitour/lobby",
                camera_type="ip",
                is_active=True,
                ai_monitoring_enabled=True,
            )
            db.add(cam)
            await db.flush()

        for i in range(12):
            db.add(
                SurveillanceEvent(
                    id=uuid.uuid4(),
                    property_id=prop.id,
                    camera_id=cam.id,
                    event_type=["motion_detected", "cleanliness_issue", "corridor_obstruction"][i % 3],
                    severity=["low", "medium", "high"][i % 3],
                    description=f"Seeded CCTV event {i + 1}. {DEMO_TAG}",
                    event_snapshot="https://placehold.co/640x360/png?text=CCTV",
                    status="open" if i % 3 == 0 else "acknowledged",
                    detected_at=now - timedelta(days=i % 20, hours=i),
                )
            )

        for i in range(6):
            db.add(
                LaundryOrder(
                    id=uuid.uuid4(),
                    property_id=prop.id,
                    room_id=rooms[i % len(rooms)].id,
                    guest_name=f"Laundry {i}",
                    status=["received", "washing", "ironing", "ready", "delivered"][i % 5],
                    priority=["low", "medium", "high"][i % 3],
                    items=[{"description": "Suits", "quantity": 1, "service_type": "dry_clean"}],
                    assigned_to=staff.id,
                )
            )

        notif_types = [
            "task_assigned",
            "ticket_created",
            "inventory_low",
            "surveillance_alert",
            "task_completed",
        ]
        for i in range(20):
            db.add(
                Notification(
                    id=uuid.uuid4(),
                    user_id=mgr.id if i % 2 == 0 else staff.id,
                    property_id=prop.id,
                    notification_type=notif_types[i % len(notif_types)],
                    title=f"Demo notification {i + 1}",
                    message=f"Seeded for inbox / channels. {DEMO_TAG}",
                    data={"index": i},
                    channels=["websocket", "push"],
                    is_read=i % 4 == 0,
                )
            )

        if prop.customer_id:
            conv = SupportConversation(
                id=uuid.uuid4(),
                customer_id=prop.customer_id,
                status="open",
                subject=f"Demo support thread {DEMO_TAG}",
            )
            db.add(conv)
            await db.flush()
            db.add(
                SupportMessage(
                    id=uuid.uuid4(),
                    conversation_id=conv.id,
                    role="user",
                    content="Hello, I need help with housekeeping scheduling.",
                )
            )
            db.add(
                SupportMessage(
                    id=uuid.uuid4(),
                    conversation_id=conv.id,
                    role="assistant",
                    content="I can help with housekeeping schedules and SLA policies.",
                )
            )
        else:
            conv = SupportConversation(
                id=uuid.uuid4(),
                session_id=f"demo-{uuid.uuid4().hex[:12]}",
                status="resolved",
                subject=f"Anonymous demo chat {DEMO_TAG}",
                satisfaction_rating=4,
                resolved_at=now - timedelta(hours=2),
            )
            db.add(conv)
            await db.flush()
            db.add(
                SupportMessage(
                    id=uuid.uuid4(),
                    conversation_id=conv.id,
                    role="user",
                    content="Pricing question from landing page visitor.",
                )
            )

        db.add(
            Notification(
                id=uuid.uuid4(),
                user_id=mgr.id,
                property_id=prop.id,
                notification_type="admin_notice",
                title=MARKER_TITLE,
                message="Monitour comprehensive demo data has been loaded for this property.",
                data={"seed_version": "v1"},
                channels=["websocket"],
            )
        )

        await db.commit()
        print(
            "[seed_comprehensive] Applied demo dataset: modules, vendors, room stays, tickets, tasks, "
            "verifications, orders, inventory txns, feedback, attendance, CCTV, laundry, notifications, support."
        )


def main() -> None:
    asyncio.run(run_comprehensive_seed())


if __name__ == "__main__":
    main()
