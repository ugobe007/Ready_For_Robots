"""Add outreach sequence tables for multi-step cadences.

Revision ID: m7n8o9p0q1r2
Revises: l6m7n8o9p0q1
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "m7n8o9p0q1r2"
down_revision: Union[str, Sequence[str], None] = "l6m7n8o9p0q1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "outreach_sequences",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("slug", sa.String(length=80), nullable=True),
        sa.Column("channel", sa.String(length=32), server_default="email", nullable=False),
        sa.Column("is_default", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="active", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_outreach_sequences_team_id", "outreach_sequences", ["team_id"])
    op.create_index("ix_outreach_sequences_slug", "outreach_sequences", ["slug"])

    op.create_table(
        "outreach_sequence_steps",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("sequence_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("step_number", sa.Integer(), nullable=False),
        sa.Column("delay_days", sa.Integer(), server_default="0", nullable=False),
        sa.Column("subject_template", sa.String(length=512), nullable=True),
        sa.Column("body_template", sa.Text(), nullable=True),
        sa.Column("action_label", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["sequence_id"], ["outreach_sequences.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sequence_id", "step_number", name="uq_sequence_step_number"),
    )
    op.create_index("ix_outreach_sequence_steps_sequence_id", "outreach_sequence_steps", ["sequence_id"])

    op.create_table(
        "outreach_sequence_enrollments",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sequence_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("crm_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("current_step", sa.Integer(), server_default="1", nullable=False),
        sa.Column("status", sa.String(length=32), server_default="active", nullable=False),
        sa.Column("enrolled_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("last_step_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_step_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paused_reason", sa.String(length=120), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sequence_id"], ["outreach_sequences.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["crm_account_id"], ["crm_accounts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("crm_account_id", "sequence_id", name="uq_account_sequence_enrollment"),
    )
    op.create_index("ix_outreach_sequence_enrollments_team_id", "outreach_sequence_enrollments", ["team_id"])
    op.create_index("ix_outreach_sequence_enrollments_sequence_id", "outreach_sequence_enrollments", ["sequence_id"])
    op.create_index("ix_outreach_sequence_enrollments_crm_account_id", "outreach_sequence_enrollments", ["crm_account_id"])
    op.create_index("ix_outreach_sequence_enrollments_status", "outreach_sequence_enrollments", ["status"])
    op.create_index("ix_outreach_sequence_enrollments_next_step_at", "outreach_sequence_enrollments", ["next_step_at"])


def downgrade() -> None:
    op.drop_index("ix_outreach_sequence_enrollments_next_step_at", table_name="outreach_sequence_enrollments")
    op.drop_index("ix_outreach_sequence_enrollments_status", table_name="outreach_sequence_enrollments")
    op.drop_index("ix_outreach_sequence_enrollments_crm_account_id", table_name="outreach_sequence_enrollments")
    op.drop_index("ix_outreach_sequence_enrollments_sequence_id", table_name="outreach_sequence_enrollments")
    op.drop_index("ix_outreach_sequence_enrollments_team_id", table_name="outreach_sequence_enrollments")
    op.drop_table("outreach_sequence_enrollments")
    op.drop_index("ix_outreach_sequence_steps_sequence_id", table_name="outreach_sequence_steps")
    op.drop_table("outreach_sequence_steps")
    op.drop_index("ix_outreach_sequences_slug", table_name="outreach_sequences")
    op.drop_index("ix_outreach_sequences_team_id", table_name="outreach_sequences")
    op.drop_table("outreach_sequences")
