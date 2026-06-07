"""Seed global catalog picklists (idempotent)."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalog import CatalogItem, CATALOG_KINDS

DEFAULT_CATALOG: dict[str, list[tuple[str, str]]] = {
    "amenity": [
        ("wifi", "Wi-Fi"),
        ("ac", "Air conditioning"),
        ("tv", "Television"),
        ("minibar", "Minibar"),
        ("safe", "In-room safe"),
        ("kettle", "Electric kettle"),
    ],
    "property_feature": [
        ("inhouse_kitchen", "In-house kitchen"),
        ("restaurant", "Restaurant"),
        ("star_3", "3 Star"),
        ("star_4", "4 Star"),
        ("star_5", "5 Star"),
        ("pool", "Swimming pool"),
        ("spa", "Spa"),
        ("parking", "Parking"),
    ],
    "room_view": [
        ("standard", "Standard view"),
        ("city", "City view"),
        ("pool", "Pool view"),
        ("sea", "Sea / beach view"),
        ("garden", "Garden view"),
    ],
    "department_duty": [
        ("bedsheet_change", "Bedsheet change"),
        ("towel_change", "Towel change"),
        ("bathroom_clean", "Bathroom cleaning"),
        ("minibar_restock", "Minibar restock"),
        ("floor_clean", "Floor cleaning"),
    ],
    "dish": [
        ("veg_biryani", "Vegetable biryani"),
        ("chicken_curry", "Chicken curry"),
        ("dal_tadka", "Dal tadka"),
        ("masala_dosa", "Masala dosa"),
        ("paneer_tikka", "Paneer tikka"),
    ],
}


async def seed_catalog_items(db: AsyncSession) -> int:
    created = 0
    for kind in CATALOG_KINDS:
        for code, display_name in DEFAULT_CATALOG.get(kind, []):
            exists = (
                await db.execute(
                    select(CatalogItem.id).where(CatalogItem.kind == kind, CatalogItem.code == code)
                )
            ).scalar_one_or_none()
            if exists:
                continue
            db.add(
                CatalogItem(
                    kind=kind,
                    code=code,
                    display_name=display_name,
                    is_system=True,
                    is_active=True,
                )
            )
            created += 1
    if created:
        await db.commit()
    return created
