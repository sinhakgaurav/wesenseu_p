"""
Celery background tasks.
Run worker: celery -A app.worker.celery_app worker --loglevel=info
Run beat:   celery -A app.worker.celery_app beat  --loglevel=info
"""
import asyncio
from datetime import datetime
from celery.utils.log import get_task_logger
from app.worker.celery_app import celery_app

logger = get_task_logger(__name__)


def _run(coro):
    """Run an async coroutine from a sync Celery task."""
    return asyncio.get_event_loop().run_until_complete(coro)


@celery_app.task(name="app.worker.tasks.check_sla_breaches")
def check_sla_breaches():
    """Find tickets past SLA deadline and send breach alerts."""
    async def _work():
        from sqlalchemy import select
        from app.db.base import AsyncSessionLocal
        from app.models.ticket import Ticket
        from app.models.employee import Employee
        from app.models.property import Property
        from app.services.email import send_sla_breach_alert

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Ticket).where(
                    Ticket.sla_deadline < datetime.utcnow(),
                    Ticket.status.notin_(["resolved", "closed"]),
                    Ticket.sla_breached == False,
                )
            )
            breached = result.scalars().all()

            for ticket in breached:
                ticket.sla_breached = True
                # fetch property manager email
                mgr_result = await db.execute(
                    select(Employee).where(
                        Employee.property_id == ticket.property_id,
                        Employee.role == "property_manager",
                        Employee.status == "active",
                    )
                )
                managers = mgr_result.scalars().all()
                for mgr in managers:
                    await send_sla_breach_alert(
                        ticket.ticket_number, ticket.title,
                        ticket.priority, mgr.email,
                    )
                logger.info("SLA breach flagged: %s", ticket.ticket_number)

            await db.commit()
            logger.info("SLA check complete. Breaches flagged: %d", len(breached))

    _run(_work())


@celery_app.task(name="app.worker.tasks.check_low_stock")
def check_low_stock():
    """Alert property managers when inventory items fall below minimum stock."""
    async def _work():
        from sqlalchemy import select
        from app.db.base import AsyncSessionLocal
        from app.models.inventory import InventoryItem
        from app.models.employee import Employee
        from app.services.email import send_low_stock_alert

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(InventoryItem).where(InventoryItem.is_active == True)
            )
            items = result.scalars().all()
            alerts_sent = 0

            for item in items:
                if item.current_stock <= item.minimum_stock:
                    mgr_result = await db.execute(
                        select(Employee).where(
                            Employee.property_id == item.property_id,
                            Employee.role == "property_manager",
                            Employee.status == "active",
                        )
                    )
                    managers = mgr_result.scalars().all()
                    for mgr in managers:
                        await send_low_stock_alert(
                            item.item_name, item.current_stock,
                            item.minimum_stock, mgr.email,
                        )
                    alerts_sent += 1

            logger.info("Low-stock check complete. Alerts sent: %d", alerts_sent)

    _run(_work())


@celery_app.task(name="app.worker.tasks.escalate_overdue_tasks")
def escalate_overdue_tasks():
    """Increment escalation count on tasks past their due time."""
    async def _work():
        from sqlalchemy import select
        from app.db.base import AsyncSessionLocal
        from app.models.task import Task
        from app.models.employee import Employee
        from app.services.email import send_email

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Task).where(
                    Task.due_time < datetime.utcnow(),
                    Task.status.notin_(["completed", "approved", "cancelled"]),
                )
            )
            overdue = result.scalars().all()

            for task in overdue:
                task.escalation_count += 1

                if task.assigned_to:
                    emp_result = await db.execute(
                        select(Employee).where(Employee.id == task.assigned_to)
                    )
                    emp = emp_result.scalar_one_or_none()
                    if emp:
                        await send_email(
                            emp.email,
                            f"OVERDUE Task – {task.task_type.replace('_', ' ').title()}",
                            f"<p>Your task is overdue (escalation #{task.escalation_count}). "
                            f"Please complete it immediately.</p>",
                        )

            await db.commit()
            logger.info("Overdue escalation complete. Tasks escalated: %d", len(overdue))

    _run(_work())


@celery_app.task(name="app.worker.tasks.send_task_assigned_email")
def send_task_assigned_email(employee_email: str, employee_name: str,
                              task_type: str, room_number: str):
    """Send email notification when a task is assigned."""
    async def _work():
        from app.services.email import send_task_assigned_notification
        await send_task_assigned_notification(employee_email, employee_name, task_type, room_number)

    _run(_work())


