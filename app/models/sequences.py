"""Outreach sequence models — multi-step cadences with pause-on-reply."""
from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func

from app.database import Base
from app.models.types import JSONB, UUID


class OutreachSequence(Base):
    __tablename__ = "outreach_sequences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=True, index=True)
    name = Column(String(120), nullable=False)
    slug = Column(String(80), nullable=True, index=True)
    channel = Column(String(32), nullable=False, server_default="email")
    is_default = Column(Boolean, nullable=False, server_default="false")
    status = Column(String(32), nullable=False, server_default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class OutreachSequenceStep(Base):
    __tablename__ = "outreach_sequence_steps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sequence_id = Column(UUID(as_uuid=True), ForeignKey("outreach_sequences.id", ondelete="CASCADE"), nullable=False, index=True)
    step_number = Column(Integer, nullable=False)
    delay_days = Column(Integer, nullable=False, server_default="0")
    subject_template = Column(String(512), nullable=True)
    body_template = Column(Text, nullable=True)
    action_label = Column(String(120), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (UniqueConstraint("sequence_id", "step_number", name="uq_sequence_step_number"),)


class OutreachSequenceEnrollment(Base):
    __tablename__ = "outreach_sequence_enrollments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    sequence_id = Column(UUID(as_uuid=True), ForeignKey("outreach_sequences.id", ondelete="CASCADE"), nullable=False, index=True)
    crm_account_id = Column(UUID(as_uuid=True), ForeignKey("crm_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    current_step = Column(Integer, nullable=False, server_default="1")
    status = Column(String(32), nullable=False, server_default="active", index=True)
    enrolled_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_step_at = Column(DateTime(timezone=True), nullable=True)
    next_step_at = Column(DateTime(timezone=True), nullable=True, index=True)
    paused_reason = Column(String(120), nullable=True)
    payload = Column(JSONB, nullable=False, server_default="{}")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (UniqueConstraint("crm_account_id", "sequence_id", name="uq_account_sequence_enrollment"),)
