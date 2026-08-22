"""Jobs watch — opt-in email when saved robot jobs change or new work appears."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func

from app.database import Base
from app.models.types import JSONB, UUID


class JobsWatch(Base):
    __tablename__ = "jobs_watches"
    __table_args__ = (UniqueConstraint("user_id", "website_domain", name="uq_jobs_watch_user_domain"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    email = Column(String(320), nullable=False)
    robot_url = Column(Text, nullable=False)
    website_domain = Column(String(240), nullable=False, index=True)
    product_name = Column(String(240), nullable=True)
    robot_submission_id = Column(
        Integer, ForeignKey("robot_submissions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    opted_in = Column(Boolean, nullable=False, server_default="true")
    last_job_keys = Column(JSONB, nullable=False, server_default="[]")
    last_checked_at = Column(DateTime(timezone=True), nullable=True)
    last_notified_at = Column(DateTime(timezone=True), nullable=True)
    notify_count = Column(Integer, nullable=False, server_default="0")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class JobsWatchEvent(Base):
    __tablename__ = "jobs_watch_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    watch_id = Column(UUID(as_uuid=True), ForeignKey("jobs_watches.id", ondelete="CASCADE"), nullable=False, index=True)
    job_key = Column(String(120), nullable=False, index=True)
    title = Column(String(512), nullable=False)
    company_name = Column(String(240), nullable=True)
    kind = Column(String(32), nullable=False, index=True)  # saved | new | changed
    emailed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
