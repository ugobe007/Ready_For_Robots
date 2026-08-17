"""Vendor / customer news items ingested from Hermes (capabilities, pricing, models)."""
from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, func

from app.database import Base
from app.models.types import JSONB, UUID


class VendorNewsItem(Base):
    """Public vendor or customer news tied to the intelligence loop (not deployment truth)."""

    __tablename__ = "vendor_news_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    news_id = Column(String(64), nullable=False, unique=True, index=True)
    news_type = Column(String(64), nullable=False, server_default="product", index=True)
    # capability | pricing | foundation_model | product | customer_signal
    entity_kind = Column(String(32), nullable=False, server_default="vendor", index=True)
    # vendor | customer
    entity_name = Column(String(240), nullable=False, index=True)
    company_id = Column(
        Integer, ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title = Column(String(480), nullable=True)
    text = Column(Text, nullable=False)
    source_url = Column(Text, nullable=True, index=True)
    source_date = Column(String(32), nullable=True)
    confidence = Column(Float, nullable=False, server_default="0.5")
    hermes_run_id = Column(String(120), nullable=True, index=True)
    extra = Column(JSONB, nullable=False, server_default="{}")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
