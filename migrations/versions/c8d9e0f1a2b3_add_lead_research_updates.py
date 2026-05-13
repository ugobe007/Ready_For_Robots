"""Add lead research updates and user notifications.

Revision ID: c8d9e0f1a2b3
Revises: b7c8d9e0f1a2
Create Date: 2026-05-12 23:45:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "c8d9e0f1a2b3"
down_revision: Union[str, Sequence[str], None] = "b7c8d9e0f1a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _json_type():
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        return postgresql.JSONB(astext_type=sa.Text())
    return sa.JSON()


def upgrade() -> None:
    op.create_table(
        "lead_research_updates",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("update_type", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("source_url", sa.String(length=1024), nullable=True),
        sa.Column("source_domain", sa.String(length=255), nullable=True),
        sa.Column("significance_score", sa.Float(), server_default="0", nullable=False),
        sa.Column("status", sa.String(length=32), server_default="new", nullable=False),
        sa.Column("dedupe_fingerprint", sa.String(length=80), nullable=False),
        sa.Column("payload", _json_type(), nullable=True),
        sa.Column("detected_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("dedupe_fingerprint", name="uq_lead_research_updates_fingerprint"),
    )
    op.create_index("ix_lead_research_updates_company_detected", "lead_research_updates", ["company_id", "detected_at"])
    op.create_index("ix_lead_research_updates_company_status", "lead_research_updates", ["company_id", "status"])
    op.create_index("ix_lead_research_updates_update_type", "lead_research_updates", ["update_type"])
    op.create_index("ix_lead_research_updates_source_domain", "lead_research_updates", ["source_domain"])

    op.create_table(
        "user_notifications",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True).with_variant(sa.String(length=36), "sqlite"), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=True),
        sa.Column("research_update_id", sa.Integer(), nullable=True),
        sa.Column("notification_type", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("delivery_state", sa.String(length=32), server_default="in_app", nullable=False),
        sa.Column("payload", _json_type(), nullable=True),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["research_update_id"], ["lead_research_updates.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["user_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_notifications_user_created", "user_notifications", ["user_id", "created_at"])
    op.create_index("ix_user_notifications_user_read", "user_notifications", ["user_id", "read_at"])
    op.create_index("ix_user_notifications_company", "user_notifications", ["company_id"])
    op.create_index("ix_user_notifications_update", "user_notifications", ["research_update_id"])
    op.create_index("ix_user_notifications_type", "user_notifications", ["notification_type"])
    op.create_index("ix_user_notifications_delivery_state", "user_notifications", ["delivery_state"])


def downgrade() -> None:
    op.drop_index("ix_user_notifications_delivery_state", table_name="user_notifications")
    op.drop_index("ix_user_notifications_type", table_name="user_notifications")
    op.drop_index("ix_user_notifications_update", table_name="user_notifications")
    op.drop_index("ix_user_notifications_company", table_name="user_notifications")
    op.drop_index("ix_user_notifications_user_read", table_name="user_notifications")
    op.drop_index("ix_user_notifications_user_created", table_name="user_notifications")
    op.drop_table("user_notifications")

    op.drop_index("ix_lead_research_updates_source_domain", table_name="lead_research_updates")
    op.drop_index("ix_lead_research_updates_update_type", table_name="lead_research_updates")
    op.drop_index("ix_lead_research_updates_company_status", table_name="lead_research_updates")
    op.drop_index("ix_lead_research_updates_company_detected", table_name="lead_research_updates")
    op.drop_table("lead_research_updates")
