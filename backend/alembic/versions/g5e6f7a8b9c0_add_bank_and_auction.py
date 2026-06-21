"""add bank accounts, loans, bankruptcy auctions

Phase G5: Bank as business (deposits, loans, interest) + bankruptcy auctions.

Revision ID: g5e6f7a8b9c0
Revises: g4d5e6f7a8b9
Create Date: 2026-06-21 18:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "g5e6f7a8b9c0"
down_revision: str | None = "g4d5e6f7a8b9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Депозити гравців у банках
    op.create_table(
        "bank_deposits",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("bank_business_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("player_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("interest_rate", sa.Numeric(5, 2), nullable=False),
        sa.Column("created_at_game_day", sa.Integer(), nullable=False),
        sa.Column("last_interest_game_day", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["bank_business_id"], ["businesses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["player_id"], ["players.id"], ondelete="CASCADE"),
    )

    # Кредити, видані банками (Phase G5) — окремо від frozen bank_loans
    op.create_table(
        "bank_credits",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("bank_business_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("borrower_player_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("principal_amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("remaining_amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("interest_rate", sa.Numeric(5, 2), nullable=False),
        sa.Column("term_days", sa.Integer(), nullable=False),
        sa.Column("created_at_game_day", sa.Integer(), nullable=False),
        sa.Column("due_game_day", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),  # active/repaid/defaulted
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["bank_business_id"], ["businesses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["borrower_player_id"], ["players.id"], ondelete="CASCADE"),
    )

    # Аукціон банкрутів
    op.create_table(
        "bankruptcy_auctions",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("business_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("city_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("starting_price", sa.Numeric(15, 2), nullable=False),
        sa.Column("debt_amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("city_percentage", sa.Numeric(5, 2), nullable=False, server_default="10"),
        sa.Column("highest_bid", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("highest_bidder_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),  # active/won/closed
        sa.Column("winner_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("winning_bid", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["business_id"], ["businesses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["city_id"], ["cities.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["highest_bidder_id"], ["players.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["winner_id"], ["players.id"], ondelete="SET NULL"),
    )

    # Ставки на аукціоні
    op.create_table(
        "auction_bids",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("auction_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("bidder_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("placed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["auction_id"], ["bankruptcy_auctions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["bidder_id"], ["players.id"], ondelete="CASCADE"),
    )


def downgrade() -> None:
    op.drop_table("auction_bids")
    op.drop_table("bankruptcy_auctions")
    op.drop_table("bank_credits")
    op.drop_table("bank_deposits")
