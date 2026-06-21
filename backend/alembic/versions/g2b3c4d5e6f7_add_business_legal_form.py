"""add business legal_form for NPC hire limits

Phase G2: NPC residents need legal_form on Business to enforce hire limits
(ФОП=1, ТОВ=5, ВАТ=10). Default "fop" for existing businesses.

Revision ID: g2b3c4d5e6f7
Revises: g1a2b3c4d5e6
Create Date: 2026-06-21 12:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "g2b3c4d5e6f7"
down_revision: str | None = "g1a2b3c4d5e6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "businesses",
        sa.Column("legal_form", sa.String(length=10), nullable=False, server_default="fop"),
    )


def downgrade() -> None:
    op.drop_column("businesses", "legal_form")
