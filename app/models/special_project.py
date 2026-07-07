"""Special projects — private admin workflow for bespoke robot-company engagements.

Each SpecialProject is a hands-on GTM engagement Cal runs for a specific robot
company (e.g. NIMO Technology): pipeline/beta motion, KPIs, and a timeline of
workflow developments. A share_token grants the client read-only access to a
private portal without an account.
"""

from __future__ import annotations

import secrets
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.types import JSONB


def _new_share_token() -> str:
    # URL-safe, unguessable client-portal key (no login required).
    return secrets.token_urlsafe(24)


class SpecialProject(Base):
    __tablename__ = "special_projects"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    slug = Column(String(80), nullable=False, unique=True, index=True)
    share_token = Column(String(64), nullable=False, unique=True, index=True, default=_new_share_token)

    name = Column(String(200), nullable=False)
    company_website = Column(String(512), nullable=True)
    contact_email = Column(String(320), nullable=True)
    robot_description = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    status = Column(String(32), nullable=False, server_default="discovery")

    # Flexible admin-editable blobs so the workflow can evolve without migrations.
    config = Column(JSONB, nullable=False, server_default="{}")   # icp, tasks, personas, motion
    metrics = Column(JSONB, nullable=False, server_default="{}")  # editable KPIs
    pipeline = Column(JSONB, nullable=False, server_default="{}")  # stage -> count (funnel viz)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    updates = relationship(
        "SpecialProjectUpdate",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="desc(SpecialProjectUpdate.created_at)",
    )
    targets = relationship(
        "SpecialProjectTarget",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="SpecialProjectTarget.sort_order",
    )


class SpecialProjectUpdate(Base):
    __tablename__ = "special_project_updates"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(
        String(36), ForeignKey("special_projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title = Column(String(300), nullable=False)
    body = Column(Text, nullable=True)
    # milestone | stat | note | outreach — drives the portal timeline styling.
    category = Column(String(32), nullable=False, server_default="note")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    project = relationship("SpecialProject", back_populates="updates")


class SpecialProjectTarget(Base):
    """A single beta-host / prospect account Cal works for a special project.

    This is a self-contained outreach queue that never touches the buyer CRM,
    so a client engagement (e.g. NIMO) can't pollute the product's own pipeline.
    ``stage`` is a funnel stage (targeted → validated) and drives the portal
    funnel counts; the review-first draft lives in ``draft_subject`` /
    ``draft_body`` and only sends after ``approved`` is set.
    """

    __tablename__ = "special_project_targets"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(
        String(36), ForeignKey("special_projects.id", ondelete="CASCADE"), nullable=False, index=True
    )

    company = Column(String(200), nullable=False)
    website = Column(String(512), nullable=True)
    segment = Column(String(120), nullable=True)       # e.g. "Ghost / cloud kitchens"
    best_fit_task = Column(String(200), nullable=True)  # e.g. "Bowl assembly + portioning"
    persona = Column(String(200), nullable=True)        # angle / who to reach
    sequence = Column(String(1), nullable=True)         # A | B | C (outreach sequence)
    fit = Column(String(1), nullable=True)              # H | W | C (beta-fit read)
    signal = Column(Text, nullable=True)                # why-now hypothesis

    contact_name = Column(String(200), nullable=True)
    contact_email = Column(String(320), nullable=True)
    contact_title = Column(String(200), nullable=True)
    # none | guessed | verified — gates real sending, mirrors lead_enrichment trust.
    contact_status = Column(String(16), nullable=False, server_default="none")

    draft_subject = Column(Text, nullable=True)
    draft_body = Column(Text, nullable=True)

    # funnel stage: targeted | contacted | replied | discovery | demo | pilot_signed | validated
    stage = Column(String(24), nullable=False, server_default="targeted")
    approved = Column(String(8), nullable=False, server_default="no")  # "yes" once admin approves the draft
    sent_at = Column(DateTime(timezone=True), nullable=True)
    last_activity_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    sort_order = Column(Integer, nullable=False, server_default="0")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    project = relationship("SpecialProject", back_populates="targets")
