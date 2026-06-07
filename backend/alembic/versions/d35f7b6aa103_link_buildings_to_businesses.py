"""link buildings to businesses

Revision ID: d35f7b6aa103
Revises: c9e2b4f7a613
Create Date: 2026-06-05 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "d35f7b6aa103"
down_revision: Union[str, None] = "c9e2b4f7a613"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("buildings", sa.Column("business_id", sa.Uuid(), nullable=True))
    op.create_unique_constraint(
        "uq_buildings_business_id", "buildings", ["business_id"]
    )
    op.create_foreign_key(
        "fk_buildings_business_id",
        "buildings",
        "businesses",
        ["business_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_buildings_business_id", "buildings", type_="foreignkey")
    op.drop_constraint("uq_buildings_business_id", "buildings", type_="unique")
    op.drop_column("buildings", "business_id")
