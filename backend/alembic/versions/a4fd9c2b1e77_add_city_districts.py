"""add city districts

Revision ID: a4fd9c2b1e77
Revises: df6a4bd0f1c2
Create Date: 2026-06-03 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "a4fd9c2b1e77"
down_revision: Union[str, None] = "df6a4bd0f1c2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "city_districts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("city_id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("zone_type", sa.String(length=50), nullable=False),
        sa.Column("description", sa.String(length=300), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("land_available_hectares", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("rent_level", sa.Integer(), nullable=False),
        sa.Column("job_supply", sa.Integer(), nullable=False),
        sa.Column("crime_risk", sa.Integer(), nullable=False),
        sa.Column("traffic", sa.Integer(), nullable=False),
        sa.Column("service_coverage", sa.Integer(), nullable=False),
        sa.Column("medical_coverage", sa.Integer(), nullable=False),
        sa.Column("land_value", sa.Integer(), nullable=False),
        sa.Column("desirability", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["city_id"], ["cities.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("city_id", "code", name="uq_city_districts_city_code"),
    )


def downgrade() -> None:
    op.drop_table("city_districts")
