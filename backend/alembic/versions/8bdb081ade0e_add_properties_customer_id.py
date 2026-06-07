"""add_properties_customer_id

Revision ID: 8bdb081ade0e
Revises: 80e9a7f06daf
Create Date: 2026-05-14 19:42:07.426374

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = '8bdb081ade0e'
down_revision: Union[str, None] = '80e9a7f06daf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if not insp.has_table("properties"):
        return
    cols = {c["name"] for c in insp.get_columns("properties")}
    if "customer_id" in cols:
        return
    op.add_column(
        "properties",
        sa.Column("customer_id", UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_properties_customer_id_customers",
        "properties",
        "customers",
        ["customer_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_properties_customer_id_customers", "properties", type_="foreignkey")
    op.drop_column("properties", "customer_id")
