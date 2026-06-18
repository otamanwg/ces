"""hash player auth tokens

Revision ID: 9c1b2a3d4e5f
Revises: 477f53e05e71
Create Date: 2026-06-16 00:00:00.000000
"""

from collections.abc import Sequence
from hashlib import sha256

import sqlalchemy as sa
from alembic import op

revision: str = "9c1b2a3d4e5f"
down_revision: str | None = "477f53e05e71"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("players", sa.Column("auth_token_hash", sa.String(length=64), nullable=True))
    connection = op.get_bind()
    legacy_tokens = connection.execute(
        sa.text("SELECT id, auth_token FROM players WHERE auth_token IS NOT NULL AND auth_token_hash IS NULL")
    )
    for player_id, auth_token in legacy_tokens:
        connection.execute(
            sa.text("UPDATE players SET auth_token_hash = :auth_token_hash WHERE id = :player_id"),
            {
                "auth_token_hash": sha256(auth_token.encode("utf-8")).hexdigest(),
                "player_id": player_id,
            },
        )
    op.execute("UPDATE players SET auth_token = NULL WHERE auth_token_hash IS NOT NULL")
    op.create_unique_constraint("uq_players_auth_token_hash", "players", ["auth_token_hash"])
    op.alter_column("players", "auth_token", nullable=True)


def downgrade() -> None:
    op.execute(
        "UPDATE players "
        "SET auth_token = md5(random()::text || clock_timestamp()::text || id::text) "
        "WHERE auth_token IS NULL"
    )
    op.alter_column("players", "auth_token", nullable=False)
    op.drop_constraint("uq_players_auth_token_hash", "players", type_="unique")
    op.drop_column("players", "auth_token_hash")
