"""CRM: teams, members, accounts (matches migrations c7d8e9f0a1b2)."""
import uuid

from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, UniqueConstraint, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database import Base


class Team(Base):
    __tablename__ = "teams"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    slug = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class TeamMember(Base):
    __tablename__ = "team_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String, nullable=False, server_default="member")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint("team_id", "user_id", name="uq_team_members_team_user"),)


class CrmAccount(Base):
    __tablename__ = "crm_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True)
    name = Column(String, nullable=False)
    website = Column(String, nullable=True)
    industry = Column(String, nullable=True)
    owner_user_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    contact_email = Column(String(320), nullable=True)
    outreach_draft = Column(Text, nullable=True)
    outreach_sent_at = Column(DateTime(timezone=True), nullable=True)
    outreach_stage = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class CrmEngagement(Base):
    __tablename__ = "crm_engagements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    crm_account_id = Column(UUID(as_uuid=True), ForeignKey("crm_accounts.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    stage = Column(String, nullable=False, server_default="qualification")
    value_amount = Column(Numeric(18, 2), nullable=True)
    currency = Column(String, nullable=True, server_default="USD")
    owner_user_id = Column(UUID(as_uuid=True), nullable=True)
    status = Column(String, nullable=False, server_default="open")
    opened_at = Column(DateTime(timezone=True), server_default=func.now())
    closed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
