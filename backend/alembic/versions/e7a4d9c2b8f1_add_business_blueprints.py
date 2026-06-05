"""add business blueprints

Revision ID: e7a4d9c2b8f1
Revises: d35f7b6aa103
Create Date: 2026-06-05 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e7a4d9c2b8f1"
down_revision: Union[str, None] = "d35f7b6aa103"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "business_blueprints",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=70), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("business_type", sa.String(length=50), nullable=False),
        sa.Column("project_type", sa.String(length=50), nullable=False),
        sa.Column("description", sa.String(length=600), nullable=False),
        sa.Column("difficulty", sa.String(length=30), nullable=False),
        sa.Column("allowed_land_types", sa.JSON(), nullable=False),
        sa.Column("allowed_zoning_types", sa.JSON(), nullable=False),
        sa.Column("min_area_hectares", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("construction_cost", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("opening_fee", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("recommended_cash_reserve", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("daily_profit_min", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("daily_profit_max", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("upkeep_daily", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("risk_level", sa.Integer(), nullable=False),
        sa.Column("risks", sa.JSON(), nullable=False),
        sa.Column("metric_effects", sa.JSON(), nullable=False),
        sa.Column("visual_archetype", sa.String(length=80), nullable=False),
        sa.Column("style_tags", sa.JSON(), nullable=False),
        sa.Column("player_hints", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_business_blueprints_code"),
    )
    op.add_column("building_applications", sa.Column("business_blueprint_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_building_applications_business_blueprint_id",
        "building_applications",
        "business_blueprints",
        ["business_blueprint_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.add_column("buildings", sa.Column("business_blueprint_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_buildings_business_blueprint_id",
        "buildings",
        "business_blueprints",
        ["business_blueprint_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_buildings_business_blueprint_id", "buildings", type_="foreignkey")
    op.drop_column("buildings", "business_blueprint_id")
    op.drop_constraint("fk_building_applications_business_blueprint_id", "building_applications", type_="foreignkey")
    op.drop_column("building_applications", "business_blueprint_id")
    op.drop_table("business_blueprints")
