"""add police officers table (Phase G8)

Revision ID: g8a8b9c0d1e2
Revises: g6f7a8b9c0d1
Create Date: 2025-01-01 00:00:00
"""
import sqlalchemy as sa
from alembic import op

revision = "g8a8b9c0d1e2"
down_revision = "g6f7a8b9c0d1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "police_officers",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("city_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("player_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rank", sa.String(20), nullable=False, server_default="patrol"),
        sa.Column("department", sa.String(50), nullable=True),
        sa.Column("patrol_district_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("successful_investigations", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("bribes_taken", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("hired_at_game_day", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("promoted_at_game_day", sa.Integer(), nullable=True),
        sa.Column("appointed_by_mayor_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["city_id"], ["cities.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["player_id"], ["players.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["patrol_district_id"], ["city_districts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["appointed_by_mayor_id"], ["players.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("city_id", "player_id", name="uq_police_officers_city_player"),
    )


def downgrade() -> None:
    op.drop_table("police_officers")
