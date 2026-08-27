"""Jobs CRM interview hold: persist a concrete slot on the application.

Revision ID: ihld0a1b2c3d4
Revises: rcrt0a1b2c3d4
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "ihld0a1b2c3d4"
down_revision: Union[str, Sequence[str], None] = "rcrt0a1b2c3d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("job_applications", sa.Column("held_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "job_applications",
        sa.Column("hold_expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "job_applications",
        sa.Column("slot_start", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column("job_applications", sa.Column("slot_end", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "job_applications",
        sa.Column("oem_hold_token", sa.String(length=80), nullable=True),
    )
    op.create_index(
        "ix_job_applications_oem_hold_token",
        "job_applications",
        ["oem_hold_token"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_job_applications_oem_hold_token", table_name="job_applications")
    op.drop_column("job_applications", "oem_hold_token")
    op.drop_column("job_applications", "slot_end")
    op.drop_column("job_applications", "slot_start")
    op.drop_column("job_applications", "hold_expires_at")
    op.drop_column("job_applications", "held_at")
