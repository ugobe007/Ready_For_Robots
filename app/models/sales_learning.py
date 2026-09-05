"""Outcome memory for SCOUT's sales workflow learning loop."""
from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, Text, func

from app.database import Base
from app.models.types import JSONB, UUID


class SalesExperienceEvent(Base):
    __tablename__ = "sales_experience_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id", ondelete="SET NULL"), nullable=True, index=True)
    crm_account_id = Column(UUID(as_uuid=True), ForeignKey("crm_accounts.id", ondelete="CASCADE"), nullable=True, index=True)
    sales_opportunity_id = Column(UUID(as_uuid=True), ForeignKey("sales_opportunities.id", ondelete="SET NULL"), nullable=True, index=True)
    sales_agent_action_id = Column(UUID(as_uuid=True), ForeignKey("sales_agent_actions.id", ondelete="SET NULL"), nullable=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True)
    robot_company_id = Column(Integer, ForeignKey("robot_companies.id", ondelete="SET NULL"), nullable=True, index=True)
    event_type = Column(String(64), nullable=False, index=True)
    outcome = Column(String(64), nullable=False, server_default="observed", index=True)
    source_domain = Column(String(240), nullable=True, index=True)
    signal_type = Column(String(80), nullable=True, index=True)
    channel = Column(String(32), nullable=True, index=True)
    score_delta = Column(Numeric(8, 4), nullable=True)
    confidence = Column(Numeric(5, 4), nullable=True)
    note = Column(Text, nullable=True)
    payload = Column(JSONB, nullable=False, server_default="{}")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
