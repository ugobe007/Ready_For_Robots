"""Expand manufacturers into market-graph vendors (role, geography, maturity).

Revision ID: y9z0a1b2c3d4
Revises: x8y9z0a1b2c3
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "y9z0a1b2c3d4"
down_revision: Union[str, Sequence[str], None] = "x8y9z0a1b2c3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _json():
    return postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite")


def upgrade() -> None:
    op.add_column("manufacturers", sa.Column("vendor_role", sa.String(length=64), server_default="robot_oem", nullable=False))
    op.add_column("manufacturers", sa.Column("vendor_type", sa.String(length=64), server_default="oem", nullable=False))
    op.add_column("manufacturers", sa.Column("headquarters", sa.String(length=240), nullable=True))
    op.add_column("manufacturers", sa.Column("founded_year", sa.Integer(), nullable=True))
    op.add_column("manufacturers", sa.Column("company_status", sa.String(length=64), server_default="active", nullable=False))
    op.add_column("manufacturers", sa.Column("robot_categories", _json(), server_default="[]", nullable=False))
    op.add_column("manufacturers", sa.Column("primary_industries", _json(), server_default="[]", nullable=False))
    op.add_column("manufacturers", sa.Column("primary_work_types", _json(), server_default="[]", nullable=False))
    op.add_column("manufacturers", sa.Column("commercial_maturity", sa.String(length=32), server_default="unknown", nullable=False))
    op.add_column("manufacturers", sa.Column("sales_geography", _json(), server_default="[]", nullable=False))
    op.add_column("manufacturers", sa.Column("service_geography", _json(), server_default="[]", nullable=False))
    op.add_column("manufacturers", sa.Column("direct_sales", sa.Boolean(), nullable=True))
    op.add_column("manufacturers", sa.Column("distributor_sales", sa.Boolean(), nullable=True))
    op.add_column("manufacturers", sa.Column("integrator_sales", sa.Boolean(), nullable=True))
    op.add_column("manufacturers", sa.Column("raas_available", sa.Boolean(), nullable=True))
    op.add_column("manufacturers", sa.Column("known_robot_count", sa.Integer(), nullable=True))
    op.add_column("manufacturers", sa.Column("active_model_count", sa.Integer(), nullable=True))
    op.add_column("manufacturers", sa.Column("source_url", sa.Text(), nullable=True))
    op.add_column("manufacturers", sa.Column("source_date", sa.String(length=32), nullable=True))
    op.add_column("manufacturers", sa.Column("verification_status", sa.String(length=64), server_default="unverified", nullable=False))
    op.add_column("manufacturers", sa.Column("confidence", sa.Float(), server_default="0", nullable=False))
    op.add_column("manufacturers", sa.Column("us_availability", sa.String(length=64), nullable=True))
    op.add_column("manufacturers", sa.Column("sales_model", sa.String(length=120), nullable=True))
    op.create_index("ix_manufacturers_vendor_role", "manufacturers", ["vendor_role"])
    op.create_index("ix_manufacturers_vendor_type", "manufacturers", ["vendor_type"])
    op.create_index("ix_manufacturers_commercial_maturity", "manufacturers", ["commercial_maturity"])


def downgrade() -> None:
    op.drop_index("ix_manufacturers_commercial_maturity", table_name="manufacturers")
    op.drop_index("ix_manufacturers_vendor_type", table_name="manufacturers")
    op.drop_index("ix_manufacturers_vendor_role", table_name="manufacturers")
    for col in [
        "sales_model",
        "us_availability",
        "confidence",
        "verification_status",
        "source_date",
        "source_url",
        "active_model_count",
        "known_robot_count",
        "raas_available",
        "integrator_sales",
        "distributor_sales",
        "direct_sales",
        "service_geography",
        "sales_geography",
        "commercial_maturity",
        "primary_work_types",
        "primary_industries",
        "robot_categories",
        "company_status",
        "founded_year",
        "headquarters",
        "vendor_type",
        "vendor_role",
    ]:
        op.drop_column("manufacturers", col)
