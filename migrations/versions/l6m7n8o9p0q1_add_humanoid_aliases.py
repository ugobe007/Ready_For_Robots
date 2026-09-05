"""Add humanoid alias fields (vendor_aliases, robot_aliases) for crawler recall

Revision ID: l6m7n8o9p0q1
Revises: k5l6m7n8o9p0
Create Date: 2026-06-14

Chinese humanoid vendors are referenced under many different English/native
spellings across press releases, WeChat posts, GitHub repos, papers, and WAIC
exhibitor lists (e.g. Leju Kuavo is "夸父"/Kuafu in Chinese sources and rarely
"Kuavo"). Storing pipe-delimited alias strings lets the crawler match any of
them, typically lifting Chinese-source recall 30-50%.

    ALTER TABLE humanoid_benchmarks
      ADD COLUMN IF NOT EXISTS vendor_aliases TEXT,
      ADD COLUMN IF NOT EXISTS robot_aliases  TEXT;
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "l6m7n8o9p0q1"
down_revision: Union[str, Sequence[str], None] = "k5l6m7n8o9p0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


NEW_COLUMNS = ("vendor_aliases", "robot_aliases")


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        cols = ",\n            ".join(f"ADD COLUMN IF NOT EXISTS {c} TEXT" for c in NEW_COLUMNS)
        op.execute(f"ALTER TABLE humanoid_benchmarks\n            {cols};")
    else:
        for c in NEW_COLUMNS:
            with op.batch_alter_table("humanoid_benchmarks") as batch:
                batch.add_column(sa.Column(c, sa.Text(), nullable=True))


def downgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        cols = ", ".join(f"DROP COLUMN IF EXISTS {c}" for c in NEW_COLUMNS)
        op.execute(f"ALTER TABLE humanoid_benchmarks {cols};")
    else:
        for c in NEW_COLUMNS:
            with op.batch_alter_table("humanoid_benchmarks") as batch:
                batch.drop_column(c)
