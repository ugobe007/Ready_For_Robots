"""Add marketplace organization, assets, RFQs, and proposals.

Revision ID: a6b7c8d9e0f1
Revises: f5a6b7c8d9e0
Create Date: 2026-05-10
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

revision: str = "a6b7c8d9e0f1"
down_revision: Union[str, Sequence[str], None] = "f5a6b7c8d9e0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _tables() -> set[str]:
    return set(inspect(op.get_bind()).get_table_names())


def _index_names(table: str) -> set[str]:
    insp = inspect(op.get_bind())
    if table not in insp.get_table_names():
        return set()
    return {i["name"] for i in insp.get_indexes(table)}


def upgrade() -> None:
    tables = _tables()

    if "organization_profiles" not in tables:
        op.create_table(
            "organization_profiles",
            sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
            sa.Column("team_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("organization_type", sa.String(length=32), server_default="vendor", nullable=False),
            sa.Column("display_name", sa.String(length=240), nullable=True),
            sa.Column("website", sa.String(length=512), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("automation_needs", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
            sa.Column("scout_preferences", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("team_id", name="uq_organization_profiles_team_id"),
        )
    if "ix_organization_profiles_team_id" not in _index_names("organization_profiles"):
        op.create_index("ix_organization_profiles_team_id", "organization_profiles", ["team_id"], unique=False)

    if "vendor_profiles" not in tables:
        op.create_table(
            "vendor_profiles",
            sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
            sa.Column("team_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("robot_categories", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
            sa.Column("target_industries", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
            sa.Column("service_regions", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
            sa.Column("qualification_rules", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("team_id", name="uq_vendor_profiles_team_id"),
        )
    if "ix_vendor_profiles_team_id" not in _index_names("vendor_profiles"):
        op.create_index("ix_vendor_profiles_team_id", "vendor_profiles", ["team_id"], unique=False)

    if "buyer_profiles" not in tables:
        op.create_table(
            "buyer_profiles",
            sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
            sa.Column("team_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("procurement_categories", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
            sa.Column("facility_types", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
            sa.Column("buying_process", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("team_id", name="uq_buyer_profiles_team_id"),
        )
    if "ix_buyer_profiles_team_id" not in _index_names("buyer_profiles"):
        op.create_index("ix_buyer_profiles_team_id", "buyer_profiles", ["team_id"], unique=False)

    if "organization_assets" not in tables:
        op.create_table(
            "organization_assets",
            sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
            sa.Column("team_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("uploaded_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("asset_type", sa.String(length=64), nullable=False),
            sa.Column("filename", sa.String(length=512), nullable=False),
            sa.Column("mime_type", sa.String(length=160), nullable=True),
            sa.Column("storage_path", sa.String(length=1024), nullable=True),
            sa.Column("visibility", sa.String(length=32), server_default="private", nullable=False),
            sa.Column("asset_metadata", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["uploaded_by_user_id"], ["user_profiles.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )
    if "ix_organization_assets_team_id" not in _index_names("organization_assets"):
        op.create_index("ix_organization_assets_team_id", "organization_assets", ["team_id"], unique=False)
    if "ix_organization_assets_uploaded_by_user_id" not in _index_names("organization_assets"):
        op.create_index("ix_organization_assets_uploaded_by_user_id", "organization_assets", ["uploaded_by_user_id"], unique=False)

    if "rfqs" not in tables:
        op.create_table(
            "rfqs",
            sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
            sa.Column("buyer_team_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("title", sa.String(length=240), nullable=False),
            sa.Column("summary", sa.Text(), nullable=True),
            sa.Column("automation_category", sa.String(length=120), nullable=True),
            sa.Column("status", sa.String(length=32), server_default="draft", nullable=False),
            sa.Column("budget_min", sa.Numeric(18, 2), nullable=True),
            sa.Column("budget_max", sa.Numeric(18, 2), nullable=True),
            sa.Column("currency", sa.String(length=8), server_default="USD", nullable=False),
            sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("evaluation_criteria", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
            sa.Column("scout_summary", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["buyer_team_id"], ["teams.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["created_by_user_id"], ["user_profiles.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )
    for idx, cols in {
        "ix_rfqs_buyer_team_id": ["buyer_team_id"],
        "ix_rfqs_created_by_user_id": ["created_by_user_id"],
        "ix_rfqs_status": ["status"],
        "ix_rfqs_due_at": ["due_at"],
    }.items():
        if idx not in _index_names("rfqs"):
            op.create_index(idx, "rfqs", cols, unique=False)

    if "rfq_requirements" not in tables:
        op.create_table(
            "rfq_requirements",
            sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
            sa.Column("rfq_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("requirement_type", sa.String(length=64), server_default="general", nullable=False),
            sa.Column("body", sa.Text(), nullable=False),
            sa.Column("priority", sa.String(length=32), server_default="required", nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["rfq_id"], ["rfqs.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
    if "ix_rfq_requirements_rfq_id" not in _index_names("rfq_requirements"):
        op.create_index("ix_rfq_requirements_rfq_id", "rfq_requirements", ["rfq_id"], unique=False)

    if "rfq_invitations" not in tables:
        op.create_table(
            "rfq_invitations",
            sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
            sa.Column("rfq_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("vendor_team_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("status", sa.String(length=32), server_default="invited", nullable=False),
            sa.Column("scout_match_score", sa.Numeric(5, 2), nullable=True),
            sa.Column("scout_reason", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["rfq_id"], ["rfqs.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["vendor_team_id"], ["teams.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("rfq_id", "vendor_team_id", name="uq_rfq_invitations_rfq_vendor"),
        )
    if "ix_rfq_invitations_rfq_id" not in _index_names("rfq_invitations"):
        op.create_index("ix_rfq_invitations_rfq_id", "rfq_invitations", ["rfq_id"], unique=False)
    if "ix_rfq_invitations_vendor_team_id" not in _index_names("rfq_invitations"):
        op.create_index("ix_rfq_invitations_vendor_team_id", "rfq_invitations", ["vendor_team_id"], unique=False)

    if "rfq_proposals" not in tables:
        op.create_table(
            "rfq_proposals",
            sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
            sa.Column("rfq_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("vendor_team_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("submitted_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("status", sa.String(length=32), server_default="draft", nullable=False),
            sa.Column("proposal_title", sa.String(length=240), nullable=True),
            sa.Column("proposal_summary", sa.Text(), nullable=True),
            sa.Column("price_estimate", sa.Numeric(18, 2), nullable=True),
            sa.Column("currency", sa.String(length=8), server_default="USD", nullable=False),
            sa.Column("asset_ids", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
            sa.Column("scout_response_plan", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["rfq_id"], ["rfqs.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["vendor_team_id"], ["teams.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["submitted_by_user_id"], ["user_profiles.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("rfq_id", "vendor_team_id", name="uq_rfq_proposals_rfq_vendor"),
        )
    for idx, cols in {
        "ix_rfq_proposals_rfq_id": ["rfq_id"],
        "ix_rfq_proposals_vendor_team_id": ["vendor_team_id"],
        "ix_rfq_proposals_submitted_by_user_id": ["submitted_by_user_id"],
    }.items():
        if idx not in _index_names("rfq_proposals"):
            op.create_index(idx, "rfq_proposals", cols, unique=False)


def downgrade() -> None:
    for table in [
        "rfq_proposals",
        "rfq_invitations",
        "rfq_requirements",
        "rfqs",
        "organization_assets",
        "buyer_profiles",
        "vendor_profiles",
        "organization_profiles",
    ]:
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
