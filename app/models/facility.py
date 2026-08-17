"""V1 Facility — primary commercial unit under a company."""
from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint, func

from app.database import Base
from app.models.types import UUID


class Facility(Base):
    __tablename__ = "facilities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(240), nullable=True)
    facility_type = Column(String(64), nullable=True)
    address_line1 = Column(String(320), nullable=True)
    city = Column(String(120), nullable=True, index=True)
    state = Column(String(64), nullable=True, index=True)
    postal_code = Column(String(32), nullable=True)
    country = Column(String(2), nullable=False, server_default="US")
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    normalized_address = Column(String(512), nullable=True)
    location_precision = Column(String(32), nullable=True)
    estimated_sqft = Column(Integer, nullable=True)
    employee_count_est = Column(Integer, nullable=True)
    industry = Column(String(120), nullable=True)
    confidence = Column(Float, nullable=False, server_default="0")
    truth_state = Column(String(32), nullable=False, server_default="inferred")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("company_id", "normalized_address", name="uq_facility_company_normalized_address"),
    )
