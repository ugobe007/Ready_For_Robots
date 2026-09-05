"""Add Stripe billing columns to user_profiles.

Revision ID: p0q1r2s3t4u5
Revises: o9p0q1r2s3t4
Create Date: 2026-06-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "p0q1r2s3t4u5"
down_revision: Union[str, Sequence[str], None] = "o9p0q1r2s3t4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    cols = {c["name"] for c in insp.get_columns("user_profiles")}
    if "billing_tier" not in cols:
        op.add_column("user_profiles", sa.Column("billing_tier", sa.String(length=32), nullable=True))
    if "stripe_customer_id" not in cols:
        op.add_column("user_profiles", sa.Column("stripe_customer_id", sa.String(length=120), nullable=True))
    if "stripe_subscription_id" not in cols:
        op.add_column("user_profiles", sa.Column("stripe_subscription_id", sa.String(length=120), nullable=True))
    if "stripe_subscription_status" not in cols:
        op.add_column("user_profiles", sa.Column("stripe_subscription_status", sa.String(length=40), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    cols = {c["name"] for c in insp.get_columns("user_profiles")}
    for name in ("stripe_subscription_status", "stripe_subscription_id", "stripe_customer_id", "billing_tier"):
        if name in cols:
            op.drop_column("user_profiles", name)
