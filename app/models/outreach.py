"""Cal outreach send and reply tracking for SCOUT workflows."""
from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func

from app.database import Base
from app.models.types import JSONB, UUID


class OutreachMessage(Base):
    __tablename__ = "outreach_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    crm_account_id = Column(UUID(as_uuid=True), ForeignKey("crm_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True)
    sender_user_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id", ondelete="SET NULL"), nullable=True, index=True)
    to_email = Column(String(320), nullable=False, index=True)
    from_email = Column(String(320), nullable=True)
    reply_to = Column(String(320), nullable=True, index=True)
    reply_token = Column(String(80), nullable=False, unique=True, index=True)
    subject = Column(String(512), nullable=False)
    body_text = Column(Text, nullable=False)
    send_identity = Column(String(32), nullable=False, server_default="scout")
    resend_id = Column(String(128), nullable=True, index=True)
    status = Column(String(32), nullable=False, server_default="queued", index=True)
    payload = Column(JSONB, nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class OutreachReply(Base):
    __tablename__ = "outreach_replies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    outreach_message_id = Column(
        UUID(as_uuid=True),
        ForeignKey("outreach_messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    crm_account_id = Column(UUID(as_uuid=True), ForeignKey("crm_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True)
    from_email = Column(String(320), nullable=True, index=True)
    to_email = Column(String(320), nullable=True)
    subject = Column(String(512), nullable=True)
    body_text = Column(Text, nullable=True)
    raw_payload = Column(JSONB, nullable=True)
    # Reply understanding — populated by the inbound webhook classifier so the
    # weekly learning report can attribute outcomes to a specific outreach angle.
    detected_intent = Column(String(32), nullable=True, index=True)
    sentiment = Column(String(16), nullable=True)
    received_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
