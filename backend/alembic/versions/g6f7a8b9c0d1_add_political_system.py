"""add political system: city offices, elections, votes, bribes, corruption

Phase G6: Political system — city office hierarchy, mayoral elections,
open voting, vote of no confidence, vote bribery, corruption log.

Revision ID: g6f7a8b9c0d1
Revises: g5e6f7a8b9c0
Create Date: 2026-06-21 20:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "g6f7a8b9c0d1"
down_revision: str | None = "g5e6f7a8b9c0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Посади у мерії (ієрархія: worker → department_head → deputy → mayor)
    op.create_table(
        "city_offices",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("city_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("player_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("position", sa.String(30), nullable=False),  # worker/department_head/deputy/mayor
        sa.Column("department", sa.String(50), nullable=True),  # для worker/head: economy/social/infrastructure
        sa.Column("hired_at_game_day", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["city_id"], ["cities.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["player_id"], ["players.id"], ondelete="CASCADE"),
    )

    # Вибори мера
    op.create_table(
        "mayor_elections",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("city_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("started_at_game_day", sa.Integer(), nullable=False),
        sa.Column("ends_at_game_day", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),  # active/concluded
        sa.Column("winner_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["city_id"], ["cities.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["winner_id"], ["players.id"], ondelete="SET NULL"),
    )

    # Кандидати у виборах
    op.create_table(
        "election_candidates",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("election_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("player_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("platform_text", sa.Text(), nullable=True),
        sa.Column("registered_at_game_day", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["election_id"], ["mayor_elections.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["player_id"], ["players.id"], ondelete="CASCADE"),
    )

    # Голоси виборців (відкрите голосування)
    op.create_table(
        "mayor_votes",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("election_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("voter_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("candidate_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("voted_at_game_day", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["election_id"], ["mayor_elections.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["voter_id"], ["players.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["candidate_id"], ["election_candidates.id"], ondelete="CASCADE"),
    )

    # Підкуп голосів
    op.create_table(
        "vote_bribes",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("election_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("briber_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("voter_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="offered"),  # offered/accepted/rejected/reported
        sa.Column("created_at_game_day", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["election_id"], ["mayor_elections.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["briber_id"], ["players.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["voter_id"], ["players.id"], ondelete="CASCADE"),
    )

    # Журнал корупції (політична — окремо від frozen corruption_log)
    op.create_table(
        "political_corruption_log",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("city_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action_type", sa.String(30), nullable=False),  # vote_bribe/embezzlement/fraud
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("evidence_strength", sa.Numeric(5, 2), nullable=False, server_default="0"),  # 0-100
        sa.Column("is_reported", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at_game_day", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["city_id"], ["cities.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_id"], ["players.id"], ondelete="CASCADE"),
    )

    # Phase G6: термін мандату мера (для вотуму недовіри)
    op.add_column(
        "cities",
        sa.Column("mayor_term_started_game_day", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("cities", "mayor_term_started_game_day")
    op.drop_table("political_corruption_log")
    op.drop_table("vote_bribes")
    op.drop_table("mayor_votes")
    op.drop_table("election_candidates")
    op.drop_table("mayor_elections")
    op.drop_table("city_offices")
