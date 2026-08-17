"""
Add work_units / work_matches + deployment evidence tables.

Revision ID: z0a1b2c3d4e5
Revises: y9z0a1b2c3d4
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "z0a1b2c3d4e5"
down_revision: Union[str, Sequence[str], None] = "y9z0a1b2c3d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _json():
    return postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite")


def _uuid():
    return postgresql.UUID(as_uuid=True).with_variant(sa.String(36), "sqlite")


def upgrade() -> None:
    op.create_table(
        "work_units",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("work_unit_id", sa.String(120), nullable=False),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="SET NULL"), nullable=True),
        sa.Column("facility_id", _uuid(), sa.ForeignKey("facilities.id", ondelete="SET NULL"), nullable=True),
        sa.Column("workflow_family", sa.String(64), server_default="unknown", nullable=False),
        sa.Column("task", sa.String(480), nullable=True),
        sa.Column("object", sa.String(120), nullable=True),
        sa.Column("origin", sa.String(120), nullable=True),
        sa.Column("destination", sa.String(120), nullable=True),
        sa.Column("action_chain", _json(), server_default="[]", nullable=False),
        sa.Column("primitive_evidence", _json(), server_default="[]", nullable=False),
        sa.Column("payload_kg_hint", sa.Float(), nullable=True),
        sa.Column("shift_hint", sa.String(64), nullable=True),
        sa.Column("job_title", sa.String(240), nullable=True),
        sa.Column("confidence", sa.Float(), server_default="0", nullable=False),
        sa.Column("truth_state", sa.String(32), server_default="SIGNAL_INFERRED", nullable=False),
        sa.Column("source", sa.String(64), server_default="work_unit_reconstruct_v1", nullable=False),
        sa.Column("source_text_hash", sa.String(64), nullable=True),
        sa.Column("raw_excerpt", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_work_units_work_unit_id", "work_units", ["work_unit_id"], unique=True)
    op.create_index("ix_work_units_company_id", "work_units", ["company_id"])
    op.create_index("ix_work_units_workflow_family", "work_units", ["workflow_family"])
    op.create_index("ix_work_units_source_text_hash", "work_units", ["source_text_hash"])

    op.create_table(
        "work_matches",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("work_unit_pk", _uuid(), sa.ForeignKey("work_units.id", ondelete="CASCADE"), nullable=False),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("manufacturer_id", sa.String(64), nullable=True),
        sa.Column("manufacturer_name", sa.String(240), nullable=True),
        sa.Column("match_score", sa.Float(), server_default="0", nullable=False),
        sa.Column("work_match", sa.Float(), nullable=True),
        sa.Column("work_match_label", sa.String(64), nullable=True),
        sa.Column("match_mode", sa.String(64), nullable=True),
        sa.Column("hard_blockers", _json(), server_default="[]", nullable=False),
        sa.Column("matched_primitives", _json(), server_default="[]", nullable=False),
        sa.Column("missing_primitives", _json(), server_default="[]", nullable=False),
        sa.Column("required_primitives", _json(), server_default="[]", nullable=False),
        sa.Column("supported_primitives", _json(), server_default="[]", nullable=False),
        sa.Column("truth_state", sa.String(32), server_default="SIGNAL_INFERRED", nullable=False),
        sa.Column("source", sa.String(64), server_default="market_graph_loop", nullable=False),
        sa.Column("why", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.UniqueConstraint("company_id", "manufacturer_id", name="uq_work_match_company_manufacturer"),
    )
    op.create_index("ix_work_matches_work_unit_pk", "work_matches", ["work_unit_pk"])
    op.create_index("ix_work_matches_company_id", "work_matches", ["company_id"])
    op.create_index("ix_work_matches_manufacturer_id", "work_matches", ["manufacturer_id"])

    op.create_table(
        "deployment_sources",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("source_type", sa.String(64), server_default="public_news", nullable=False),
        sa.Column("source_tier", sa.String(8), server_default="F", nullable=False),
        sa.Column("title", sa.String(480), nullable=True),
        sa.Column("domain", sa.String(240), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("raw_excerpt", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.UniqueConstraint("url", name="uq_deployment_sources_url"),
    )
    op.create_index("ix_deployment_sources_source_type", "deployment_sources", ["source_type"])
    op.create_index("ix_deployment_sources_source_tier", "deployment_sources", ["source_tier"])
    op.create_index("ix_deployment_sources_domain", "deployment_sources", ["domain"])

    op.create_table(
        "deployment_events",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("deployment_id", sa.String(64), nullable=False),
        sa.Column("vendor_name", sa.String(240), nullable=True),
        sa.Column("manufacturer_id", sa.String(64), nullable=True),
        sa.Column("robot_model", sa.String(240), nullable=True),
        sa.Column("customer_name", sa.String(240), nullable=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="SET NULL"), nullable=True),
        sa.Column("facility_name", sa.String(240), nullable=True),
        sa.Column("facility_id", _uuid(), sa.ForeignKey("facilities.id", ondelete="SET NULL"), nullable=True),
        sa.Column("industry", sa.String(120), nullable=True),
        sa.Column("work_type", sa.String(120), nullable=True),
        sa.Column("workflow", _json(), server_default="{}", nullable=False),
        sa.Column("deployment_stage", sa.String(64), server_default="UNKNOWN", nullable=False),
        sa.Column("evidence_level", sa.String(8), server_default="F", nullable=False),
        sa.Column("confidence", sa.Float(), server_default="0", nullable=False),
        sa.Column("work_unit_id", sa.String(120), nullable=True),
        sa.Column("performed_primitives", _json(), server_default="[]", nullable=False),
        sa.Column("robots_announced", sa.Integer(), nullable=True),
        sa.Column("robots_committed", sa.Integer(), nullable=True),
        sa.Column("robots_pilot", sa.Integer(), nullable=True),
        sa.Column("robots_live", sa.Integer(), nullable=True),
        sa.Column("robots_verified", sa.Integer(), nullable=True),
        sa.Column("sites_announced", sa.Integer(), nullable=True),
        sa.Column("sites_live", sa.Integer(), nullable=True),
        sa.Column("sites_verified", sa.Integer(), nullable=True),
        sa.Column("primary_source_id", _uuid(), sa.ForeignKey("deployment_sources.id", ondelete="SET NULL"), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_deployment_events_deployment_id", "deployment_events", ["deployment_id"], unique=True)
    op.create_index("ix_deployment_events_vendor_name", "deployment_events", ["vendor_name"])
    op.create_index("ix_deployment_events_robot_model", "deployment_events", ["robot_model"])
    op.create_index("ix_deployment_events_customer_name", "deployment_events", ["customer_name"])
    op.create_index("ix_deployment_events_deployment_stage", "deployment_events", ["deployment_stage"])
    op.create_index("ix_deployment_events_evidence_level", "deployment_events", ["evidence_level"])
    op.create_index("ix_deployment_events_work_unit_id", "deployment_events", ["work_unit_id"])

    op.create_table(
        "deployment_evidence",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("deployment_event_id", _uuid(), sa.ForeignKey("deployment_events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_id", _uuid(), sa.ForeignKey("deployment_sources.id", ondelete="CASCADE"), nullable=False),
        sa.Column("claim_text", sa.Text(), nullable=False),
        sa.Column("evidence_level", sa.String(8), server_default="F", nullable=False),
        sa.Column("confidence", sa.Float(), server_default="0", nullable=False),
        sa.Column("supports_stage", sa.String(64), nullable=True),
        sa.Column("extracted_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.UniqueConstraint("deployment_event_id", "source_id", "claim_text", name="uq_deployment_evidence_claim"),
    )
    op.create_index("ix_deployment_evidence_event", "deployment_evidence", ["deployment_event_id"])

    op.create_table(
        "deployment_metrics",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("deployment_event_id", _uuid(), sa.ForeignKey("deployment_events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_id", _uuid(), sa.ForeignKey("deployment_sources.id", ondelete="SET NULL"), nullable=True),
        sa.Column("metric_key", sa.String(64), nullable=False),
        sa.Column("metric_value_numeric", sa.Float(), nullable=True),
        sa.Column("metric_value_text", sa.String(240), nullable=True),
        sa.Column("unit", sa.String(32), nullable=True),
        sa.Column("confidence", sa.Float(), server_default="0.5", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_deployment_metrics_event", "deployment_metrics", ["deployment_event_id"])
    op.create_index("ix_deployment_metrics_key", "deployment_metrics", ["metric_key"])


def downgrade() -> None:
    op.drop_table("deployment_metrics")
    op.drop_table("deployment_evidence")
    op.drop_table("deployment_events")
    op.drop_table("deployment_sources")
    op.drop_table("work_matches")
    op.drop_table("work_units")
