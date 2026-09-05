"""Lead research updates and user notifications."""
from __future__ import annotations

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.types import JSONB, UUID


class LeadResearchUpdate(Base):
    __tablename__ = "lead_research_updates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    update_type = Column(String(64), nullable=False, index=True)
    title = Column(String(512), nullable=False)
    summary = Column(Text, nullable=False)
    source_url = Column(String(1024), nullable=True)
    source_domain = Column(String(255), nullable=True, index=True)
    significance_score = Column(Float, nullable=False, server_default="0")
    status = Column(String(32), nullable=False, server_default="new", index=True)
    dedupe_fingerprint = Column(String(80), nullable=False, unique=True, index=True)
    payload = Column(JSONB, nullable=True)
    detected_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    company = relationship("Company")


class UserNotification(Base):
    __tablename__ = "user_notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True)
    research_update_id = Column(
        Integer,
        ForeignKey("lead_research_updates.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    notification_type = Column(String(64), nullable=False, index=True)
    title = Column(String(512), nullable=False)
    body = Column(Text, nullable=False)
    delivery_state = Column(String(32), nullable=False, server_default="in_app", index=True)
    payload = Column(JSONB, nullable=True)
    read_at = Column(DateTime(timezone=True), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    company = relationship("Company")
    research_update = relationship("LeadResearchUpdate")
