"""SCOUT marketing chat and activation persistence."""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.database import Base


class ScoutSession(Base):
    __tablename__ = "scout_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fingerprint = Column(String(80), nullable=False, unique=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id", ondelete="SET NULL"), nullable=True)
    robot_category = Column(String(32), nullable=True)
    vertical = Column(Text, nullable=True)
    territory = Column(String(128), nullable=True)
    company_name = Column(String(256), nullable=True)
    company_url = Column(String(512), nullable=True)
    conversation_count = Column(Integer, nullable=False, server_default="0")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_seen_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class ScoutMessage(Base):
    __tablename__ = "scout_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("scout_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(16), nullable=False)  # "scout" | "user"
    content = Column(Text, nullable=False)
    skill_invoked = Column(String(64), nullable=True)
    skill_data = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ScoutProfile(Base):
    __tablename__ = "scout_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("scout_sessions.id", ondelete="CASCADE"), nullable=False, unique=True)
    companies_viewed = Column(JSONB, nullable=False, server_default="[]")
    drafts_approved = Column(JSONB, nullable=False, server_default="[]")
    signals_seen = Column(JSONB, nullable=False, server_default="[]")
    inferred_needs = Column(Text, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class ScoutActivation(Base):
    __tablename__ = "scout_activations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("scout_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id", ondelete="SET NULL"), nullable=True, index=True)
    source_url = Column(String(512), nullable=True)
    material_choice = Column(String(32), nullable=False)
    material_filename = Column(String(512), nullable=True)
    scope_choice = Column(String(32), nullable=False)
    mode_choice = Column(String(32), nullable=False)
    status = Column(String(32), nullable=False, server_default="queued")
    lead_ids = Column(JSONB, nullable=False, server_default="[]")
    leads_snapshot = Column(JSONB, nullable=False, server_default="[]")
    work_plan = Column(JSONB, nullable=False, server_default="{}")
    activity_log = Column(JSONB, nullable=False, server_default="[]")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
