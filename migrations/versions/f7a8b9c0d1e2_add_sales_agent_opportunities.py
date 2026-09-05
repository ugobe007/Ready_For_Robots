"""Add stateful SCOUT sales agent opportunities.

Revision ID: f7a8b9c0d1e2
Revises: f6a7b8c9d0e1
Create Date: 2026-05-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "f7a8b9c0d1e2"
down_revision: Union[str, Sequence[str], None] = "f6a7b8c9d0e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sales_opportunities",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("opportunity_type", sa.String(length=32), nullable=False),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("crm_account_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("company_id", sa.Integer(), nullable=True),
        sa.Column("robot_company_id", sa.Integer(), nullable=True),
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("current_stage", sa.String(length=64), server_default="new", nullable=False),
        sa.Column("status", sa.String(length=32), server_default="open", nullable=False),
        sa.Column("automation_level", sa.String(length=32), server_default="first_reply_auto", nullable=False),
        sa.Column("next_best_action", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("last_inbound_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_outbound_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["crm_account_id"], ["crm_accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["owner_user_id"], ["user_profiles.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["robot_company_id"], ["robot_companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("opportunity_type", "crm_account_id", name="uq_sales_opportunity_type_crm_account"),
        sa.UniqueConstraint("opportunity_type", "robot_company_id", name="uq_sales_opportunity_type_robot_company"),
    )
    for idx, cols in {
        "ix_sales_opportunities_opportunity_type": ["opportunity_type"],
        "ix_sales_opportunities_team_id": ["team_id"],
        "ix_sales_opportunities_crm_account_id": ["crm_account_id"],
        "ix_sales_opportunities_company_id": ["company_id"],
        "ix_sales_opportunities_robot_company_id": ["robot_company_id"],
        "ix_sales_opportunities_owner_user_id": ["owner_user_id"],
        "ix_sales_opportunities_current_stage": ["current_stage"],
        "ix_sales_opportunities_status": ["status"],
        "ix_sales_opportunities_last_inbound_at": ["last_inbound_at"],
        "ix_sales_opportunities_last_outbound_at": ["last_outbound_at"],
    }.items():
        op.create_index(idx, "sales_opportunities", cols)

    op.create_table(
        "sales_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("sales_opportunity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("direction", sa.String(length=16), nullable=False),
        sa.Column("channel", sa.String(length=32), server_default="email", nullable=False),
        sa.Column("source_type", sa.String(length=64), nullable=True),
        sa.Column("source_id", sa.String(length=80), nullable=True),
        sa.Column("from_email", sa.String(length=320), nullable=True),
        sa.Column("to_email", sa.String(length=320), nullable=True),
        sa.Column("subject", sa.String(length=512), nullable=True),
        sa.Column("body_text", sa.Text(), nullable=True),
        sa.Column("detected_intent", sa.String(length=64), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["sales_opportunity_id"], ["sales_opportunities.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    for idx, cols in {
        "ix_sales_messages_sales_opportunity_id": ["sales_opportunity_id"],
        "ix_sales_messages_direction": ["direction"],
        "ix_sales_messages_source_type": ["source_type"],
        "ix_sales_messages_source_id": ["source_id"],
        "ix_sales_messages_from_email": ["from_email"],
        "ix_sales_messages_detected_intent": ["detected_intent"],
        "ix_sales_messages_created_at": ["created_at"],
    }.items():
        op.create_index(idx, "sales_messages", cols)

    op.create_table(
        "sales_agent_actions",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("sales_opportunity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action_type", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="planned", nullable=False),
        sa.Column("risk_level", sa.String(length=32), server_default="low", nullable=False),
        sa.Column("requires_approval", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("stage_before", sa.String(length=64), nullable=True),
        sa.Column("stage_after", sa.String(length=64), nullable=True),
        sa.Column("detected_intent", sa.String(length=64), nullable=True),
        sa.Column("recommendation", sa.Text(), nullable=True),
        sa.Column("draft_subject", sa.String(length=512), nullable=True),
        sa.Column("draft_body", sa.Text(), nullable=True),
        sa.Column("resend_id", sa.String(length=128), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["sales_opportunity_id"], ["sales_opportunities.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    for idx, cols in {
        "ix_sales_agent_actions_sales_opportunity_id": ["sales_opportunity_id"],
        "ix_sales_agent_actions_action_type": ["action_type"],
        "ix_sales_agent_actions_status": ["status"],
        "ix_sales_agent_actions_requires_approval": ["requires_approval"],
        "ix_sales_agent_actions_detected_intent": ["detected_intent"],
        "ix_sales_agent_actions_resend_id": ["resend_id"],
        "ix_sales_agent_actions_sent_at": ["sent_at"],
    }.items():
        op.create_index(idx, "sales_agent_actions", cols)


def downgrade() -> None:
    for table in ["sales_agent_actions", "sales_messages", "sales_opportunities"]:
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
