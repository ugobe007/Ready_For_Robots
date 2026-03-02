"""
Daily Report model
==================
Stores the published top-25 daily strategy brief as a JSON snapshot.
Each business day has exactly one record. Re-publishing overwrites the
existing record for that date.
"""
import json
from datetime import date, datetime, timezone

from sqlalchemy import Column, Integer, String, Date, DateTime, Text, func
from app.database import Base


class DailyReport(Base):
    __tablename__ = "daily_reports"

    id              = Column(Integer, primary_key=True, index=True)
    report_date     = Column(Date, nullable=False, unique=True, index=True)
    generated_at    = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    opportunity_count = Column(Integer, default=0)
    contacts_found  = Column(Integer, default=0)
    # Full JSON payload — the same structure returned by GET /api/strategy
    report_json     = Column(Text, nullable=False, default="{}")

    # ── convenience helpers ────────────────────────────────────────────────
    def set_data(self, data: dict) -> None:
        self.report_json = json.dumps(data, default=str)
        self.opportunity_count = data.get("opportunity_count", 0)

    def get_data(self) -> dict:
        try:
            return json.loads(self.report_json)
        except (ValueError, TypeError):
            return {}
