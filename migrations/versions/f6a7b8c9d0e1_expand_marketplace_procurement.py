"""Expand marketplace procurement workflows.

Revision ID: f6a7b8c9d0e1
Revises: f2a3b4c5d6e7
Create Date: 2026-05-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, Sequence[str], None] = "f2a3b4c5d6e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _columns(table: str) -> set[str]:
    insp = inspect(op.get_bind())
    if table not in insp.get_table_names():
        return set()
    return {c["name"] for c in insp.get_columns(table)}


def upgrade() -> None:
    buyer_cols = _columns("buyer_profiles")
    for name, default in {
        "decision_makers": "'[]'::jsonb",
        "procurement_workflow": "'{}'::jsonb",
        "po_preferences": "'{}'::jsonb",
    }.items():
        if name not in buyer_cols:
            op.add_column(
                "buyer_profiles",
                sa.Column(name, postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text(default), nullable=False),
            )

    rfq_cols = _columns("rfqs")
    if "project_description" not in rfq_cols:
        op.add_column("rfqs", sa.Column("project_description", sa.Text(), nullable=True))
    if "timeline_summary" not in rfq_cols:
        op.add_column("rfqs", sa.Column("timeline_summary", sa.Text(), nullable=True))
    for name, default in {
        "decision_makers": "'[]'::jsonb",
        "workflow_process": "'{}'::jsonb",
        "technical_specs": "'{}'::jsonb",
        "schedule": "'[]'::jsonb",
    }.items():
        if name not in rfq_cols:
            op.add_column(
                "rfqs",
                sa.Column(name, postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text(default), nullable=False),
            )

    op.create_table(
        "marketplace_commercial_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("rfq_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("proposal_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("buyer_team_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("vendor_team_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("document_type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="draft", nullable=False),
        sa.Column("document_number", sa.String(length=120), nullable=True),
        sa.Column("title", sa.String(length=240), nullable=True),
        sa.Column("amount", sa.Numeric(18, 2), nullable=True),
        sa.Column("currency", sa.String(length=8), server_default="USD", nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("asset_ids", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["buyer_team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["user_profiles.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["proposal_id"], ["rfq_proposals.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["rfq_id"], ["rfqs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["vendor_team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    for idx, cols in {
        "ix_marketplace_commercial_documents_rfq_id": ["rfq_id"],
        "ix_marketplace_commercial_documents_proposal_id": ["proposal_id"],
        "ix_marketplace_commercial_documents_buyer_team_id": ["buyer_team_id"],
        "ix_marketplace_commercial_documents_vendor_team_id": ["vendor_team_id"],
        "ix_marketplace_commercial_documents_created_by_user_id": ["created_by_user_id"],
        "ix_marketplace_commercial_documents_document_type": ["document_type"],
        "ix_marketplace_commercial_documents_status": ["status"],
        "ix_marketplace_commercial_documents_document_number": ["document_number"],
        "ix_marketplace_commercial_documents_due_at": ["due_at"],
        "ix_marketplace_commercial_documents_issued_at": ["issued_at"],
    }.items():
        op.create_index(idx, "marketplace_commercial_documents", cols)

    op.create_table(
        "marketplace_integration_connections",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("connection_type", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="draft", nullable=False),
        sa.Column("base_url", sa.String(length=1024), nullable=True),
        sa.Column("mcp_server_url", sa.String(length=1024), nullable=True),
        sa.Column("auth_type", sa.String(length=64), nullable=True),
        sa.Column("secret_ref", sa.String(length=240), nullable=True),
        sa.Column("allowed_scopes", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("config", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["user_profiles.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    for idx, cols in {
        "ix_marketplace_integration_connections_team_id": ["team_id"],
        "ix_marketplace_integration_connections_created_by_user_id": ["created_by_user_id"],
        "ix_marketplace_integration_connections_connection_type": ["connection_type"],
        "ix_marketplace_integration_connections_status": ["status"],
    }.items():
        op.create_index(idx, "marketplace_integration_connections", cols)

    op.create_table(
        "rfq_schedule_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("rfq_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reminder_offsets", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("email_recipients", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="scheduled", nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["rfq_id"], ["rfqs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    for idx, cols in {
        "ix_rfq_schedule_events_rfq_id": ["rfq_id"],
        "ix_rfq_schedule_events_event_type": ["event_type"],
        "ix_rfq_schedule_events_due_at": ["due_at"],
        "ix_rfq_schedule_events_status": ["status"],
    }.items():
        op.create_index(idx, "rfq_schedule_events", cols)


def downgrade() -> None:
    for table in ["rfq_schedule_events", "marketplace_integration_connections", "marketplace_commercial_documents"]:
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
    for col in ["schedule", "technical_specs", "workflow_process", "decision_makers", "timeline_summary", "project_description"]:
        if col in _columns("rfqs"):
            op.drop_column("rfqs", col)
    for col in ["po_preferences", "procurement_workflow", "decision_makers"]:
        if col in _columns("buyer_profiles"):
            op.drop_column("buyer_profiles", col)
