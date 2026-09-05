"""add_workflow_fields

Revision ID: 3b95a4c9c416
Revises: 62c6bf204268
Create Date: 2026-03-07 05:15:56.902786

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3b95a4c9c416'
down_revision: Union[str, Sequence[str], None] = '62c6bf204268'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add workflow tracking fields
    op.add_column('robot_companies', sa.Column('workflow_stage', sa.String(), nullable=True))
    op.add_column('robot_companies', sa.Column('next_action', sa.String(), nullable=True))
    op.add_column('robot_companies', sa.Column('next_action_date', sa.DateTime(), nullable=True))
    op.add_column('robot_companies', sa.Column('assigned_to', sa.String(), nullable=True))
    op.add_column('robot_companies', sa.Column('workflow_notes', sa.Text(), nullable=True))
    op.add_column('robot_companies', sa.Column('workflow_history', sa.JSON(), nullable=True))
    op.add_column('robot_companies', sa.Column('blockers', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove workflow fields
    op.drop_column('robot_companies', 'blockers')
    op.drop_column('robot_companies', 'workflow_history')
    op.drop_column('robot_companies', 'workflow_notes')
    op.drop_column('robot_companies', 'assigned_to')
    op.drop_column('robot_companies', 'next_action_date')
    op.drop_column('robot_companies', 'next_action')
    op.drop_column('robot_companies', 'workflow_stage')
