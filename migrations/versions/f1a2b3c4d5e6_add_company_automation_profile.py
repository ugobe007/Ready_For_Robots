"""Add companies.automation_profile — persisted rules_v1 robot / automation spec JSON.

Revision ID: f1a2b3c4d5e6
Revises: c7d8e9f0a1b2
Create Date: 2026-04-07

Supabase / psql (optional manual DDL — Alembic runs this for you):

    ALTER TABLE companies ADD COLUMN IF NOT EXISTS automation_profile JSONB;

Backfill uses Python (industry + signal rules); it is not expressible as plain SQL.
Run: alembic upgrade head
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session, joinedload

revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, Sequence[str], None] = "c7d8e9f0a1b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name
    if dialect == "postgresql":
        col = postgresql.JSONB(astext_type=sa.Text())
    else:
        col = sa.JSON()
    op.add_column("companies", sa.Column("automation_profile", col, nullable=True))

    # Backfill existing rows (batched commits).
    from app.models.company import Company
    from app.services.automation_profile import build_automation_profile_dict_from_company

    session = Session(bind=bind)
    try:
        ids = [r[0] for r in session.query(Company.id).order_by(Company.id).all()]
        batch_size = 400
        for i in range(0, len(ids), batch_size):
            chunk = ids[i : i + batch_size]
            companies = (
                session.query(Company)
                .options(joinedload(Company.signals))
                .filter(Company.id.in_(chunk))
                .all()
            )
            for c in companies:
                c.automation_profile = build_automation_profile_dict_from_company(c)
            session.commit()
    finally:
        session.close()


def downgrade() -> None:
    op.drop_column("companies", "automation_profile")
