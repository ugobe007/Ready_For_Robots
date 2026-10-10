"""One day's operator lead list, stored as inline text plus CSV."""
from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.sql import func

from app.database import Base


class DailyJobsReportEdition(Base):
    """Plain-text body and CSV for the daily 25 leads. Not a job-card snapshot."""

    __tablename__ = "daily_jobs_report_editions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_date = Column(String(10), nullable=False)
    body_text = Column(Text, nullable=False)
    csv_text = Column(Text, nullable=False)
    job_count = Column(Integer, nullable=False, default=0)
    stored_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("report_date", name="uq_daily_jobs_report_editions_date"),
    )
