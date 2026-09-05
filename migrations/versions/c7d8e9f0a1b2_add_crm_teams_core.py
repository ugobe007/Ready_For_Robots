"""Add CRM core: teams, members, accounts (SSOT link to companies), engagements, tasks, notes, agent_runs, playbook templates

Revision ID: c7d8e9f0a1b2
Revises: a1b2c3d4e5f6
Create Date: 2026-04-04

- Teams scope all CRM rows; members reference user_profiles.id (Supabase auth user UUID as text).
- crm_accounts: one row per (team, buyer company). company_id -> companies.id (platform SSOT), nullable for prospects not yet in leads DB.
- crm_engagements: separate sales motions per account (multiple concurrent or sequential).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "c7d8e9f0a1b2"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "teams",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("slug", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_teams_slug", "teams", ["slug"], unique=True)

    op.create_table(
        "team_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column(
            "role",
            sa.String(),
            nullable=False,
            server_default="member",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["user_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("team_id", "user_id", name="uq_team_members_team_user"),
    )
    op.create_index("ix_team_members_team_id", "team_members", ["team_id"], unique=False)
    op.create_index("ix_team_members_user_id", "team_members", ["user_id"], unique=False)

    op.create_table(
        "crm_accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("website", sa.String(), nullable=True),
        sa.Column("industry", sa.String(), nullable=True),
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_crm_accounts_team_id", "crm_accounts", ["team_id"], unique=False)
    op.create_index("ix_crm_accounts_company_id", "crm_accounts", ["company_id"], unique=False)
    op.create_index("ix_crm_accounts_owner_user_id", "crm_accounts", ["owner_user_id"], unique=False)

    # One CRM account per team per platform company (when linked)
    op.execute(
        """
        CREATE UNIQUE INDEX uq_crm_accounts_team_company
        ON crm_accounts (team_id, company_id)
        WHERE company_id IS NOT NULL
        """
    )

    op.create_table(
        "crm_engagements",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("crm_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("stage", sa.String(), nullable=False, server_default="qualification"),
        sa.Column("value_amount", sa.Numeric(18, 2), nullable=True),
        sa.Column("currency", sa.String(), nullable=True, server_default="USD"),
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="open"),
        sa.Column("opened_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["crm_account_id"], ["crm_accounts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_crm_engagements_team_id", "crm_engagements", ["team_id"], unique=False)
    op.create_index("ix_crm_engagements_crm_account_id", "crm_engagements", ["crm_account_id"], unique=False)
    op.create_index("ix_crm_engagements_owner_user_id", "crm_engagements", ["owner_user_id"], unique=False)
    op.create_index("ix_crm_engagements_status", "crm_engagements", ["status"], unique=False)

    op.create_table(
        "crm_tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("crm_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("engagement_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="todo"),
        sa.Column("priority", sa.String(), nullable=True, server_default="normal"),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("assignee_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("source", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["crm_account_id"], ["crm_accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["engagement_id"], ["crm_engagements.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_crm_tasks_team_id", "crm_tasks", ["team_id"], unique=False)
    op.create_index("ix_crm_tasks_crm_account_id", "crm_tasks", ["crm_account_id"], unique=False)
    op.create_index("ix_crm_tasks_engagement_id", "crm_tasks", ["engagement_id"], unique=False)
    op.create_index("ix_crm_tasks_assignee_user_id", "crm_tasks", ["assignee_user_id"], unique=False)
    op.create_index("ix_crm_tasks_due_at", "crm_tasks", ["due_at"], unique=False)

    op.create_table(
        "crm_notes",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("crm_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("engagement_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("author_user_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("source", sa.String(), nullable=True, server_default="user"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["crm_account_id"], ["crm_accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["engagement_id"], ["crm_engagements.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_crm_notes_team_id", "crm_notes", ["team_id"], unique=False)
    op.create_index("ix_crm_notes_crm_account_id", "crm_notes", ["crm_account_id"], unique=False)

    op.create_table(
        "agent_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("crm_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("engagement_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("model", sa.String(), nullable=True),
        sa.Column("prompt_version", sa.String(), nullable=True),
        sa.Column("input_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("output_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("tokens_in", sa.Integer(), nullable=True),
        sa.Column("tokens_out", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["crm_account_id"], ["crm_accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["engagement_id"], ["crm_engagements.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_agent_runs_team_id", "agent_runs", ["team_id"], unique=False)
    op.create_index("ix_agent_runs_user_id", "agent_runs", ["user_id"], unique=False)
    op.create_index("ix_agent_runs_crm_account_id", "agent_runs", ["crm_account_id"], unique=False)
    op.create_index("ix_agent_runs_created_at", "agent_runs", ["created_at"], unique=False)

    op.create_table(
        "crm_playbook_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("slug", sa.String(), nullable=True),
        sa.Column("definition", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_crm_playbook_templates_team_id", "crm_playbook_templates", ["team_id"], unique=False)
    op.create_index("ix_crm_playbook_templates_slug", "crm_playbook_templates", ["slug"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_crm_playbook_templates_slug", table_name="crm_playbook_templates")
    op.drop_index("ix_crm_playbook_templates_team_id", table_name="crm_playbook_templates")
    op.drop_table("crm_playbook_templates")

    op.drop_index("ix_agent_runs_created_at", table_name="agent_runs")
    op.drop_index("ix_agent_runs_crm_account_id", table_name="agent_runs")
    op.drop_index("ix_agent_runs_user_id", table_name="agent_runs")
    op.drop_index("ix_agent_runs_team_id", table_name="agent_runs")
    op.drop_table("agent_runs")

    op.drop_index("ix_crm_notes_crm_account_id", table_name="crm_notes")
    op.drop_index("ix_crm_notes_team_id", table_name="crm_notes")
    op.drop_table("crm_notes")

    op.drop_index("ix_crm_tasks_due_at", table_name="crm_tasks")
    op.drop_index("ix_crm_tasks_assignee_user_id", table_name="crm_tasks")
    op.drop_index("ix_crm_tasks_engagement_id", table_name="crm_tasks")
    op.drop_index("ix_crm_tasks_crm_account_id", table_name="crm_tasks")
    op.drop_index("ix_crm_tasks_team_id", table_name="crm_tasks")
    op.drop_table("crm_tasks")

    op.drop_index("ix_crm_engagements_status", table_name="crm_engagements")
    op.drop_index("ix_crm_engagements_owner_user_id", table_name="crm_engagements")
    op.drop_index("ix_crm_engagements_crm_account_id", table_name="crm_engagements")
    op.drop_index("ix_crm_engagements_team_id", table_name="crm_engagements")
    op.drop_table("crm_engagements")

    op.execute("DROP INDEX IF EXISTS uq_crm_accounts_team_company")
    op.drop_index("ix_crm_accounts_owner_user_id", table_name="crm_accounts")
    op.drop_index("ix_crm_accounts_company_id", table_name="crm_accounts")
    op.drop_index("ix_crm_accounts_team_id", table_name="crm_accounts")
    op.drop_table("crm_accounts")

    op.drop_index("ix_team_members_user_id", table_name="team_members")
    op.drop_index("ix_team_members_team_id", table_name="team_members")
    op.drop_table("team_members")

    op.drop_index("ix_teams_slug", table_name="teams")
    op.drop_table("teams")
