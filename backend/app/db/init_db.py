"""Seed initial data for Monitour."""
import asyncio
import os
import subprocess
import sys
import uuid
from datetime import datetime, date
from urllib.parse import quote

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.base import AsyncSessionLocal, engine, Base
from app.models.property import Property
from app.models.customer import Customer
from app.models.property_group import PropertyGroup
from app.models.property_room_category import PropertyRoomCategory
from app.models.benchmark import RoomCategoryBenchmark
from app.models.employee import Employee
from app.models.department import Department
from app.models.room import Room
from app.models.inventory import InventoryItem
from app.models.plan import Plan
from app.models.page import Page
from app.models.task_sla import TaskSlaPolicy
from app.core.security import get_password_hash


DEFAULT_PLANS = [
    {
        "name": "Starter", "slug": "starter", "display_order": 1,
        "tagline": "Perfect for small properties", "cta_text": "Start Free",
        "price_monthly": 4000.0, "price_yearly": 40000.0, "currency": "INR",
        "room_limit": 10, "employee_limit": 15, "is_popular": False,
        "is_active": True,
        "features": [
            "Up to 10 rooms", "15 staff accounts",
            "Task management", "Ticketing system",
            "Guest portal (QR-based feedback)", "Basic reports",
            "Email notifications",
        ],
        "module_defaults": {
            "rooms": True, "tasks": True, "tickets": True,
            "inventory": False, "surveillance": False, "verification": False,
        },
    },
    {
        "name": "Growth", "slug": "growth", "display_order": 2,
        "tagline": "For growing hospitality businesses", "cta_text": "Get Growth",
        "price_monthly": 11999.0, "price_yearly": 119990.0, "currency": "INR",
        "room_limit": 30, "employee_limit": 50, "is_popular": True,
        "is_active": True,
        "features": [
            "Up to 30 rooms", "50 staff accounts", "All Starter features",
            "AI room verification (WesenseU)", "CCTV surveillance + alerts",
            "Benchmark image management", "Inventory & orders",
            "Attendance tracking", "Advanced analytics",
        ],
        "module_defaults": {
            "rooms": True, "tasks": True, "tickets": True,
            "inventory": True, "surveillance": True, "verification": True,
            "orders": True, "attendance": True,
        },
    },
    {
        "name": "Enterprise", "slug": "enterprise", "display_order": 3,
        "tagline": "Full-scale operations management", "cta_text": "Contact Sales",
        "price_monthly": 20000.0, "price_yearly": 200000.0, "currency": "INR",
        "room_limit": 50, "employee_limit": None, "is_popular": False,
        "is_active": True,
        "features": [
            "Up to 50 rooms", "Unlimited staff accounts",
            "All Growth features", "Multi-property dashboard",
            "AI support chat for customers", "Custom integrations",
            "Priority support", "White-label option",
        ],
        "module_defaults": {
            "rooms": True, "tasks": True, "tickets": True,
            "inventory": True, "surveillance": True, "verification": True,
            "orders": True, "attendance": True,
            "support_chat": True, "reports": True,
        },
    },
    {
        "name": "Custom", "slug": "custom", "display_order": 4,
        "tagline": "Enterprise-scale & IoT ready", "cta_text": "Talk to Us",
        "price_monthly": None, "price_yearly": None, "currency": "INR",
        "room_limit": None, "employee_limit": None, "is_popular": False,
        "is_active": True,
        "features": [
            "Unlimited rooms & staff", "IoT / Smart Lock integration",
            "Predictive AI analytics", "Custom white-labeling",
            "Dedicated infrastructure", "SLA-backed support",
        ],
        "module_defaults": {},
    },
]


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def _run_alembic_upgrade() -> None:
    """Apply additive migrations after create_all (idempotent migrations; no-op when already aligned)."""
    backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    print("Running database migrations (alembic upgrade head)...")
    r = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=backend_root,
        env=os.environ.copy(),
    )
    if r.returncode != 0:
        raise SystemExit(f"alembic upgrade head failed with exit code {r.returncode}")
    print("  [OK] Alembic upgrade head completed.")


