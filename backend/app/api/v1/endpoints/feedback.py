from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from pydantic import BaseModel
import uuid

from app.db.base import get_db
from app.db.soft_delete import apply_soft_delete, not_deleted_clause, restore_soft_deleted
from app.models.feedback import Feedback
from app.models.employee import Employee
from app.schemas.feedback import FeedbackCreate, FeedbackResponse
from app.api.v1.deps import get_current_user


class FeedbackStatusUpdate(BaseModel):
    status: str  # pending | reviewed | flagged | resolved

router = APIRouter()


@router.post("/", response_model=FeedbackResponse, status_code=201)
async def submit_feedback(data: FeedbackCreate, db: AsyncSession = Depends(get_db)):
    """Public endpoint for guest feedback."""
    feedback = Feedback(**data.model_dump())

    if feedback.review_text:
        positive_words = ["great", "excellent", "good", "amazing", "wonderful", "clean", "friendly", "love", "best", "perfect"]
        negative_words = ["bad", "poor", "dirty", "rude", "terrible", "worst", "broken", "slow", "awful", "horrible"]
        text_lower = feedback.review_text.lower()
        pos_count = sum(1 for w in positive_words if w in text_lower)
        neg_count = sum(1 for w in negative_words if w in text_lower)
        if pos_count > neg_count:
            feedback.sentiment_label = "positive"
            feedback.sentiment_score = min(1.0, 0.5 + pos_count * 0.1)
        elif neg_count > pos_count:
            feedback.sentiment_label = "negative"
            feedback.sentiment_score = max(-1.0, -0.5 - neg_count * 0.1)
        else:
            feedback.sentiment_label = "neutral"
            feedback.sentiment_score = 0.0

    db.add(feedback)
    await db.commit()
    await db.refresh(feedback)
    return feedback


@router.get("/", response_model=List[FeedbackResponse])
async def list_feedback(
    property_id: Optional[uuid.UUID] = None,
    room_id: Optional[uuid.UUID] = None,
    department_id: Optional[uuid.UUID] = None,
    min_rating: Optional[int] = None,
    skip: int = 0,
    limit: int = 50,
    include_deleted: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    query = select(Feedback)
    if not include_deleted:
        clause = not_deleted_clause(Feedback)
        if clause is not None:
            query = query.where(clause)
    prop_id = property_id or current_user.property_id
    if prop_id:
        query = query.where(Feedback.property_id == prop_id)
    if room_id:
        query = query.where(Feedback.room_id == room_id)
    if department_id:
        query = query.where(Feedback.department_id == department_id)
    if min_rating:
        query = query.where(Feedback.rating >= min_rating)

    query = query.offset(skip).limit(limit).order_by(Feedback.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/summary")
async def feedback_summary(
    property_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    prop_id = property_id or current_user.property_id
    result = await db.execute(
        select(
            func.avg(Feedback.rating).label("avg_rating"),
            func.count(Feedback.id).label("total"),
            func.sum(func.case((Feedback.sentiment_label == "positive", 1), else_=0)).label("positive"),
            func.sum(func.case((Feedback.sentiment_label == "negative", 1), else_=0)).label("negative"),
            func.sum(func.case((Feedback.sentiment_label == "neutral", 1), else_=0)).label("neutral"),
        ).where(Feedback.property_id == prop_id)
    )
    row = result.one()
    return {
        "avg_rating": round(float(row.avg_rating or 0), 2),
        "total_feedback": row.total,
        "positive": row.positive or 0,
        "negative": row.negative or 0,
        "neutral": row.neutral or 0,
    }


@router.get("/{feedback_id}", response_model=FeedbackResponse)
async def get_feedback(
    feedback_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    result = await db.execute(select(Feedback).where(Feedback.id == feedback_id))
    fb = result.scalar_one_or_none()
    if not fb:
        raise HTTPException(status_code=404, detail="Feedback not found")
    return fb


@router.patch("/{feedback_id}", response_model=FeedbackResponse)
async def update_feedback_status(
    feedback_id: uuid.UUID,
    data: FeedbackStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if current_user.role not in ("super_admin", "property_manager"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    result = await db.execute(select(Feedback).where(Feedback.id == feedback_id))
    fb = result.scalar_one_or_none()
    if not fb:
        raise HTTPException(status_code=404, detail="Feedback not found")
    if hasattr(fb, "status"):
        fb.status = data.status
    await db.commit()
    await db.refresh(fb)
    return fb


@router.delete("/{feedback_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_feedback(
    feedback_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if current_user.role not in ("super_admin", "property_manager"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    result = await db.execute(select(Feedback).where(Feedback.id == feedback_id))
    fb = result.scalar_one_or_none()
    if not fb:
        raise HTTPException(status_code=404, detail="Feedback not found")
    apply_soft_delete(fb)
    await db.commit()


@router.post("/{feedback_id}/restore", response_model=FeedbackResponse)
async def restore_feedback(
    feedback_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if current_user.role not in ("super_admin", "property_manager"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    result = await db.execute(select(Feedback).where(Feedback.id == feedback_id))
    fb = result.scalar_one_or_none()
    if not fb:
        raise HTTPException(status_code=404, detail="Feedback not found")
    restore_soft_deleted(fb)
    await db.commit()
    await db.refresh(fb)
    return fb
