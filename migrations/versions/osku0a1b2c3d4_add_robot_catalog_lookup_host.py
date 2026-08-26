"""Add lookup_host on manufacturers and robot_models for FIND host match.

Revision ID: osku0a1b2c3d4
Revises: jwch0a1b2c3d4
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "osku0a1b2c3d4"
down_revision: Union[str, Sequence[str], None] = "jwch0a1b2c3d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("manufacturers", sa.Column("lookup_host", sa.String(length=240), nullable=True))
    op.add_column("robot_models", sa.Column("lookup_host", sa.String(length=240), nullable=True))
    op.create_index("ix_manufacturers_lookup_host", "manufacturers", ["lookup_host"])
    op.create_index("ix_robot_models_lookup_host", "robot_models", ["lookup_host"])
    op.create_index("ix_robot_models_product_url", "robot_models", ["product_url"])


def downgrade() -> None:
    op.drop_index("ix_robot_models_product_url", table_name="robot_models")
    op.drop_index("ix_robot_models_lookup_host", table_name="robot_models")
    op.drop_index("ix_manufacturers_lookup_host", table_name="manufacturers")
    op.drop_column("robot_models", "lookup_host")
    op.drop_column("manufacturers", "lookup_host")
