"""
Surveillance / CCTV Management

GET    /surveillance/cameras                  – list cameras for a property
POST   /surveillance/cameras                  – add camera to system
GET    /surveillance/cameras/{id}             – get single camera
PATCH  /surveillance/cameras/{id}             – update camera
DELETE /surveillance/cameras/{id}             – remove camera
POST   /surveillance/cameras/discover         – simulate WiFi/network RTSP discovery
POST   /surveillance/cameras/{id}/toggle-ai   – enable / disable AI monitoring

GET    /surveillance/events                   – list events
GET    /surveillance/events/{id}              – get single event
PATCH  /surveillance/events/{id}/status       – acknowledge / resolve event
POST   /surveillance/analyze                  – submit clip/snapshot to WesenseU
POST   /surveillance/callback                 – WesenseU webhook for analysis result
"""
import uuid
from datetime import datetime
from typing import List, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.models.employee import Employee
from app.models.surveillance import SurveillanceCamera, SurveillanceEvent
from app.models.notification import Notification
from app.api.v1.deps import get_current_user
from app.core.config import settings
from app.services.storage import upload_file
from app.constants.surveillance_hotel_scenarios import (
    HOTEL_SURVEILLANCE_SCENARIOS,
    default_scenario_rules_for_camera,
)

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────

class CameraCreate(BaseModel):
    property_id: uuid.UUID
    name: str
    location: str
    stream_url: Optional[str] = None
    camera_type: str = "ip"
    ai_monitoring_enabled: bool = False
    scenario_rules: Optional[list] = None


class CameraUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    stream_url: Optional[str] = None
    camera_type: Optional[str] = None
    ai_monitoring_enabled: Optional[bool] = None
    is_active: Optional[bool] = None
    scenario_rules: Optional[list] = None


class EventStatusUpdate(BaseModel):
    status: str  # acknowledged | resolved


class TimerSurveillanceEventCreate(BaseModel):
    """Demo / integration: record a duration-based surveillance breach (e.g. guard absent > 3 min)."""
    property_id: uuid.UUID
    camera_id: Optional[uuid.UUID] = None
    scenario_code: str
    duration_seconds: int
    threshold_seconds: int
    description: str = ""


# ── Hotel scenario checklist (unwanted situations + timer guidance) ───────────

@router.get("/hotel-surveillance-scenarios")
async def hotel_surveillance_scenarios(
    current_user: Employee = Depends(get_current_user),
):
    """Reference checklist for hotel CCTV / AI monitoring (includes timer-based examples)."""
    return {"scenarios": HOTEL_SURVEILLANCE_SCENARIOS}


