"""Slice 1 tables: robot analyses, evidence claims, profile versions, capabilities.

Revision ID: v6w7x8y9z0a1
Revises: u5v6w7x8y9z0
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "v6w7x8y9z0a1"
down_revision: Union[str, Sequence[str], None] = "u5v6w7x8y9z0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _uuid():
    return postgresql.UUID(as_uuid=True).with_variant(sa.String(36), "sqlite")


def _json():
    return postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite")


def upgrade() -> None:
    op.create_table(
        "evidence_claims",
        sa.Column("id", _uuid(), primary_key=True, nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.String(length=80), nullable=False),
        sa.Column("field_path", sa.String(length=160), nullable=False),
        sa.Column("value", _json(), nullable=True),
        sa.Column("truth_state", sa.String(length=32), nullable=False),
        sa.Column("source_type", sa.String(length=64), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("source_id", sa.String(length=120), nullable=True),
        sa.Column("excerpt", sa.Text(), nullable=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("confidence", sa.Float(), server_default="0", nullable=False),
        sa.Column("supersedes_claim_id", _uuid(), nullable=True),
        sa.Column("recorded_by_user_id", _uuid(), nullable=True),
        sa.ForeignKeyConstraint(["supersedes_claim_id"], ["evidence_claims.id"]),
    )
    op.create_index("ix_evidence_claims_entity", "evidence_claims", ["entity_type", "entity_id"])
    op.create_index("ix_evidence_claims_field", "evidence_claims", ["field_path"])
    op.create_index("ix_evidence_claims_source_id", "evidence_claims", ["source_id"])

    op.create_table(
        "robot_analyses",
        sa.Column("id", _uuid(), primary_key=True, nullable=False),
        sa.Column("analysis_token", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=64), server_default="queued", nullable=False),
        sa.Column("progress", sa.Integer(), server_default="0", nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("retryable", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("warnings", _json(), server_default="[]", nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("normalized_url", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("robot_id", sa.Integer(), nullable=True),
        sa.Column("draft_profile", _json(), nullable=True),
        sa.Column("profile_etag", sa.String(length=64), nullable=True),
        sa.Column("confirmed_profile_version_id", _uuid(), nullable=True),
        sa.Column("opportunity_search_id", _uuid(), nullable=True),
        sa.Column("requester_scope", sa.String(length=120), nullable=True),
        sa.Column("created_by_user_id", _uuid(), nullable=True),
        sa.Column("raw_fetch", _json(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["robot_id"], ["robots.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("analysis_token"),
    )
    op.create_index("ix_robot_analyses_status", "robot_analyses", ["status"])
    op.create_index("ix_robot_analyses_normalized_url", "robot_analyses", ["normalized_url"])

    op.create_table(
        "robot_profile_versions",
        sa.Column("id", _uuid(), primary_key=True, nullable=False),
        sa.Column("robot_id", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("manufacturer", sa.String(length=240), nullable=True),
        sa.Column("model", sa.String(length=240), nullable=True),
        sa.Column("category", sa.String(length=64), nullable=True),
        sa.Column("work_envelope", _json(), server_default="[]", nullable=False),
        sa.Column("physical_capabilities", _json(), server_default="{}", nullable=False),
        sa.Column("commercial_status", sa.String(length=64), nullable=True),
        sa.Column("service_geography", _json(), nullable=True),
        sa.Column("verification_state", sa.String(length=32), server_default="inferred", nullable=False),
        sa.Column("confidence", sa.Float(), server_default="0", nullable=False),
        sa.Column("created_by_user_id", _uuid(), nullable=True),
        sa.Column("supersedes_version_id", _uuid(), nullable=True),
        sa.Column("analysis_id", _uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["robot_id"], ["robots.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["supersedes_version_id"], ["robot_profile_versions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["analysis_id"], ["robot_analyses.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("robot_id", "version", name="uq_robot_profile_version"),
    )
    op.create_index("ix_robot_profile_versions_robot_id", "robot_profile_versions", ["robot_id"])
    op.create_index("ix_robot_profile_versions_category", "robot_profile_versions", ["category"])

    op.create_table(
        "robot_capabilities",
        sa.Column("id", _uuid(), primary_key=True, nullable=False),
        sa.Column("robot_profile_version_id", _uuid(), nullable=False),
        sa.Column("capability_key", sa.String(length=120), nullable=False),
        sa.Column("operator", sa.String(length=16), nullable=True),
        sa.Column("numeric_value", sa.Float(), nullable=True),
        sa.Column("text_value", sa.Text(), nullable=True),
        sa.Column("unit", sa.String(length=32), nullable=True),
        sa.Column("constraints", _json(), server_default="{}", nullable=False),
        sa.Column("truth_state", sa.String(length=32), nullable=False),
        sa.Column("confidence", sa.Float(), server_default="0", nullable=False),
        sa.Column("claim_ids", _json(), server_default="[]", nullable=False),
        sa.ForeignKeyConstraint(["robot_profile_version_id"], ["robot_profile_versions.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("robot_profile_version_id", "capability_key", name="uq_robot_capability_key"),
    )
    op.create_index(
        "ix_robot_capabilities_profile_version_id",
        "robot_capabilities",
        ["robot_profile_version_id"],
    )


def downgrade() -> None:
    op.drop_table("robot_capabilities")
    op.drop_table("robot_profile_versions")
    op.drop_table("robot_analyses")
    op.drop_table("evidence_claims")
