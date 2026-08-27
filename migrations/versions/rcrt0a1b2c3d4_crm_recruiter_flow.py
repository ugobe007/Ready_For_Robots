"""Jobs CRM recruiter flow: docs, employer tokens, interview tracking.

Revision ID: rcrt0a1b2c3d4
Revises: jkep0a1b2c3d4
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "rcrt0a1b2c3d4"
down_revision: Union[str, Sequence[str], None] = "jkep0a1b2c3d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _uuid():
    return postgresql.UUID(as_uuid=True).with_variant(sa.String(36), "sqlite")


def upgrade() -> None:
    op.add_column("job_applications", sa.Column("employer_token", sa.String(length=80), nullable=True))
    op.add_column(
        "job_applications",
        sa.Column("status", sa.String(length=40), server_default="applied", nullable=False),
    )
    op.add_column("job_applications", sa.Column("interview_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("job_applications", sa.Column("interview_note", sa.Text(), nullable=True))
    op.add_column("job_applications", sa.Column("interview_mode", sa.String(length=32), nullable=True))
    op.add_column("job_applications", sa.Column("oem_email", sa.String(length=320), nullable=True))
    op.create_index("ix_job_applications_employer_token", "job_applications", ["employer_token"], unique=True)
    op.create_index("ix_job_applications_status", "job_applications", ["status"])

    op.create_table(
        "user_robot_documents",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("user_id", _uuid(), nullable=False),
        sa.Column("filename", sa.String(length=240), nullable=False),
        sa.Column("original_name", sa.String(length=240), nullable=False),
        sa.Column("mime_type", sa.String(length=120), nullable=False),
        sa.Column("size_bytes", sa.Integer(), server_default="0", nullable=False),
        sa.Column("storage_path", sa.Text(), nullable=False),
        sa.Column("kind", sa.String(length=32), server_default="spec", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.create_index("ix_user_robot_documents_user_id", "user_robot_documents", ["user_id"])
    op.create_index("ix_user_robot_documents_created_at", "user_robot_documents", ["created_at"])

    op.create_table(
        "application_documents",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("application_id", _uuid(), nullable=False),
        sa.Column("document_id", _uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.UniqueConstraint("application_id", "document_id", name="uq_application_documents_app_doc"),
    )
    op.create_index("ix_application_documents_application_id", "application_documents", ["application_id"])
    op.create_index("ix_application_documents_document_id", "application_documents", ["document_id"])
    bind = op.get_bind()
    if bind.dialect.name != "sqlite":
        op.create_foreign_key(
            "fk_application_documents_application_id",
            "application_documents",
            "job_applications",
            ["application_id"],
            ["id"],
            ondelete="CASCADE",
        )
        op.create_foreign_key(
            "fk_application_documents_document_id",
            "application_documents",
            "user_robot_documents",
            ["document_id"],
            ["id"],
            ondelete="CASCADE",
        )


def downgrade() -> None:
    op.drop_table("application_documents")
    op.drop_table("user_robot_documents")
    op.drop_index("ix_job_applications_status", table_name="job_applications")
    op.drop_index("ix_job_applications_employer_token", table_name="job_applications")
    op.drop_column("job_applications", "oem_email")
    op.drop_column("job_applications", "interview_mode")
    op.drop_column("job_applications", "interview_note")
    op.drop_column("job_applications", "interview_at")
    op.drop_column("job_applications", "status")
    op.drop_column("job_applications", "employer_token")