async def seed_plans(db: AsyncSession) -> int:
    """Insert default plans if they don't exist yet. Returns count created."""
    created = 0
    for p_data in DEFAULT_PLANS:
        existing = (
            await db.execute(select(Plan).where(Plan.slug == p_data["slug"]))
        ).scalar_one_or_none()
        if not existing:
            db.add(Plan(**p_data))
            created += 1
    if created:
        await db.commit()
        print(f"  [OK] Seeded {created} subscription plan(s).")
    return created


async def auto_seed_plans():
    """Called on every startup — idempotent plan seeding."""
    async with AsyncSessionLocal() as db:
        await seed_plans(db)


async def ensure_cms_pages() -> int:
    """Idempotent CMS pages for public site and diagnostics (about, contact, pricing)."""
    cms_pages = [
        ("about", "About Monitour", "about", "About Monitour", "Hospitality operations platform"),
        ("contact", "Contact Us", "contact", "Get in touch", "We respond within 24 hours"),
        ("pricing", "Pricing", "pricing", "Plans & pricing", "Choose the right plan"),
    ]
    created = 0
    async with AsyncSessionLocal() as db:
        for slug, title, ptype, hero, sub in cms_pages:
            exists = (await db.execute(select(Page.id).where(Page.slug == slug))).scalar_one_or_none()
            if exists:
                continue
            db.add(
                Page(
                    slug=slug,
                    title=title,
                    page_type=ptype,
                    hero_heading=hero,
                    hero_subheading=sub,
                    content_blocks=[
                        {
                            "type": "html",
                            "data": {
                                "body": f"<p>Demo content for <strong>{title}</strong>. Edit in Super Admin → CMS.</p>",
                            },
                        }
                    ],
                    is_published=True,
                    published_at=datetime.utcnow(),
                )
            )
            created += 1
        if created:
            await db.commit()
            print(f"  [OK] Seeded {created} CMS page(s).")
    return created


