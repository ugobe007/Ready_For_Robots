"""Add internal calendar events.

Revision ID: a2b3c4d5e6f7
Revises: f8a9b0c1d2e3
Create Date: 2026-05-16

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "a2b3c4d5e6f7"
down_revision: Union[str, Sequence[str], None] = "f8a9b0c1d2e3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "calendar_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("sales_opportunity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("crm_account_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("robot_company_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("timezone", sa.String(length=80), server_default="UTC", nullable=False),
        sa.Column("location", sa.String(length=320), nullable=True),
        sa.Column("meeting_url", sa.String(length=500), nullable=True),
        sa.Column("attendees", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="scheduled", nullable=False),
        sa.Column("invite_status", sa.String(length=32), server_default="not_sent", nullable=False),
        sa.Column("ics_uid", sa.String(length=160), nullable=False),
        sa.Column("external_provider", sa.String(length=32), nullable=True),
        sa.Column("external_event_id", sa.String(length=160), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["crm_account_id"], ["crm_accounts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["owner_user_id"], ["user_profiles.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["robot_company_id"], ["robot_companies.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["sales_opportunity_id"], ["sales_opportunities.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ics_uid", name="uq_calendar_events_ics_uid"),
    )
    for name, cols in {
        "ix_calendar_events_team_id": ["team_id"],
        "ix_calendar_events_owner_user_id": ["owner_user_id"],
        "ix_calendar_events_sales_opportunity_id": ["sales_opportunity_id"],
        "ix_calendar_events_crm_account_id": ["crm_account_id"],
        "ix_calendar_events_robot_company_id": ["robot_company_id"],
        "ix_calendar_events_start_at": ["start_at"],
        "ix_calendar_events_end_at": ["end_at"],
        "ix_calendar_events_status": ["status"],
        "ix_calendar_events_invite_status": ["invite_status"],
        "ix_calendar_events_ics_uid": ["ics_uid"],
        "ix_calendar_events_external_event_id": ["external_event_id"],
    }.items():
        op.create_index(name, "calendar_events", cols)


def downgrade() -> None:
    op.drop_table("calendar_events")
