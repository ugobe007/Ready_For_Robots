"""Add user tables (user_profiles, user_saved_companies, user_lists, user_list_companies, ai_reports)

Revision ID: a1b2c3d4e5f6
Revises: 3b95a4c9c416
Create Date: 2026-03-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '3b95a4c9c416'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('user_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('display_name', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_user_profiles_email', 'user_profiles', ['email'], unique=False)

    op.create_table('user_saved_companies',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('company_name', sa.String(), nullable=False),
        sa.Column('industry', sa.String(), nullable=True),
        sa.Column('tier', sa.String(), nullable=True),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('website', sa.String(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('saved_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'company_id', name='uq_user_saved_user_company')
    )
    op.create_index('ix_user_saved_user_id', 'user_saved_companies', ['user_id'], unique=False)

    op.create_table('user_lists',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_user_lists_user_id', 'user_lists', ['user_id'], unique=False)

    op.create_table('user_list_companies',
        sa.Column('list_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('company_name', sa.String(), nullable=False),
        sa.Column('added_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('list_id', 'company_id')
    )

    op.create_table('ai_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('company_name', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('report_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('summary_card', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_ai_reports_user_id', 'ai_reports', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_ai_reports_user_id', table_name='ai_reports')
    op.drop_table('ai_reports')
    op.drop_table('user_list_companies')
    op.drop_index('ix_user_lists_user_id', table_name='user_lists')
    op.drop_table('user_lists')
    op.drop_index('ix_user_saved_user_id', table_name='user_saved_companies')
    op.drop_table('user_saved_companies')
    op.drop_index('ix_user_profiles_email', table_name='user_profiles')
    op.drop_table('user_profiles')
