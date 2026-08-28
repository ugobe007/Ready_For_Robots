"""Jobs CRM: employer decline reason code + note on job_applications.

Revision ID: edcl0a1b2c3d4
Revises: pvud0a1b2c3d4
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "edcl0a1b2c3d4"
down_revision: Union[str, Sequence[str], None] = "pvud0a1b2c3d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "job_applications",
        sa.Column("decline_reason_code", sa.String(length=40), nullable=True),
    )
    op.add_column(
        "job_applications",
        sa.Column("decline_note", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("job_applications", "decline_note")
    op.drop_column("job_applications", "decline_reason_code")
