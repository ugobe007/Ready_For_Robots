"""Deployment Evidence — public-source deployment intelligence (not live telemetry)."""
from __future__ import annotations

import uuid

from sqlalchemy import (
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


class DeploymentSource(Base):
    __tablename__ = "deployment_sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url = Column(Text, nullable=False, unique=True)
    source_type = Column(String(64), nullable=False, server_default="public_news", index=True)
    source_tier = Column(String(8), nullable=False, server_default="F", index=True)  # A–F
    title = Column(String(480), nullable=True)
    domain = Column(String(240), nullable=True, index=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    fetched_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    raw_excerpt = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class DeploymentEvent(Base):
    """One claimed deployment / agreement / pilot linked into the Work Graph."""

    __tablename__ = "deployment_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    deployment_id = Column(String(64), nullable=False, unique=True, index=True)
    vendor_name = Column(String(240), nullable=True, index=True)
    manufacturer_id = Column(String(64), nullable=True, index=True)
    robot_model = Column(String(240), nullable=True, index=True)
    customer_name = Column(String(240), nullable=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True)
    facility_name = Column(String(240), nullable=True)
    facility_id = Column(UUID(as_uuid=True), ForeignKey("facilities.id", ondelete="SET NULL"), nullable=True)
    industry = Column(String(120), nullable=True)
    work_type = Column(String(120), nullable=True)
    workflow = Column(JSONB, nullable=False, server_default="{}")  # origin/action/destination
    deployment_stage = Column(String(64), nullable=False, server_default="UNKNOWN", index=True)
    evidence_level = Column(String(8), nullable=False, server_default="F", index=True)
    confidence = Column(Float, nullable=False, server_default="0")
    work_unit_id = Column(String(120), nullable=True, index=True)
    performed_primitives = Column(JSONB, nullable=False, server_default="[]")
    robots_announced = Column(Integer, nullable=True)
    robots_committed = Column(Integer, nullable=True)
    robots_pilot = Column(Integer, nullable=True)
    robots_live = Column(Integer, nullable=True)
    robots_verified = Column(Integer, nullable=True)
    sites_announced = Column(Integer, nullable=True)
    sites_live = Column(Integer, nullable=True)
    sites_verified = Column(Integer, nullable=True)
    primary_source_id = Column(UUID(as_uuid=True), ForeignKey("deployment_sources.id", ondelete="SET NULL"), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class DeploymentEvidence(Base):
    """Individual claim/excerpt supporting a deployment event."""

    __tablename__ = "deployment_evidence"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    deployment_event_id = Column(
        UUID(as_uuid=True), ForeignKey("deployment_events.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_id = Column(UUID(as_uuid=True), ForeignKey("deployment_sources.id", ondelete="CASCADE"), nullable=False)
    claim_text = Column(Text, nullable=False)
    evidence_level = Column(String(8), nullable=False, server_default="F")
    confidence = Column(Float, nullable=False, server_default="0")
    supports_stage = Column(String(64), nullable=True)
    extracted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("deployment_event_id", "source_id", "claim_text", name="uq_deployment_evidence_claim"),
    )


class DeploymentMetric(Base):
    __tablename__ = "deployment_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    deployment_event_id = Column(
        UUID(as_uuid=True), ForeignKey("deployment_events.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_id = Column(UUID(as_uuid=True), ForeignKey("deployment_sources.id", ondelete="SET NULL"), nullable=True)
    metric_key = Column(String(64), nullable=False, index=True)
    metric_value_numeric = Column(Float, nullable=True)
    metric_value_text = Column(String(240), nullable=True)
    unit = Column(String(32), nullable=True)
    confidence = Column(Float, nullable=False, server_default="0.5")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
