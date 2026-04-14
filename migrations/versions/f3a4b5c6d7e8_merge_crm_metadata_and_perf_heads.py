"""Merge Alembic heads: crm_metadata branch + perf_indexes branch.

`f1a2b3c4d5e6` (automation_profile) had two child revisions:
  - a9b8c7d6e5f4 → b1c2d3e4f5a6 → e1f2a3b4c5d6 (website_domain + indexes)
  - d4e5f6a7b8c9 (crm_metadata)

Without this merge, `alembic upgrade head` fails with multiple heads and the DB
never receives newer columns — ORM loads of Company then error at runtime.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "f3a4b5c6d7e8"
down_revision: Union[str, Sequence[str], None] = ("d4e5f6a7b8c9", "e1f2a3b4c5d6")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
