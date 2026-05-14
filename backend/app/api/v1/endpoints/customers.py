"""
Customer API  (B2B clients who own one or more Properties)

POST   /customers/login            – customer login
POST   /customers/refresh-token    – refresh customer token
GET    /customers/me               – current customer profile
PATCH  /customers/me               – update profile
GET    /customers/dashboard        – aggregated stats across all owned properties
GET    /customers/properties       – list owned properties
GET    /customers/verifications    – recent verifications across all properties
POST   /customers/                 – register new customer  (super_admin only)
GET    /customers/{id}             – get customer  (super_admin only)
"""
from datetime import datetime
from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.models.customer import Customer
from app.models.employee import Employee
from app.models.property import Property
from app.models.room import Room
from app.models.room_verification import RoomVerification
from app.models.task import Task
from app.models.ticket import Ticket
from app.core.security import (
    get_password_hash,
    verify_password_async,
    create_customer_access_token,
    create_customer_refresh_token,
    decode_token,
)
from app.schemas.customer import (
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse,
    CustomerLoginRequest,
    CustomerLoginResponse,
    CustomerDashboard,
    PropertySummary,
    VerificationSummaryItem,
)
from app.api.v1.deps import get_current_user, get_current_customer

router = APIRouter()


# ── Auth ──────────────────────────────────────────────────────────────────────

@router.post("/login", response_model=CustomerLoginResponse)
async def customer_login(
    request: CustomerLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Customer).where(Customer.email == request.email))
    customer = result.scalar_one_or_none()

    if not customer or not await verify_password_async(request.password, customer.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not customer.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")
    if customer.subscription_status != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Subscription is not active")

    customer.last_login = datetime.utcnow()
    await db.commit()

    return CustomerLoginResponse(
        access_token=create_customer_access_token(str(customer.id)),
        refresh_token=create_customer_refresh_token(str(customer.id)),
        customer=customer,
    )


@router.post("/refresh-token")
async def customer_refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db),
):
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "customer_refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    customer_id = payload.get("sub")
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    customer = result.scalar_one_or_none()
    if not customer or not customer.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Customer not found or inactive")

    return {
        "access_token": create_customer_access_token(str(customer.id)),
        "refresh_token": create_customer_refresh_token(str(customer.id)),
        "token_type": "bearer",
    }


# ── Self ──────────────────────────────────────────────────────────────────────

@router.get("/me", response_model=CustomerResponse)
async def get_my_profile(current_customer: Customer = Depends(get_current_customer)):
    return current_customer


