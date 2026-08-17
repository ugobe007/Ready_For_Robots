"""Add disposition to sales_opportunities (V1 Slice 0).

WATCH / PAUSED / LOST are dispositions and must not overwrite monotonic truth
stored in current_stage.

Revision ID: u5v6w7x8y9z0
Revises: t4u5v6w7x8y9
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "u5v6w7x8y9z0"
down_revision: Union[str, Sequence[str], None] = "t4u5v6w7x8y9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "sales_opportunities",
        sa.Column("disposition", sa.String(length=32), nullable=False, server_default="active"),
    )
    op.create_index(
        "ix_sales_opportunities_disposition",
        "sales_opportunities",
        ["disposition"],
        unique=False,
    )
    # Legacy rows that stored lost as a stage: move to disposition without inventing a new truth stage.
    op.execute(
        """
        UPDATE sales_opportunities
        SET disposition = 'lost',
            status = 'closed',
            current_stage = 'discovered'
        WHERE current_stage = 'lost'
        """
    )


def downgrade() -> None:
    op.drop_index("ix_sales_opportunities_disposition", table_name="sales_opportunities")
    op.drop_column("sales_opportunities", "disposition")
