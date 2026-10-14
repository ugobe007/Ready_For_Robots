"""Core table definitions for the rfr_ buyer-opportunity tables.

Mirrors migration rfr0a1b2c3d4. Kept off app.database.Base on purpose: scripts
that call Base.metadata.create_all must never create these tables outside the
migration. tests/test_rfr_phase1.py checks the two stay identical.
"""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

metadata = sa.MetaData()


def _json():
    return postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite")


def _now():
    return sa.text("CURRENT_TIMESTAMP")


rfr_robot_products = sa.Table(
    "rfr_robot_products", metadata,
    sa.Column("id", sa.Integer(), primary_key=True),
    sa.Column("source_url", sa.String(2048), nullable=False),
    sa.Column("company_name", sa.String(255)),
    sa.Column("product_name", sa.String(255), nullable=False),
    sa.Column("page_type", sa.String(64)),
    sa.Column("offering_type", sa.String(64)),
    sa.Column("form", sa.String(64)),
    sa.Column("primary_class", sa.String(64)),
    sa.Column("primary_function", sa.String(64)),
    sa.Column("secondary_functions", _json(), server_default="[]", nullable=False),
    sa.Column("industries", _json(), server_default="[]", nullable=False),
    sa.Column("evidence", _json(), server_default="{}", nullable=False),
    sa.Column("unsupported_facts", _json(), server_default="[]", nullable=False),
    sa.Column("prompt_version", sa.String(16), nullable=False),
    sa.Column("taxonomy_version", sa.String(16), nullable=False),
    sa.Column("extracted_at", sa.DateTime(timezone=True), server_default=_now(), nullable=False),
)

rfr_buyers = sa.Table(
    "rfr_buyers", metadata,
    sa.Column("id", sa.Integer(), primary_key=True),
    sa.Column("company_id", sa.Integer()),
    sa.Column("name", sa.String(255), nullable=False),
    sa.Column("name_normalized", sa.String(255), nullable=False),
    sa.Column("website_domain", sa.String(255)),
    sa.Column("hq_city", sa.String(128)),
    sa.Column("hq_state", sa.String(64)),
    sa.Column("hq_country", sa.String(64)),
    sa.Column("priority", sa.String(1)),
    sa.Column("source", sa.String(64), nullable=False),
    sa.Column("is_robot_maker", sa.Boolean(), server_default=sa.false(), nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=_now(), nullable=False),
    sa.Column("updated_at", sa.DateTime(timezone=True), server_default=_now(), nullable=False),
)

rfr_buyer_industries = sa.Table(
    "rfr_buyer_industries", metadata,
    sa.Column("id", sa.Integer(), primary_key=True),
    sa.Column("buyer_id", sa.Integer(), sa.ForeignKey("rfr_buyers.id"), nullable=False),
    sa.Column("industry", sa.String(64), nullable=False),
    sa.Column("confidence", sa.Float(), server_default="1", nullable=False),
    sa.Column("source", sa.String(64), nullable=False),
    sa.Column("source_url", sa.String(2048)),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=_now(), nullable=False),
)

rfr_workflows = sa.Table(
    "rfr_workflows", metadata,
    sa.Column("id", sa.Integer(), primary_key=True),
    sa.Column("buyer_id", sa.Integer(), sa.ForeignKey("rfr_buyers.id"), nullable=False),
    sa.Column("workflow", sa.String(64), nullable=False),
    sa.Column("status", sa.String(16), server_default="unknown", nullable=False),
    sa.Column("status_source_url", sa.String(2048)),
    sa.Column("status_note", sa.Text()),
    sa.Column("committed_vendor", sa.String(255)),
    sa.Column("updated_at", sa.DateTime(timezone=True), server_default=_now(), nullable=False),
)

rfr_signals = sa.Table(
    "rfr_signals", metadata,
    sa.Column("id", sa.Integer(), primary_key=True),
    sa.Column("buyer_id", sa.Integer(), sa.ForeignKey("rfr_buyers.id"), nullable=False),
    sa.Column("workflow", sa.String(64)),
    sa.Column("signal_type", sa.String(32), nullable=False),
    sa.Column("tier", sa.String(1)),
    sa.Column("intent_strength", sa.String(16)),
    sa.Column("title", sa.String(512), nullable=False),
    sa.Column("evidence_text", sa.Text()),
    sa.Column("source_url", sa.String(2048)),
    sa.Column("source_feed", sa.String(64), nullable=False),
    sa.Column("observed_at", sa.DateTime(timezone=True)),
    sa.Column("expires_at", sa.DateTime(timezone=True)),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=_now(), nullable=False),
)

rfr_opportunities = sa.Table(
    "rfr_opportunities", metadata,
    sa.Column("id", sa.Integer(), primary_key=True),
    sa.Column("buyer_id", sa.Integer(), sa.ForeignKey("rfr_buyers.id"), nullable=False),
    sa.Column("workflow", sa.String(64), nullable=False),
    sa.Column("score", sa.Float(), server_default="0", nullable=False),
    sa.Column("top_tier", sa.String(1)),
    sa.Column("reasons", _json(), server_default="[]", nullable=False),
    sa.Column("matched_robot_product_ids", _json(), server_default="[]", nullable=False),
    sa.Column("computed_at", sa.DateTime(timezone=True), server_default=_now(), nullable=False),
)

RFR_TABLES = (rfr_robot_products, rfr_buyers, rfr_buyer_industries, rfr_workflows, rfr_signals, rfr_opportunities)
