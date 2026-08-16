"""
Thin universal core for robot-directed discovery.

Revision ID: rdd0a1b2c3d4
Revises: a0b1c2d3e4f5

Semantics:
  robot_jobs.discovery_profile_id = provenance (who found it), not ownership
  robot_job_matches = which robots can perform the job
  discovered_via_capability_family = search lens, not exclusive family of the work
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "rdd0a1b2c3d4"
down_revision: Union[str, Sequence[str], None] = "a0b1c2d3e4f5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _json():
    return postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite")


def _uuid():
    return postgresql.UUID(as_uuid=True).with_variant(sa.String(36), "sqlite")


def upgrade() -> None:
    op.create_table(
        "robot_capability_profiles",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("profile_key", sa.String(120), nullable=False),
        sa.Column("display_name", sa.String(240), nullable=False),
        sa.Column("manufacturer", sa.String(120), nullable=True),
        sa.Column("product_url", sa.String(512), nullable=True),
        sa.Column("capability_family", sa.String(64), nullable=False),
        sa.Column("can_actions", _json(), server_default="[]", nullable=False),
        sa.Column("cannot_or_weak", _json(), server_default="[]", nullable=False),
        sa.Column("search_vocabulary", _json(), server_default="{}", nullable=False),
        sa.Column("envelope_path", sa.String(512), nullable=True),
        sa.Column("source", sa.String(64), server_default="envelope_v1", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_rcp_profile_key", "robot_capability_profiles", ["profile_key"], unique=True)
    op.create_index("ix_rcp_capability_family", "robot_capability_profiles", ["capability_family"])

    op.create_table(
        "work_claims",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("claim_key", sa.String(160), nullable=False),
        sa.Column("company_name", sa.String(240), nullable=False),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="SET NULL"), nullable=True),
        sa.Column("locality", sa.String(240), nullable=True),
        sa.Column("worksite_label", sa.String(240), nullable=True),
        sa.Column("observed_workflow", sa.Text(), nullable=False),
        sa.Column("operating_context", sa.String(64), nullable=True),
        sa.Column("existence_confidence", sa.Float(), server_default="0.5", nullable=False),
        sa.Column("status", sa.String(32), server_default="watching", nullable=False),
        sa.Column("capability_family_hint", sa.String(64), nullable=True),
        sa.Column("source_run", sa.String(120), nullable=True),
        sa.Column("extras", _json(), server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_work_claims_claim_key", "work_claims", ["claim_key"], unique=True)
    op.create_index("ix_work_claims_company_name", "work_claims", ["company_name"])
    op.create_index("ix_work_claims_company_id", "work_claims", ["company_id"])
    op.create_index("ix_work_claims_status", "work_claims", ["status"])
    op.create_index("ix_work_claims_operating_context", "work_claims", ["operating_context"])

    op.create_table(
        "robot_jobs",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("job_key", sa.String(160), nullable=False),
        sa.Column("work_claim_id", _uuid(), sa.ForeignKey("work_claims.id", ondelete="SET NULL"), nullable=True),
        sa.Column(
            "discovery_profile_id",
            _uuid(),
            sa.ForeignKey("robot_capability_profiles.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("company_name", sa.String(240), nullable=False),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="SET NULL"), nullable=True),
        sa.Column("locality", sa.String(240), nullable=True),
        sa.Column("worksite_label", sa.String(240), nullable=True),
        sa.Column("action", sa.String(120), nullable=False),
        sa.Column("target", sa.String(120), nullable=True),
        sa.Column("operating_context", sa.String(64), nullable=True),
        sa.Column("robot_compatible_task", sa.Text(), nullable=False),
        sa.Column("observed_workflow", sa.Text(), nullable=True),
        sa.Column("why_job", sa.Text(), nullable=True),
        sa.Column("existence_confidence", sa.Float(), server_default="0.7", nullable=False),
        sa.Column("definition_completeness", sa.Float(), server_default="0.4", nullable=False),
        sa.Column("automation_state", sa.String(64), server_default="unknown", nullable=False),
        sa.Column("commercial_availability", sa.String(64), server_default="unknown", nullable=False),
        sa.Column("investigate_status", sa.String(16), server_default="weak", nullable=False),
        sa.Column("promotion_class", sa.String(32), server_default="DERIVED", nullable=False),
        sa.Column("evidence_grade", sa.String(8), server_default="E2", nullable=False),
        sa.Column("discovered_via_capability_family", sa.String(64), nullable=True),
        sa.Column("requirements", _json(), server_default="{}", nullable=False),
        sa.Column("unknowns", _json(), server_default="[]", nullable=False),
        sa.Column("source_run", sa.String(120), nullable=True),
        sa.Column("provenance", _json(), server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_robot_jobs_job_key", "robot_jobs", ["job_key"], unique=True)
    op.create_index("ix_robot_jobs_company_name", "robot_jobs", ["company_name"])
    op.create_index("ix_robot_jobs_company_id", "robot_jobs", ["company_id"])
    op.create_index("ix_robot_jobs_work_claim_id", "robot_jobs", ["work_claim_id"])
    op.create_index("ix_robot_jobs_discovery_profile_id", "robot_jobs", ["discovery_profile_id"])
    op.create_index("ix_robot_jobs_investigate", "robot_jobs", ["investigate_status"])
    op.create_index("ix_robot_jobs_discovered_via_family", "robot_jobs", ["discovered_via_capability_family"])
    op.create_index("ix_robot_jobs_operating_context", "robot_jobs", ["operating_context"])

    op.create_table(
        "job_evidence",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("work_claim_id", _uuid(), sa.ForeignKey("work_claims.id", ondelete="CASCADE"), nullable=True),
        sa.Column("robot_job_id", _uuid(), sa.ForeignKey("robot_jobs.id", ondelete="CASCADE"), nullable=True),
        sa.Column("evidence_grade", sa.String(8), server_default="E3", nullable=False),
        sa.Column("source_url", sa.String(1024), nullable=True),
        sa.Column("source_title", sa.String(480), nullable=True),
        sa.Column("excerpt", sa.Text(), nullable=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("extras", _json(), server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint(
            "work_claim_id IS NOT NULL OR robot_job_id IS NOT NULL",
            name="ck_job_evidence_has_parent",
        ),
    )
    op.create_index("ix_job_evidence_work_claim_id", "job_evidence", ["work_claim_id"])
    op.create_index("ix_job_evidence_robot_job_id", "job_evidence", ["robot_job_id"])

    op.create_table(
        "automation_interpretations",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("work_claim_id", _uuid(), sa.ForeignKey("work_claims.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "profile_id",
            _uuid(),
            sa.ForeignKey("robot_capability_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("human_portion", sa.Text(), nullable=True),
        sa.Column("robot_portion", sa.Text(), nullable=True),
        sa.Column("action_class", sa.String(32), server_default="SPECULATIVE", nullable=False),
        sa.Column("evidence_grade", sa.String(8), server_default="E4", nullable=False),
        sa.Column("transformation_confidence", sa.String(8), server_default="L", nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.UniqueConstraint("work_claim_id", "profile_id", name="uq_automation_interp_claim_profile"),
    )
    op.create_index("ix_auto_interp_work_claim_id", "automation_interpretations", ["work_claim_id"])
    op.create_index("ix_auto_interp_profile_id", "automation_interpretations", ["profile_id"])

    op.create_table(
        "robot_job_matches",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("robot_job_id", _uuid(), sa.ForeignKey("robot_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "profile_id",
            _uuid(),
            sa.ForeignKey("robot_capability_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("fit", sa.String(8), server_default="M", nullable=False),
        sa.Column("match_score", sa.Float(), server_default="0.5", nullable=False),
        sa.Column("hard_blockers", _json(), server_default="[]", nullable=False),
        sa.Column("why", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.UniqueConstraint("robot_job_id", "profile_id", name="uq_robot_job_match_job_profile"),
    )
    op.create_index("ix_robot_job_matches_job_id", "robot_job_matches", ["robot_job_id"])
    op.create_index("ix_robot_job_matches_profile_id", "robot_job_matches", ["profile_id"])


def downgrade() -> None:
    op.drop_table("robot_job_matches")
    op.drop_table("automation_interpretations")
    op.drop_table("job_evidence")
    op.drop_table("robot_jobs")
    op.drop_table("work_claims")
    op.drop_table("robot_capability_profiles")
