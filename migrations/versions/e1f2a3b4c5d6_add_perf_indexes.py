"""Add performance indexes on signals and scores for lead query speed

Revision ID: e1f2a3b4c5d6
Revises: b1c2d3e4f5a6
Create Date: 2026-04-10

The _lead_rows_query does a three-way JOIN:
  companies → scores (company_id) → signals (company_id)
with GROUP BY and ORDER BY overall_intent_score.

Without indexes on these FK/sort columns the DB does a full table scan on every
homepage, summary, and dashboard load — 60+ seconds on 4 000+ companies.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e1f2a3b4c5d6"
down_revision: Union[str, Sequence[str], None] = "b1c2d3e4f5a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_signals_company_id", "signals", ["company_id"],
        unique=False, if_not_exists=True,
    )
    op.create_index(
        "ix_signals_signal_type", "signals", ["signal_type"],
        unique=False, if_not_exists=True,
    )
    op.create_index(
        "ix_scores_company_id", "scores", ["company_id"],
        unique=False, if_not_exists=True,
    )
    op.create_index(
        "ix_scores_overall_intent_score", "scores", [sa.text("overall_intent_score DESC NULLS LAST")],
        unique=False, if_not_exists=True,
    )
    op.create_index(
        "ix_scores_last_calculated_at", "scores", [sa.text("last_calculated_at DESC NULLS LAST")],
        unique=False, if_not_exists=True,
    )
    op.create_index(
        "ix_companies_industry", "companies", ["industry"],
        unique=False, if_not_exists=True,
    )


def downgrade() -> None:
    op.drop_index("ix_signals_company_id", table_name="signals", if_exists=True)
    op.drop_index("ix_signals_signal_type", table_name="signals", if_exists=True)
    op.drop_index("ix_scores_company_id", table_name="scores", if_exists=True)
    op.drop_index("ix_scores_overall_intent_score", table_name="scores", if_exists=True)
    op.drop_index("ix_scores_last_calculated_at", table_name="scores", if_exists=True)
    op.drop_index("ix_companies_industry", table_name="companies", if_exists=True)
