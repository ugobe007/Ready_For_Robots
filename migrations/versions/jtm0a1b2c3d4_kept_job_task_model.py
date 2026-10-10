"""Store OEM task-model answer on kept jobs.

Revision ID: jtm0a1b2c3d4
Revises: jcnt0a1b2c3d4

User-entered. Unknown until they answer. Do not invent a model name.
Fly leftover: `alembic upgrade head`.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "jtm0a1b2c3d4"
down_revision: Union[str, Sequence[str], None] = "jcnt0a1b2c3d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "user_kept_jobs",
        sa.Column(
            "work_task_model_kind",
            sa.String(length=32),
            nullable=False,
            server_default="unknown",
        ),
    )
    op.add_column(
        "user_kept_jobs",
        sa.Column("work_task_model_source", sa.String(length=240), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("user_kept_jobs", "work_task_model_source")
    op.drop_column("user_kept_jobs", "work_task_model_kind")
