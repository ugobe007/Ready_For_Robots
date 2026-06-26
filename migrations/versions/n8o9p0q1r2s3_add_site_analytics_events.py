"""Add persistent site analytics events table.

Revision ID: n8o9p0q1r2s3
Revises: m7n8o9p0q1r2
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "n8o9p0q1r2s3"
down_revision: Union[str, Sequence[str], None] = "m7n8o9p0q1r2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "site_analytics_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column(
            "payload",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_site_analytics_events_event_type", "site_analytics_events", ["event_type"])
    op.create_index("ix_site_analytics_events_created_at", "site_analytics_events", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_site_analytics_events_created_at", table_name="site_analytics_events")
    op.drop_index("ix_site_analytics_events_event_type", table_name="site_analytics_events")
    op.drop_table("site_analytics_events")
