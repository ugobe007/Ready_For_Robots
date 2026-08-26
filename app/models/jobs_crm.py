"""Jobs CRM — kept Job Cards, applications, and employer threads on the user account."""
from __future__ import annotations

import uuid

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)

from app.database import Base
from app.models.types import JSONB, UUID


class KeptJob(Base):
    """A Job Card the user kept on their account (collect / Keep jobs)."""

    __tablename__ = "user_kept_jobs"
    __table_args__ = (UniqueConstraint("user_id", "job_key", name="uq_user_kept_jobs_user_job"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    job_key = Column(String(160), nullable=False, index=True)
    employer_name = Column(String(240), nullable=False)
    work_title = Column(String(512), nullable=False)
    workplace = Column(String(240), nullable=True)
    source_ids = Column(JSONB, nullable=False, server_default="{}")
    job_payload = Column(JSONB, nullable=False, server_default="{}")
    robot_name = Column(String(240), nullable=True)
    robot_url = Column(Text, nullable=True)
    robot_submission_id = Column(Integer, nullable=True, index=True)
    employer_email = Column(String(320), nullable=True)
    acted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class JobApplication(Base):
    """Offer snapshot + outreach status for one kept job."""

    __tablename__ = "job_applications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    kept_job_id = Column(
        UUID(as_uuid=True),
        ForeignKey("user_kept_jobs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    job_key = Column(String(160), nullable=False, index=True)
    employer_name = Column(String(240), nullable=False)
    work_title = Column(String(512), nullable=False)
    workplace = Column(String(240), nullable=True)
    robot_name = Column(String(240), nullable=False)
    selected_models = Column(JSONB, nullable=False, server_default="[]")
    poc_evidence = Column(Text, nullable=True)
    poc_skipped = Column(String(8), nullable=False, server_default="false")
    monthly_price = Column(String(160), nullable=False)
    offer_snapshot = Column(JSONB, nullable=False, server_default="{}")
    employer_email = Column(String(320), nullable=True)
    send_status = Column(String(40), nullable=False, server_default="stored", index=True)
    send_error = Column(Text, nullable=True)
    resend_id = Column(String(128), nullable=True, index=True)
    reply_token = Column(String(80), nullable=False, unique=True, index=True)
    reply_to = Column(String(320), nullable=True)
    thread_state = Column(String(32), nullable=False, server_default="draft", index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class ApplicationMessage(Base):
    """Outbound apply / reply and inbound employer responses for one application."""

    __tablename__ = "application_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(
        UUID(as_uuid=True),
        ForeignKey("job_applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    direction = Column(String(16), nullable=False, index=True)  # inbound | outbound
    body = Column(Text, nullable=False)
    subject = Column(String(512), nullable=True)
    from_email = Column(String(320), nullable=True)
    to_email = Column(String(320), nullable=True)
    provider_id = Column(String(160), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)


class JobsCrmActivity(Base):
    """Account-level pipeline activity (graduates rfr_pipeline_activity_v1)."""

    __tablename__ = "jobs_crm_activity"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    job_key = Column(String(160), nullable=True, index=True)
    kind = Column(String(32), nullable=False, index=True)
    label = Column(String(240), nullable=False)
    company = Column(String(240), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
