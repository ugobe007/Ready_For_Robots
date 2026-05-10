"""Archive raw signal body before in-DB cleanup.

Adds ``signals.ingestion_raw_text`` (nullable TEXT). One-off scripts copy the
pre-cleanup ``signal_text`` here, then replace ``signal_text`` with a cleaned
value (see ``scripts/cleanup_signal_text.py``).

Revision ID: c0d1e2f3a4b5
Revises: 8a9b0c1d2e3f
Create Date: 2026-04-28
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c0d1e2f3a4b5"
down_revision: Union[str, Sequence[str], None] = "8a9b0c1d2e3f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "signals",
        sa.Column("ingestion_raw_text", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("signals", "ingestion_raw_text")