async def ensure_demo_users():
    """Ensure local demo login users exist and have the documented passwords."""
    async with AsyncSessionLocal() as db:
        prop = (
            await db.execute(select(Property).where(Property.email == "admin@grandpalace.com"))
        ).scalar_one_or_none()
        if not prop:
            prop = Property(
                id=uuid.uuid4(),
                name="Grand Palace Hotel",
                property_type="Hotel",
                address="123 MG Road",
                city="Bengaluru",
                state="Karnataka",
                country="India",
                phone="+91-80-12345678",
                email="admin@grandpalace.com",
                total_rooms=50,
                subscription_plan="enterprise",
            )
            db.add(prop)
            await db.flush()

        departments_data = [
            ("Housekeeping", "Room cleaning and maintenance"),
            ("Reception", "Front desk and guest services"),
            ("Maintenance", "Property maintenance and repairs"),
            ("Security", "Property security"),
        ]
        departments = {}
        for name, desc in departments_data:
            dept = (
                await db.execute(
                    select(Department).where(
                        Department.property_id == prop.id,
                        Department.name == name,
                    )
                )
            ).scalar_one_or_none()
            if not dept:
                dept = Department(
                    id=uuid.uuid4(),
                    property_id=prop.id,
                    name=name,
                    description=desc,
                )
                db.add(dept)
                await db.flush()
            departments[name] = dept

        demo_users = [
            {
                "email": "admin@monitour.in",
                "password": "Admin@2026",
                "employee_code": "EMP00001",
                "full_name": "Admin User",
                "role": "super_admin",
                "department": "Reception",
                "phone": "+91-9876543210",
                "shift_type": "morning",
                "salary": 100000,
            },
            {
                "email": "manager@grandpalace.com",
                "password": "Manager@123",
                "employee_code": "EMP00002",
                "full_name": "Rajesh Kumar",
                "role": "property_manager",
                "department": "Housekeeping",
                "phone": "+91-9876543211",
                "shift_type": "morning",
                "salary": 60000,
            },
            {
                "email": "hk_head@grandpalace.com",
                "password": "DeptHead@123",
                "employee_code": "EMP00003",
                "full_name": "Housekeeping Head",
                "role": "dept_manager",
                "department": "Housekeeping",
                "phone": "+91-9555555555",
                "shift_type": "morning",
                "salary": 45000,
            },
            {
                "email": "priya@grandpalace.com",
                "password": "Password@123",
                "employee_code": "EMP00004",
                "full_name": "Priya Sharma",
                "role": "employee",
                "department": "Housekeeping",
                "phone": "+91-9111111111",
                "shift_type": "morning",
                "salary": 25000,
            },
        ]

        for data in demo_users:
            dept = departments[data["department"]]
            employee = (
                await db.execute(select(Employee).where(Employee.email == data["email"]))
            ).scalar_one_or_none()
            fields = {
                "property_id": prop.id,
                "department_id": dept.id,
                "employee_code": data["employee_code"],
                "full_name": data["full_name"],
                "role": data["role"],
                "phone": data["phone"],
                "hashed_password": get_password_hash(data["password"]),
                "shift_type": data["shift_type"],
                "joining_date": date(2024, 1, 1),
                "salary": data["salary"],
                "status": "active",
            }
            if employee:
                for key, value in fields.items():
                    setattr(employee, key, value)
            else:
                db.add(Employee(id=uuid.uuid4(), email=data["email"], **fields))

        await db.commit()
        print("  [OK] Demo login users are ready.")

        # Default task SLA policies (idempotent)
        sla_exists = (
            await db.execute(select(TaskSlaPolicy).where(TaskSlaPolicy.property_id == prop.id).limit(1))
        ).scalar_one_or_none()
        if not sla_exists:
            db.add(
                TaskSlaPolicy(
                    property_id=prop.id,
                    task_type="cleaning",
                    service_type="*",
                    sla_minutes=120,
                    root_cause_category="capacity_or_priority_mismatch",
                )
            )
            db.add(
                TaskSlaPolicy(
                    property_id=prop.id,
                    task_type="cleaning",
                    service_type="housekeeping",
                    sla_minutes=90,
                    root_cause_category="hk_staffing_or_floor_load",
                )
            )
            db.add(
                TaskSlaPolicy(
                    property_id=prop.id,
                    task_type="laundry",
                    service_type="*",
                    sla_minutes=240,
                    root_cause_category="laundry_vendor_or_machine_capacity",
                )
            )
            await db.commit()
            print("  [OK] Default task SLA policies seeded.")


