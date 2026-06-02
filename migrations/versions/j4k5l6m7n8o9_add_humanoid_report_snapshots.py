"""Add monthly humanoid report snapshots for MoM comparison.

Revision ID: j4k5l6m7n8o9
Revises: i3j4k5l6m7n8
Create Date: 2026-06-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "j4k5l6m7n8o9"
down_revision: Union[str, Sequence[str], None] = "i3j4k5l6m7n8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    if "humanoid_report_snapshots" not in insp.get_table_names():
        op.create_table(
            "humanoid_report_snapshots",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("period_key", sa.String(length=7), nullable=False),
            sa.Column("captured_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("summary", sa.JSON(), nullable=False),
            sa.Column("rankings", sa.JSON(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("period_key", name="uq_humanoid_report_snapshots_period"),
        )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS humanoid_report_snapshots CASCADE")