@router.patch("/me", response_model=CustomerResponse)
async def update_my_profile(
    data: CustomerUpdate,
    db: AsyncSession = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(current_customer, field, value)
    await db.commit()
    await db.refresh(current_customer)
    return current_customer


# ── Dashboard ─────────────────────────────────────────────────────────────────

@router.get("/dashboard", response_model=CustomerDashboard)
async def customer_dashboard(
    db: AsyncSession = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    # All properties owned by this customer
    props_result = await db.execute(
        select(Property).where(
            Property.customer_id == current_customer.id,
            Property.is_active == True,
        )
    )
    properties = props_result.scalars().all()
    property_ids = [p.id for p in properties]

    if not property_ids:
        return CustomerDashboard(
            customer_id=current_customer.id,
            company_name=current_customer.company_name,
            total_properties=0,
            total_rooms=0,
            active_tickets=0,
            verifications_today=0,
            avg_score_today=None,
            properties=[],
            recent_verifications=[],
        )

    # ── Global counts ─────────────────────────────────────────────────────────
    rooms_q = await db.execute(
        select(func.count(Room.id)).where(
            Room.property_id.in_(property_ids), Room.is_active == True
        )
    )
    total_rooms = rooms_q.scalar() or 0

    tickets_q = await db.execute(
        select(func.count(Ticket.id)).where(
            Ticket.property_id.in_(property_ids),
            Ticket.status.notin_(["resolved", "closed"]),
        )
    )
    active_tickets = tickets_q.scalar() or 0

    # ── Today's verifications ─────────────────────────────────────────────────
    verif_q = await db.execute(
        select(RoomVerification)
        .join(Task, RoomVerification.task_id == Task.id)
        .where(
            Task.property_id.in_(property_ids),
            RoomVerification.created_at >= today_start,
        )
    )
    today_verifs = verif_q.scalars().all()
    verifications_today = len(today_verifs)
    scores = [float(v.verification_score) for v in today_verifs if v.verification_score is not None]
    avg_score_today = round(sum(scores) / len(scores), 1) if scores else None

    # ── Per-property summaries ────────────────────────────────────────────────
    prop_summaries: List[PropertySummary] = []
    for prop in properties:
        rooms_r = await db.execute(
            select(Room).where(Room.property_id == prop.id, Room.is_active == True)
        )
        prop_rooms = rooms_r.scalars().all()

        occ     = sum(1 for r in prop_rooms if r.occupancy_status == "occupied")
        cleaning = sum(1 for r in prop_rooms if r.room_status in ("cleaning_in_progress", "cleaning_pending"))
        ready    = sum(1 for r in prop_rooms if r.room_status == "ready")

        open_tkt_q = await db.execute(
            select(func.count(Ticket.id)).where(
                Ticket.property_id == prop.id,
                Ticket.status.notin_(["resolved", "closed"]),
            )
        )
        open_tkts = open_tkt_q.scalar() or 0

        tasks_today_q = await db.execute(
            select(func.count(Task.id)).where(
                Task.property_id == prop.id,
                Task.created_at >= today_start,
            )
        )
        tasks_today = tasks_today_q.scalar() or 0

        pv_q = await db.execute(
            select(RoomVerification)
            .join(Task, RoomVerification.task_id == Task.id)
            .where(
                Task.property_id == prop.id,
                RoomVerification.created_at >= today_start,
            )
        )
        pv_list = pv_q.scalars().all()
        pv_scores = [float(v.verification_score) for v in pv_list if v.verification_score is not None]
        last_v_q = await db.execute(
            select(RoomVerification)
            .join(Task, RoomVerification.task_id == Task.id)
            .where(Task.property_id == prop.id)
            .order_by(RoomVerification.created_at.desc())
        )
        last_v = last_v_q.scalars().first()

        prop_summaries.append(PropertySummary(
            property_id=prop.id,
            property_name=prop.name,
            property_type=prop.property_type,
            city=prop.city,
            total_rooms=len(prop_rooms),
            occupied_rooms=occ,
            rooms_being_cleaned=cleaning,
            rooms_ready=ready,
            open_tickets=open_tkts,
            tasks_today=tasks_today,
            verifications_today=len(pv_list),
            avg_verification_score=round(sum(pv_scores) / len(pv_scores), 1) if pv_scores else None,
            last_verification_at=last_v.created_at if last_v else None,
        ))

    # ── Recent verifications (last 20 across all properties) ─────────────────
    recent_v_q = await db.execute(
        select(RoomVerification, Task, Room, Property)
        .join(Task, RoomVerification.task_id == Task.id)
        .join(Room, Task.room_id == Room.id)
        .join(Property, Task.property_id == Property.id)
        .where(Task.property_id.in_(property_ids))
        .order_by(RoomVerification.created_at.desc())
        .limit(20)
    )
    recent_verifs: List[VerificationSummaryItem] = []
    for v, t, r, p in recent_v_q.all():
        defects = v.defects_found or {}
        defect_list = defects.get("defects", defects) if isinstance(defects, dict) else defects
        recent_verifs.append(VerificationSummaryItem(
            verification_id=v.id,
            property_name=p.name,
            room_number=r.room_number,
            task_type=t.task_type,
            score=float(v.verification_score) if v.verification_score is not None else None,
            status=v.status,
            defects_count=len(defect_list) if isinstance(defect_list, list) else 0,
            created_at=v.created_at,
        ))

    return CustomerDashboard(
        customer_id=current_customer.id,
        company_name=current_customer.company_name,
        total_properties=len(properties),
        total_rooms=total_rooms,
        active_tickets=active_tickets,
        verifications_today=verifications_today,
        avg_score_today=avg_score_today,
        properties=prop_summaries,
        recent_verifications=recent_verifs,
    )


@router.get("/properties", response_model=List[dict])
async def list_my_properties(
    db: AsyncSession = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    result = await db.execute(
        select(Property).where(
            Property.customer_id == current_customer.id,
            Property.is_active == True,
        )
    )
    properties = result.scalars().all()
    return [
        {
            "id": str(p.id),
            "name": p.name,
            "property_type": p.property_type,
            "city": p.city,
            "state": p.state,
            "country": p.country,
            "total_rooms": p.total_rooms,
            "subscription_plan": p.subscription_plan,
            "is_active": p.is_active,
        }
        for p in properties
    ]


@router.get("/verifications")
async def list_my_verifications(
    limit: int = Query(50, le=200),
    offset: int = 0,
    status_filter: Optional[str] = Query(None, alias="status"),
    property_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    props_result = await db.execute(
        select(Property.id).where(Property.customer_id == current_customer.id)
    )
    property_ids = [row[0] for row in props_result.all()]
    if not property_ids:
        return []

    q = (
        select(RoomVerification, Task, Room, Property)
        .join(Task, RoomVerification.task_id == Task.id)
        .join(Room, Task.room_id == Room.id)
        .join(Property, Task.property_id == Property.id)
        .where(Task.property_id.in_(property_ids))
    )
    if property_id:
        q = q.where(Task.property_id == property_id)
    if status_filter:
        q = q.where(RoomVerification.status == status_filter)

    q = q.order_by(RoomVerification.created_at.desc()).offset(offset).limit(limit)
    rows = (await db.execute(q)).all()

    return [
        {
            "verification_id": str(v.id),
            "property_id": str(p.id),
            "property_name": p.name,
            "room_number": r.room_number,
            "task_type": t.task_type,
            "score": float(v.verification_score) if v.verification_score is not None else None,
            "cleanliness_score": float(v.cleanliness_score) if v.cleanliness_score else None,
            "organization_score": float(v.organization_score) if v.organization_score else None,
            "status": v.status,
            "queue_status": v.queue_status,
            "defects": v.defects_found,
            "check_results": v.check_results,
            "wesenseu_job_id": v.wesenseu_job_id,
            "created_at": v.created_at.isoformat(),
            "verified_at": v.verified_at.isoformat() if v.verified_at else None,
        }
        for v, t, r, p in rows
    ]


# ── Admin: create / view customers ───────────────────────────────────────────

@router.post("/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    data: CustomerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if current_user.role != "super_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="super_admin only")

    exists = (await db.execute(select(Customer).where(Customer.email == data.email))).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=400, detail="Email already registered")

    customer = Customer(
        **{k: v for k, v in data.model_dump().items() if k != "password"},
        hashed_password=get_password_hash(data.password),
    )
    db.add(customer)
    await db.commit()
    await db.refresh(customer)
    return customer


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    if current_user.role != "super_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="super_admin only")

    customer = await db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer
