"""Jobs CRM: keep jobs, applications, employer threads on the account.

Revision ID: jkep0a1b2c3d4
Revises: osku0a1b2c3d4
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "jkep0a1b2c3d4"
down_revision: Union[str, Sequence[str], None] = "osku0a1b2c3d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _json():
    return postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite")


def _uuid():
    return postgresql.UUID(as_uuid=True).with_variant(sa.String(36), "sqlite")


def upgrade() -> None:
    op.create_table(
        "user_kept_jobs",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("user_id", _uuid(), nullable=False),
        sa.Column("job_key", sa.String(length=160), nullable=False),
        sa.Column("employer_name", sa.String(length=240), nullable=False),
        sa.Column("work_title", sa.String(length=512), nullable=False),
        sa.Column("workplace", sa.String(length=240), nullable=True),
        sa.Column("source_ids", _json(), server_default=sa.text("'{}'"), nullable=False),
        sa.Column("job_payload", _json(), server_default=sa.text("'{}'"), nullable=False),
        sa.Column("robot_name", sa.String(length=240), nullable=True),
        sa.Column("robot_url", sa.Text(), nullable=True),
        sa.Column("robot_submission_id", sa.Integer(), nullable=True),
        sa.Column("employer_email", sa.String(length=320), nullable=True),
        sa.Column("acted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.UniqueConstraint("user_id", "job_key", name="uq_user_kept_jobs_user_job"),
    )
    op.create_index("ix_user_kept_jobs_user_id", "user_kept_jobs", ["user_id"])
    op.create_index("ix_user_kept_jobs_job_key", "user_kept_jobs", ["job_key"])
    op.create_index("ix_user_kept_jobs_created_at", "user_kept_jobs", ["created_at"])
    op.create_index("ix_user_kept_jobs_expires_at", "user_kept_jobs", ["expires_at"])
    op.create_index("ix_user_kept_jobs_acted_at", "user_kept_jobs", ["acted_at"])
    op.create_index("ix_user_kept_jobs_user_created", "user_kept_jobs", ["user_id", "created_at"])

    op.create_table(
        "job_applications",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("user_id", _uuid(), nullable=False),
        sa.Column("kept_job_id", _uuid(), nullable=True),
        sa.Column("job_key", sa.String(length=160), nullable=False),
        sa.Column("employer_name", sa.String(length=240), nullable=False),
        sa.Column("work_title", sa.String(length=512), nullable=False),
        sa.Column("workplace", sa.String(length=240), nullable=True),
        sa.Column("robot_name", sa.String(length=240), nullable=False),
        sa.Column("selected_models", _json(), server_default=sa.text("'[]'"), nullable=False),
        sa.Column("poc_evidence", sa.Text(), nullable=True),
        sa.Column("poc_skipped", sa.String(length=8), server_default="false", nullable=False),
        sa.Column("monthly_price", sa.String(length=160), nullable=False),
        sa.Column("offer_snapshot", _json(), server_default=sa.text("'{}'"), nullable=False),
        sa.Column("employer_email", sa.String(length=320), nullable=True),
        sa.Column("send_status", sa.String(length=40), server_default="stored", nullable=False),
        sa.Column("send_error", sa.Text(), nullable=True),
        sa.Column("resend_id", sa.String(length=128), nullable=True),
        sa.Column("reply_token", sa.String(length=80), nullable=False),
        sa.Column("reply_to", sa.String(length=320), nullable=True),
        sa.Column("thread_state", sa.String(length=32), server_default="draft", nullable=False),
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
        sa.UniqueConstraint("reply_token", name="uq_job_applications_reply_token"),
    )
    op.create_index("ix_job_applications_user_id", "job_applications", ["user_id"])
    op.create_index("ix_job_applications_job_key", "job_applications", ["job_key"])
    op.create_index("ix_job_applications_kept_job_id", "job_applications", ["kept_job_id"])
    op.create_index("ix_job_applications_send_status", "job_applications", ["send_status"])
    op.create_index("ix_job_applications_resend_id", "job_applications", ["resend_id"])
    op.create_index("ix_job_applications_user_job", "job_applications", ["user_id", "job_key"])
    bind = op.get_bind()
    if bind.dialect.name != "sqlite":
        op.create_foreign_key(
            "fk_job_applications_kept_job_id",
            "job_applications",
            "user_kept_jobs",
            ["kept_job_id"],
            ["id"],
            ondelete="SET NULL",
        )

    op.create_table(
        "application_messages",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("application_id", _uuid(), nullable=False),
        sa.Column("user_id", _uuid(), nullable=False),
        sa.Column("direction", sa.String(length=16), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("subject", sa.String(length=512), nullable=True),
        sa.Column("from_email", sa.String(length=320), nullable=True),
        sa.Column("to_email", sa.String(length=320), nullable=True),
        sa.Column("provider_id", sa.String(length=160), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.create_index("ix_application_messages_application_id", "application_messages", ["application_id"])
    op.create_index("ix_application_messages_user_id", "application_messages", ["user_id"])
    op.create_index("ix_application_messages_provider_id", "application_messages", ["provider_id"])
    op.create_index(
        "ix_application_messages_app_created",
        "application_messages",
        ["application_id", "created_at"],
    )
    if bind.dialect.name != "sqlite":
        op.create_foreign_key(
            "fk_application_messages_application_id",
            "application_messages",
            "job_applications",
            ["application_id"],
            ["id"],
            ondelete="CASCADE",
        )

    op.create_table(
        "jobs_crm_activity",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("user_id", _uuid(), nullable=False),
        sa.Column("job_key", sa.String(length=160), nullable=True),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("label", sa.String(length=240), nullable=False),
        sa.Column("company", sa.String(length=240), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.create_index("ix_jobs_crm_activity_user_id", "jobs_crm_activity", ["user_id"])
    op.create_index("ix_jobs_crm_activity_job_key", "jobs_crm_activity", ["job_key"])
    op.create_index("ix_jobs_crm_activity_user_created", "jobs_crm_activity", ["user_id", "created_at"])


def downgrade() -> None:
    op.drop_table("jobs_crm_activity")
    op.drop_table("application_messages")
    op.drop_table("job_applications")
    op.drop_table("user_kept_jobs")
