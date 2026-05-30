"""Add HEIF columns to humanoid_benchmarks.

Revision ID: g1h2i3j4k5l6
Revises: f8a9b0c1d2e3
Create Date: 2026-05-29

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "g1h2i3j4k5l6"
down_revision: Union[str, Sequence[str], None] = "a2b3c4d5e6f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

HEIF_COLUMNS = (
    ("heif_mobility", "HEIF mobility (0–4)"),
    ("heif_manipulation", "HEIF manipulation (0–4)"),
    ("heif_cognition", "HEIF cognition / task planning (0–4)"),
    ("heif_safety", "HEIF safety (0–4)"),
    ("heif_data_pipeline", "HEIF data pipeline / fleet learning (0–4)"),
    ("heif_production", "HEIF production readiness (0–4)"),
    ("heif_total", "HEIF weighted composite (0–4)"),
)


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    if "humanoid_benchmarks" not in insp.get_table_names():
        return

    existing = {c["name"] for c in insp.get_columns("humanoid_benchmarks")}
    for name, comment in HEIF_COLUMNS:
        if name in existing:
            continue
        op.add_column(
            "humanoid_benchmarks",
            sa.Column(name, sa.Float(), nullable=True, comment=comment),
        )


def downgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    if "humanoid_benchmarks" not in insp.get_table_names():
        return

    existing = {c["name"] for c in insp.get_columns("humanoid_benchmarks")}
    for name, _ in reversed(HEIF_COLUMNS):
        if name in existing:
            op.drop_column("humanoid_benchmarks", name)
