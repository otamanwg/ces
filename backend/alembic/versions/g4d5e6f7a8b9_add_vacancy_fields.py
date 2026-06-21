"""add vacancy fields: bonus_pct, shift_type, is_npc_position

Phase G4: Player vacancies with owner-set bonus %, shift types (day/evening/student),
NPC position flag to distinguish NPC slots from player vacancies.

Revision ID: g4d5e6f7a8b9
Revises: g3c4d5e6f7a8
Create Date: 2026-06-21 16:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "g4d5e6f7a8b9"
down_revision: str | None = "g3c4d5e6f7a8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "jobs",
        sa.Column("bonus_pct", sa.Numeric(5, 2), nullable=False, server_default="0"),
    )
    op.add_column(
        "jobs",
        sa.Column("shift_type", sa.String(length=20), nullable=False, server_default="day"),
    )
    op.add_column(
        "jobs",
        sa.Column("is_npc_position", sa.Boolean(), nullable=False, server_default="false"),
    )


def downgrade() -> None:
    op.drop_column("jobs", "is_npc_position")
    op.drop_column("jobs", "shift_type")
    op.drop_column("jobs", "bonus_pct")
