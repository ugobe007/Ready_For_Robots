"""Jobs CRM: async video résumé URL on job_applications.

Revision ID: pvud0a1b2c3d4
Revises: ihld0a1b2c3d4
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "pvud0a1b2c3d4"
down_revision: Union[str, Sequence[str], None] = "ihld0a1b2c3d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("job_applications", sa.Column("poc_video_url", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("job_applications", "poc_video_url")
