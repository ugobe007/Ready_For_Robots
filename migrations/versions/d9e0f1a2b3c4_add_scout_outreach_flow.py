"""Add SCOUT outreach settings, messages, and replies.

Revision ID: d9e0f1a2b3c4
Revises: c8d9e0f1a2b3
Create Date: 2026-05-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "d9e0f1a2b3c4"
down_revision: Union[str, Sequence[str], None] = "c8d9e0f1a2b3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "user_settings",
        sa.Column("scout_automation_level", sa.String(length=32), nullable=False, server_default="assisted"),
    )
    op.add_column(
        "user_settings",
        sa.Column("reply_forwarding_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.add_column("user_settings", sa.Column("reply_forward_email", sa.String(length=320), nullable=True))

    op.create_table(
        "outreach_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("crm_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=True),
        sa.Column("sender_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("to_email", sa.String(length=320), nullable=False),
        sa.Column("from_email", sa.String(length=320), nullable=True),
        sa.Column("reply_to", sa.String(length=320), nullable=True),
        sa.Column("reply_token", sa.String(length=80), nullable=False),
        sa.Column("subject", sa.String(length=512), nullable=False),
        sa.Column("body_text", sa.Text(), nullable=False),
        sa.Column("send_identity", sa.String(length=32), server_default="scout", nullable=False),
        sa.Column("resend_id", sa.String(length=128), nullable=True),
        sa.Column("status", sa.String(length=32), server_default="queued", nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["crm_account_id"], ["crm_accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sender_user_id"], ["user_profiles.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("reply_token", name="uq_outreach_messages_reply_token"),
    )
    op.create_index("ix_outreach_messages_team_id", "outreach_messages", ["team_id"])
    op.create_index("ix_outreach_messages_crm_account_id", "outreach_messages", ["crm_account_id"])
    op.create_index("ix_outreach_messages_company_id", "outreach_messages", ["company_id"])
    op.create_index("ix_outreach_messages_sender_user_id", "outreach_messages", ["sender_user_id"])
    op.create_index("ix_outreach_messages_to_email", "outreach_messages", ["to_email"])
    op.create_index("ix_outreach_messages_reply_to", "outreach_messages", ["reply_to"])
    op.create_index("ix_outreach_messages_reply_token", "outreach_messages", ["reply_token"], unique=True)
    op.create_index("ix_outreach_messages_resend_id", "outreach_messages", ["resend_id"])
    op.create_index("ix_outreach_messages_status", "outreach_messages", ["status"])
    op.create_index("ix_outreach_messages_sent_at", "outreach_messages", ["sent_at"])

    op.create_table(
        "outreach_replies",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("outreach_message_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("crm_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=True),
        sa.Column("from_email", sa.String(length=320), nullable=True),
        sa.Column("to_email", sa.String(length=320), nullable=True),
        sa.Column("subject", sa.String(length=512), nullable=True),
        sa.Column("body_text", sa.Text(), nullable=True),
        sa.Column("raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["crm_account_id"], ["crm_accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["outreach_message_id"], ["outreach_messages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_outreach_replies_outreach_message_id", "outreach_replies", ["outreach_message_id"])
    op.create_index("ix_outreach_replies_team_id", "outreach_replies", ["team_id"])
    op.create_index("ix_outreach_replies_crm_account_id", "outreach_replies", ["crm_account_id"])
    op.create_index("ix_outreach_replies_company_id", "outreach_replies", ["company_id"])
    op.create_index("ix_outreach_replies_from_email", "outreach_replies", ["from_email"])
    op.create_index("ix_outreach_replies_received_at", "outreach_replies", ["received_at"])


def downgrade() -> None:
    op.drop_index("ix_outreach_replies_received_at", table_name="outreach_replies")
    op.drop_index("ix_outreach_replies_from_email", table_name="outreach_replies")
    op.drop_index("ix_outreach_replies_company_id", table_name="outreach_replies")
    op.drop_index("ix_outreach_replies_crm_account_id", table_name="outreach_replies")
    op.drop_index("ix_outreach_replies_team_id", table_name="outreach_replies")
    op.drop_index("ix_outreach_replies_outreach_message_id", table_name="outreach_replies")
    op.drop_table("outreach_replies")

    op.drop_index("ix_outreach_messages_sent_at", table_name="outreach_messages")
    op.drop_index("ix_outreach_messages_status", table_name="outreach_messages")
    op.drop_index("ix_outreach_messages_resend_id", table_name="outreach_messages")
    op.drop_index("ix_outreach_messages_reply_token", table_name="outreach_messages")
    op.drop_index("ix_outreach_messages_reply_to", table_name="outreach_messages")
    op.drop_index("ix_outreach_messages_to_email", table_name="outreach_messages")
    op.drop_index("ix_outreach_messages_sender_user_id", table_name="outreach_messages")
    op.drop_index("ix_outreach_messages_company_id", table_name="outreach_messages")
    op.drop_index("ix_outreach_messages_crm_account_id", table_name="outreach_messages")
    op.drop_index("ix_outreach_messages_team_id", table_name="outreach_messages")
    op.drop_table("outreach_messages")

    op.drop_column("user_settings", "reply_forward_email")
    op.drop_column("user_settings", "reply_forwarding_enabled")
    op.drop_column("user_settings", "scout_automation_level")
