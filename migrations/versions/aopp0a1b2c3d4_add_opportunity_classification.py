"""Add opportunity classification to robot_jobs

Revision ID: aopp0a1b2c3d4
Revises: jcnt0a1b2c3d4
Create Date: 2026-10-12 02:35:00.000000

Adds opportunity_tier and opportunity_class columns to classify jobs:
- opportunity_tier: 1=robot_jobs, 2=signals, 3=human_labor
- opportunity_class: Detailed classification (11, 12, 21-24, 30, 0)

Only tier=1 (robot_jobs) should be in this table.
Tier=2 (signals) should be in signals table.
Tier=3 (human_labor) should be rejected at scraping.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'aopp0a1b2c3d4'
down_revision = 'jcnt0a1b2c3d4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add opportunity classification columns
    op.add_column('robot_jobs', sa.Column('opportunity_tier', sa.Integer(), nullable=True))
    op.add_column('robot_jobs', sa.Column('opportunity_class', sa.Integer(), nullable=True))
    
    # Add indexes for filtering
    op.create_index('idx_robot_jobs_opportunity_tier', 'robot_jobs', ['opportunity_tier'])
    op.create_index('idx_robot_jobs_opportunity_class', 'robot_jobs', ['opportunity_class'])
    
    # Set default values for existing rows (assume they need reclassification)
    op.execute("UPDATE robot_jobs SET opportunity_tier = 0, opportunity_class = 0 WHERE opportunity_tier IS NULL")


def downgrade() -> None:
    op.drop_index('idx_robot_jobs_opportunity_class', table_name='robot_jobs')
    op.drop_index('idx_robot_jobs_opportunity_tier', table_name='robot_jobs')
    op.drop_column('robot_jobs', 'opportunity_class')
    op.drop_column('robot_jobs', 'opportunity_tier')
