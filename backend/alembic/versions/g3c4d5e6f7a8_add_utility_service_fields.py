"""add utility service fields and emergency contracts

Phase G3: Utility services (power/water/waste) as businesses with capacity,
load, and emergency contracts for bankruptcy fallback.

Revision ID: g3c4d5e6f7a8
Revises: g2b3c4d5e6f7
Create Date: 2026-06-21 14:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "g3c4d5e6f7a8"
down_revision: str | None = "g2b3c4d5e6f7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Utility-поля на Business: тип сервісу, потужність, навантаження.
    op.add_column(
        "businesses",
        sa.Column("utility_service_type", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "businesses",
        sa.Column("service_capacity", sa.Numeric(15, 2), nullable=False, server_default="0"),
    )
    op.add_column(
        "businesses",
        sa.Column("service_load", sa.Numeric(15, 2), nullable=False, server_default="0"),
    )
    op.add_column(
        "businesses",
        sa.Column("is_emergency_contract", sa.Boolean(), nullable=False, server_default="false"),
    )

    # Таблиця контрактів з сусіднім містом (emergency fallback).
    op.create_table(
        "utility_emergency_contracts",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("city_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("utility_service_type", sa.String(length=20), nullable=False),
        sa.Column("provider_name", sa.String(length=100), nullable=False),
        sa.Column("price_per_unit", sa.Numeric(15, 2), nullable=False),
        sa.Column("normal_price_per_unit", sa.Numeric(15, 2), nullable=False),
        sa.Column("started_at_game_day", sa.Integer(), nullable=False),
        sa.Column("ended_at_game_day", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["city_id"], ["cities.id"], ondelete="CASCADE"),
    )

    # Позначаємо існуючі муніципальні бізнеси як utility-служби.
    op.execute(
        """
        UPDATE businesses
        SET utility_service_type = 'water',
            service_capacity = 100,
            service_load = 0
        WHERE type = 'utility_water'
        """
    )
    op.execute(
        """
        UPDATE businesses
        SET utility_service_type = 'housing',
            service_capacity = 100,
            service_load = 0
        WHERE type = 'utility_housing'
        """
    )


def downgrade() -> None:
    op.drop_table("utility_emergency_contracts")
    op.drop_column("businesses", "is_emergency_contract")
    op.drop_column("businesses", "service_load")
    op.drop_column("businesses", "service_capacity")
    op.drop_column("businesses", "utility_service_type")
