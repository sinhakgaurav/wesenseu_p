"""Idempotent P2 sample data: vendors, F&B, contacts, schedules, dept duties, onboarding session."""
import uuid
from datetime import time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.property import Property
from app.models.customer import Customer
from app.models.department import Department
from app.models.catalog import CatalogItem
from app.models.contact import PropertyContact, CustomerContact
from app.models.onboarding import OnboardingSession
from app.models.inventory import Vendor
from app.models.p2_extensions import (
    PropertyOutlet,
    PropertyMenuItem,
    PropertySchedule,
    DepartmentCatalogDuty,
)

MARKER = "p2_sample_v1"


async def seed_p2_sample(db: AsyncSession) -> int:
    """Returns count of new rows created."""
    prop = (
        await db.execute(
            select(Property).where(Property.email == "admin@grandpalace.com").limit(1)
        )
    ).scalar_one_or_none()
    if not prop:
        return 0

    customer = None
    if prop.customer_id:
        customer = await db.get(Customer, prop.customer_id)

    created = 0

    # Property contacts
    if not (
        await db.execute(
            select(PropertyContact).where(
                PropertyContact.property_id == prop.id,
                PropertyContact.label == MARKER,
            )
        )
    ).scalar_one_or_none():
        db.add(
            PropertyContact(
                property_id=prop.id,
                contact_type="phone",
                value="+91-80-55551234",
                label=MARKER,
                is_primary=False,
            )
        )
        db.add(
            PropertyContact(
                property_id=prop.id,
                contact_type="email",
                value="frontdesk@grandpalace.com",
                label=f"{MARKER}_email",
                is_primary=True,
            )
        )
        created += 2

    if customer and not (
        await db.execute(
            select(CustomerContact).where(
                CustomerContact.customer_id == customer.id,
                CustomerContact.label == MARKER,
            )
        )
    ).scalar_one_or_none():
        db.add(
            CustomerContact(
                customer_id=customer.id,
                contact_type="email",
                value="owner@grandpalace.com",
                label=MARKER,
                is_primary=True,
            )
        )
        created += 1

    # Vendors
    vendor_names = [
        ("Linen Supply Co", "+91-9000000001"),
        ("Amenities Wholesale", "+91-9000000002"),
    ]
    for name, phone in vendor_names:
        exists = (
            await db.execute(
                select(Vendor).where(Vendor.property_id == prop.id, Vendor.name == name)
            )
        ).scalar_one_or_none()
        if not exists:
            db.add(
                Vendor(
                    property_id=prop.id,
                    name=name,
                    contact_person="Sales Desk",
                    phone=phone,
                    email=f"{name.lower().replace(' ', '.')}@example.com",
                )
            )
            created += 1

    # F&B outlet + menu
    outlet = (
        await db.execute(
            select(PropertyOutlet).where(
                PropertyOutlet.property_id == prop.id,
                PropertyOutlet.name == "Grand Palace Restaurant",
            )
        )
    ).scalar_one_or_none()
    if not outlet:
        outlet = PropertyOutlet(
            property_id=prop.id,
            name="Grand Palace Restaurant",
            outlet_type="restaurant",
        )
        db.add(outlet)
        await db.flush()
        created += 1

    menu_items = [
        ("Masala Dosa", 180),
        ("Filter Coffee", 80),
        ("Continental Breakfast", 450),
    ]
    for mname, price in menu_items:
        exists = (
            await db.execute(
                select(PropertyMenuItem).where(
                    PropertyMenuItem.outlet_id == outlet.id,
                    PropertyMenuItem.name == mname,
                )
            )
        ).scalar_one_or_none()
        if not exists:
            db.add(PropertyMenuItem(outlet_id=outlet.id, name=mname, price=price))
            created += 1

    # Property schedules (Mon–Sun 6:00–23:00)
    sched_count = (
        await db.execute(
            select(PropertySchedule).where(PropertySchedule.property_id == prop.id).limit(1)
        )
    ).scalar_one_or_none()
    if not sched_count:
        for dow in range(7):
            db.add(
                PropertySchedule(
                    property_id=prop.id,
                    day_of_week=dow,
                    open_time=time(6, 0),
                    close_time=time(23, 0),
                    is_closed=False,
                )
            )
        created += 7

    # Department duties (Housekeeping)
    hk = (
        await db.execute(
            select(Department).where(
                Department.property_id == prop.id,
                Department.name == "Housekeeping",
            )
        )
    ).scalar_one_or_none()
    if hk:
        duty = (
            await db.execute(
                select(CatalogItem).where(
                    CatalogItem.kind == "department_duty",
                    CatalogItem.is_active == True,
                ).limit(1)
            )
        ).scalar_one_or_none()
        if duty:
            link = (
                await db.execute(
                    select(DepartmentCatalogDuty).where(
                        DepartmentCatalogDuty.department_id == hk.id,
                        DepartmentCatalogDuty.catalog_item_id == duty.id,
                    )
                )
            ).scalar_one_or_none()
            if not link:
                db.add(
                    DepartmentCatalogDuty(department_id=hk.id, catalog_item_id=duty.id)
                )
                created += 1

    # Sample onboarding session
    if customer:
        sess = (
            await db.execute(
                select(OnboardingSession).where(
                    OnboardingSession.property_id == prop.id,
                    OnboardingSession.status == "in_progress",
                ).limit(1)
            )
        ).scalar_one_or_none()
        if not sess:
            db.add(
                OnboardingSession(
                    customer_id=customer.id,
                    property_id=prop.id,
                    current_step="inventory",
                    step_index=6,
                    status="in_progress",
                    payload={"seed_marker": MARKER, "property_name": prop.name},
                )
            )
            created += 1

    if created:
        await db.commit()
    return created
