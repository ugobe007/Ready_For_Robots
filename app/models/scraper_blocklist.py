from sqlalchemy import Column, Integer, String, DateTime, func
from app.database import Base


class ScraperBlocklist(Base):
    __tablename__ = "scraper_blocklist"

    id           = Column(Integer, primary_key=True, index=True)
    name_lower   = Column(String, nullable=False, unique=True, index=True)
    original_name = Column(String, nullable=False)
    reason       = Column(String, nullable=True)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())
