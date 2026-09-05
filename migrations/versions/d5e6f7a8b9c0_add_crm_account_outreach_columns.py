"""Add outreach columns to crm_accounts.

Revision ID: d5e6f7a8b9c0
Revises: c3d4e5f6a7b0
Create Date: 2026-05-07

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "d5e6f7a8b9c0"
down_revision: Union[str, Sequence[str], None] = "c3d4e5f6a7b0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("crm_accounts", sa.Column("contact_email", sa.String(length=320), nullable=True))
    op.add_column("crm_accounts", sa.Column("outreach_draft", sa.Text(), nullable=True))
    op.add_column(
        "crm_accounts",
        sa.Column("outreach_sent_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "crm_accounts",
        sa.Column("outreach_stage", sa.String(length=64), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("crm_accounts", "outreach_stage")
    op.drop_column("crm_accounts", "outreach_sent_at")
    op.drop_column("crm_accounts", "outreach_draft")
    op.drop_column("crm_accounts", "contact_email")
