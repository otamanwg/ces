"""add player tutorial age group

Revision ID: a1b2c3d4e5f6
Revises: f2c8d4a9b601
Create Date: 2026-06-06 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "f2c8d4a9b601"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "players",
        sa.Column(
            "tutorial_age_group",
            sa.String(length=20),
            nullable=False,
            server_default="adult",
        ),
    )
    op.create_check_constraint(
        "ck_players_tutorial_age_group",
        "players",
        "tutorial_age_group IN ('teen', 'adult', 'mature')",
    )
    op.alter_column("players", "tutorial_age_group", server_default=None)


def downgrade() -> None:
    op.drop_constraint("ck_players_tutorial_age_group", "players", type_="check")
    op.drop_column("players", "tutorial_age_group")
