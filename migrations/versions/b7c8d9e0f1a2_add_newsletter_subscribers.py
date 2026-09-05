"""Add newsletter subscribers.

Revision ID: b7c8d9e0f1a2
Revises: a6b7c8d9e0f1
Create Date: 2026-05-10
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

revision: str = "b7c8d9e0f1a2"
down_revision: Union[str, Sequence[str], None] = "a6b7c8d9e0f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    insp = inspect(op.get_bind())
    if "newsletter_subscribers" not in insp.get_table_names():
        op.create_table(
            "newsletter_subscribers",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("email", sa.String(length=320), nullable=False),
            sa.Column("name", sa.String(length=200), nullable=True),
            sa.Column("company", sa.String(length=240), nullable=True),
            sa.Column("robot_category", sa.String(length=160), nullable=True),
            sa.Column("source", sa.String(length=120), nullable=True),
            sa.Column("status", sa.String(length=32), server_default="active", nullable=False),
            sa.Column("consent_text", sa.Text(), nullable=True),
            sa.Column("subscriber_metadata", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("email", name="uq_newsletter_subscribers_email"),
        )
    indexes = {i["name"] for i in inspect(op.get_bind()).get_indexes("newsletter_subscribers")}
    if "ix_newsletter_subscribers_email" not in indexes:
        op.create_index("ix_newsletter_subscribers_email", "newsletter_subscribers", ["email"], unique=False)
    if "ix_newsletter_subscribers_status" not in indexes:
        op.create_index("ix_newsletter_subscribers_status", "newsletter_subscribers", ["status"], unique=False)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS newsletter_subscribers CASCADE")
