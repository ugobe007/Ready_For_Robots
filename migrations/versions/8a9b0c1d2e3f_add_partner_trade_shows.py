"""Add partner_trade_shows for partner GTM (The Robot Guild, etc.).

Revision ID: 8a9b0c1d2e3f
Revises: f3a4b5c6d7e8
Create Date: 2026-04-22
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "8a9b0c1d2e3f"
down_revision: Union[str, Sequence[str], None] = "f3a4b5c6d7e8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "partner_trade_shows",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("partner_slug", sa.String(length=64), nullable=False),
        sa.Column("source_key", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=512), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("location", sa.String(length=512), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("event_url", sa.String(length=1024), nullable=True),
        sa.Column("source_page_url", sa.String(length=1024), nullable=True),
        sa.Column("exhibitor_hints", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_key", name="uq_partner_trade_shows_source_key"),
    )
    op.create_index(
        "ix_partner_trade_shows_partner_slug",
        "partner_trade_shows",
        ["partner_slug"],
        unique=False,
    )
    op.create_index(
        "ix_partner_trade_shows_start_date",
        "partner_trade_shows",
        ["start_date"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_partner_trade_shows_start_date", table_name="partner_trade_shows")
    op.drop_index("ix_partner_trade_shows_partner_slug", table_name="partner_trade_shows")
    op.drop_table("partner_trade_shows")
