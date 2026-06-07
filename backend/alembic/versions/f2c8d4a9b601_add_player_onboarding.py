"""add player onboarding

Revision ID: f2c8d4a9b601
Revises: e7a4d9c2b8f1
Create Date: 2026-06-06 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "f2c8d4a9b601"
down_revision: Union[str, None] = "e7a4d9c2b8f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "player_onboarding",
        sa.Column("player_id", sa.Uuid(), nullable=False),
        sa.Column("stage", sa.String(length=30), nullable=False),
        sa.Column("police_report_status", sa.String(length=30), nullable=False),
        sa.Column("police_recovery_amount", sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column("police_recovery_available_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["player_id"], ["players.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("player_id"),
    )
    op.execute("""
        INSERT INTO player_onboarding (
            player_id,
            stage,
            police_report_status,
            completed_at
        )
        SELECT id, 'completed', 'not_filed', now()
        FROM players
        """)


def downgrade() -> None:
    op.drop_table("player_onboarding")
