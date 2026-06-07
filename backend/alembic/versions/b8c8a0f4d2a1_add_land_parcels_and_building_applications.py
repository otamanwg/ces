"""add land parcels and building applications

Revision ID: b8c8a0f4d2a1
Revises: a4fd9c2b1e77
Create Date: 2026-06-03 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "b8c8a0f4d2a1"
down_revision: Union[str, None] = "a4fd9c2b1e77"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "land_parcels",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("city_id", sa.Uuid(), nullable=False),
        sa.Column("district_id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=70), nullable=False),
        sa.Column("label", sa.String(length=120), nullable=False),
        sa.Column("land_type", sa.String(length=50), nullable=False),
        sa.Column("zoning_type", sa.String(length=50), nullable=False),
        sa.Column("area_hectares", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column(
            "base_price_per_hectare", sa.Numeric(precision=15, scale=2), nullable=False
        ),
        sa.Column("current_price", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("owner_player_id", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["city_id"], ["cities.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["district_id"], ["city_districts.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["owner_player_id"], ["players.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("city_id", "code", name="uq_land_parcels_city_code"),
    )
    op.create_table(
        "building_applications",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("city_id", sa.Uuid(), nullable=False),
        sa.Column("district_id", sa.Uuid(), nullable=False),
        sa.Column("land_parcel_id", sa.Uuid(), nullable=False),
        sa.Column("applicant_player_id", sa.Uuid(), nullable=False),
        sa.Column("proposed_name", sa.String(length=120), nullable=False),
        sa.Column("project_type", sa.String(length=50), nullable=False),
        sa.Column(
            "land_area_hectares", sa.Numeric(precision=10, scale=2), nullable=False
        ),
        sa.Column("expected_jobs", sa.Integer(), nullable=False),
        sa.Column("traffic_load", sa.Integer(), nullable=False),
        sa.Column("service_load", sa.Integer(), nullable=False),
        sa.Column("medical_load", sa.Integer(), nullable=False),
        sa.Column("public_benefit", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("mayor_score", sa.Integer(), nullable=False),
        sa.Column("mayor_summary", sa.String(length=300), nullable=False),
        sa.Column("mayor_issues", sa.JSON(), nullable=False),
        sa.Column("mayor_questions", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["applicant_player_id"], ["players.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["city_id"], ["cities.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["district_id"], ["city_districts.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["land_parcel_id"], ["land_parcels.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("building_applications")
    op.drop_table("land_parcels")
