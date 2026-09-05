"""Add robot buyer leads for inbound automation requests.

Revision ID: i3j4k5l6m7n8
Revises: h2i3j4k5l6m7
Create Date: 2026-05-25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "i3j4k5l6m7n8"
down_revision: Union[str, Sequence[str], None] = "h2i3j4k5l6m7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    if "robot_buyer_leads" not in insp.get_table_names():
        op.create_table(
            "robot_buyer_leads",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("email", sa.String(length=320), nullable=False),
            sa.Column("name", sa.String(length=200), nullable=True),
            sa.Column("company", sa.String(length=240), nullable=False),
            sa.Column("phone", sa.String(length=40), nullable=True),
            sa.Column("job_title", sa.String(length=160), nullable=True),
            sa.Column("use_case", sa.Text(), nullable=False),
            sa.Column("robot_type", sa.String(length=80), nullable=False),
            sa.Column("implementation_timeline", sa.String(length=80), nullable=False),
            sa.Column("source", sa.String(length=120), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_robot_buyer_leads_email", "robot_buyer_leads", ["email"])
        op.create_index("ix_robot_buyer_leads_created_at", "robot_buyer_leads", ["created_at"])


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS robot_buyer_leads CASCADE")
