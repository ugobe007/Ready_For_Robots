"""Durable ledger of robots submitted through the front door.

One row per canonical product URL — the missing durable, ID'd, timestamped
record for "a robot URL pasted looking for work". Complements:
- ``understanding_shadow_observations`` (one row per *build*, audit/QA), and
- ``robot_companies`` (curated vendor lead DB / catalog).

Keyed by canonical URL so FIND identity stays isolated (#173): Agtonomy
qualify_robot still writes a row, and a later Greenfield paste does not
overwrite it. ``website_domain`` remains the host for grouping, not the
unique key.

Written best-effort (fail-open) so persistence never breaks the research
request.
"""
from __future__ import annotations

from sqlalchemy import Column, DateTime, Integer, String, Text, UniqueConstraint, func

from app.database import Base
from app.models.types import JSONB


class RobotSubmission(Base):
    __tablename__ = "robot_submissions"
    __table_args__ = (
        UniqueConstraint("canonical_url", name="uq_robot_submissions_canonical_url"),
    )

    # Clean integer ID number, parallel to companies.id / robots.id.
    id = Column(Integer, primary_key=True, index=True)

    # Dedupe key: one durable record per canonical robot URL.
    canonical_url = Column(Text, nullable=False, index=True)
    website_domain = Column(String(240), nullable=False, index=True)
    host = Column(String(240), nullable=True, index=True)
    submitted_url = Column(Text, nullable=False)

    # Identity (from the Understanding profile). Incomplete stays incomplete.
    company_name = Column(String(240), nullable=True)
    product_name = Column(String(240), nullable=True)
    robot_class = Column(String(64), nullable=True)
    profile_tier = Column(String(8), nullable=True, index=True)

    # Enrichment (from the match surfaces).
    capabilities = Column(JSONB, nullable=False, server_default="[]")
    matched_company_ids = Column(JSONB, nullable=False, server_default="[]")
    last_job_count = Column(Integer, nullable=True)      # corpus example matches
    last_match_count = Column(Integer, nullable=True)    # real buyer matches

    # How many times this robot has been submitted/researched.
    submission_count = Column(Integer, nullable=False, server_default="1")
    source = Column(String(120), nullable=True)

    first_seen_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_seen_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    last_matched_at = Column(DateTime(timezone=True), nullable=True)
    last_researched_at = Column(DateTime(timezone=True), nullable=True, index=True)
    research_status = Column(String(32), nullable=True, index=True)
    research_snippets = Column(JSONB, nullable=False, server_default="[]")

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<RobotSubmission {self.id} {self.canonical_url} x{self.submission_count}>"


class RobotPresentationRequest(Base):
    """Paid product-presentation offer for a robot company (value-first: after Job Cards)."""

    __tablename__ = "robot_presentation_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(64), nullable=True, index=True)
    canonical_url = Column(Text, nullable=False, index=True)
    submitted_url = Column(Text, nullable=False)
    company_name = Column(String(240), nullable=True)
    product_name = Column(String(240), nullable=True)
    # queued | paid_queued | building | ready | failed
    status = Column(String(32), nullable=False, server_default="queued", index=True)
    provider = Column(String(40), nullable=True)
    provider_job_id = Column(String(160), nullable=True)
    deck_url = Column(Text, nullable=True)
    note = Column(Text, nullable=True)
    paid = Column(String(8), nullable=False, server_default="false")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
