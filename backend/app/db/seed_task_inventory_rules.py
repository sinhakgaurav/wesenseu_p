"""Default task → inventory deduction rules per property (cleaning)."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory import InventoryItem
from app.models.property import Property
from app.models.p2_extensions import TaskInventoryRule

# task_type -> list of (item_name_substring, qty_per_task)
CLEANING_RULES: list[tuple[str, int]] = [
    ("Bath Towel", 2),
    ("Hand Towel", 2),
    ("Soap", 1),
    ("Shampoo", 1),
    ("Toilet Paper", 1),
]


async def seed_task_inventory_rules(db: AsyncSession) -> int:
    """Idempotent: ensure cleaning rules exist for each active property."""
    props = (await db.execute(select(Property).where(Property.is_active == True))).scalars().all()
    created = 0
    for prop in props:
        items = (
            await db.execute(
                select(InventoryItem).where(
                    InventoryItem.property_id == prop.id,
                    InventoryItem.is_active == True,
                )
            )
        ).scalars().all()
        if not items:
            continue
        for substr, qty in CLEANING_RULES:
            match = next((i for i in items if substr.lower() in i.item_name.lower()), None)
            if not match:
                continue
            existing = (
                await db.execute(
                    select(TaskInventoryRule).where(
                        TaskInventoryRule.property_id == prop.id,
                        TaskInventoryRule.task_type == "cleaning",
                        TaskInventoryRule.inventory_item_id == match.id,
                    )
                )
            ).scalar_one_or_none()
            if existing:
                continue
            db.add(
                TaskInventoryRule(
                    property_id=prop.id,
                    task_type="cleaning",
                    inventory_item_id=match.id,
                    quantity_per_task=qty,
                    is_active=True,
                )
            )
            created += 1
    if created:
        await db.commit()
    return created


if __name__ == "__main__":
    import asyncio
    from app.db.base import AsyncSessionLocal

    async def _main():
        async with AsyncSessionLocal() as db:
            n = await seed_task_inventory_rules(db)
            print(f"Seeded {n} task inventory rule(s)")

    asyncio.run(_main())
