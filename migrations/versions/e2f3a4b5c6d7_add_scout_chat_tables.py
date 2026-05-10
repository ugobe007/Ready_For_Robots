"""Add SCOUT chat persistence (sessions, messages, profiles).

Revision ID: e2f3a4b5c6d7
Revises: d5e6f7a8b9c0
Create Date: 2026-05-10

Anonymous visitors are keyed by browser fingerprint (see rfr_cursor_package scoutDb).
Authenticated users can optionally link user_profiles.id to the same row.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

revision: str = "e2f3a4b5c6d7"
down_revision: Union[str, Sequence[str], None] = "d5e6f7a8b9c0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _index_names(bind: sa.engine.Connection, table: str) -> set[str]:
    insp = inspect(bind)
    if table not in insp.get_table_names():
        return set()
    return {i["name"] for i in insp.get_indexes(table)}


def upgrade() -> None:
    """Create SCOUT tables if missing (idempotent with Supabase `IF NOT EXISTS` SQL)."""
    bind = op.get_bind()
    insp = inspect(bind)
    tables = set(insp.get_table_names())

    if "scout_sessions" not in tables:
        op.create_table(
            "scout_sessions",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("fingerprint", sa.String(length=80), nullable=False),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("robot_category", sa.String(length=32), nullable=True),
            sa.Column("vertical", sa.Text(), nullable=True),
            sa.Column("territory", sa.String(length=128), nullable=True),
            sa.Column("company_name", sa.String(length=256), nullable=True),
            sa.Column("company_url", sa.String(length=512), nullable=True),
            sa.Column("conversation_count", sa.Integer(), server_default="0", nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.Column(
                "last_seen_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["user_id"], ["user_profiles.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("fingerprint", name="uq_scout_sessions_fingerprint"),
        )
    if "ix_scout_sessions_user_id" not in _index_names(bind, "scout_sessions"):
        op.create_index("ix_scout_sessions_user_id", "scout_sessions", ["user_id"], unique=False)

    insp = inspect(bind)
    tables = set(insp.get_table_names())
    if "scout_messages" not in tables:
        op.create_table(
            "scout_messages",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("session_id", sa.Integer(), nullable=False),
            sa.Column("role", sa.String(length=16), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("skill_invoked", sa.String(length=64), nullable=True),
            sa.Column("skill_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["session_id"], ["scout_sessions.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
    if "ix_scout_messages_session_id" not in _index_names(bind, "scout_messages"):
        op.create_index("ix_scout_messages_session_id", "scout_messages", ["session_id"], unique=False)

    insp = inspect(bind)
    tables = set(insp.get_table_names())
    if "scout_profiles" not in tables:
        op.create_table(
            "scout_profiles",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("session_id", sa.Integer(), nullable=False),
            sa.Column(
                "companies_viewed",
                postgresql.JSONB(astext_type=sa.Text()),
                server_default=sa.text("'[]'::jsonb"),
                nullable=False,
            ),
            sa.Column(
                "drafts_approved",
                postgresql.JSONB(astext_type=sa.Text()),
                server_default=sa.text("'[]'::jsonb"),
                nullable=False,
            ),
            sa.Column(
                "signals_seen",
                postgresql.JSONB(astext_type=sa.Text()),
                server_default=sa.text("'[]'::jsonb"),
                nullable=False,
            ),
            sa.Column("inferred_needs", sa.Text(), nullable=True),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["session_id"], ["scout_sessions.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("session_id", name="uq_scout_profiles_session_id"),
        )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS scout_profiles CASCADE")
    op.execute("DROP TABLE IF EXISTS scout_messages CASCADE")
    op.execute("DROP TABLE IF EXISTS scout_sessions CASCADE")
