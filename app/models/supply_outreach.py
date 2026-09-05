"""Supply-side marketplace outreach tracking."""
from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, func

from app.database import Base
from app.models.types import JSONB, UUID


class SupplyOutreachMessage(Base):
    __tablename__ = "supply_outreach_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    robot_company_id = Column(Integer, ForeignKey("robot_companies.id", ondelete="CASCADE"), nullable=False, index=True)
    to_emails = Column(JSONB, nullable=False)
    from_email = Column(String(320), nullable=True)
    reply_to = Column(String(320), nullable=True, index=True)
    reply_token = Column(String(80), nullable=False, unique=True, index=True)
    subject = Column(String(512), nullable=False)
    body_text = Column(Text, nullable=False)
    template_type = Column(String(80), nullable=False, server_default="supply_pipeline")
    resend_id = Column(String(128), nullable=True, index=True)
    status = Column(String(32), nullable=False, server_default="draft_approved", index=True)
    is_test = Column(Boolean, nullable=False, server_default="false", index=True)
    payload = Column(JSONB, nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True, index=True)
    sent_at = Column(DateTime(timezone=True), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class SupplyOutreachReply(Base):
    __tablename__ = "supply_outreach_replies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supply_outreach_message_id = Column(
        UUID(as_uuid=True),
        ForeignKey("supply_outreach_messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    robot_company_id = Column(Integer, ForeignKey("robot_companies.id", ondelete="CASCADE"), nullable=False, index=True)
    from_email = Column(String(320), nullable=True, index=True)
    to_email = Column(String(320), nullable=True)
    subject = Column(String(512), nullable=True)
    body_text = Column(Text, nullable=True)
    raw_payload = Column(JSONB, nullable=True)
    received_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
