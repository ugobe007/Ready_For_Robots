"""Add waitlist signups.

Revision ID: f4a5b6c7d8e9
Revises: e2f3a4b5c6d7
Create Date: 2026-05-09

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "f4a5b6c7d8e9"
down_revision: Union[str, Sequence[str], None] = "e2f3a4b5c6d7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    if "waitlist_signups" not in insp.get_table_names():
        op.create_table(
            "waitlist_signups",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("email", sa.String(length=320), nullable=False),
            sa.Column("name", sa.String(length=200), nullable=True),
            sa.Column("company", sa.String(length=240), nullable=True),
            sa.Column("use_case", sa.Text(), nullable=True),
            sa.Column("source", sa.String(length=120), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("email", name="uq_waitlist_signups_email"),
        )
    insp = inspect(bind)
    if "waitlist_signups" in insp.get_table_names():
        names = {i["name"] for i in insp.get_indexes("waitlist_signups")}
        if "ix_waitlist_signups_email" not in names:
            op.create_index("ix_waitlist_signups_email", "waitlist_signups", ["email"], unique=False)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_waitlist_signups_email")
    op.execute("DROP TABLE IF EXISTS waitlist_signups CASCADE")
