from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, String, Text, UniqueConstraint
from sqlalchemy.sql import func

from app.database import Base


class WaitlistSignup(Base):
    __tablename__ = "waitlist_signups"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(320), nullable=False)
    name = Column(String(200), nullable=True)
    company = Column(String(240), nullable=True)
    use_case = Column(Text, nullable=True)
    source = Column(String(120), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (UniqueConstraint("email", name="uq_waitlist_signups_email"),)
