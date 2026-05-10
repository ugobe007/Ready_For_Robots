"""Partner-facing trade show intel (e.g. The Robot Guild — robot experience marketing)."""

from sqlalchemy import Column, Date, DateTime, Integer, JSON, String, Text, func

from app.database import Base


class PartnerTradeShow(Base):
    """
    Trade shows and conferences scraped for partner GTM (exhibit floors, dates, robot OEM hints).
    """

    __tablename__ = "partner_trade_shows"

    id = Column(Integer, primary_key=True, index=True)
    partner_slug = Column(String(64), nullable=False, index=True)
    # Stable dedupe across refresh runs
    source_key = Column(String(64), nullable=False, unique=True, index=True)

    name = Column(String(512), nullable=False)
    summary = Column(Text, nullable=True)
    location = Column(String(512), nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    event_url = Column(String(1024), nullable=True)
    source_page_url = Column(String(1024), nullable=True)

    # OEM / brand names likely exhibiting (substring hits vs robot directory + keywords)
    exhibitor_hints = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
