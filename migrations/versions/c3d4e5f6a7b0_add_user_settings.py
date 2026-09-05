"""Add user_settings for PDF/email sender display.

Revision ID: c3d4e5f6a7b0
Revises: b2c3d4e5f6a7
Create Date: 2026-05-07

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "c3d4e5f6a7b0"
down_revision: Union[str, Sequence[str], None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_settings",
        sa.Column("user_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("sender_name", sa.String(length=200), nullable=True),
        sa.Column("sender_title", sa.String(length=200), nullable=True),
        sa.Column("sender_company", sa.String(length=200), nullable=True),
        sa.Column("sender_email", sa.String(length=320), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("user_id"),
        sa.ForeignKeyConstraint(["user_id"], ["user_profiles.id"], ondelete="CASCADE"),
    )


def downgrade() -> None:
    op.drop_table("user_settings")
