"""Add follow-up (T2) outreach fields to special project targets.

A second, review-first touch for accounts Cal has already contacted: its own
draft, approval flag, and sent timestamp so follow-ups never send without a
human approving them and never double-send.

Revision ID: s3t4u5v6w7x8
Revises: r2s3t4u5v6w7
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "s3t4u5v6w7x8"
down_revision: Union[str, Sequence[str], None] = "r2s3t4u5v6w7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "special_project_targets",
        sa.Column("followup_subject", sa.Text(), nullable=True),
    )
    op.add_column(
        "special_project_targets",
        sa.Column("followup_body", sa.Text(), nullable=True),
    )
    op.add_column(
        "special_project_targets",
        sa.Column("followup_approved", sa.String(length=8), server_default="no", nullable=False),
    )
    op.add_column(
        "special_project_targets",
        sa.Column("followup_sent_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("special_project_targets", "followup_sent_at")
    op.drop_column("special_project_targets", "followup_approved")
    op.drop_column("special_project_targets", "followup_body")
    op.drop_column("special_project_targets", "followup_subject")
