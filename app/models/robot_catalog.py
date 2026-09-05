"""Product catalog hierarchy: manufacturer → family → model → configuration."""
from __future__ import annotations

import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)

from app.database import Base
from app.models.types import JSONB, UUID


class Manufacturer(Base):
    __tablename__ = "manufacturers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug = Column(String(120), nullable=False, unique=True, index=True)
    name = Column(String(240), nullable=False, index=True)
    website = Column(Text, nullable=True)
    lookup_host = Column(String(240), nullable=True, index=True)
    country = Column(String(80), nullable=True)
    headquarters = Column(String(240), nullable=True)
    founded_year = Column(Integer, nullable=True)
    company_status = Column(String(64), nullable=False, server_default="active")
    vendor_role = Column(String(64), nullable=False, server_default="robot_oem", index=True)
    vendor_type = Column(String(64), nullable=False, server_default="oem", index=True)
    robot_categories = Column(JSONB, nullable=False, server_default="[]")
    primary_industries = Column(JSONB, nullable=False, server_default="[]")
    primary_work_types = Column(JSONB, nullable=False, server_default="[]")
    commercial_maturity = Column(String(32), nullable=False, server_default="unknown", index=True)
    sales_geography = Column(JSONB, nullable=False, server_default="[]")
    service_geography = Column(JSONB, nullable=False, server_default="[]")
    direct_sales = Column(Boolean, nullable=True)
    distributor_sales = Column(Boolean, nullable=True)
    integrator_sales = Column(Boolean, nullable=True)
    raas_available = Column(Boolean, nullable=True)
    known_robot_count = Column(Integer, nullable=True)
    active_model_count = Column(Integer, nullable=True)
    source_url = Column(Text, nullable=True)
    source_date = Column(String(32), nullable=True)
    verification_status = Column(String(64), nullable=False, server_default="unverified")
    confidence = Column(Float, nullable=False, server_default="0")
    us_availability = Column(String(64), nullable=True)
    sales_model = Column(String(120), nullable=True)
    robot_company_id = Column(
        Integer, ForeignKey("robot_companies.id", ondelete="SET NULL"), nullable=True, index=True
    )
    calibration_tier = Column(Integer, nullable=False, server_default="2", index=True)
    notes = Column(Text, nullable=True)
    external_refs = Column(JSONB, nullable=False, server_default="{}")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class RobotFamily(Base):
    __tablename__ = "robot_families"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    manufacturer_id = Column(
        UUID(as_uuid=True), ForeignKey("manufacturers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    slug = Column(String(160), nullable=False, index=True)
    name = Column(String(240), nullable=False)
    description = Column(Text, nullable=True)
    primary_class = Column(String(80), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (UniqueConstraint("manufacturer_id", "slug", name="uq_robot_family_mfr_slug"),)


class RobotModel(Base):
    __tablename__ = "robot_models"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    manufacturer_id = Column(
        UUID(as_uuid=True), ForeignKey("manufacturers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    family_id = Column(
        UUID(as_uuid=True), ForeignKey("robot_families.id", ondelete="CASCADE"), nullable=False, index=True
    )
    slug = Column(String(160), nullable=False, unique=True, index=True)
    name = Column(String(240), nullable=False, index=True)
    primary_class = Column(String(80), nullable=False, index=True)
    work_to_map = Column(JSONB, nullable=False, server_default="[]")
    calibration_tier = Column(Integer, nullable=False, server_default="2", index=True)
    commercial_maturity = Column(String(32), nullable=False, server_default="unknown", index=True)
    availability_geography = Column(JSONB, nullable=True)
    deployment_evidence = Column(JSONB, nullable=True)
    known_customers = Column(JSONB, nullable=True)
    pricing_model = Column(String(80), nullable=True)
    direct_sales = Column(Boolean, nullable=True)
    distributor_sales = Column(Boolean, nullable=True)
    integrator_sales = Column(Boolean, nullable=True)
    raas_available = Column(Boolean, nullable=True)
    service_regions = Column(JSONB, nullable=True)
    product_url = Column(Text, nullable=True)
    lookup_host = Column(String(240), nullable=True, index=True)
    capability_stubs = Column(JSONB, nullable=False, server_default="[]")
    work_envelope_stubs = Column(JSONB, nullable=False, server_default="[]")
    external_refs = Column(JSONB, nullable=False, server_default="{}")
    is_active = Column(Boolean, nullable=False, server_default="true", index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class RobotConfiguration(Base):
    __tablename__ = "robot_configurations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    robot_model_id = Column(
        UUID(as_uuid=True), ForeignKey("robot_models.id", ondelete="CASCADE"), nullable=False, index=True
    )
    slug = Column(String(160), nullable=False, index=True)
    name = Column(String(240), nullable=False)
    description = Column(Text, nullable=True)
    options = Column(JSONB, nullable=False, server_default="{}")
    is_default = Column(Boolean, nullable=False, server_default="false")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (UniqueConstraint("robot_model_id", "slug", name="uq_robot_config_model_slug"),)
