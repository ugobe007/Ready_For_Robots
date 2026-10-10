"""Sales sheets on a robot profile, shared with each job submission.

Revision ID: rsht0a1b2c3d4
Revises: jtm0a1b2c3d4
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "rsht0a1b2c3d4"
down_revision: Union[str, Sequence[str], None] = "jtm0a1b2c3d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("user_robot_documents", sa.Column("robot_url", sa.String(length=2048), nullable=True))
    op.add_column("user_robot_documents", sa.Column("robot_name", sa.String(length=240), nullable=True))
    op.add_column(
        "user_robot_documents",
        sa.Column(
            "include_with_submissions",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.create_index("ix_user_robot_documents_robot_url", "user_robot_documents", ["robot_url"])


def downgrade() -> None:
    op.drop_index("ix_user_robot_documents_robot_url", table_name="user_robot_documents")
    op.drop_column("user_robot_documents", "include_with_submissions")
    op.drop_column("user_robot_documents", "robot_name")
    op.drop_column("user_robot_documents", "robot_url")
