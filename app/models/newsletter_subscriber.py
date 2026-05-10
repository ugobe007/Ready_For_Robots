from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from app.database import Base


class NewsletterSubscriber(Base):
    __tablename__ = "newsletter_subscribers"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(320), nullable=False)
    name = Column(String(200), nullable=True)
    company = Column(String(240), nullable=True)
    robot_category = Column(String(160), nullable=True)
    source = Column(String(120), nullable=True)
    status = Column(String(32), nullable=False, server_default="active")
    consent_text = Column(Text, nullable=True)
    subscriber_metadata = Column(JSONB, nullable=False, server_default="{}")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)

    __table_args__ = (UniqueConstraint("email", name="uq_newsletter_subscribers_email"),)
