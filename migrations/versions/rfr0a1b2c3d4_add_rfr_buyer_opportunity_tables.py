"""Add rfr_ buyer-opportunity tables (buyer_opportunity_spec §4, Phase 1).

Additive only: six new tables, no change to any existing table.

Parented on mhd0a1b2c3d4, the single head already on main. That head merged
aopp0a1b2c3d4 and djrt0a1b2c3d4, so a database at mhd upgrades here by
creating these tables only. This revision does not ALTER robot_jobs.

Revision ID: rfr0a1b2c3d4
Revises: mhd0a1b2c3d4
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "rfr0a1b2c3d4"
down_revision: Union[str, Sequence[str], None] = "mhd0a1b2c3d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

WORKFLOW_STATUSES = ("unknown", "open", "exploring", "piloting", "committed")


def _json():
    return postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite")


def _now():
    return sa.text("CURRENT_TIMESTAMP")


def _in(column: str, values: Sequence[str]) -> str:
    return f"{column} IN ({', '.join(repr(v) for v in values)})"


def upgrade() -> None:
    op.create_table(
        "rfr_robot_products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_url", sa.String(2048), nullable=False),
        sa.Column("company_name", sa.String(255), nullable=True),
        sa.Column("product_name", sa.String(255), nullable=False),
        sa.Column("page_type", sa.String(64), nullable=True),
        sa.Column("offering_type", sa.String(64), nullable=True),
        sa.Column("form", sa.String(64), nullable=True),
        sa.Column("primary_class", sa.String(64), nullable=True),
        sa.Column("primary_function", sa.String(64), nullable=True),
        sa.Column("secondary_functions", _json(), server_default="[]", nullable=False),
        sa.Column("industries", _json(), server_default="[]", nullable=False),
        sa.Column("evidence", _json(), server_default="{}", nullable=False),
        sa.Column("unsupported_facts", _json(), server_default="[]", nullable=False),
        sa.Column("prompt_version", sa.String(16), nullable=False),
        sa.Column("taxonomy_version", sa.String(16), nullable=False),
        sa.Column("extracted_at", sa.DateTime(timezone=True), server_default=_now(), nullable=False),
    )
    op.create_index(
        "ix_rfr_robot_products_current", "rfr_robot_products", ["source_url", "product_name", "extracted_at"]
    )

    op.create_table(
        "rfr_buyers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="SET NULL"), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("name_normalized", sa.String(255), nullable=False),
        sa.Column("website_domain", sa.String(255), nullable=True),
        sa.Column("hq_city", sa.String(128), nullable=True),
        sa.Column("hq_state", sa.String(64), nullable=True),
        sa.Column("hq_country", sa.String(64), nullable=True),
        sa.Column("priority", sa.String(1), nullable=True),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("is_robot_maker", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=_now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=_now(), nullable=False),
        sa.CheckConstraint("priority IS NULL OR " + _in("priority", ("A", "B", "C")), name="ck_rfr_buyers_priority"),
    )
    op.create_index("ix_rfr_buyers_company_id", "rfr_buyers", ["company_id"])
    op.create_index(
        "ux_rfr_buyers_website_domain", "rfr_buyers", ["website_domain"], unique=True,
        postgresql_where=sa.text("website_domain IS NOT NULL"),
        sqlite_where=sa.text("website_domain IS NOT NULL"),
    )
    op.create_index(
        "ux_rfr_buyers_name_normalized", "rfr_buyers", ["name_normalized"], unique=True,
        postgresql_where=sa.text("website_domain IS NULL"),
        sqlite_where=sa.text("website_domain IS NULL"),
    )

    op.create_table(
        "rfr_buyer_industries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("buyer_id", sa.Integer(), sa.ForeignKey("rfr_buyers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("industry", sa.String(64), nullable=False),
        sa.Column("confidence", sa.Float(), server_default="1", nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("source_url", sa.String(2048), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=_now(), nullable=False),
        sa.UniqueConstraint("buyer_id", "industry", "source", name="uq_rfr_buyer_industries"),
        sa.CheckConstraint("confidence >= 0 AND confidence <= 1", name="ck_rfr_buyer_industries_confidence"),
    )

    op.create_table(
        "rfr_workflows",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("buyer_id", sa.Integer(), sa.ForeignKey("rfr_buyers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("workflow", sa.String(64), nullable=False),
        sa.Column("status", sa.String(16), server_default="unknown", nullable=False),
        sa.Column("status_source_url", sa.String(2048), nullable=True),
        sa.Column("status_note", sa.Text(), nullable=True),
        sa.Column("committed_vendor", sa.String(255), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=_now(), nullable=False),
        sa.UniqueConstraint("buyer_id", "workflow", name="uq_rfr_workflows"),
        sa.CheckConstraint(_in("status", WORKFLOW_STATUSES), name="ck_rfr_workflows_status"),
    )

    op.create_table(
        "rfr_signals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("buyer_id", sa.Integer(), sa.ForeignKey("rfr_buyers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("workflow", sa.String(64), nullable=True),
        sa.Column("signal_type", sa.String(32), nullable=False),
        sa.Column("tier", sa.String(1), nullable=True),
        sa.Column("intent_strength", sa.String(16), nullable=True),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("evidence_text", sa.Text(), nullable=True),
        sa.Column("source_url", sa.String(2048), nullable=True),
        sa.Column("source_feed", sa.String(64), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=_now(), nullable=False),
        sa.CheckConstraint("tier IS NULL OR " + _in("tier", ("A", "B", "C", "D", "E")), name="ck_rfr_signals_tier"),
        sa.CheckConstraint(
            "intent_strength IS NULL OR " + _in("intent_strength", ("explicit", "implicit")),
            name="ck_rfr_signals_intent_strength",
        ),
        sa.CheckConstraint("source_url IS NOT NULL OR source_feed = 'bob_seed'", name="ck_rfr_signals_source"),
    )
    op.create_index("ix_rfr_signals_buyer_workflow", "rfr_signals", ["buyer_id", "workflow"])
    # One source can yield one signal per workflow (spec §5a), so workflow is part of the key.
    op.create_index(
        "ux_rfr_signals_dedupe", "rfr_signals",
        ["buyer_id", "signal_type", sa.text("coalesce(source_url, '')"), sa.text("coalesce(workflow, '')")],
        unique=True,
    )

    op.create_table(
        "rfr_opportunities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("buyer_id", sa.Integer(), sa.ForeignKey("rfr_buyers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("workflow", sa.String(64), nullable=False),
        sa.Column("score", sa.Float(), server_default="0", nullable=False),
        sa.Column("top_tier", sa.String(1), nullable=True),
        sa.Column("reasons", _json(), server_default="[]", nullable=False),
        sa.Column("matched_robot_product_ids", _json(), server_default="[]", nullable=False),
        sa.Column("computed_at", sa.DateTime(timezone=True), server_default=_now(), nullable=False),
        sa.UniqueConstraint("buyer_id", "workflow", name="uq_rfr_opportunities"),
    )


def downgrade() -> None:
    op.drop_table("rfr_opportunities")
    op.drop_index("ux_rfr_signals_dedupe", table_name="rfr_signals")
    op.drop_index("ix_rfr_signals_buyer_workflow", table_name="rfr_signals")
    op.drop_table("rfr_signals")
    op.drop_table("rfr_workflows")
    op.drop_table("rfr_buyer_industries")
    op.drop_index("ux_rfr_buyers_name_normalized", table_name="rfr_buyers")
    op.drop_index("ux_rfr_buyers_website_domain", table_name="rfr_buyers")
    op.drop_index("ix_rfr_buyers_company_id", table_name="rfr_buyers")
    op.drop_table("rfr_buyers")
    op.drop_index("ix_rfr_robot_products_current", table_name="rfr_robot_products")
    op.drop_table("rfr_robot_products")
