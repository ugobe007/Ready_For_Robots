"""Internal operator calendar and meeting invites."""
from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func

from app.database import Base
from app.models.types import JSONB, UUID


class CalendarEvent(Base):
    __tablename__ = "calendar_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    owner_user_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id", ondelete="SET NULL"), nullable=True, index=True)
    sales_opportunity_id = Column(UUID(as_uuid=True), ForeignKey("sales_opportunities.id", ondelete="SET NULL"), nullable=True, index=True)
    crm_account_id = Column(UUID(as_uuid=True), ForeignKey("crm_accounts.id", ondelete="SET NULL"), nullable=True, index=True)
    robot_company_id = Column(Integer, ForeignKey("robot_companies.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(240), nullable=False)
    description = Column(Text, nullable=True)
    start_at = Column(DateTime(timezone=True), nullable=False, index=True)
    end_at = Column(DateTime(timezone=True), nullable=False, index=True)
    timezone = Column(String(80), nullable=False, server_default="UTC")
    location = Column(String(320), nullable=True)
    meeting_url = Column(String(500), nullable=True)
    attendees = Column(JSONB, nullable=False, server_default="[]")
    status = Column(String(32), nullable=False, server_default="scheduled", index=True)
    invite_status = Column(String(32), nullable=False, server_default="not_sent", index=True)
    ics_uid = Column(String(160), nullable=False, unique=True, index=True)
    external_provider = Column(String(32), nullable=True)
    external_event_id = Column(String(160), nullable=True, index=True)
    payload = Column(JSONB, nullable=False, server_default="{}")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
