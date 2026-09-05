"""Add SCOUT sales experience memory.

Revision ID: f8a9b0c1d2e3
Revises: f7a8b9c0d1e2
Create Date: 2026-05-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "f8a9b0c1d2e3"
down_revision: Union[str, Sequence[str], None] = "f7a8b9c0d1e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sales_experience_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("crm_account_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("sales_opportunity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("sales_agent_action_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("company_id", sa.Integer(), nullable=True),
        sa.Column("robot_company_id", sa.Integer(), nullable=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("outcome", sa.String(length=64), server_default="observed", nullable=False),
        sa.Column("source_domain", sa.String(length=240), nullable=True),
        sa.Column("signal_type", sa.String(length=80), nullable=True),
        sa.Column("channel", sa.String(length=32), nullable=True),
        sa.Column("score_delta", sa.Numeric(8, 4), nullable=True),
        sa.Column("confidence", sa.Numeric(5, 4), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["crm_account_id"], ["crm_accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["robot_company_id"], ["robot_companies.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["sales_agent_action_id"], ["sales_agent_actions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["sales_opportunity_id"], ["sales_opportunities.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["user_profiles.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    for name, cols in {
        "ix_sales_experience_events_team_id": ["team_id"],
        "ix_sales_experience_events_user_id": ["user_id"],
        "ix_sales_experience_events_crm_account_id": ["crm_account_id"],
        "ix_sales_experience_events_sales_opportunity_id": ["sales_opportunity_id"],
        "ix_sales_experience_events_sales_agent_action_id": ["sales_agent_action_id"],
        "ix_sales_experience_events_company_id": ["company_id"],
        "ix_sales_experience_events_robot_company_id": ["robot_company_id"],
        "ix_sales_experience_events_event_type": ["event_type"],
        "ix_sales_experience_events_outcome": ["outcome"],
        "ix_sales_experience_events_source_domain": ["source_domain"],
        "ix_sales_experience_events_signal_type": ["signal_type"],
        "ix_sales_experience_events_channel": ["channel"],
        "ix_sales_experience_events_created_at": ["created_at"],
    }.items():
        op.create_index(name, "sales_experience_events", cols)


def downgrade() -> None:
    op.drop_table("sales_experience_events")
