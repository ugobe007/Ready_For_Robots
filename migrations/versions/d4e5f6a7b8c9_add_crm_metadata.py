"""Add companies.crm_metadata — CRM descriptor JSON (budget, timing, requirements, decision makers).

Revision ID: d4e5f6a7b8c9
Revises: f1a2b3c4d5e6
Create Date: 2026-04-14

Supabase / psql (optional manual DDL — Alembic runs this for you):

    ALTER TABLE companies ADD COLUMN IF NOT EXISTS crm_metadata JSONB;

No backfill is needed — crm_extractor populates this field asynchronously
after each enrichment + rectification pass.
Run: alembic upgrade head
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, Sequence[str], None] = "f1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name
    if dialect == "postgresql":
        col = postgresql.JSONB(astext_type=sa.Text())
    else:
        col = sa.JSON()
    op.add_column("companies", sa.Column("crm_metadata", col, nullable=True))


def downgrade() -> None:
    op.drop_column("companies", "crm_metadata")
