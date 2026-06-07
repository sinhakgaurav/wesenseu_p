from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import uuid

from app.db.base import get_db
from app.models.onboarding import OnboardingSession, ONBOARDING_STEPS
from app.models.employee import Employee
from app.schemas.onboarding import (
    OnboardingSessionCreate,
    OnboardingSessionResponse,
    OnboardingStepUpdate,
)
from app.api.v1.deps import get_current_user

router = APIRouter()


@router.get("/steps", response_model=list[str])
async def list_onboarding_steps():
    return list(ONBOARDING_STEPS)


@router.post("/sessions", response_model=OnboardingSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_onboarding_session(
    data: OnboardingSessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if current_user.role not in ("super_admin", "property_manager"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    session = OnboardingSession(
        customer_id=data.customer_id,
        property_id=data.property_id or current_user.property_id,
        current_step="business",
        step_index=0,
        payload={},
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


@router.get("/sessions", response_model=List[OnboardingSessionResponse])
async def list_onboarding_sessions(
    customer_id: Optional[uuid.UUID] = None,
    property_id: Optional[uuid.UUID] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if current_user.role not in ("super_admin", "property_manager"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    q = select(OnboardingSession)
    if customer_id:
        q = q.where(OnboardingSession.customer_id == customer_id)
    if property_id:
        q = q.where(OnboardingSession.property_id == property_id)
    elif current_user.property_id:
        q = q.where(OnboardingSession.property_id == current_user.property_id)
    if status_filter:
        q = q.where(OnboardingSession.status == status_filter)
    q = q.order_by(OnboardingSession.updated_at.desc()).offset(skip).limit(limit)
    return (await db.execute(q)).scalars().all()


@router.get("/sessions/{session_id}", response_model=OnboardingSessionResponse)
async def get_onboarding_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    session = (
        await db.execute(select(OnboardingSession).where(OnboardingSession.id == session_id))
    ).scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Onboarding session not found")
    return session


@router.patch("/sessions/{session_id}", response_model=OnboardingSessionResponse)
async def update_onboarding_session(
    session_id: uuid.UUID,
    data: OnboardingStepUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    session = (
        await db.execute(select(OnboardingSession).where(OnboardingSession.id == session_id))
    ).scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Onboarding session not found")

    if data.current_step is not None:
        if data.current_step not in ONBOARDING_STEPS:
            raise HTTPException(status_code=400, detail="Invalid step")
        session.current_step = data.current_step
    if data.step_index is not None:
        session.step_index = data.step_index
    if data.payload_patch:
        merged = dict(session.payload or {})
        merged.update(data.payload_patch)
        session.payload = merged
    if data.customer_id is not None:
        session.customer_id = data.customer_id
    if data.property_id is not None:
        session.property_id = data.property_id
    if data.status is not None:
        session.status = data.status

    await db.commit()
    await db.refresh(session)
    return session
