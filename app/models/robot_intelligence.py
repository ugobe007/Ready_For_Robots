"""V1 robot analysis jobs, profile versions, capabilities, and evidence claims."""
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


class EvidenceClaim(Base):
    __tablename__ = "evidence_claims"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type = Column(String(64), nullable=False, index=True)
    entity_id = Column(String(80), nullable=False, index=True)
    field_path = Column(String(160), nullable=False, index=True)
    value = Column(JSONB, nullable=True)
    truth_state = Column(String(32), nullable=False, index=True)
    source_type = Column(String(64), nullable=True)
    source_url = Column(Text, nullable=True)
    source_id = Column(String(120), nullable=True, index=True)
    excerpt = Column(Text, nullable=True)
    observed_at = Column(DateTime(timezone=True), nullable=False)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    confidence = Column(Float, nullable=False, server_default="0")
    supersedes_claim_id = Column(UUID(as_uuid=True), ForeignKey("evidence_claims.id"), nullable=True)
    recorded_by_user_id = Column(UUID(as_uuid=True), nullable=True)


class RobotAnalysis(Base):
    __tablename__ = "robot_analyses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_token = Column(String(64), nullable=False, unique=True, index=True)
    status = Column(String(64), nullable=False, server_default="queued", index=True)
    progress = Column(Integer, nullable=False, server_default="0")
    message = Column(Text, nullable=True)
    retryable = Column(Boolean, nullable=False, server_default="false")
    warnings = Column(JSONB, nullable=False, server_default="[]")

    source_url = Column(Text, nullable=True)
    normalized_url = Column(Text, nullable=True, index=True)
    description = Column(Text, nullable=True)

    robot_id = Column(Integer, ForeignKey("robots.id", ondelete="SET NULL"), nullable=True, index=True)
    draft_profile = Column(JSONB, nullable=True)
    profile_etag = Column(String(64), nullable=True)
    confirmed_profile_version_id = Column(UUID(as_uuid=True), nullable=True)
    opportunity_search_id = Column(UUID(as_uuid=True), nullable=True)

    requester_scope = Column(String(120), nullable=True, index=True)
    created_by_user_id = Column(UUID(as_uuid=True), nullable=True)
    raw_fetch = Column(JSONB, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class RobotProfileVersion(Base):
    __tablename__ = "robot_profile_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    robot_id = Column(Integer, ForeignKey("robots.id", ondelete="CASCADE"), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    source_url = Column(Text, nullable=True)
    manufacturer = Column(String(240), nullable=True)
    model = Column(String(240), nullable=True)
    category = Column(String(64), nullable=True, index=True)
    robot_model_id = Column(UUID(as_uuid=True), ForeignKey("robot_models.id", ondelete="SET NULL"), nullable=True, index=True)
    robot_configuration_id = Column(
        UUID(as_uuid=True), ForeignKey("robot_configurations.id", ondelete="SET NULL"), nullable=True, index=True
    )
    work_envelope = Column(JSONB, nullable=False, server_default="[]")
    physical_capabilities = Column(JSONB, nullable=False, server_default="{}")
    commercial_status = Column(String(64), nullable=True)
    commercial_maturity = Column(String(32), nullable=True)
    service_geography = Column(JSONB, nullable=True)
    verification_state = Column(String(32), nullable=False, server_default="inferred")
    confidence = Column(Float, nullable=False, server_default="0")
    created_by_user_id = Column(UUID(as_uuid=True), nullable=True)
    supersedes_version_id = Column(
        UUID(as_uuid=True), ForeignKey("robot_profile_versions.id", ondelete="SET NULL"), nullable=True
    )
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("robot_analyses.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (UniqueConstraint("robot_id", "version", name="uq_robot_profile_version"),)


class RobotCapability(Base):
    __tablename__ = "robot_capabilities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    robot_profile_version_id = Column(
        UUID(as_uuid=True),
        ForeignKey("robot_profile_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    capability_key = Column(String(120), nullable=False)
    operator = Column(String(16), nullable=True)
    numeric_value = Column(Float, nullable=True)
    text_value = Column(Text, nullable=True)
    unit = Column(String(32), nullable=True)
    constraints = Column(JSONB, nullable=False, server_default="{}")
    truth_state = Column(String(32), nullable=False)
    confidence = Column(Float, nullable=False, server_default="0")
    claim_ids = Column(JSONB, nullable=False, server_default="[]")

    __table_args__ = (
        UniqueConstraint("robot_profile_version_id", "capability_key", name="uq_robot_capability_key"),
    )