@celery_app.task(
    name="app.worker.tasks.dispatch_to_wesenseu",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
)
def dispatch_to_wesenseu(
    self,
    verification_id: str,
    task_id: str,
    image_urls: list,
    room_number: str = "",
    task_type: str = "",
    property_id: str = "",
    room_id: str = None,
):
    """
    Submit room images to WesenseU for AI analysis.
    Downloads each stored image URL, POSTs multipart form to WesenseU ``/rooms/verify``
    (required by WesenseU), including ``room_category`` and optional ``benchmark_image_url``
    resolved from ``RoomCategoryBenchmark``.
    Updates RoomVerification.queue_status and stores wesenseu_job_id.
    WesenseU will POST the result back to /api/v1/verification/callback.
    """
    async def _work():
        import uuid
        import httpx
        from sqlalchemy import select
        from app.db.base import AsyncSessionLocal
        from app.models.room_verification import RoomVerification
        from app.models.task import Task
        from app.models.room import Room
        from app.models.property_room_category import PropertyRoomCategory
        from app.core.config import settings
        from app.services.wesenseu_dispatch import (
            resolve_benchmark_image_url,
            download_verification_images,
        )

        callback_url = f"{settings.MONITOUR_PUBLIC_URL}/api/v1/verification/callback"
        task_uuid = uuid.UUID(task_id)

        room_category = ""
        room_cat_id = None
        benchmark_image_url = None
        prop_uuid = None

        async with AsyncSessionLocal() as db:
            ver_res = await db.execute(
                select(RoomVerification).where(RoomVerification.id == verification_id)
            )
            verification = ver_res.scalar_one_or_none()
            if not verification:
                logger.error("Verification %s not found", verification_id)
                return

            verification.queue_status = "dispatched"
            await db.commit()

            task_row = await db.execute(select(Task).where(Task.id == task_uuid))
            task = task_row.scalar_one_or_none()
            if property_id:
                try:
                    prop_uuid = uuid.UUID(property_id)
                except ValueError:
                    prop_uuid = None
            if task:
                if prop_uuid is None:
                    prop_uuid = task.property_id
                if task.room_id:
                    rres = await db.execute(select(Room).where(Room.id == task.room_id))
                    room_obj = rres.scalar_one_or_none()
                    if room_obj:
                        room_cat_id = room_obj.property_room_category_id
                        if room_cat_id:
                            dn = (
                                await db.execute(
                                    select(PropertyRoomCategory.display_name).where(
                                        PropertyRoomCategory.id == room_cat_id
                                    )
                                )
                            ).scalar_one_or_none()
                            room_category = (dn or room_obj.room_category or "")
                        else:
                            room_category = room_obj.room_category or ""
                if prop_uuid:
                    benchmark_image_url = await resolve_benchmark_image_url(
                        db, prop_uuid, room_category or None, room_cat_id
                    )

        try:
            form_data = {
                "caller_ref": verification_id,
                "property_id": property_id or (str(prop_uuid) if prop_uuid else ""),
                "room_id": room_id or "",
                "room_number": room_number or "",
                "room_category": room_category or "",
                "task_type": task_type or "",
                "callback_url": callback_url,
            }
            if benchmark_image_url:
                form_data["benchmark_image_url"] = benchmark_image_url

            async with httpx.AsyncClient(timeout=120.0) as client:
                file_parts = await download_verification_images(client, image_urls)
                files = [("files", (name, content, ctype)) for name, content, ctype in file_parts]
                resp = await client.post(
                    f"{settings.WESENSEU_API_URL}/rooms/verify",
                    data=form_data,
                    files=files,
                    headers={"X-API-Key": settings.WESENSEU_API_KEY or "wesenseu-api-key-for-enterweu"},
                )
                resp.raise_for_status()
                data = resp.json()
                wesenseu_job_id = str(data.get("id", ""))

            async with AsyncSessionLocal() as db:
                ver_res = await db.execute(
                    select(RoomVerification).where(RoomVerification.id == verification_id)
                )
                verification = ver_res.scalar_one_or_none()
                if verification:
                    verification.queue_status = "processing"
                    verification.wesenseu_job_id = wesenseu_job_id
                    await db.commit()

            logger.info(
                "Dispatched verification %s to WesenseU as job %s (benchmark=%s)",
                verification_id,
                wesenseu_job_id,
                bool(benchmark_image_url),
            )

        except Exception as exc:
            logger.error("dispatch_to_wesenseu failed: %s", exc)
            async with AsyncSessionLocal() as db:
                ver_res = await db.execute(
                    select(RoomVerification).where(RoomVerification.id == verification_id)
                )
                verification = ver_res.scalar_one_or_none()
                if verification:
                    verification.queue_status = "queued"  # allow retry
                    await db.commit()
            raise self.retry(exc=exc)

    _run(_work())
