"""Force idempotent demo data for dashboards, all sidebar modules, CMS, and multi-property."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from sqlalchemy import select

from app.db.base import AsyncSessionLocal
from app.models.customer import Customer
from app.models.employee import Employee
from app.models.notification import Notification
from app.models.page import Page
from app.models.property import Property
from app.models.property_approval import PropertyApproval

MARKER = "MONITOUR_ALL_DEMO_V2"


async def seed_all_demo() -> int:
    """Returns number of actions performed."""
    from app.db.seed_comprehensive import run_comprehensive_seed, MARKER_TITLE

    actions = 0
    async with AsyncSessionLocal() as db:
        prop = (
            await db.execute(
                select(Property).where(Property.email == "admin@grandpalace.com").limit(1)
            )
        ).scalar_one_or_none()
        if not prop:
            prop = (
                await db.execute(select(Property).where(Property.is_active == True).limit(1))
            ).scalar_one_or_none()
        if not prop:
            print("[seed_all_demo] No property found; run init_db first.")
            return 0

        # Ensure super_admin has property context
        sa = (
            await db.execute(select(Employee).where(Employee.email == "admin@monitour.in"))
        ).scalar_one_or_none()
        if sa and not sa.property_id:
            sa.property_id = prop.id
            actions += 1

        # Second demo property for multi-property views
        prop2 = (
            await db.execute(select(Property).where(Property.name == "Seaside Resort Goa"))
        ).scalar_one_or_none()
        customer = (
            await db.execute(select(Customer).where(Customer.email == "customer@grandpalace.com"))
        ).scalar_one_or_none()
        if not prop2:
            prop2 = Property(
                id=uuid.uuid4(),
                name="Seaside Resort Goa",
                property_type="Resort",
                address="Calangute Beach Road",
                city="Goa",
                state="Goa",
                country="India",
                phone="+91-832-5550100",
                email="goa@monitour.demo",
                total_rooms=24,
                subscription_plan="growth",
                subscription_status="active",
                is_active=True,
                customer_id=customer.id if customer else None,
            )
            db.add(prop2)
            await db.flush()
            db.add(
                PropertyApproval(
                    property_id=prop2.id,
                    status="approved",
                    requested_plan="growth",
                    reviewed_at=datetime.utcnow(),
                )
            )
            actions += 1

        # Platform notification for super_admin
        if sa:
            exists_n = (
                await db.execute(
                    select(Notification.id).where(
                        Notification.user_id == sa.id,
                        Notification.title == MARKER,
                    )
                )
            ).scalar_one_or_none()
            if not exists_n:
                for title, msg in [
                    (MARKER, "Full demo dataset is active for Grand Palace Hotel."),
                    ("Pending property review", "Check Admin Panel → Businesses for approvals."),
                    ("Inventory alert", "Low stock on bath towels — review Inventory."),
                ]:
                    db.add(
                        Notification(
                            property_id=prop.id,
                            user_id=sa.id,
                            notification_type="system",
                            title=title,
                            message=msg,
                            is_read=False,
                        )
                    )
                actions += 1

        # CMS pages for public site
        cms_pages = [
            ("about", "About Monitour", "about", "About Monitour", "Hospitality operations platform"),
            ("contact", "Contact Us", "contact", "Get in touch", "We respond within 24 hours"),
            ("pricing", "Pricing", "pricing", "Plans & pricing", "Choose the right plan"),
        ]
        for slug, title, ptype, hero, sub in cms_pages:
            exists_p = (
                await db.execute(select(Page.id).where(Page.slug == slug))
            ).scalar_one_or_none()
            if not exists_p:
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
                actions += 1

        await db.commit()

    from sqlalchemy import func
    from app.models.room import Room

    async with AsyncSessionLocal() as db:
        prop = (
            await db.execute(select(Property).where(Property.is_active == True).limit(1))
        ).scalar_one_or_none()
        room_n = 0
        if prop:
            room_n = (
                await db.execute(select(func.count(Room.id)).where(Room.property_id == prop.id))
            ).scalar() or 0
        has_comp = (
            await db.execute(select(Notification.id).where(Notification.title == MARKER_TITLE))
        ).scalar_one_or_none()
    if not has_comp or room_n < 8:
        if has_comp and room_n < 8:
            from sqlalchemy import delete
            async with AsyncSessionLocal() as db:
                await db.execute(delete(Notification).where(Notification.title == MARKER_TITLE))
                await db.commit()
        await run_comprehensive_seed()
        actions += 1
        print("[seed_all_demo] Ran comprehensive operational seed.")

    from app.db.seed_p2_sample import seed_p2_sample
    from app.db.seed_catalog import seed_catalog_items

    async with AsyncSessionLocal() as db:
        n_cat = await seed_catalog_items(db)
        n_p2 = await seed_p2_sample(db)
        if n_cat or n_p2:
            actions += (n_cat or 0) + (n_p2 or 0)

    print(f"[seed_all_demo] Completed ({actions} actions).")
    return actions


if __name__ == "__main__":
    import asyncio
    asyncio.run(seed_all_demo())
