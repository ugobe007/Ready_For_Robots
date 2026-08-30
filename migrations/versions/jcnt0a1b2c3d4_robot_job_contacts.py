"""Store employer contacts found on the job posting (page only).

Revision ID: jcnt0a1b2c3d4
Revises: jruc0a1b2c3d4

Nullable. Do not invent values. Fly leftover: `alembic upgrade head`.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "jcnt0a1b2c3d4"
down_revision: Union[str, Sequence[str], None] = "jruc0a1b2c3d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "robot_jobs",
        sa.Column("employer_email", sa.String(length=320), nullable=True),
    )
    op.add_column(
        "robot_jobs",
        sa.Column("contact_url", sa.String(length=1024), nullable=True),
    )
    op.add_column(
        "robot_jobs",
        sa.Column("apply_url", sa.String(length=1024), nullable=True),
    )
    op.create_index(
        "ix_robot_jobs_employer_email",
        "robot_jobs",
        ["employer_email"],
    )


def downgrade() -> None:
    op.drop_index("ix_robot_jobs_employer_email", table_name="robot_jobs")
    op.drop_column("robot_jobs", "apply_url")
    op.drop_column("robot_jobs", "contact_url")
    op.drop_column("robot_jobs", "employer_email")
