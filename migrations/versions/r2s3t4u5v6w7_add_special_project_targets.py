"""Add special project targets (Cal outreach queue for a special project).

Revision ID: r2s3t4u5v6w7
Revises: q1r2s3t4u5v6
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "r2s3t4u5v6w7"
down_revision: Union[str, Sequence[str], None] = "q1r2s3t4u5v6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "special_project_targets",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("company", sa.String(length=200), nullable=False),
        sa.Column("website", sa.String(length=512), nullable=True),
        sa.Column("segment", sa.String(length=120), nullable=True),
        sa.Column("best_fit_task", sa.String(length=200), nullable=True),
        sa.Column("persona", sa.String(length=200), nullable=True),
        sa.Column("sequence", sa.String(length=1), nullable=True),
        sa.Column("fit", sa.String(length=1), nullable=True),
        sa.Column("signal", sa.Text(), nullable=True),
        sa.Column("contact_name", sa.String(length=200), nullable=True),
        sa.Column("contact_email", sa.String(length=320), nullable=True),
        sa.Column("contact_title", sa.String(length=200), nullable=True),
        sa.Column("contact_status", sa.String(length=16), server_default="none", nullable=False),
        sa.Column("draft_subject", sa.Text(), nullable=True),
        sa.Column("draft_body", sa.Text(), nullable=True),
        sa.Column("stage", sa.String(length=24), server_default="targeted", nullable=False),
        sa.Column("approved", sa.String(length=8), server_default="no", nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["special_projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_special_project_targets_project_id", "special_project_targets", ["project_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_special_project_targets_project_id", table_name="special_project_targets")
    op.drop_table("special_project_targets")
