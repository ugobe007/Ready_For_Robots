"""V1 Source entity — durable capture of external evidence."""
from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, String, Text, func

from app.database import Base
from app.models.types import JSONB, UUID


class Source(Base):
    __tablename__ = "sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_type = Column(String(64), nullable=False, index=True)
    url = Column(Text, nullable=True)
    title = Column(Text, nullable=True)
    publisher = Column(String(240), nullable=True)
    captured_at = Column(DateTime(timezone=True), nullable=True)
    content_hash = Column(String(128), nullable=True, index=True)
    raw_text = Column(Text, nullable=True)
    metadata_json = Column("metadata", JSONB, nullable=False, server_default="{}")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
