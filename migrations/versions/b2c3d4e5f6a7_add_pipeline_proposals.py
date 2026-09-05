"""Add pipeline_proposals for per-user saved proposal text.

Revision ID: b2c3d4e5f6a7
Revises: c0d1e2f3a4b5
Create Date: 2026-05-07

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, Sequence[str], None] = "c0d1e2f3a4b5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "pipeline_proposals",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=True),
        sa.Column("company_name", sa.String(length=500), nullable=False),
        sa.Column("proposal_text", sa.Text(), nullable=False),
        sa.Column("contact_email", sa.String(length=320), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["user_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("user_id", "company_name", name="uq_pipeline_proposals_user_company_name"),
    )
    op.create_index("ix_pipeline_proposals_user_id", "pipeline_proposals", ["user_id"], unique=False)
    op.create_index("ix_pipeline_proposals_company_id", "pipeline_proposals", ["company_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_pipeline_proposals_company_id", table_name="pipeline_proposals")
    op.drop_index("ix_pipeline_proposals_user_id", table_name="pipeline_proposals")
    op.drop_table("pipeline_proposals")
