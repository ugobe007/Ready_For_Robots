from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.sql import func

from app.database import Base


class RobotBuyerLead(Base):
    """Inbound lead from companies seeking robot automation."""

    __tablename__ = "robot_buyer_leads"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(320), nullable=False)
    name = Column(String(200), nullable=True)
    company = Column(String(240), nullable=False)
    phone = Column(String(40), nullable=True)
    job_title = Column(String(160), nullable=True)
    use_case = Column(Text, nullable=False)
    robot_type = Column(String(80), nullable=False)
    implementation_timeline = Column(String(80), nullable=False)
    source = Column(String(120), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
