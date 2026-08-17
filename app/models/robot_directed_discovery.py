"""Robot-directed discovery — thin universal core.

Universal columns describe claim + reasoning.
Physics live in requirements JSONB (extension layer).

Semantics (locked):
  work_claim     — physical work appears to occur here
  robot_job      — work is defined enough + robot-compatible to investigate
                   (solution-neutral; not owned by a robot)
  robot_job_match — this particular robot appears capable of doing it
  discovery_profile_id — which profile's search caused us to find the job
"""
from __future__ import annotations

import uuid

from sqlalchemy import (
    CheckConstraint,
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


class RobotCapabilityProfile(Base):
    """Envelope-derived: what physical actions this robot can perform."""

    __tablename__ = "robot_capability_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_key = Column(String(120), nullable=False, unique=True, index=True)
    display_name = Column(String(240), nullable=False)
    manufacturer = Column(String(120), nullable=True)
    product_url = Column(String(512), nullable=True)
    capability_family = Column(String(64), nullable=False, index=True)
    # transport_amr | floor_scrub | inspection_mobile | manipulator | other
    can_actions = Column(JSONB, nullable=False, server_default="[]")
    cannot_or_weak = Column(JSONB, nullable=False, server_default="[]")
    search_vocabulary = Column(JSONB, nullable=False, server_default="{}")
    envelope_path = Column(String(512), nullable=True)
    source = Column(String(64), nullable=False, server_default="envelope_v1")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class WorkClaim(Base):
    """First-class uncertainty: work probably occurs here — not a failed job."""

    __tablename__ = "work_claims"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_key = Column(String(160), nullable=False, unique=True, index=True)
    company_name = Column(String(240), nullable=False, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True)
    locality = Column(String(240), nullable=True)
    worksite_label = Column(String(240), nullable=True)
    observed_workflow = Column(Text, nullable=False)
    operating_context = Column(String(64), nullable=True, index=True)
    existence_confidence = Column(Float, nullable=False, server_default="0.5")
    status = Column(String(32), nullable=False, server_default="watching", index=True)
    # watching | matured | rejected | superseded
    capability_family_hint = Column(String(64), nullable=True)
    # Soft string today; may later become discovery_run_id FK — keep opaque.
    source_run = Column(String(120), nullable=True)
    extras = Column(JSONB, nullable=False, server_default="{}")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class JobEvidence(Base):
    """Evidence must attach to a claim and/or a job (not orphans)."""

    __tablename__ = "job_evidence"
    __table_args__ = (
        CheckConstraint(
            "work_claim_id IS NOT NULL OR robot_job_id IS NOT NULL",
            name="ck_job_evidence_has_parent",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    work_claim_id = Column(UUID(as_uuid=True), ForeignKey("work_claims.id", ondelete="CASCADE"), nullable=True, index=True)
    robot_job_id = Column(UUID(as_uuid=True), ForeignKey("robot_jobs.id", ondelete="CASCADE"), nullable=True, index=True)
    evidence_grade = Column(String(8), nullable=False, server_default="E3")  # E1..E4
    source_url = Column(String(1024), nullable=True)
    source_title = Column(String(480), nullable=True)
    excerpt = Column(Text, nullable=True)
    observed_at = Column(DateTime(timezone=True), nullable=True)
    extras = Column(JSONB, nullable=False, server_default="{}")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class AutomationInterpretation(Base):
    """How a specific robot profile would own part of a claimed workflow."""

    __tablename__ = "automation_interpretations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    work_claim_id = Column(
        UUID(as_uuid=True), ForeignKey("work_claims.id", ondelete="CASCADE"), nullable=False, index=True
    )
    profile_id = Column(
        UUID(as_uuid=True),
        ForeignKey("robot_capability_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    human_portion = Column(Text, nullable=True)
    robot_portion = Column(Text, nullable=True)
    action_class = Column(String(32), nullable=False, server_default="SPECULATIVE")
    # DIRECT | DERIVED | SPECULATIVE
    evidence_grade = Column(String(8), nullable=False, server_default="E4")
    transformation_confidence = Column(String(8), nullable=False, server_default="L")  # H|M|L
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("work_claim_id", "profile_id", name="uq_automation_interp_claim_profile"),
    )


class RobotJob(Base):
    """Promoted robot-compatible task — solution-neutral.

    Physics in requirements JSONB. Ownership of *who can do it* lives on
    robot_job_match. discovery_profile_id is provenance only.
    """

    __tablename__ = "robot_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_key = Column(String(160), nullable=False, unique=True, index=True)
    work_claim_id = Column(
        UUID(as_uuid=True), ForeignKey("work_claims.id", ondelete="SET NULL"), nullable=True, index=True
    )
    # Provenance: which capability search discovered this work — not ownership.
    discovery_profile_id = Column(
        UUID(as_uuid=True),
        ForeignKey("robot_capability_profiles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    company_name = Column(String(240), nullable=False, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True)
    locality = Column(String(240), nullable=True)
    worksite_label = Column(String(240), nullable=True)
    action = Column(String(120), nullable=False)
    target = Column(String(120), nullable=True)
    operating_context = Column(String(64), nullable=True, index=True)
    robot_compatible_task = Column(Text, nullable=False)
    observed_workflow = Column(Text, nullable=True)
    why_job = Column(Text, nullable=True)
    existence_confidence = Column(Float, nullable=False, server_default="0.7")
    definition_completeness = Column(Float, nullable=False, server_default="0.4")
    automation_state = Column(String(64), nullable=False, server_default="unknown")
    commercial_availability = Column(String(64), nullable=False, server_default="unknown")
    investigate_status = Column(String(16), nullable=False, server_default="weak", index=True)
    # yes | weak | no
    promotion_class = Column(String(32), nullable=False, server_default="DERIVED")
    evidence_grade = Column(String(8), nullable=False, server_default="E2")
    # Provenance only — which family lens found it. Compatibility is many via matches.
    discovered_via_capability_family = Column(String(64), nullable=True, index=True)
    requirements = Column(JSONB, nullable=False, server_default="{}")
    unknowns = Column(JSONB, nullable=False, server_default="[]")
    source_run = Column(String(120), nullable=True)  # opaque; future discovery_run_id
    provenance = Column(JSONB, nullable=False, server_default="{}")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class RobotJobMatch(Base):
    """Which robots can perform a (solution-neutral) robot_job."""

    __tablename__ = "robot_job_matches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    robot_job_id = Column(
        UUID(as_uuid=True), ForeignKey("robot_jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    profile_id = Column(
        UUID(as_uuid=True),
        ForeignKey("robot_capability_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    fit = Column(String(8), nullable=False, server_default="M")  # H|M|L
    match_score = Column(Float, nullable=False, server_default="0.5")
    hard_blockers = Column(JSONB, nullable=False, server_default="[]")
    why = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("robot_job_id", "profile_id", name="uq_robot_job_match_job_profile"),
    )
