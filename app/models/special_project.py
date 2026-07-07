"""Special projects — private admin workflow for bespoke robot-company engagements.

Each SpecialProject is a hands-on GTM engagement Cal runs for a specific robot
company (e.g. NIMO Technology): pipeline/beta motion, KPIs, and a timeline of
workflow developments. A share_token grants the client read-only access to a
private portal without an account.
"""

from __future__ import annotations

import secrets
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, func
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
