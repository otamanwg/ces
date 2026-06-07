"""add player hunger

Revision ID: df6a4bd0f1c2
Revises: 8ef75cf56fbd
Create Date: 2026-06-01 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "df6a4bd0f1c2"
down_revision: str | None = "8ef75cf56fbd"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("players", sa.Column("hunger", sa.Integer(), nullable=False, server_default="0"))
    op.alter_column("players", "hunger", server_default=None)


def downgrade() -> None:
    op.drop_column("players", "hunger")
