"""Observe-only Understanding v1.0 production shadow observations."""

from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, Float, Integer, String, Text, func

from app.database import Base
from app.models.types import JSONB

# Human review labels — do not invent others without updating docs + tests.
SHADOW_REVIEW_LABELS = ("GOOD", "INCOMPLETE", "WRONG", "UNVERIFIABLE")

# Optional lightweight failure-theme tags (aggregate later; not required to review).
SHADOW_FAILURE_THEMES = (
    "pdf",
    "js_page",
    "cn_oem",
    "multi_product",
    "sparse_startup",
    "fetch_failure",
    "identity",
    "other",
)


class UnderstandingShadowObservation(Base):
    """
    One row per real URL → Robot Profile build on the product path.

    Observe-only: never mutates the profile returned to the user or job-match results.
    """

    __tablename__ = "understanding_shadow_observations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    correlation_id = Column(String(64), nullable=True, index=True)

    submitted_url = Column(Text, nullable=False, index=True)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    research_duration_ms = Column(Integer, nullable=True)

    company_name = Column(String(240), nullable=True)
    company_domain = Column(String(240), nullable=True, index=True)
    selected_product = Column(String(240), nullable=True)
    products_found = Column(JSONB, nullable=False, server_default="[]")

    profile_tier = Column(String(8), nullable=True, index=True)
    coverage_rate = Column(Float, nullable=True)
    coverage_level = Column(String(16), nullable=True)
    source_quality_rate = Column(Float, nullable=True)
    source_quality_level = Column(String(16), nullable=True)
    source_grounding_rate = Column(Float, nullable=True)
    research_morphology = Column(String(64), nullable=True)

    source_pack = Column(JSONB, nullable=False, server_default="[]")
    grounded_facts = Column(JSONB, nullable=False, server_default="[]")
    unknowns = Column(JSONB, nullable=False, server_default="[]")
    contradictions = Column(JSONB, nullable=False, server_default="[]")
    notes = Column(JSONB, nullable=False, server_default="[]")
    research_stages = Column(JSONB, nullable=False, server_default="[]")
    profile_snapshot = Column(JSONB, nullable=True)

    # Review loop
    review_label = Column(String(32), nullable=True, index=True)
    review_notes = Column(Text, nullable=True)
    failure_themes = Column(JSONB, nullable=False, server_default="[]")
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    reviewed_by = Column(String(120), nullable=True)