async def seed_data():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Property).limit(1))
        if result.scalar_one_or_none():
            print("Database already seeded.")
            return

        customer_portal_user = Customer(
            id=uuid.uuid4(),
            company_name="Grand Palace Holdings",
            contact_name="Portfolio Owner",
            email="customer@grandpalace.com",
            hashed_password=get_password_hash("Customer@123"),
            phone="+91-80-11110000",
            subscription_plan="enterprise",
        )
        db.add(customer_portal_user)
        await db.flush()

        portfolio_group = PropertyGroup(
            id=uuid.uuid4(),
            customer_id=customer_portal_user.id,
            name="Grand Palace Portfolio",
            description="Demo B2B owner portfolio (groups properties under one customer).",
        )
        db.add(portfolio_group)
        await db.flush()

        prop = Property(
            id=uuid.uuid4(),
            customer_id=customer_portal_user.id,
            property_group_id=portfolio_group.id,
            name="Grand Palace Hotel",
            property_type="Hotel",
            address="123 MG Road",
            city="Bengaluru",
            state="Karnataka",
            country="India",
            phone="+91-80-12345678",
            email="admin@grandpalace.com",
            total_rooms=50,
            subscription_plan="enterprise",
        )
        db.add(prop)
        await db.flush()

        departments_data = [
            ("Housekeeping", "Room cleaning and maintenance"),
            ("Reception", "Front desk and guest services"),
            ("Maintenance", "Property maintenance and repairs"),
            ("Security", "Property security"),
            ("Kitchen", "Food and beverage"),
            ("Laundry", "Laundry services"),
        ]
        departments = []
        for name, desc in departments_data:
            dept = Department(
                id=uuid.uuid4(),
                property_id=prop.id,
                name=name,
                description=desc,
            )
            db.add(dept)
            departments.append(dept)
        await db.flush()

        super_admin = Employee(
            id=uuid.uuid4(),
            property_id=prop.id,
            department_id=departments[1].id,
            employee_code="EMP00001",
            full_name="Admin User",
            role="super_admin",
            phone="+91-9876543210",
            email="admin@monitour.in",
            hashed_password=get_password_hash("Admin@2026"),
            shift_type="morning",
            joining_date=date(2024, 1, 1),
            salary=100000,
            status="active",
        )
        db.add(super_admin)

        manager = Employee(
            id=uuid.uuid4(),
            property_id=prop.id,
            department_id=departments[0].id,
            employee_code="EMP00002",
            full_name="Rajesh Kumar",
            role="property_manager",
            phone="+91-9876543211",
            email="manager@grandpalace.com",
            hashed_password=get_password_hash("Manager@123"),
            shift_type="morning",
            joining_date=date(2024, 2, 1),
            salary=60000,
            status="active",
        )
        db.add(manager)
        await db.flush()

        emp_data = [
            ("Priya Sharma", "employee", departments[0].id, "+91-9111111111", "priya@grandpalace.com", "morning"),
            ("Arjun Nair", "employee", departments[0].id, "+91-9222222222", "arjun@grandpalace.com", "afternoon"),
            ("Sunita Devi", "employee", departments[2].id, "+91-9333333333", "sunita@grandpalace.com", "morning"),
            ("Mohan Singh", "employee", departments[3].id, "+91-9444444444", "mohan@grandpalace.com", "night"),
            ("Anita Rao", "dept_manager", departments[0].id, "+91-9555555555", "anita@grandpalace.com", "morning"),
        ]
        for i, (name, role, dept_id, phone, email, shift) in enumerate(emp_data, 3):
            emp = Employee(
                id=uuid.uuid4(),
                property_id=prop.id,
                department_id=dept_id,
                employee_code=f"EMP{str(i + 2).zfill(5)}",
                full_name=name,
                role=role,
                phone=phone,
                email=email,
                hashed_password=get_password_hash("Password@123"),
                shift_type=shift,
                joining_date=date(2024, 3, 1),
                salary=25000,
                status="active",
            )
            db.add(emp)

        cat_specs = [
            ("deluxe", "Deluxe", "Upscale rooms", 0),
            ("standard", "Standard", "Standard rooms", 1),
            ("suite", "Suite", "Suites", 2),
            ("executive", "Executive", "Executive floor", 3),
            ("classic_room", "Classic Room", "Classic layout (multi-aspect benchmarks)", 4),
        ]
        cat_rows = []
        for code, display_name, desc, sort_order in cat_specs:
            rc = PropertyRoomCategory(
                id=uuid.uuid4(),
                property_id=prop.id,
                code=code,
                display_name=display_name,
                description=desc,
                sort_order=sort_order,
            )
            db.add(rc)
            cat_rows.append(rc)
        await db.flush()

        def _bench_url(label: str) -> str:
            return "https://placehold.co/1400x900/e8e8e8/333333/png?text=" + quote(label, safe="")

        classic_aspects = ["general", "washroom", "bed", "sidetable", "ac", "floor"]
        default_aspects = ["general", "bathroom", "bed", "floor"]
        for cat in cat_rows:
            aspects = classic_aspects if cat.code == "classic_room" else default_aspects
            for asp in aspects:
                db.add(
                    RoomCategoryBenchmark(
                        id=uuid.uuid4(),
                        property_id=prop.id,
                        property_room_category_id=cat.id,
                        room_category=cat.display_name,
                        aspect=asp,
                        image_url=_bench_url(f"{cat.code}-{asp}"),
                        created_by=manager.id,
                    )
                )

        for i in range(1, 21):
            floor = (i - 1) // 5 + 1
            cat = cat_rows[(i - 1) % len(cat_rows)]
            room = Room(
                id=uuid.uuid4(),
                property_id=prop.id,
                room_number=str(100 + i),
                room_category=cat.display_name,
                property_room_category_id=cat.id,
                floor_number=floor,
                room_status="vacant" if i % 3 != 0 else "occupied",
                occupancy_status="occupied" if i % 3 == 0 else "vacant",
            )
            db.add(room)

        inventory_data = [
            ("Bath Towels", "Towels", "piece", 100, 20, 150),
            ("Hand Towels", "Towels", "piece", 150, 30, 80),
            ("Soap", "Toiletries", "piece", 200, 50, 15),
            ("Shampoo", "Toiletries", "bottle", 150, 40, 25),
            ("Conditioner", "Toiletries", "bottle", 100, 30, 30),
            ("Toothpaste", "Toiletries", "piece", 120, 40, 20),
            ("Toilet Paper", "Cleaning", "roll", 300, 100, 10),
            ("Bedsheets", "Bedsheets", "set", 80, 20, 500),
            ("Pillowcases", "Bedsheets", "piece", 100, 30, 120),
            ("Cleaning Spray", "Cleaning", "bottle", 50, 15, 200),
            ("Water Bottles", "Guest Consumables", "piece", 500, 100, 20),
            ("Tea Bags", "Guest Consumables", "box", 100, 30, 50),
        ]
        for item_name, category, unit, stock, min_stock, cost in inventory_data:
            item = InventoryItem(
                id=uuid.uuid4(),
                property_id=prop.id,
                item_name=item_name,
                category=category,
                unit=unit,
                current_stock=stock,
                minimum_stock=min_stock,
                unit_cost=cost,
            )
            db.add(item)

        await db.commit()
        print("Database seeded successfully!")
        print("\n=== Login Credentials ===")
        print("Super Admin:      admin@monitour.in / Admin@2026")
        print("Property Manager: manager@grandpalace.com / Manager@123")
        print("Dept Manager:     hk_head@grandpalace.com / DeptHead@123")
        print("Employee:         priya@grandpalace.com / Password@123")
        print("Customer (B2B):   customer@grandpalace.com / Customer@123")

        # Always seed plans (idempotent)
        await seed_plans(db)

        from app.db.seed_task_inventory_rules import seed_task_inventory_rules

        n_rules = await seed_task_inventory_rules(db)
        if n_rules:
            print(f"  [OK] Seeded {n_rules} task inventory rule(s).")


