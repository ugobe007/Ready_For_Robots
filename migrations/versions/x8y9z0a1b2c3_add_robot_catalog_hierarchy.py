"""Robot catalog hierarchy — manufacturers, families, models, configurations.

Revision ID: x8y9z0a1b2c3
Revises: w7x8y9z0a1b2
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "x8y9z0a1b2c3"
down_revision: Union[str, Sequence[str], None] = "w7x8y9z0a1b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _uuid():
    return postgresql.UUID(as_uuid=True).with_variant(sa.String(36), "sqlite")


def _json():
    return postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite")


def upgrade() -> None:
    op.create_table(
        "manufacturers",
        sa.Column("id", _uuid(), primary_key=True, nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("name", sa.String(length=240), nullable=False),
        sa.Column("website", sa.Text(), nullable=True),
        sa.Column("country", sa.String(length=80), nullable=True),
        sa.Column("robot_company_id", sa.Integer(), sa.ForeignKey("robot_companies.id", ondelete="SET NULL"), nullable=True),
        sa.Column("calibration_tier", sa.Integer(), server_default="2", nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("external_refs", _json(), server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("slug", name="uq_manufacturers_slug"),
    )
    op.create_index("ix_manufacturers_slug", "manufacturers", ["slug"])
    op.create_index("ix_manufacturers_name", "manufacturers", ["name"])
    op.create_index("ix_manufacturers_calibration_tier", "manufacturers", ["calibration_tier"])
    op.create_index("ix_manufacturers_robot_company_id", "manufacturers", ["robot_company_id"])

    op.create_table(
        "robot_families",
        sa.Column("id", _uuid(), primary_key=True, nullable=False),
        sa.Column("manufacturer_id", _uuid(), sa.ForeignKey("manufacturers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("slug", sa.String(length=160), nullable=False),
        sa.Column("name", sa.String(length=240), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("primary_class", sa.String(length=80), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("manufacturer_id", "slug", name="uq_robot_family_mfr_slug"),
    )
    op.create_index("ix_robot_families_manufacturer_id", "robot_families", ["manufacturer_id"])
    op.create_index("ix_robot_families_slug", "robot_families", ["slug"])
    op.create_index("ix_robot_families_primary_class", "robot_families", ["primary_class"])

    op.create_table(
        "robot_models",
        sa.Column("id", _uuid(), primary_key=True, nullable=False),
        sa.Column("manufacturer_id", _uuid(), sa.ForeignKey("manufacturers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("family_id", _uuid(), sa.ForeignKey("robot_families.id", ondelete="CASCADE"), nullable=False),
        sa.Column("slug", sa.String(length=160), nullable=False),
        sa.Column("name", sa.String(length=240), nullable=False),
        sa.Column("primary_class", sa.String(length=80), nullable=False),
        sa.Column("work_to_map", _json(), server_default="[]", nullable=False),
        sa.Column("calibration_tier", sa.Integer(), server_default="2", nullable=False),
        sa.Column("commercial_maturity", sa.String(length=32), server_default="unknown", nullable=False),
        sa.Column("availability_geography", _json(), nullable=True),
        sa.Column("deployment_evidence", _json(), nullable=True),
        sa.Column("known_customers", _json(), nullable=True),
        sa.Column("pricing_model", sa.String(length=80), nullable=True),
        sa.Column("direct_sales", sa.Boolean(), nullable=True),
        sa.Column("distributor_sales", sa.Boolean(), nullable=True),
        sa.Column("integrator_sales", sa.Boolean(), nullable=True),
        sa.Column("raas_available", sa.Boolean(), nullable=True),
        sa.Column("service_regions", _json(), nullable=True),
        sa.Column("product_url", sa.Text(), nullable=True),
        sa.Column("capability_stubs", _json(), server_default="[]", nullable=False),
        sa.Column("work_envelope_stubs", _json(), server_default="[]", nullable=False),
        sa.Column("external_refs", _json(), server_default="{}", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("slug", name="uq_robot_models_slug"),
    )
    op.create_index("ix_robot_models_manufacturer_id", "robot_models", ["manufacturer_id"])
    op.create_index("ix_robot_models_family_id", "robot_models", ["family_id"])
    op.create_index("ix_robot_models_slug", "robot_models", ["slug"])
    op.create_index("ix_robot_models_name", "robot_models", ["name"])
    op.create_index("ix_robot_models_primary_class", "robot_models", ["primary_class"])
    op.create_index("ix_robot_models_calibration_tier", "robot_models", ["calibration_tier"])
    op.create_index("ix_robot_models_commercial_maturity", "robot_models", ["commercial_maturity"])
    op.create_index("ix_robot_models_is_active", "robot_models", ["is_active"])

    op.create_table(
        "robot_configurations",
        sa.Column("id", _uuid(), primary_key=True, nullable=False),
        sa.Column("robot_model_id", _uuid(), sa.ForeignKey("robot_models.id", ondelete="CASCADE"), nullable=False),
        sa.Column("slug", sa.String(length=160), nullable=False),
        sa.Column("name", sa.String(length=240), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("options", _json(), server_default="{}", nullable=False),
        sa.Column("is_default", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("robot_model_id", "slug", name="uq_robot_config_model_slug"),
    )
    op.create_index("ix_robot_configurations_robot_model_id", "robot_configurations", ["robot_model_id"])
    op.create_index("ix_robot_configurations_slug", "robot_configurations", ["slug"])

    op.add_column("robots", sa.Column("manufacturer_id", _uuid(), nullable=True))
    op.add_column("robots", sa.Column("robot_model_id", _uuid(), nullable=True))
    op.add_column("robots", sa.Column("robot_configuration_id", _uuid(), nullable=True))
    op.create_foreign_key("fk_robots_manufacturer_id", "robots", "manufacturers", ["manufacturer_id"], ["id"], ondelete="SET NULL")
    op.create_foreign_key("fk_robots_robot_model_id", "robots", "robot_models", ["robot_model_id"], ["id"], ondelete="SET NULL")
    op.create_foreign_key("fk_robots_robot_configuration_id", "robots", "robot_configurations", ["robot_configuration_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_robots_manufacturer_id", "robots", ["manufacturer_id"])
    op.create_index("ix_robots_robot_model_id", "robots", ["robot_model_id"])
    op.create_index("ix_robots_robot_configuration_id", "robots", ["robot_configuration_id"])

    op.add_column("robot_profile_versions", sa.Column("robot_model_id", _uuid(), nullable=True))
    op.add_column("robot_profile_versions", sa.Column("robot_configuration_id", _uuid(), nullable=True))
    op.add_column("robot_profile_versions", sa.Column("commercial_maturity", sa.String(length=32), nullable=True))
    op.create_foreign_key(
        "fk_robot_profile_versions_robot_model_id",
        "robot_profile_versions",
        "robot_models",
        ["robot_model_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_robot_profile_versions_robot_configuration_id",
        "robot_profile_versions",
        "robot_configurations",
        ["robot_configuration_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_robot_profile_versions_robot_model_id", "robot_profile_versions", ["robot_model_id"])
    op.create_index("ix_robot_profile_versions_robot_configuration_id", "robot_profile_versions", ["robot_configuration_id"])


def downgrade() -> None:
    op.drop_index("ix_robot_profile_versions_robot_configuration_id", table_name="robot_profile_versions")
    op.drop_index("ix_robot_profile_versions_robot_model_id", table_name="robot_profile_versions")
    op.drop_constraint("fk_robot_profile_versions_robot_configuration_id", "robot_profile_versions", type_="foreignkey")
    op.drop_constraint("fk_robot_profile_versions_robot_model_id", "robot_profile_versions", type_="foreignkey")
    op.drop_column("robot_profile_versions", "commercial_maturity")
    op.drop_column("robot_profile_versions", "robot_configuration_id")
    op.drop_column("robot_profile_versions", "robot_model_id")

    op.drop_index("ix_robots_robot_configuration_id", table_name="robots")
    op.drop_index("ix_robots_robot_model_id", table_name="robots")
    op.drop_index("ix_robots_manufacturer_id", table_name="robots")
    op.drop_constraint("fk_robots_robot_configuration_id", "robots", type_="foreignkey")
    op.drop_constraint("fk_robots_robot_model_id", "robots", type_="foreignkey")
    op.drop_constraint("fk_robots_manufacturer_id", "robots", type_="foreignkey")
    op.drop_column("robots", "robot_configuration_id")
    op.drop_column("robots", "robot_model_id")
    op.drop_column("robots", "manufacturer_id")

    op.drop_table("robot_configurations")
    op.drop_table("robot_models")
    op.drop_table("robot_families")
    op.drop_table("manufacturers")
