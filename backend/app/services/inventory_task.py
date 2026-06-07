"""Deduct inventory when tasks complete per property rules."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory import InventoryItem, InventoryTransaction
from app.models.p2_extensions import TaskInventoryRule
from app.models.task import Task


async def deduct_inventory_for_task(db: AsyncSession, task: Task, performed_by: uuid.UUID | None) -> list[InventoryTransaction]:
    """Apply OUT transactions for active rules; skips if stock insufficient (partial deduct allowed)."""
    rules = (
        await db.execute(
            select(TaskInventoryRule).where(
                TaskInventoryRule.property_id == task.property_id,
                TaskInventoryRule.task_type == task.task_type,
                TaskInventoryRule.is_active == True,
            )
        )
    ).scalars().all()
    if not rules:
        return []

    created: list[InventoryTransaction] = []
    for rule in rules:
        item = (await db.execute(select(InventoryItem).where(InventoryItem.id == rule.inventory_item_id))).scalar_one_or_none()
        if not item or not item.is_active:
            continue
        qty = min(rule.quantity_per_task, item.current_stock)
        if qty <= 0:
            continue
        item.current_stock -= qty
        tx = InventoryTransaction(
            inventory_item_id=item.id,
            transaction_type="OUT",
            quantity=qty,
            reference_type="task",
            reference_id=task.id,
            notes=f"Auto-deduct on task {task.task_type} completion",
            performed_by=performed_by,
        )
        db.add(tx)
        created.append(tx)
    return created
