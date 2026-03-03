"""SignalSource — canonical store for article / page URLs.

Every unique URL scraped across all sources gets one row here.
Signals carry a FK (source_id) pointing to this table.
This avoids storing and re-cleaning URL strings in every signal row
and lets us update a URL once (e.g. if we later resolve the real
publisher link) without touching the signals table.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class SignalSource(Base):
    __tablename__ = "signal_sources"

    id         = Column(Integer, primary_key=True, index=True)
    url        = Column(Text, nullable=False, unique=True)
    title      = Column(Text, nullable=True)
    domain     = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False,
                        default=lambda: datetime.now(timezone.utc))

    signals = relationship("Signal", back_populates="source")