@router.post("/timer-events", status_code=status.HTTP_201_CREATED)
async def create_timer_surveillance_event(
    data: TimerSurveillanceEventCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if current_user.role not in ("super_admin", "property_manager", "dept_manager"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    meta = next((s for s in HOTEL_SURVEILLANCE_SCENARIOS if s["code"] == data.scenario_code), None)
    label = meta["label"] if meta else data.scenario_code
    hint = meta.get("root_cause_hint") if meta else None
    sev = meta.get("default_severity", "medium") if meta else "medium"
    event = SurveillanceEvent(
        property_id=data.property_id,
        camera_id=data.camera_id,
        event_type=label,
        scenario_code=data.scenario_code,
        detection_mode="duration",
        duration_seconds=data.duration_seconds,
        threshold_seconds=data.threshold_seconds,
        root_cause_hint=hint,
        severity=sev,
        description=data.description or f"Timer rule: condition persisted {data.duration_seconds}s (threshold {data.threshold_seconds}s).",
        status="open",
        detected_at=datetime.utcnow(),
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return {"id": str(event.id), "message": "Timer-based surveillance event recorded"}


# ── Cameras ───────────────────────────────────────────────────────────────────

@router.get("/cameras")
async def list_cameras(
    property_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    prop_id = property_id or current_user.property_id
    q = select(SurveillanceCamera).where(SurveillanceCamera.is_active == True)
    if prop_id:
        q = q.where(SurveillanceCamera.property_id == prop_id)
    result = await db.execute(q.order_by(SurveillanceCamera.name))
    cameras = result.scalars().all()
    return [
        {
            "id": str(c.id),
            "property_id": str(c.property_id),
            "name": c.name,
            "location": c.location,
            "stream_url": c.stream_url,
            "camera_type": c.camera_type,
            "is_active": c.is_active,
            "ai_monitoring_enabled": c.ai_monitoring_enabled,
            "scenario_rules": c.scenario_rules or [],
            "created_at": c.created_at,
        }
        for c in cameras
    ]


@router.post("/cameras", status_code=status.HTTP_201_CREATED)
async def create_camera(
    data: CameraCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if current_user.role not in ("super_admin", "property_manager"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    payload = data.model_dump()
    if not payload.get("scenario_rules"):
        payload["scenario_rules"] = default_scenario_rules_for_camera()
    cam = SurveillanceCamera(**payload)
    db.add(cam)
    await db.commit()
    await db.refresh(cam)
    return {"id": str(cam.id), "name": cam.name, "message": "Camera added"}


@router.get("/cameras/{camera_id}")
async def get_camera(
    camera_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    result = await db.execute(select(SurveillanceCamera).where(SurveillanceCamera.id == camera_id))
    cam = result.scalar_one_or_none()
    if not cam:
        raise HTTPException(status_code=404, detail="Camera not found")
    return {
        "id": str(cam.id), "property_id": str(cam.property_id),
        "name": cam.name, "location": cam.location,
        "stream_url": cam.stream_url, "camera_type": cam.camera_type,
        "is_active": cam.is_active, "ai_monitoring_enabled": cam.ai_monitoring_enabled,
        "scenario_rules": cam.scenario_rules or [],
        "created_at": cam.created_at,
    }


@router.patch("/cameras/{camera_id}")
async def update_camera(
    camera_id: uuid.UUID,
    data: CameraUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if current_user.role not in ("super_admin", "property_manager"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    result = await db.execute(select(SurveillanceCamera).where(SurveillanceCamera.id == camera_id))
    cam = result.scalar_one_or_none()
    if not cam:
        raise HTTPException(status_code=404, detail="Camera not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(cam, field, value)
    await db.commit()
    return {"message": "Camera updated", "id": str(cam.id)}


@router.delete("/cameras/{camera_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_camera(
    camera_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if current_user.role not in ("super_admin", "property_manager"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    result = await db.execute(select(SurveillanceCamera).where(SurveillanceCamera.id == camera_id))
    cam = result.scalar_one_or_none()
    if not cam:
        raise HTTPException(status_code=404, detail="Camera not found")
    cam.is_active = False  # soft-delete
    await db.commit()


@router.post("/cameras/{camera_id}/toggle-ai")
async def toggle_ai_monitoring(
    camera_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if current_user.role not in ("super_admin", "property_manager"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    result = await db.execute(select(SurveillanceCamera).where(SurveillanceCamera.id == camera_id))
    cam = result.scalar_one_or_none()
    if not cam:
        raise HTTPException(status_code=404, detail="Camera not found")
    cam.ai_monitoring_enabled = not cam.ai_monitoring_enabled
    await db.commit()
    return {"id": str(cam.id), "ai_monitoring_enabled": cam.ai_monitoring_enabled}


@router.post("/cameras/discover")
async def discover_cameras(
    property_id: uuid.UUID,
    subnet: Optional[str] = "192.168.1",
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    """
    Simulate scanning the local network for RTSP / ONVIF IP cameras.
    In production, replace with actual network scan (e.g. nmap + ONVIF probing).
    Returns a list of discovered devices that can be added to the system.
    """
    if current_user.role not in ("super_admin", "property_manager"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    # Simulated discovery — replace with actual nmap/ONVIF probe
    discovered = [
        {"ip": f"{subnet}.{host}", "rtsp_url": f"rtsp://{subnet}.{host}:554/stream",
         "model": model, "manufacturer": mfr, "onvif": True}
        for host, model, mfr in [
            (101, "DS-2CD2143G2-I", "Hikvision"),
            (102, "IPC-HDW3849H", "Dahua"),
            (110, "C3W Pro", "Reolink"),
        ]
    ]
    return {"property_id": str(property_id), "subnet_scanned": subnet, "discovered": discovered}


# ── Events ────────────────────────────────────────────────────────────────────

@router.get("/events")
async def list_events(
    property_id: Optional[uuid.UUID] = None,
    camera_id: Optional[uuid.UUID] = None,
    status_filter: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    prop_id = property_id or current_user.property_id
    q = select(SurveillanceEvent)
    if prop_id:
        q = q.where(SurveillanceEvent.property_id == prop_id)
    if camera_id:
        q = q.where(SurveillanceEvent.camera_id == camera_id)
    if status_filter:
        q = q.where(SurveillanceEvent.status == status_filter)
    if severity:
        q = q.where(SurveillanceEvent.severity == severity)
    q = q.order_by(SurveillanceEvent.detected_at.desc()).limit(limit)
    result = await db.execute(q)
    events = result.scalars().all()
    return [
        {
            "id": str(e.id), "property_id": str(e.property_id),
            "camera_id": str(e.camera_id) if e.camera_id else None,
            "event_type": e.event_type, "severity": e.severity,
            "scenario_code": e.scenario_code,
            "detection_mode": e.detection_mode,
            "duration_seconds": e.duration_seconds,
            "threshold_seconds": e.threshold_seconds,
            "root_cause_hint": e.root_cause_hint,
            "description": e.description, "event_snapshot": e.event_snapshot,
            "status": e.status, "ai_confidence": e.ai_confidence,
            "detected_at": e.detected_at, "resolved_at": e.resolved_at,
        }
        for e in events
    ]


@router.get("/events/{event_id}")
async def get_event(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    result = await db.execute(select(SurveillanceEvent).where(SurveillanceEvent.id == event_id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return {
        "id": str(event.id), "event_type": event.event_type,
        "scenario_code": event.scenario_code,
        "detection_mode": event.detection_mode,
        "duration_seconds": event.duration_seconds,
        "threshold_seconds": event.threshold_seconds,
        "root_cause_hint": event.root_cause_hint,
        "severity": event.severity, "description": event.description,
        "event_snapshot": event.event_snapshot, "status": event.status,
        "ai_confidence": event.ai_confidence, "detected_at": event.detected_at,
    }


@router.patch("/events/{event_id}/status")
async def update_event_status(
    event_id: uuid.UUID,
    data: EventStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if data.status not in ("acknowledged", "resolved"):
        raise HTTPException(status_code=400, detail="status must be 'acknowledged' or 'resolved'")
    result = await db.execute(select(SurveillanceEvent).where(SurveillanceEvent.id == event_id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    event.status = data.status
    if data.status == "resolved":
        event.resolved_at = datetime.utcnow()
    await db.commit()
    return {"message": f"Event {data.status}", "id": str(event.id)}


# ── Send clip/snapshot to WesenseU for analysis ───────────────────────────────

@router.post("/analyze")
async def submit_for_analysis(
    property_id: uuid.UUID,
    camera_id: Optional[uuid.UUID] = None,
    media_url: Optional[str] = None,
    file: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    """Submit a CCTV clip or snapshot to WesenseU for AI anomaly detection."""
    if current_user.role not in ("super_admin", "property_manager", "dept_manager"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    # Upload file if provided
    if file:
        media_url = await upload_file(file, folder=f"surveillance/{property_id}")
    if not media_url:
        raise HTTPException(status_code=422, detail="media_url or file is required")

    job_type = "clip" if media_url.endswith((".mp4", ".avi", ".mov")) else "snapshot"
    callback_url = f"{settings.MONITOUR_PUBLIC_URL}/api/v1/surveillance/callback"

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{settings.WESENSEU_API_URL}/surveillance/analyze",
                json={
                    "caller_ref": str(camera_id) if camera_id else str(property_id),
                    "property_id": str(property_id),
                    "camera_id": str(camera_id) if camera_id else None,
                    "media_url": media_url,
                    "job_type": job_type,
                    "callback_url": callback_url,
                },
                headers={"X-API-Key": settings.WESENSEU_API_KEY or "wesenseu-api-key-for-enterweu"},
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"WesenseU unreachable: {exc}")


# ── WesenseU callback for surveillance results ────────────────────────────────

@router.post("/callback")
async def surveillance_callback(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Receive surveillance analysis results from WesenseU and create events."""
    body = await request.json()
    property_id = body.get("property_id")
    camera_id = body.get("camera_id")
    detected_events = body.get("detected_events", [])
    overall_risk = body.get("overall_risk", "low")

    for det in detected_events:
        severity = det.get("severity", "low")
        event = SurveillanceEvent(
            property_id=uuid.UUID(property_id) if property_id else None,
            camera_id=uuid.UUID(camera_id) if camera_id else None,
            event_type=det.get("event_type", "unknown"),
            scenario_code=det.get("scenario_code"),
            detection_mode=det.get("detection_mode", "instant"),
            duration_seconds=det.get("duration_seconds"),
            threshold_seconds=det.get("threshold_seconds"),
            root_cause_hint=det.get("root_cause_hint"),
            severity=severity,
            description=det.get("description", ""),
            event_snapshot=body.get("snapshot_url"),
            ai_confidence=det.get("confidence"),
            status="open",
            detected_at=datetime.utcnow(),
        )
        db.add(event)

        # Notify managers for high/critical events
        if severity in ("high", "critical") and property_id:
            from sqlalchemy import select as sa_select
            mgrs = (await db.execute(
                sa_select(Employee).where(
                    Employee.property_id == uuid.UUID(property_id),
                    Employee.role.in_(["property_manager", "dept_manager"]),
                    Employee.status == "active",
                )
            )).scalars().all()
            for mgr in mgrs:
                db.add(Notification(
                    user_id=mgr.id,
                    property_id=uuid.UUID(property_id),
                    notification_type="security_alert",
                    title=f"Security Alert: {det.get('event_type', 'Unknown')}",
                    message=f"Severity: {severity}. {det.get('description', '')}",
                    data={"camera_id": camera_id, "risk": overall_risk},
                    channels=["websocket", "push"],
                ))

    await db.commit()
    return {"received": True, "events_created": len(detected_events)}
