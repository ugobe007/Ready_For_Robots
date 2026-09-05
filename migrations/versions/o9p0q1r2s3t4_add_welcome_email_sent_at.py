"""Add welcome_email_sent_at to user_profiles.

Revision ID: o9p0q1r2s3t4
Revises: n8o9p0q1r2s3
Create Date: 2026-06-16

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "o9p0q1r2s3t4"
down_revision: Union[str, Sequence[str], None] = "n8o9p0q1r2s3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    cols = {c["name"] for c in insp.get_columns("user_profiles")}
    if "welcome_email_sent_at" not in cols:
        op.add_column(
            "user_profiles",
            sa.Column("welcome_email_sent_at", sa.DateTime(timezone=True), nullable=True),
        )


def downgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    cols = {c["name"] for c in insp.get_columns("user_profiles")}
    if "welcome_email_sent_at" in cols:
        op.drop_column("user_profiles", "welcome_email_sent_at")
