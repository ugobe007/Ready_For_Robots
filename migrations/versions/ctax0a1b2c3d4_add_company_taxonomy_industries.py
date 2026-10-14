"""Add company_taxonomy_industries. Does not alter existing tables.

Revision ID: ctax0a1b2c3d4
Revises: aopp0a1b2c3d4, djrt0a1b2c3d4
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "ctax0a1b2c3d4"
down_revision: Union[str, Sequence[str], None] = ("aopp0a1b2c3d4", "djrt0a1b2c3d4")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    if "company_taxonomy_industries" in insp.get_table_names():
        return
    op.create_table(
        "company_taxonomy_industries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("company_name", sa.String(length=300), nullable=False),
        sa.Column("source_industry", sa.String(length=300), nullable=False),
        sa.Column("taxonomy_industry", sa.String(length=64), nullable=False),
        sa.Column("readiness", sa.String(length=32), nullable=True),
        sa.Column("source_kind", sa.String(length=64), nullable=True),
        sa.Column("functions", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "taxonomy_industry", name="uq_company_taxonomy_industry"),
    )
    op.create_index(
        "ix_company_taxonomy_industries_company_id",
        "company_taxonomy_industries",
        ["company_id"],
    )
    op.create_index(
        "ix_company_taxonomy_industries_taxonomy_industry",
        "company_taxonomy_industries",
        ["taxonomy_industry"],
    )


def downgrade() -> None:
    op.drop_index("ix_company_taxonomy_industries_taxonomy_industry", table_name="company_taxonomy_industries")
    op.drop_index("ix_company_taxonomy_industries_company_id", table_name="company_taxonomy_industries")
    op.drop_table("company_taxonomy_industries")
