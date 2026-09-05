"""Add SCOUT activation persistence.

Revision ID: f5a6b7c8d9e0
Revises: f4a5b6c7d8e9
Create Date: 2026-05-10
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

revision: str = "f5a6b7c8d9e0"
down_revision: Union[str, Sequence[str], None] = "f4a5b6c7d8e9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _index_names(bind: sa.engine.Connection, table: str) -> set[str]:
    insp = inspect(bind)
    if table not in insp.get_table_names():
        return set()
    return {i["name"] for i in insp.get_indexes(table)}


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    tables = set(insp.get_table_names())

    if "scout_activations" not in tables:
        op.create_table(
            "scout_activations",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("session_id", sa.Integer(), nullable=False),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("source_url", sa.String(length=512), nullable=True),
            sa.Column("material_choice", sa.String(length=32), nullable=False),
            sa.Column("material_filename", sa.String(length=512), nullable=True),
            sa.Column("scope_choice", sa.String(length=32), nullable=False),
            sa.Column("mode_choice", sa.String(length=32), nullable=False),
            sa.Column("status", sa.String(length=32), server_default="queued", nullable=False),
            sa.Column("lead_ids", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
            sa.Column("leads_snapshot", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
            sa.Column("work_plan", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
            sa.Column("activity_log", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["session_id"], ["scout_sessions.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["user_id"], ["user_profiles.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )
    if "ix_scout_activations_session_id" not in _index_names(bind, "scout_activations"):
        op.create_index("ix_scout_activations_session_id", "scout_activations", ["session_id"], unique=False)
    if "ix_scout_activations_user_id" not in _index_names(bind, "scout_activations"):
        op.create_index("ix_scout_activations_user_id", "scout_activations", ["user_id"], unique=False)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS scout_activations CASCADE")
