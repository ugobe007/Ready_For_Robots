"""Add robot_submissions — durable, deduped ledger of submitted robots.

Revision ID: rsub0a1b2c3d4
Revises: ush0a1b2c3d4
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "rsub0a1b2c3d4"
down_revision: Union[str, Sequence[str], None] = "ush0a1b2c3d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _json():
    return postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite")


def upgrade() -> None:
    op.create_table(
        "robot_submissions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("website_domain", sa.String(length=240), nullable=False),
        sa.Column("submitted_url", sa.Text(), nullable=False),
        sa.Column("company_name", sa.String(length=240), nullable=True),
        sa.Column("product_name", sa.String(length=240), nullable=True),
        sa.Column("robot_class", sa.String(length=64), nullable=True),
        sa.Column("profile_tier", sa.String(length=8), nullable=True),
        sa.Column("capabilities", _json(), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("matched_company_ids", _json(), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("last_job_count", sa.Integer(), nullable=True),
        sa.Column("last_match_count", sa.Integer(), nullable=True),
        sa.Column("submission_count", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("source", sa.String(length=120), nullable=True),
        sa.Column(
            "first_seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "last_seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("last_matched_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("website_domain", name="uq_robot_submissions_website_domain"),
    )
    op.create_index(
        "ix_robot_submissions_website_domain",
        "robot_submissions",
        ["website_domain"],
    )
    op.create_index(
        "ix_robot_submissions_profile_tier",
        "robot_submissions",
        ["profile_tier"],
    )
    op.create_index(
        "ix_robot_submissions_last_seen_at",
        "robot_submissions",
        ["last_seen_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_robot_submissions_last_seen_at", table_name="robot_submissions")
    op.drop_index("ix_robot_submissions_profile_tier", table_name="robot_submissions")
    op.drop_index("ix_robot_submissions_website_domain", table_name="robot_submissions")
    op.drop_table("robot_submissions")
