"""Add SCOUT communication style preferences.

Revision ID: e0f1a2b3c4d5
Revises: d9e0f1a2b3c4
Create Date: 2026-05-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "e0f1a2b3c4d5"
down_revision: Union[str, Sequence[str], None] = "d9e0f1a2b3c4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("user_settings", sa.Column("scout_message_style", sa.Text(), nullable=True))
    op.add_column(
        "user_settings",
        sa.Column("scout_preferred_channel", sa.String(length=32), nullable=False, server_default="email"),
    )
    op.add_column("user_settings", sa.Column("scout_meeting_preference", sa.Text(), nullable=True))
    op.add_column("user_settings", sa.Column("scout_default_cc", sa.Text(), nullable=True))
    op.add_column("user_settings", sa.Column("scout_default_bcc", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("user_settings", "scout_default_bcc")
    op.drop_column("user_settings", "scout_default_cc")
    op.drop_column("user_settings", "scout_meeting_preference")
    op.drop_column("user_settings", "scout_preferred_channel")
    op.drop_column("user_settings", "scout_message_style")
