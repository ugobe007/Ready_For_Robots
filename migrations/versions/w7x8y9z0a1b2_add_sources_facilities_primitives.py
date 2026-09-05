"""Sprint 1 — sources, facilities, primitives.

Revision ID: w7x8y9z0a1b2
Revises: v6w7x8y9z0a1
"""
from typing import Sequence, Union
import json
from pathlib import Path

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "w7x8y9z0a1b2"
down_revision: Union[str, Sequence[str], None] = "v6w7x8y9z0a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _uuid():
    return postgresql.UUID(as_uuid=True).with_variant(sa.String(36), "sqlite")


def _json():
    return postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite")


def upgrade() -> None:
    op.create_table(
        "sources",
        sa.Column("id", _uuid(), primary_key=True, nullable=False),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("publisher", sa.String(length=240), nullable=True),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("content_hash", sa.String(length=128), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("metadata", _json(), server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_sources_source_type", "sources", ["source_type"])
    op.create_index("ix_sources_content_hash", "sources", ["content_hash"])

    op.create_table(
        "facilities",
        sa.Column("id", _uuid(), primary_key=True, nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=240), nullable=True),
        sa.Column("facility_type", sa.String(length=64), nullable=True),
        sa.Column("address_line1", sa.String(length=320), nullable=True),
        sa.Column("city", sa.String(length=120), nullable=True),
        sa.Column("state", sa.String(length=64), nullable=True),
        sa.Column("postal_code", sa.String(length=32), nullable=True),
        sa.Column("country", sa.String(length=2), server_default="US", nullable=False),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("normalized_address", sa.String(length=512), nullable=True),
        sa.Column("location_precision", sa.String(length=32), nullable=True),
        sa.Column("estimated_sqft", sa.Integer(), nullable=True),
        sa.Column("employee_count_est", sa.Integer(), nullable=True),
        sa.Column("industry", sa.String(length=120), nullable=True),
        sa.Column("confidence", sa.Float(), server_default="0", nullable=False),
        sa.Column("truth_state", sa.String(length=32), server_default="inferred", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("company_id", "normalized_address", name="uq_facility_company_normalized_address"),
    )
    op.create_index("ix_facilities_company_id", "facilities", ["company_id"])
    op.create_index("ix_facilities_city", "facilities", ["city"])
    op.create_index("ix_facilities_state", "facilities", ["state"])

    op.create_table(
        "primitives",
        sa.Column("id", _uuid(), primary_key=True, nullable=False),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=240), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("ontology_version", sa.String(length=32), server_default="1.0.0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("code", name="uq_primitives_code"),
    )
    op.create_index("ix_primitives_category", "primitives", ["category"])

    # Seed primitives from frozen ontology JSON (portable across Postgres/SQLite).
    conn = op.get_bind()
    root = Path(__file__).resolve().parents[2]
    data = json.loads((root / "docs" / "ontology" / "primitives.v1.json").read_text(encoding="utf-8"))
    version = data.get("version") or "1.0.0"
    import uuid as _uuid_mod

    rows = []
    for p in data.get("primitives") or []:
        rows.append(
            {
                "id": str(_uuid_mod.uuid5(_uuid_mod.NAMESPACE_URL, f"rfr:primitive:{p['code']}")),
                "code": p["code"],
                "category": p["category"],
                "name": p["name"],
                "description": p.get("description"),
                "ontology_version": version,
            }
        )
    if rows:
        for row in rows:
            conn.execute(
                sa.text(
                    "INSERT INTO primitives (id, code, category, name, description, ontology_version) "
                    "VALUES (:id, :code, :category, :name, :description, :ontology_version)"
                ),
                row,
            )


def downgrade() -> None:
    op.drop_table("primitives")
    op.drop_table("facilities")
    op.drop_table("sources")
