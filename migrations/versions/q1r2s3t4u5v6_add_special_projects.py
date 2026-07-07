"""Add special projects (private admin GTM workflow + client portal).

Revision ID: q1r2s3t4u5v6
Revises: p0q1r2s3t4u5
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "q1r2s3t4u5v6"
down_revision: Union[str, Sequence[str], None] = "p0q1r2s3t4u5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "special_projects",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("share_token", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("company_website", sa.String(length=512), nullable=True),
        sa.Column("contact_email", sa.String(length=320), nullable=True),
        sa.Column("robot_description", sa.Text(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), server_default="discovery", nullable=False),
        sa.Column("config", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("metrics", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("pipeline", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_special_projects_slug", "special_projects", ["slug"], unique=True)
    op.create_index("ix_special_projects_share_token", "special_projects", ["share_token"], unique=True)

    op.create_table(
        "special_project_updates",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=32), server_default="note", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["special_projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_special_project_updates_project_id", "special_project_updates", ["project_id"])
    op.create_index("ix_special_project_updates_created_at", "special_project_updates", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_special_project_updates_created_at", table_name="special_project_updates")
    op.drop_index("ix_special_project_updates_project_id", table_name="special_project_updates")
    op.drop_table("special_project_updates")
    op.drop_index("ix_special_projects_share_token", table_name="special_projects")
    op.drop_index("ix_special_projects_slug", table_name="special_projects")
    op.drop_table("special_projects")
