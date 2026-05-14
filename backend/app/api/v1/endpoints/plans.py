"""
Subscription Plans (Pricing)

GET    /plans           – public list of active plans (no auth)
GET    /plans/{id}      – public plan detail
POST   /plans           – super_admin: create plan
PATCH  /plans/{id}      – super_admin: update plan
DELETE /plans/{id}      – super_admin: deactivate plan
POST   /plans/seed      – super_admin: seed default plans
"""
import uuid
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.models.plan import Plan
from app.models.employee import Employee
from app.api.v1.deps import get_current_user

router = APIRouter()


class PlanCreate(BaseModel):
    name: str
    slug: str
    tagline: Optional[str] = None
    price_monthly: Optional[float] = None
    price_yearly: Optional[float] = None
    currency: str = "INR"
    room_limit: Optional[int] = None
    employee_limit: Optional[int] = None
    features: List[str] = []
    module_defaults: dict = {}
    is_active: bool = True
    is_popular: bool = False
    display_order: int = 0
    cta_text: str = "Get Started"


class PlanUpdate(BaseModel):
    name: Optional[str] = None
    tagline: Optional[str] = None
    price_monthly: Optional[float] = None
    price_yearly: Optional[float] = None
    room_limit: Optional[int] = None
    employee_limit: Optional[int] = None
    features: Optional[List[str]] = None
    module_defaults: Optional[dict] = None
    is_active: Optional[bool] = None
    is_popular: Optional[bool] = None
    display_order: Optional[int] = None
    cta_text: Optional[str] = None


def _plan_dict(p: Plan) -> dict:
    return {
        "id": str(p.id), "name": p.name, "slug": p.slug,
        "tagline": p.tagline,
        "price_monthly": float(p.price_monthly) if p.price_monthly else None,
        "price_yearly": float(p.price_yearly) if p.price_yearly else None,
        "currency": p.currency,
        "room_limit": p.room_limit, "employee_limit": p.employee_limit,
        "features": p.features or [],
        "is_active": p.is_active, "is_popular": p.is_popular,
        "display_order": p.display_order, "cta_text": p.cta_text,
    }


@router.get("")
async def list_plans(
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """Public endpoint — no auth required."""
    q = select(Plan)
    if not include_inactive:
        q = q.where(Plan.is_active == True)
    result = await db.execute(q.order_by(Plan.display_order))
    return [_plan_dict(p) for p in result.scalars().all()]


@router.get("/{plan_id}")
async def get_plan(plan_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Plan).where(Plan.id == plan_id))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Plan not found")
    return _plan_dict(p)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_plan(
    data: PlanCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Super admin only")
    plan = Plan(**data.model_dump())
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return _plan_dict(plan)


@router.patch("/{plan_id}")
async def update_plan(
    plan_id: uuid.UUID,
    data: PlanUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Super admin only")
    result = await db.execute(select(Plan).where(Plan.id == plan_id))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Plan not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(p, field, value)
    await db.commit()
    return _plan_dict(p)


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_plan(
    plan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Super admin only")
    result = await db.execute(select(Plan).where(Plan.id == plan_id))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Plan not found")
    p.is_active = False
    await db.commit()


DEFAULT_PLANS = [
    {
        "name": "Starter", "slug": "starter", "display_order": 1,
        "tagline": "Perfect for small properties", "cta_text": "Start Free",
        "price_monthly": 4000, "price_yearly": 40000, "currency": "INR",
        "room_limit": 10, "employee_limit": 15, "is_popular": False,
        "features": [
            "Up to 10 rooms", "15 staff accounts", "Task management",
            "Ticketing system", "Basic reports", "Email notifications",
            "Guest portal (QR-based feedback)",
        ],
        "module_defaults": {"rooms": True, "tasks": True, "tickets": True, "inventory": False,
                            "surveillance": False, "verification": False},
    },
    {
        "name": "Growth", "slug": "growth", "display_order": 2,
        "tagline": "For growing hospitality businesses", "cta_text": "Get Growth",
        "price_monthly": 11999, "price_yearly": 119990, "currency": "INR",
        "room_limit": 30, "employee_limit": 50, "is_popular": True,
        "features": [
            "Up to 30 rooms", "50 staff accounts", "All Starter features",
            "AI room verification (WesenseU)", "CCTV surveillance + alerts",
            "Benchmark image management", "Inventory & orders",
            "Attendance tracking", "Advanced analytics",
        ],
        "module_defaults": {"rooms": True, "tasks": True, "tickets": True, "inventory": True,
                            "surveillance": True, "verification": True, "orders": True,
                            "attendance": True},
    },
    {
        "name": "Enterprise", "slug": "enterprise", "display_order": 3,
        "tagline": "Full-scale operations management", "cta_text": "Contact Sales",
        "price_monthly": 20000, "price_yearly": 200000, "currency": "INR",
        "room_limit": 50, "employee_limit": None, "is_popular": False,
        "features": [
            "Up to 50 rooms", "Unlimited staff accounts",
            "All Growth features", "Multi-property dashboard",
            "AI support chat for customers", "Custom integrations",
            "Priority support", "White-label option",
        ],
        "module_defaults": {"rooms": True, "tasks": True, "tickets": True, "inventory": True,
                            "surveillance": True, "verification": True, "orders": True,
                            "attendance": True, "support_chat": True, "reports": True},
    },
    {
        "name": "Custom", "slug": "custom", "display_order": 4,
        "tagline": "Enterprise-scale & IoT ready", "cta_text": "Talk to Us",
        "price_monthly": None, "price_yearly": None, "currency": "INR",
        "room_limit": None, "employee_limit": None, "is_popular": False,
        "features": [
            "Unlimited rooms & staff", "IoT / Smart Lock integration",
            "Predictive AI analytics", "Custom white-labeling",
            "Dedicated infrastructure", "SLA-backed support",
        ],
        "module_defaults": {},
    },
]


@router.post("/seed", status_code=status.HTTP_201_CREATED)
async def seed_plans(
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    """Seed default Starter / Growth / Enterprise / Custom plans if they don't exist."""
    if current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Super admin only")
    created = []
    for p_data in DEFAULT_PLANS:
        existing = (await db.execute(select(Plan).where(Plan.slug == p_data["slug"]))).scalar_one_or_none()
        if not existing:
            plan = Plan(**p_data)
            db.add(plan)
            created.append(p_data["slug"])
    await db.commit()
    return {"created": created, "message": f"{len(created)} plans seeded"}
