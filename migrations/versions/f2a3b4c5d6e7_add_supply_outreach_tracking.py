"""Add supply-side outreach tracking.

Revision ID: f2a3b4c5d6e7
Revises: e1f2a3b4c5d7
Create Date: 2026-05-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "f2a3b4c5d6e7"
down_revision: Union[str, Sequence[str], None] = "e1f2a3b4c5d7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "supply_outreach_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("robot_company_id", sa.Integer(), nullable=False),
        sa.Column("to_emails", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("from_email", sa.String(length=320), nullable=True),
        sa.Column("reply_to", sa.String(length=320), nullable=True),
        sa.Column("reply_token", sa.String(length=80), nullable=False),
        sa.Column("subject", sa.String(length=512), nullable=False),
        sa.Column("body_text", sa.Text(), nullable=False),
        sa.Column("template_type", sa.String(length=80), server_default="supply_pipeline", nullable=False),
        sa.Column("resend_id", sa.String(length=128), nullable=True),
        sa.Column("status", sa.String(length=32), server_default="draft_approved", nullable=False),
        sa.Column("is_test", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["robot_company_id"], ["robot_companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("reply_token", name="uq_supply_outreach_messages_reply_token"),
    )
    op.create_index("ix_supply_outreach_messages_robot_company_id", "supply_outreach_messages", ["robot_company_id"])
    op.create_index("ix_supply_outreach_messages_reply_to", "supply_outreach_messages", ["reply_to"])
    op.create_index("ix_supply_outreach_messages_reply_token", "supply_outreach_messages", ["reply_token"], unique=True)
    op.create_index("ix_supply_outreach_messages_resend_id", "supply_outreach_messages", ["resend_id"])
    op.create_index("ix_supply_outreach_messages_status", "supply_outreach_messages", ["status"])
    op.create_index("ix_supply_outreach_messages_is_test", "supply_outreach_messages", ["is_test"])
    op.create_index("ix_supply_outreach_messages_approved_at", "supply_outreach_messages", ["approved_at"])
    op.create_index("ix_supply_outreach_messages_sent_at", "supply_outreach_messages", ["sent_at"])

    op.create_table(
        "supply_outreach_replies",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("supply_outreach_message_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("robot_company_id", sa.Integer(), nullable=False),
        sa.Column("from_email", sa.String(length=320), nullable=True),
        sa.Column("to_email", sa.String(length=320), nullable=True),
        sa.Column("subject", sa.String(length=512), nullable=True),
        sa.Column("body_text", sa.Text(), nullable=True),
        sa.Column("raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["robot_company_id"], ["robot_companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["supply_outreach_message_id"], ["supply_outreach_messages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_supply_outreach_replies_supply_outreach_message_id", "supply_outreach_replies", ["supply_outreach_message_id"])
    op.create_index("ix_supply_outreach_replies_robot_company_id", "supply_outreach_replies", ["robot_company_id"])
    op.create_index("ix_supply_outreach_replies_from_email", "supply_outreach_replies", ["from_email"])
    op.create_index("ix_supply_outreach_replies_received_at", "supply_outreach_replies", ["received_at"])


def downgrade() -> None:
    op.drop_index("ix_supply_outreach_replies_received_at", table_name="supply_outreach_replies")
    op.drop_index("ix_supply_outreach_replies_from_email", table_name="supply_outreach_replies")
    op.drop_index("ix_supply_outreach_replies_robot_company_id", table_name="supply_outreach_replies")
    op.drop_index("ix_supply_outreach_replies_supply_outreach_message_id", table_name="supply_outreach_replies")
    op.drop_table("supply_outreach_replies")

    op.drop_index("ix_supply_outreach_messages_sent_at", table_name="supply_outreach_messages")
    op.drop_index("ix_supply_outreach_messages_approved_at", table_name="supply_outreach_messages")
    op.drop_index("ix_supply_outreach_messages_is_test", table_name="supply_outreach_messages")
    op.drop_index("ix_supply_outreach_messages_status", table_name="supply_outreach_messages")
    op.drop_index("ix_supply_outreach_messages_resend_id", table_name="supply_outreach_messages")
    op.drop_index("ix_supply_outreach_messages_reply_token", table_name="supply_outreach_messages")
    op.drop_index("ix_supply_outreach_messages_reply_to", table_name="supply_outreach_messages")
    op.drop_index("ix_supply_outreach_messages_robot_company_id", table_name="supply_outreach_messages")
    op.drop_table("supply_outreach_messages")
