"""
AI Room Verification  (async queue-based flow)

POST /verification/task/{task_id}          – upload images → queues job to WesenseU
GET  /verification/task/{task_id}          – poll verification status / result
POST /verification/task/{task_id}/override – manual approve / reject
POST /verification/callback                – WesenseU webhook (internal)
"""
from datetime import datetime
from typing import List, Optional
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status, UploadFile, File
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.models.employee import Employee
from app.models.notification import Notification
from app.models.room import Room
from app.models.room_verification import RoomVerification
from app.models.task import Task
from app.services.storage import upload_file
from app.services.benchmark_requirements import validate_cleaning_task_photos
from app.api.v1.deps import get_current_user
from app.core.config import settings

router = APIRouter()


# ── Submit images → enqueue ───────────────────────────────────────────────────

@router.post("/task/{task_id}", status_code=status.HTTP_202_ACCEPTED)
async def submit_verification(
    task_id: uuid.UUID,
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    """
    Upload room images and queue them for AI verification by WesenseU.
    Returns immediately with a verification_id; result arrives via webhook callback.
    """
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Upload images to storage
    image_urls: List[str] = []
    for f in files:
        url = await upload_file(f, folder=f"verification/{task_id}")
        image_urls.append(url)

    if not image_urls:
        raise HTTPException(status_code=422, detail="No images could be uploaded")

    err = await validate_cleaning_task_photos(db, task)
    if err:
        raise HTTPException(status_code=400, detail=err)

    # Resolve room number for context
    room_number = ""
    if task.room_id:
        room_res = await db.execute(select(Room).where(Room.id == task.room_id))
        room = room_res.scalar_one_or_none()
        room_number = room.room_number if room else ""

    # Create verification record in "queued" state
    verification = RoomVerification(
        task_id=task_id,
        queue_status="queued",
        status="pending",
        submitted_image_urls=image_urls,
    )
    db.add(verification)
    task.status = "verification_pending"
    await db.commit()
    await db.refresh(verification)

    # Dispatch Celery task to call WesenseU
    try:
        from app.worker.tasks import dispatch_to_wesenseu
        dispatch_to_wesenseu.delay(
            verification_id=str(verification.id),
            task_id=str(task_id),
            image_urls=image_urls,
            room_number=room_number,
            task_type=task.task_type,
            property_id=str(task.property_id),
            room_id=str(task.room_id) if task.room_id else None,
        )
    except Exception:
        verification.queue_status = "queued"
        await db.commit()

    return {
        "verification_id": str(verification.id),
        "task_id": str(task_id),
        "queue_status": "queued",
        "images_uploaded": len(image_urls),
        "message": "Verification queued. Check status via GET /verification/task/{task_id}",
    }


# ── Poll status / result ──────────────────────────────────────────────────────

@router.get("/task/{task_id}")
async def get_verification_result(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    result = await db.execute(
        select(RoomVerification)
        .where(RoomVerification.task_id == task_id)
        .order_by(RoomVerification.created_at.desc())
    )
    verification = result.scalar_one_or_none()
    if not verification:
        raise HTTPException(status_code=404, detail="No verification record found for this task")

    return {
        "verification_id": str(verification.id),
        "task_id": str(task_id),
        "queue_status": verification.queue_status,
        "wesenseu_job_id": verification.wesenseu_job_id,
        "score": float(verification.verification_score) if verification.verification_score is not None else None,
        "cleanliness_score": float(verification.cleanliness_score) if verification.cleanliness_score else None,
        "organization_score": float(verification.organization_score) if verification.organization_score else None,
        "amenities_score": float(verification.amenities_score) if verification.amenities_score else None,
        "status": verification.status,
        "check_results": verification.check_results,
        "defects": verification.defects_found,
        "ai_response": verification.ai_response,
        "verified_at": verification.verified_at,
        "created_at": verification.created_at,
    }


# ── WesenseU webhook callback ─────────────────────────────────────────────────

@router.post("/callback")
async def wesenseu_callback(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Internal endpoint called by WesenseU Celery task when room verification completes.
    Payload: { job_id, caller_ref (verification_id), score, status, defects, check_results }
    """
    body = await request.json()

    caller_ref = body.get("caller_ref")
    if not caller_ref:
        raise HTTPException(status_code=422, detail="caller_ref missing in callback")

    try:
        verification_id = uuid.UUID(caller_ref)
    except ValueError:
        raise HTTPException(status_code=422, detail="caller_ref is not a valid UUID")

    ver_result = await db.execute(
        select(RoomVerification).where(RoomVerification.id == verification_id)
    )
    verification = ver_result.scalar_one_or_none()
    if not verification:
        raise HTTPException(status_code=404, detail="Verification record not found")

    score = body.get("score")
    verdict = body.get("status", "pending")
    defects = body.get("defects", [])
    check_results = body.get("check_results", {})
    wesenseu_job_id = body.get("job_id")

    # Map WesenseU statuses → Monitour statuses
    status_map = {
        "approved":     "approved",
        "needs_review": "pending",
        "rejected":     "rejected",
    }
    monitour_status = status_map.get(verdict, "pending")

    # Update verification
    verification.verification_score = score
    verification.cleanliness_score = check_results.get("cleanliness_score")
    verification.organization_score = check_results.get("organization_score")
    verification.amenities_score = check_results.get("amenities_score")
    verification.check_results = check_results
    verification.status = monitour_status
    verification.defects_found = {"defects": defects}
    verification.ai_response = {
        "wesenseu_job_id": wesenseu_job_id,
        "raw_status": verdict,
        "received_at": datetime.utcnow().isoformat(),
    }
    verification.wesenseu_job_id = wesenseu_job_id
    verification.queue_status = "completed"
    verification.verified_at = datetime.utcnow()

    # Update Task
    task_result = await db.execute(select(Task).where(Task.id == verification.task_id))
    task = task_result.scalar_one_or_none()
    if task:
        if monitour_status == "approved":
            task.status = "approved"
            task.completed_at = datetime.utcnow()

            # Mark room ready if it was a cleaning task
            if task.room_id and task.task_type == "cleaning":
                room_res = await db.execute(select(Room).where(Room.id == task.room_id))
                room = room_res.scalar_one_or_none()
                if room:
                    room.room_status = "ready"
                    room.last_cleaned_at = datetime.utcnow()

        elif monitour_status == "rejected":
            task.status = "rework_required"
        else:
            task.status = "verification_pending"

    # Send notification to property manager / dept manager
    if task:
        notif_type = "ai_mismatch" if monitour_status == "rejected" else "task_completed"
        title = (
            f"Room {_room_label(task)} Verification: {'✓ Approved' if monitour_status == 'approved' else '✗ Rejected'}"
        )
        message = (
            f"Score: {score:.1f}/100. "
            + (f"{len(defects)} defect(s) found." if defects else "No defects found.")
        )
        # Notify managers at this property
        mgr_res = await db.execute(
            select(Employee).where(
                Employee.property_id == task.property_id,
                Employee.role.in_(["property_manager", "dept_manager"]),
                Employee.status == "active",
            )
        )
        for mgr in mgr_res.scalars().all():
            db.add(Notification(
                user_id=mgr.id,
                property_id=task.property_id,
                notification_type=notif_type,
                title=title,
                message=message,
                data={
                    "task_id": str(task.id),
                    "verification_id": str(verification.id),
                    "score": score,
                    "status": monitour_status,
                },
                channels=["websocket", "push"],
            ))

    await db.commit()
    return {"received": True, "verification_id": str(verification.id)}


def _room_label(task: Task) -> str:
    return f"(task {str(task.id)[:8]})"


# ── Manual override ───────────────────────────────────────────────────────────

@router.post("/task/{task_id}/override")
async def manual_override(
    task_id: uuid.UUID,
    action: str,
    notes: str = "",
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if action not in ("approve", "reject"):
        raise HTTPException(status_code=400, detail="action must be 'approve' or 'reject'")
    if current_user.role not in ("super_admin", "property_manager", "dept_manager"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    ver_result = await db.execute(
        select(RoomVerification)
        .where(RoomVerification.task_id == task_id)
        .order_by(RoomVerification.created_at.desc())
    )
    verification = ver_result.scalar_one_or_none()
    if verification:
        verification.status = "manual_override"
        verification.queue_status = "completed"
        verification.verified_by = current_user.id
        verification.notes = notes
        verification.verified_at = datetime.utcnow()

    if action == "approve":
        task.status = "approved"
        task.completed_at = datetime.utcnow()
        if task.room_id and task.task_type == "cleaning":
            room_res = await db.execute(select(Room).where(Room.id == task.room_id))
            room = room_res.scalar_one_or_none()
            if room:
                room.room_status = "ready"
                room.last_cleaned_at = datetime.utcnow()
    else:
        task.status = "rework_required"

    await db.commit()
    return {"message": f"Task manually {action}d", "task_id": str(task_id)}
