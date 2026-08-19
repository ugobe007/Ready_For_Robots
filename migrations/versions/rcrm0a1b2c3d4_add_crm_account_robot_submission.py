"""Add crm_accounts.robot_submission_id — tie saved leads to the sourcing robot.

Revision ID: rcrm0a1b2c3d4
Revises: rsub0a1b2c3d4
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "rcrm0a1b2c3d4"
down_revision: Union[str, Sequence[str], None] = "rsub0a1b2c3d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "crm_accounts",
        sa.Column("robot_submission_id", sa.Integer(), nullable=True),
    )
    op.create_index(
        "ix_crm_accounts_robot_submission_id",
        "crm_accounts",
        ["robot_submission_id"],
    )
    # FK is best-effort: skip on SQLite (no ALTER ADD CONSTRAINT) — the column +
    # index are what the hub query needs; app enforces the relationship.
    bind = op.get_bind()
    if bind.dialect.name != "sqlite":
        op.create_foreign_key(
            "fk_crm_accounts_robot_submission_id",
            "crm_accounts",
            "robot_submissions",
            ["robot_submission_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "sqlite":
        op.drop_constraint(
            "fk_crm_accounts_robot_submission_id", "crm_accounts", type_="foreignkey"
        )
    op.drop_index("ix_crm_accounts_robot_submission_id", table_name="crm_accounts")
    op.drop_column("crm_accounts", "robot_submission_id")
