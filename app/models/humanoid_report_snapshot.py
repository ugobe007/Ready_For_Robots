from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.types import JSON

from app.database import Base

# JSON works on SQLite tests; JSONB on Postgres when available.
SnapshotJSON = JSON().with_variant(JSONB(), "postgresql")


class HumanoidReportSnapshot(Base):
    """Monthly frozen summary of the humanoid index for month-over-month reporting."""

    __tablename__ = "humanoid_report_snapshots"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    period_key = Column(String(7), nullable=False)
    captured_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    summary = Column(SnapshotJSON, nullable=False)
    rankings = Column(SnapshotJSON, nullable=False)

    __table_args__ = (UniqueConstraint("period_key", name="uq_humanoid_report_snapshots_period"),)
