"""add player avatar profiles

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-06-07 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "player_avatars",
        sa.Column("player_id", sa.Uuid(), nullable=False),
        sa.Column("body_preset_code", sa.String(length=40), nullable=False),
        sa.Column("face_preset_code", sa.String(length=40), nullable=False),
        sa.Column("skin_tone_code", sa.String(length=40), nullable=False),
        sa.Column("hair_style_code", sa.String(length=40), nullable=False),
        sa.Column("hair_color_code", sa.String(length=40), nullable=False),
        sa.Column("equipped_outfit", sa.JSON(), nullable=False),
        sa.Column("animation_profile_code", sa.String(length=50), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["player_id"], ["players.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("player_id"),
    )
    op.execute("""
        INSERT INTO player_avatars (
            player_id,
            body_preset_code,
            face_preset_code,
            skin_tone_code,
            hair_style_code,
            hair_color_code,
            equipped_outfit,
            animation_profile_code
        )
        SELECT
            id,
            'body_standard',
            'face_01',
            'skin_03',
            'hair_short_01',
            'hair_brown',
            '{"upper":"upper_stock_jacket","lower":"lower_stock_jeans","footwear":"footwear_stock_sneakers"}'::json,
            'humanoid_context_v1'
        FROM players
        """)


def downgrade() -> None:
    op.drop_table("player_avatars")
