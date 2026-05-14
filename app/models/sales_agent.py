"""Stateful SCOUT sales agent opportunity tracking."""
from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func

from app.database import Base
from app.models.types import JSONB, UUID


class SalesOpportunity(Base):
    __tablename__ = "sales_opportunities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    opportunity_type = Column(String(32), nullable=False, index=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=True, index=True)
    crm_account_id = Column(UUID(as_uuid=True), ForeignKey("crm_accounts.id", ondelete="CASCADE"), nullable=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True)
    robot_company_id = Column(Integer, ForeignKey("robot_companies.id", ondelete="CASCADE"), nullable=True, index=True)
    owner_user_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(240), nullable=False)
    current_stage = Column(String(64), nullable=False, server_default="new", index=True)
    status = Column(String(32), nullable=False, server_default="open", index=True)
    automation_level = Column(String(32), nullable=False, server_default="first_reply_auto")
    next_best_action = Column(JSONB, nullable=False, server_default="{}")
    payload = Column(JSONB, nullable=False, server_default="{}")
    last_inbound_at = Column(DateTime(timezone=True), nullable=True, index=True)
    last_outbound_at = Column(DateTime(timezone=True), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("opportunity_type", "crm_account_id", name="uq_sales_opportunity_type_crm_account"),
        UniqueConstraint("opportunity_type", "robot_company_id", name="uq_sales_opportunity_type_robot_company"),
    )


class SalesMessage(Base):
    __tablename__ = "sales_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sales_opportunity_id = Column(UUID(as_uuid=True), ForeignKey("sales_opportunities.id", ondelete="CASCADE"), nullable=False, index=True)
    direction = Column(String(16), nullable=False, index=True)
    channel = Column(String(32), nullable=False, server_default="email")
    source_type = Column(String(64), nullable=True, index=True)
    source_id = Column(String(80), nullable=True, index=True)
    from_email = Column(String(320), nullable=True, index=True)
    to_email = Column(String(320), nullable=True)
    subject = Column(String(512), nullable=True)
    body_text = Column(Text, nullable=True)
    detected_intent = Column(String(64), nullable=True, index=True)
    payload = Column(JSONB, nullable=False, server_default="{}")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)


class SalesAgentAction(Base):
    __tablename__ = "sales_agent_actions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sales_opportunity_id = Column(UUID(as_uuid=True), ForeignKey("sales_opportunities.id", ondelete="CASCADE"), nullable=False, index=True)
    action_type = Column(String(64), nullable=False, index=True)
    status = Column(String(32), nullable=False, server_default="planned", index=True)
    risk_level = Column(String(32), nullable=False, server_default="low")
    requires_approval = Column(Boolean, nullable=False, server_default="false", index=True)
    stage_before = Column(String(64), nullable=True)
    stage_after = Column(String(64), nullable=True)
    detected_intent = Column(String(64), nullable=True, index=True)
    recommendation = Column(Text, nullable=True)
    draft_subject = Column(String(512), nullable=True)
    draft_body = Column(Text, nullable=True)
    resend_id = Column(String(128), nullable=True, index=True)
    error = Column(Text, nullable=True)
    payload = Column(JSONB, nullable=False, server_default="{}")
    sent_at = Column(DateTime(timezone=True), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
