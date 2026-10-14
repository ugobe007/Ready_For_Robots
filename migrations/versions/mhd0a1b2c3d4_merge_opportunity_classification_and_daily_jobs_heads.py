"""Merge Alembic heads: opportunity classification + daily jobs report text.

Two revisions branched from the same history on 2026-10-10/12:
  - aopp0a1b2c3d4 (robot_jobs.opportunity_tier / opportunity_class)
  - djrt0a1b2c3d4 (daily jobs report text)

Without this merge, `alembic upgrade head` (scripts/fly_release_migrate.sh)
fails with multiple heads. On a database at djrt0a1b2c3d4, upgrading to this
revision also runs aopp0a1b2c3d4.

Revision ID: mhd0a1b2c3d4
Revises: aopp0a1b2c3d4, djrt0a1b2c3d4
"""
from typing import Sequence, Union

revision: str = "mhd0a1b2c3d4"
down_revision: Union[str, Sequence[str], None] = ("aopp0a1b2c3d4", "djrt0a1b2c3d4")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
