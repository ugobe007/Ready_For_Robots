"""Add SCOUT persona and collateral controls.

Revision ID: e1f2a3b4c5d7
Revises: e0f1a2b3c4d5
Create Date: 2026-05-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "e1f2a3b4c5d7"
down_revision: Union[str, Sequence[str], None] = "e0f1a2b3c4d5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("user_settings", sa.Column("scout_persona_traits", sa.Text(), nullable=True))
    op.add_column(
        "user_settings",
        sa.Column("scout_collateral_policy", sa.String(length=32), nullable=False, server_default="selective"),
    )
    op.add_column("user_settings", sa.Column("scout_collateral_links", sa.Text(), nullable=True))
    op.add_column(
        "user_settings",
        sa.Column("scout_background_briefing_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )


def downgrade() -> None:
    op.drop_column("user_settings", "scout_background_briefing_enabled")
    op.drop_column("user_settings", "scout_collateral_links")
    op.drop_column("user_settings", "scout_collateral_policy")
    op.drop_column("user_settings", "scout_persona_traits")
