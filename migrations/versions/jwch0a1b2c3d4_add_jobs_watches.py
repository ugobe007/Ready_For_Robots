"""Add jobs_watches — opt-in cron watch for a user's robot URL.

Revision ID: jwch0a1b2c3d4
Revises: rcrm0a1b2c3d4
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "jwch0a1b2c3d4"
down_revision: Union[str, Sequence[str], None] = "rcrm0a1b2c3d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _json():
    return postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite")


def _uuid():
    return postgresql.UUID(as_uuid=True).with_variant(sa.String(36), "sqlite")


def upgrade() -> None:
    op.create_table(
        "jobs_watches",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("user_id", _uuid(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("robot_url", sa.Text(), nullable=False),
        sa.Column("website_domain", sa.String(length=240), nullable=False),
        sa.Column("product_name", sa.String(length=240), nullable=True),
        sa.Column("robot_submission_id", sa.Integer(), nullable=True),
        sa.Column("opted_in", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("last_job_keys", _json(), server_default=sa.text("'[]'"), nullable=False),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_notified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notify_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.UniqueConstraint("user_id", "website_domain", name="uq_jobs_watch_user_domain"),
    )
    op.create_index("ix_jobs_watches_user_id", "jobs_watches", ["user_id"])
    op.create_index("ix_jobs_watches_website_domain", "jobs_watches", ["website_domain"])
    op.create_index("ix_jobs_watches_robot_submission_id", "jobs_watches", ["robot_submission_id"])
    bind = op.get_bind()
    if bind.dialect.name != "sqlite":
        op.create_foreign_key(
            "fk_jobs_watches_robot_submission_id",
            "jobs_watches",
            "robot_submissions",
            ["robot_submission_id"],
            ["id"],
            ondelete="SET NULL",
        )

    op.create_table(
        "jobs_watch_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("watch_id", _uuid(), nullable=False),
        sa.Column("job_key", sa.String(length=120), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("company_name", sa.String(length=240), nullable=True),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("emailed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_jobs_watch_events_watch_id", "jobs_watch_events", ["watch_id"])
    op.create_index("ix_jobs_watch_events_job_key", "jobs_watch_events", ["job_key"])
    op.create_index("ix_jobs_watch_events_kind", "jobs_watch_events", ["kind"])
    if bind.dialect.name != "sqlite":
        op.create_foreign_key(
            "fk_jobs_watch_events_watch_id",
            "jobs_watch_events",
            "jobs_watches",
            ["watch_id"],
            ["id"],
            ondelete="CASCADE",
        )


def downgrade() -> None:
    op.drop_table("jobs_watch_events")
    op.drop_table("jobs_watches")
