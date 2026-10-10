"""Store each day's 25 leads as inline text and CSV.

Revision ID: djrt0a1b2c3d4
Revises: rsht0a1b2c3d4
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "djrt0a1b2c3d4"
down_revision: Union[str, Sequence[str], None] = "rsht0a1b2c3d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "daily_jobs_report_editions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("report_date", sa.String(length=10), nullable=False),
        sa.Column("body_text", sa.Text(), nullable=False),
        sa.Column("csv_text", sa.Text(), nullable=False),
        sa.Column("job_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "stored_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("report_date", name="uq_daily_jobs_report_editions_date"),
    )


def downgrade() -> None:
    op.drop_table("daily_jobs_report_editions")
