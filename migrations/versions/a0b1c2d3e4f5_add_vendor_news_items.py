"""
Add vendor_news_items for Hermes vendor/customer news ingest.

Revision ID: a0b1c2d3e4f5
Revises: z0a1b2c3d4e5
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "a0b1c2d3e4f5"
down_revision: Union[str, Sequence[str], None] = "z0a1b2c3d4e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _json():
    return postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite")


def _uuid():
    return postgresql.UUID(as_uuid=True).with_variant(sa.String(36), "sqlite")


def upgrade() -> None:
    op.create_table(
        "vendor_news_items",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("news_id", sa.String(64), nullable=False),
        sa.Column("news_type", sa.String(64), server_default="product", nullable=False),
        sa.Column("entity_kind", sa.String(32), server_default="vendor", nullable=False),
        sa.Column("entity_name", sa.String(240), nullable=False),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(480), nullable=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("source_date", sa.String(32), nullable=True),
        sa.Column("confidence", sa.Float(), server_default="0.5", nullable=False),
        sa.Column("hermes_run_id", sa.String(120), nullable=True),
        sa.Column("extra", _json(), server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_vendor_news_items_news_id", "vendor_news_items", ["news_id"], unique=True)
    op.create_index("ix_vendor_news_items_news_type", "vendor_news_items", ["news_type"])
    op.create_index("ix_vendor_news_items_entity_kind", "vendor_news_items", ["entity_kind"])
    op.create_index("ix_vendor_news_items_entity_name", "vendor_news_items", ["entity_name"])
    op.create_index("ix_vendor_news_items_company_id", "vendor_news_items", ["company_id"])
    op.create_index("ix_vendor_news_items_source_url", "vendor_news_items", ["source_url"])
    op.create_index("ix_vendor_news_items_hermes_run_id", "vendor_news_items", ["hermes_run_id"])


def downgrade() -> None:
    op.drop_table("vendor_news_items")
