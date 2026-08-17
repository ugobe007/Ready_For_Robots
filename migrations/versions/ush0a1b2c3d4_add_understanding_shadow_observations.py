"""Add understanding_shadow_observations for observe-only v1.0 production shadow.

Revision ID: ush0a1b2c3d4
Revises: rdd0a1b2c3d4
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "ush0a1b2c3d4"
down_revision: Union[str, Sequence[str], None] = "rdd0a1b2c3d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _json():
    return postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite")


def upgrade() -> None:
    op.create_table(
        "understanding_shadow_observations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("correlation_id", sa.String(length=64), nullable=True),
        sa.Column("submitted_url", sa.Text(), nullable=False),
        sa.Column(
            "submitted_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("research_duration_ms", sa.Integer(), nullable=True),
        sa.Column("company_name", sa.String(length=240), nullable=True),
        sa.Column("company_domain", sa.String(length=240), nullable=True),
        sa.Column("selected_product", sa.String(length=240), nullable=True),
        sa.Column("products_found", _json(), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("profile_tier", sa.String(length=8), nullable=True),
        sa.Column("coverage_rate", sa.Float(), nullable=True),
        sa.Column("coverage_level", sa.String(length=16), nullable=True),
        sa.Column("source_quality_rate", sa.Float(), nullable=True),
        sa.Column("source_quality_level", sa.String(length=16), nullable=True),
        sa.Column("source_grounding_rate", sa.Float(), nullable=True),
        sa.Column("research_morphology", sa.String(length=64), nullable=True),
        sa.Column("source_pack", _json(), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("grounded_facts", _json(), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("unknowns", _json(), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("contradictions", _json(), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("notes", _json(), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("research_stages", _json(), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("profile_snapshot", _json(), nullable=True),
        sa.Column("review_label", sa.String(length=32), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("failure_themes", _json(), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_by", sa.String(length=120), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_understanding_shadow_observations_correlation_id",
        "understanding_shadow_observations",
        ["correlation_id"],
    )
    op.create_index(
        "ix_understanding_shadow_observations_submitted_url",
        "understanding_shadow_observations",
        ["submitted_url"],
    )
    op.create_index(
        "ix_understanding_shadow_observations_submitted_at",
        "understanding_shadow_observations",
        ["submitted_at"],
    )
    op.create_index(
        "ix_understanding_shadow_observations_company_domain",
        "understanding_shadow_observations",
        ["company_domain"],
    )
    op.create_index(
        "ix_understanding_shadow_observations_profile_tier",
        "understanding_shadow_observations",
        ["profile_tier"],
    )
    op.create_index(
        "ix_understanding_shadow_observations_review_label",
        "understanding_shadow_observations",
        ["review_label"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_understanding_shadow_observations_review_label",
        table_name="understanding_shadow_observations",
    )
    op.drop_index(
        "ix_understanding_shadow_observations_profile_tier",
        table_name="understanding_shadow_observations",
    )
    op.drop_index(
        "ix_understanding_shadow_observations_company_domain",
        table_name="understanding_shadow_observations",
    )
    op.drop_index(
        "ix_understanding_shadow_observations_submitted_at",
        table_name="understanding_shadow_observations",
    )
    op.drop_index(
        "ix_understanding_shadow_observations_submitted_url",
        table_name="understanding_shadow_observations",
    )
    op.drop_index(
        "ix_understanding_shadow_observations_correlation_id",
        table_name="understanding_shadow_observations",
    )
    op.drop_table("understanding_shadow_observations")
