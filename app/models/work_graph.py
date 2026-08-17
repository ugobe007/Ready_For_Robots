"""Persisted WORK units + best robot matches (primitives.v1 spine)."""
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


class WorkUnitRecord(Base):
    __tablename__ = "work_units"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    work_unit_id = Column(String(120), nullable=False, unique=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True)
    facility_id = Column(UUID(as_uuid=True), ForeignKey("facilities.id", ondelete="SET NULL"), nullable=True)
    workflow_family = Column(String(64), nullable=False, server_default="unknown", index=True)
    task = Column(String(480), nullable=True)
    object = Column(String(120), nullable=True)
    origin = Column(String(120), nullable=True)
    destination = Column(String(120), nullable=True)
    action_chain = Column(JSONB, nullable=False, server_default="[]")
    primitive_evidence = Column(JSONB, nullable=False, server_default="[]")
    payload_kg_hint = Column(Float, nullable=True)
    shift_hint = Column(String(64), nullable=True)
    job_title = Column(String(240), nullable=True)
    confidence = Column(Float, nullable=False, server_default="0")
    truth_state = Column(String(32), nullable=False, server_default="SIGNAL_INFERRED")
    source = Column(String(64), nullable=False, server_default="work_unit_reconstruct_v1")
    source_text_hash = Column(String(64), nullable=True, index=True)
    raw_excerpt = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class WorkMatchRecord(Base):
    """Best Knowledge-layer ROBOT MATCHES WORK edge for a company/work unit."""

    __tablename__ = "work_matches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    work_unit_pk = Column(UUID(as_uuid=True), ForeignKey("work_units.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    manufacturer_id = Column(String(64), nullable=True, index=True)
    manufacturer_name = Column(String(240), nullable=True)
    match_score = Column(Float, nullable=False, server_default="0")
    work_match = Column(Float, nullable=True)
    work_match_label = Column(String(64), nullable=True)
    match_mode = Column(String(64), nullable=True)
    hard_blockers = Column(JSONB, nullable=False, server_default="[]")
    matched_primitives = Column(JSONB, nullable=False, server_default="[]")
    missing_primitives = Column(JSONB, nullable=False, server_default="[]")
    required_primitives = Column(JSONB, nullable=False, server_default="[]")
    supported_primitives = Column(JSONB, nullable=False, server_default="[]")
    truth_state = Column(String(32), nullable=False, server_default="SIGNAL_INFERRED")
    source = Column(String(64), nullable=False, server_default="market_graph_loop")
    why = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("company_id", "manufacturer_id", name="uq_work_match_company_manufacturer"),
    )
