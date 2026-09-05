"""Add humanoid entity-resolution fields (Chinese names, vendor/guide/github URLs, country, verification status)

Revision ID: k5l6m7n8o9p0
Revises: j4k5l6m7n8o9, e1f2a3b4c5d6
Create Date: 2026-06-14

This migration does double duty:

1. MERGE the two divergent heads that had accumulated:
     - j4k5l6m7n8o9 (add_humanoid_report_snapshots)  ← deployed
     - e1f2a3b4c5d6 (add_perf_indexes)               ← never deployed
   `alembic upgrade head` was ambiguous with two heads; this collapses them.

2. ADD entity-resolution columns to humanoid_benchmarks. Many humanoid vendors
   (especially Chinese firms) are mis-resolved because English names in investor
   decks / WAIC lists / media don't match official branding. Storing the native
   names + distinct URL classes turns "URL hunting" into entity resolution and
   dramatically improves crawler accuracy.

     ALTER TABLE humanoid_benchmarks
       ADD COLUMN IF NOT EXISTS country             TEXT,
       ADD COLUMN IF NOT EXISTS vendor_name_cn       TEXT,
       ADD COLUMN IF NOT EXISTS robot_name_cn        TEXT,
       ADD COLUMN IF NOT EXISTS vendor_url           TEXT,
       ADD COLUMN IF NOT EXISTS humanoid_guide_url   TEXT,
       ADD COLUMN IF NOT EXISTS github_url           TEXT,
       ADD COLUMN IF NOT EXISTS verification_status  TEXT;

Note: the existing `product_url` column is the canonical robot URL; the API
exposes it as `robot_url` as well. `status` keeps its availability meaning
(available/pilot/research); resolution confidence lives in `verification_status`
(VERIFIED / PARTIAL / NEEDS_VERIFICATION).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "k5l6m7n8o9p0"
down_revision: Union[str, Sequence[str], None] = ("j4k5l6m7n8o9", "e1f2a3b4c5d6")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


NEW_COLUMNS = (
    "country",
    "vendor_name_cn",
    "robot_name_cn",
    "vendor_url",
    "humanoid_guide_url",
    "github_url",
    "verification_status",
)


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
