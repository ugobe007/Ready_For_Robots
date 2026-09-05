"""Add companies.website_domain — normalized hostname for domain-level entity resolution.

Revision ID: a9b8c7d6e5f4
Revises: f1a2b3c4d5e6
Create Date: 2026-04-07

Run: alembic upgrade head
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.orm import Session

revision: str = "a9b8c7d6e5f4"
down_revision: Union[str, Sequence[str], None] = "f1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "companies",
        sa.Column("website_domain", sa.String(), nullable=True),
    )
    op.create_index(
        "ix_companies_website_domain",
        "companies",
        ["website_domain"],
        unique=False,
    )

    from app.models.company import Company
    from app.services.company_domain import normalize_website_domain

    bind = op.get_bind()
    session = Session(bind=bind)
    try:
        rows = session.query(Company.id, Company.website).filter(Company.website.isnot(None)).all()
        for cid, website in rows:
            dom = normalize_website_domain(website)
            if dom:
                session.query(Company).filter(Company.id == cid).update(
                    {"website_domain": dom},
                    synchronize_session=False,
                )
        session.commit()
    finally:
        session.close()


def downgrade() -> None:
    op.drop_index("ix_companies_website_domain", table_name="companies")
    op.drop_column("companies", "website_domain")
