"""add district metrics and foundation tables

Phase G1: dynamic district metrics + composite indices + seasonality.
Also lays schema foundation (empty tables, no services yet) for later
post-MVP gameplay phases (G2-G12): NPC residents, utility services,
vacancies/hiring, bank, politics, 3D avatar/skins, prison/police/press/
court/lawyer, casino/atelier/shadow niches, education tree, poker engine.

Revision ID: g1a2b3c4d5e6
Revises: f8b7c6d5e4a3
Create Date: 2026-06-21 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "g1a2b3c4d5e6"
down_revision: str | None = "f8b7c6d5e4a3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- 1. Dynamic district metrics on city_districts ---
    new_metric_columns = [
        "pollution",
        "education_coverage",
        "fire_safety",
        "power_supply",
        "water_supply",
        "waste_management",
        "population",
        "housing_capacity",
        "green_space",
        "happiness",
    ]
    for column in new_metric_columns:
        op.add_column(
            "city_districts",
            sa.Column(column, sa.Float(), nullable=False, server_default="50.0"),
        )

    # --- 2. Player foundation fields ---
    op.add_column(
        "players",
        sa.Column("criminal_rep", sa.Float(), nullable=False, server_default="0.0"),
    )
    op.add_column(
        "players",
        sa.Column("successful_deals", sa.Integer(), nullable=False, server_default="0"),
    )

    # --- 3. District metric snapshots (history per game day) ---
    op.create_table(
        "district_metric_snapshots",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("district_id", sa.Uuid(), nullable=False),
        sa.Column("game_day", sa.Integer(), nullable=False),
        sa.Column("rent_level", sa.Float(), nullable=False),
        sa.Column("job_supply", sa.Float(), nullable=False),
        sa.Column("crime_risk", sa.Float(), nullable=False),
        sa.Column("traffic", sa.Float(), nullable=False),
        sa.Column("service_coverage", sa.Float(), nullable=False),
        sa.Column("medical_coverage", sa.Float(), nullable=False),
        sa.Column("land_value", sa.Float(), nullable=False),
        sa.Column("desirability", sa.Float(), nullable=False),
        sa.Column("pollution", sa.Float(), nullable=False),
        sa.Column("education_coverage", sa.Float(), nullable=False),
        sa.Column("fire_safety", sa.Float(), nullable=False),
        sa.Column("power_supply", sa.Float(), nullable=False),
        sa.Column("water_supply", sa.Float(), nullable=False),
        sa.Column("waste_management", sa.Float(), nullable=False),
        sa.Column("population", sa.Float(), nullable=False),
        sa.Column("housing_capacity", sa.Float(), nullable=False),
        sa.Column("green_space", sa.Float(), nullable=False),
        sa.Column("happiness", sa.Float(), nullable=False),
        sa.Column("economy_score", sa.Float(), nullable=False),
        sa.Column("production_score", sa.Float(), nullable=False),
        sa.Column("household_score", sa.Float(), nullable=False),
        sa.Column("commerce_score", sa.Float(), nullable=False),
        sa.Column("infrastructure_score", sa.Float(), nullable=False),
        sa.Column("social_score", sa.Float(), nullable=False),
        sa.Column("season", sa.String(length=10), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["district_id"], ["city_districts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "district_id", "game_day", name="uq_district_metric_snapshots_district_day"
        ),
    )
    op.create_index(
        "ix_district_metric_snapshots_district_day",
        "district_metric_snapshots",
        ["district_id", "game_day"],
        unique=False,
    )

    # --- 4. NPC residents (Phase G2 foundation) ---
    op.create_table(
        "npc_residents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("city_id", sa.Uuid(), nullable=False),
        sa.Column("district_id", sa.Uuid(), nullable=False),
        sa.Column("workplace_business_id", sa.Uuid(), nullable=True),
        sa.Column("cash_balance", sa.Numeric(precision=15, scale=2), nullable=False, server_default="0"),
        sa.Column("salary", sa.Numeric(precision=15, scale=2), nullable=False, server_default="0"),
        sa.Column("employed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("npc_type", sa.String(length=30), nullable=False, server_default="worker"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["city_id"], ["cities.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["district_id"], ["city_districts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workplace_business_id"], ["businesses.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    # --- 5. Skins (Phase G9 / atelier foundation) ---
    op.create_table(
        "skins",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("designer_id", sa.Uuid(), nullable=False),
        sa.Column("atelier_id", sa.Uuid(), nullable=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("config", sa.JSON(), nullable=False),
        sa.Column("rarity", sa.String(length=20), nullable=False, server_default="common"),
        sa.Column("is_unique", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("copies_total", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("copies_sold", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("price", sa.Numeric(precision=15, scale=2), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["designer_id"], ["players.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["atelier_id"], ["businesses.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "player_skins",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("player_id", sa.Uuid(), nullable=False),
        sa.Column("skin_id", sa.Uuid(), nullable=False),
        sa.Column("is_equipped", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "acquired_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["player_id"], ["players.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["skin_id"], ["skins.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("player_id", "skin_id", name="uq_player_skins_player_skin"),
    )

    # --- 6. Education (Phase G10 foundation) ---
    op.create_table(
        "education",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("player_id", sa.Uuid(), nullable=False),
        sa.Column("course", sa.String(length=40), nullable=False),
        sa.Column("mode", sa.String(length=20), nullable=False, server_default="full_time"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="enrolled"),
        sa.Column("is_fake", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("enrolled_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["player_id"], ["players.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "education_exams",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("player_id", sa.Uuid(), nullable=False),
        sa.Column("exam_type", sa.String(length=40), nullable=False),
        sa.Column("is_passed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("taken_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["player_id"], ["players.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # --- 7. Criminal reputation log (Phase G9 foundation) ---
    op.create_table(
        "criminal_rep_log",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("player_id", sa.Uuid(), nullable=False),
        sa.Column("delta", sa.Float(), nullable=False),
        sa.Column("reason", sa.String(length=40), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["player_id"], ["players.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # --- 8. Corruption log (Phase G8 foundation) ---
    op.create_table(
        "corruption_log",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("incident_type", sa.String(length=40), nullable=False),
        sa.Column("perpetrator_id", sa.Uuid(), nullable=False),
        sa.Column("victim_id", sa.Uuid(), nullable=True),
        sa.Column("amount", sa.Numeric(precision=15, scale=2), nullable=False, server_default="0"),
        sa.Column("district_id", sa.Uuid(), nullable=True),
        sa.Column("evidence_strength", sa.Float(), nullable=False, server_default="0.1"),
        sa.Column("is_reported", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("reported_by_id", sa.Uuid(), nullable=True),
        sa.Column("is_investigated", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_proven", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("consequence", sa.String(length=40), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("discovered_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["perpetrator_id"], ["players.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["victim_id"], ["players.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["district_id"], ["city_districts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["reported_by_id"], ["players.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    # --- 9. Press investigations (Phase G8 foundation) ---
    op.create_table(
        "press_investigations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("target_player_id", sa.Uuid(), nullable=False),
        sa.Column("journalist_id", sa.Uuid(), nullable=True),
        sa.Column("incident_type", sa.String(length=40), nullable=False),
        sa.Column("press_evidence", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scale", sa.String(length=20), nullable=False, server_default="local"),
        sa.Column("article_title", sa.String(length=200), nullable=True),
        sa.Column("happiness_impact", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reputation_impact", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["target_player_id"], ["players.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["journalist_id"], ["players.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    # --- 10. Court cases (Phase G8 foundation) ---
    op.create_table(
        "court_cases",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("corruption_log_id", sa.Uuid(), nullable=True),
        sa.Column("defendant_id", sa.Uuid(), nullable=False),
        sa.Column("verdict", sa.String(length=40), nullable=False),
        sa.Column("is_appealed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("appeal_deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("judge_1_vote", sa.String(length=20), nullable=True),
        sa.Column("judge_2_vote", sa.String(length=20), nullable=True),
        sa.Column("judge_3_vote", sa.String(length=20), nullable=True),
        sa.Column("judge_1_bribed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("judge_2_bribed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("judge_3_bribed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("final_verdict", sa.String(length=40), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["corruption_log_id"], ["corruption_log.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["defendant_id"], ["players.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # --- 11. Prison sentences (Phase G8 foundation) ---
    op.create_table(
        "prison_sentences",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("player_id", sa.Uuid(), nullable=False),
        sa.Column("court_case_id", sa.Uuid(), nullable=True),
        sa.Column("days_total", sa.Integer(), nullable=False),
        sa.Column("days_served", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("days_remaining", sa.Integer(), nullable=False),
        sa.Column("good_behavior_reduction", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("business_impact", sa.String(length=20), nullable=False, server_default="none"),
        sa.Column("frozen_business_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="serving"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["player_id"], ["players.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["court_case_id"], ["court_cases.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["frozen_business_id"], ["businesses.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    # --- 12. Casino games (Phase G9 foundation) ---
    op.create_table(
        "casino_games",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("casino_business_id", sa.Uuid(), nullable=False),
        sa.Column("game_type", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="waiting"),
        sa.Column("players", sa.JSON(), nullable=False),
        sa.Column("pot", sa.Numeric(precision=15, scale=2), nullable=False, server_default="0"),
        sa.Column("rake", sa.Numeric(precision=15, scale=2), nullable=False, server_default="0"),
        sa.Column("winner_id", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["casino_business_id"], ["businesses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["winner_id"], ["players.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    # --- 13. Shadow businesses (Phase G9 foundation) ---
    op.create_table(
        "shadow_businesses",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("type", sa.String(length=40), nullable=False),
        sa.Column("district_id", sa.Uuid(), nullable=False),
        sa.Column("cash_balance", sa.Numeric(precision=15, scale=2), nullable=False, server_default="0"),
        sa.Column("is_discovered", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("discovered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["owner_id"], ["players.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["district_id"], ["city_districts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # --- 14. Lawyer engagements (Phase G8 foundation) ---
    op.create_table(
        "lawyer_engagements",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("lawyer_id", sa.Uuid(), nullable=False),
        sa.Column("client_id", sa.Uuid(), nullable=False),
        sa.Column("deal_type", sa.String(length=40), nullable=False),
        sa.Column("amount", sa.Numeric(precision=15, scale=2), nullable=False, server_default="0"),
        sa.Column("commission", sa.Numeric(precision=15, scale=2), nullable=False, server_default="0"),
        sa.Column("success_chance_bonus", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("is_successful", sa.Boolean(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["lawyer_id"], ["players.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["client_id"], ["players.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # --- 15. Press blackmail (Phase G8 foundation) ---
    op.create_table(
        "press_blackmails",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("journalist_id", sa.Uuid(), nullable=False),
        sa.Column("target_id", sa.Uuid(), nullable=False),
        sa.Column("investigation_id", sa.Uuid(), nullable=True),
        sa.Column("amount_demanded", sa.Numeric(precision=15, scale=2), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="pending"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["journalist_id"], ["players.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_id"], ["players.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["investigation_id"], ["press_investigations.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("press_blackmails")
    op.drop_table("lawyer_engagements")
    op.drop_table("shadow_businesses")
    op.drop_table("casino_games")
    op.drop_table("prison_sentences")
    op.drop_table("court_cases")
    op.drop_table("press_investigations")
    op.drop_table("corruption_log")
    op.drop_table("criminal_rep_log")
    op.drop_table("education_exams")
    op.drop_table("education")
    op.drop_table("player_skins")
    op.drop_table("skins")
    op.drop_table("npc_residents")
    op.drop_index(
        "ix_district_metric_snapshots_district_day",
        table_name="district_metric_snapshots",
    )
    op.drop_table("district_metric_snapshots")

    op.drop_column("players", "successful_deals")
    op.drop_column("players", "criminal_rep")

    for column in [
        "happiness",
        "green_space",
        "housing_capacity",
        "population",
        "waste_management",
        "water_supply",
        "power_supply",
        "fire_safety",
        "education_coverage",
        "pollution",
    ]:
        op.drop_column("city_districts", column)
