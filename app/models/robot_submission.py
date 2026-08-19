"""Durable ledger of robots submitted through the front door.

One row per robot (deduped by normalized website domain) — the missing durable,
ID'd, timestamped record for "a robot company that pasted its URL looking for
customers". Complements:
- ``understanding_shadow_observations`` (one row per *build*, audit/QA), and
- ``robot_companies`` (curated vendor lead DB / catalog).

This table is the entity that lets us trace: submitter (id) → capabilities →
matched real buyers (company_ids) → over time (first/last seen, counts). Written
best-effort (fail-open) so persistence never breaks the research/match request.
"""
from __future__ import annotations

from sqlalchemy import Column, DateTime, Integer, String, Text, func

from app.database import Base
from app.models.types import JSONB


class RobotSubmission(Base):
    __tablename__ = "robot_submissions"

    # Clean integer ID number, parallel to companies.id / robots.id.
    id = Column(Integer, primary_key=True, index=True)

    # Dedupe key: one durable record per robot vendor domain.
    website_domain = Column(String(240), nullable=False, unique=True, index=True)
    submitted_url = Column(Text, nullable=False)

    # Identity (from the Understanding profile).
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
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False, index=True
    )
    last_matched_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<RobotSubmission {self.id} {self.website_domain} x{self.submission_count}>"
