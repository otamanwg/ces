"""add player auth token

Revision ID: 8ef75cf56fbd
Revises: 129500974fc0
Create Date: 2026-05-31 15:06:19.297671
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "8ef75cf56fbd"
down_revision: Union[str, None] = "129500974fc0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "players", sa.Column("auth_token", sa.String(length=120), nullable=True)
    )
    op.execute(
        "UPDATE players "
        "SET auth_token = md5(random()::text || clock_timestamp()::text || id::text) "
        "WHERE auth_token IS NULL"
    )
    op.alter_column("players", "auth_token", nullable=False)
    op.create_unique_constraint("uq_players_auth_token", "players", ["auth_token"])


def downgrade() -> None:
    op.drop_constraint("uq_players_auth_token", "players", type_="unique")
    op.drop_column("players", "auth_token")