async def main():
    await create_tables()
    _run_alembic_upgrade()
    from app.db.seed_catalog import seed_catalog_items

    async with AsyncSessionLocal() as db:
        n = await seed_catalog_items(db)
        if n:
            print(f"  [OK] Seeded {n} catalog item(s).")
    await seed_data()
    await ensure_demo_users()
    from app.db.seed_comprehensive import run_comprehensive_seed

    await run_comprehensive_seed()
    from app.db.seed_p2_sample import seed_p2_sample

    async with AsyncSessionLocal() as db:
        n_p2 = await seed_p2_sample(db)
        if n_p2:
            print(f"  [OK] Seeded {n_p2} P2 sample row(s).")

    from app.db.seed_all_demo import seed_all_demo

    n_demo = await seed_all_demo()
    if n_demo:
        print(f"  [OK] All-demo seed: {n_demo} action(s).")
    from app.db.seed_task_inventory_rules import seed_task_inventory_rules

    async with AsyncSessionLocal() as db:
        n_rules = await seed_task_inventory_rules(db)
        if n_rules:
            print(f"  [OK] Seeded {n_rules} task inventory rule(s).")
    # Ensure plans exist even if seed_data was skipped (already seeded)
    async with AsyncSessionLocal() as db:
        await seed_plans(db)
    await ensure_cms_pages()


if __name__ == "__main__":
    asyncio.run(main())
