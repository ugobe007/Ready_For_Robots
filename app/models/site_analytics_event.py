"""Persistent marketing site analytics events (page views, URL scans, ROI, buyer intake)."""

from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, String, func

from app.database import Base
from app.models.types import JSONB


class SiteAnalyticsEvent(Base):
    __tablename__ = "site_analytics_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_type = Column(String(64), nullable=False, index=True)
    payload = Column(JSONB, nullable=False, server_default="{}")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
