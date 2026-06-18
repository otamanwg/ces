"""add city economy snapshots

Revision ID: f8b7c6d5e4a3
Revises: 9c1b2a3d4e5f
Create Date: 2026-06-16 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f8b7c6d5e4a3"
down_revision: str | None = "9c1b2a3d4e5f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "city_economy_snapshots",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("city_id", sa.Uuid(), nullable=False),
        sa.Column("game_day", sa.Integer(), nullable=False),
        sa.Column("active_money_supply", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("previous_active_money_supply", sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column("target_growth_rate", sa.Numeric(precision=6, scale=4), nullable=False),
        sa.Column("money_growth_rate", sa.Numeric(precision=8, scale=4), nullable=False),
        sa.Column("inflation_rate", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["city_id"], ["cities.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("city_id", "game_day", name="uq_city_economy_snapshots_city_day"),
    )
    op.create_index(
        "ix_city_economy_snapshots_city_day",
        "city_economy_snapshots",
        ["city_id", "game_day"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_city_economy_snapshots_city_day", table_name="city_economy_snapshots")
    op.drop_table("city_economy_snapshots")
