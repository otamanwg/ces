"""add buildings

Revision ID: c9e2b4f7a613
Revises: b8c8a0f4d2a1
Create Date: 2026-06-05 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "c9e2b4f7a613"
down_revision: Union[str, None] = "b8c8a0f4d2a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "buildings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("city_id", sa.Uuid(), nullable=False),
        sa.Column("district_id", sa.Uuid(), nullable=False),
        sa.Column("land_parcel_id", sa.Uuid(), nullable=False),
        sa.Column("source_application_id", sa.Uuid(), nullable=False),
        sa.Column("owner_player_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("project_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("operating_status", sa.String(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["city_id"], ["cities.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["district_id"], ["city_districts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["land_parcel_id"], ["land_parcels.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["owner_player_id"], ["players.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_application_id"], ["building_applications.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("land_parcel_id", name="uq_buildings_land_parcel_id"),
        sa.UniqueConstraint("source_application_id", name="uq_buildings_source_application_id"),
    )


def downgrade() -> None:
    op.drop_table("buildings")
