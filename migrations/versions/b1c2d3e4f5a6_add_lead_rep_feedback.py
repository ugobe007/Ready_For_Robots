"""Add lead_rep_feedback — rep thumbs / reason codes for lead quality loop.

Revision ID: b1c2d3e4f5a6
Revises: a9b8c7d6e5f4
Create Date: 2026-04-10

Run: alembic upgrade head
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b1c2d3e4f5a6"
down_revision: Union[str, Sequence[str], None] = "a9b8c7d6e5f4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "lead_rep_feedback",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("vote", sa.String(length=16), nullable=False),
        sa.Column("reason_code", sa.String(length=32), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("user_id", sa.String(length=36), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_lead_rep_feedback_company_id", "lead_rep_feedback", ["company_id"], unique=False)
    op.create_index("ix_lead_rep_feedback_created_at", "lead_rep_feedback", ["created_at"], unique=False)
    op.create_index("ix_lead_rep_feedback_user_id", "lead_rep_feedback", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_lead_rep_feedback_user_id", table_name="lead_rep_feedback")
    op.drop_index("ix_lead_rep_feedback_created_at", table_name="lead_rep_feedback")
    op.drop_index("ix_lead_rep_feedback_company_id", table_name="lead_rep_feedback")
    op.drop_table("lead_rep_feedback")
