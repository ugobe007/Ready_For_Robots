"""V1 physical primitives ontology (immutable codes after release)."""
from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, String, Text, func

from app.database import Base
from app.models.types import UUID


class Primitive(Base):
    __tablename__ = "primitives"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(80), nullable=False, unique=True)
    category = Column(String(64), nullable=False, index=True)
    name = Column(String(240), nullable=False)
    description = Column(Text, nullable=True)
    ontology_version = Column(String(32), nullable=False, server_default="1.0.0")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
