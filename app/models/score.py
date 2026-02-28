from sqlalchemy import Column, Float, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base

class Score(Base):
    __tablename__ = 'scores'

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    automation_score = Column(Float, nullable=False, default=0.0)
    labor_pain_score = Column(Float, nullable=False, default=0.0)
    expansion_score = Column(Float, nullable=False, default=0.0)
    robotics_fit_score = Column(Float, nullable=False, default=0.0)
    overall_intent_score = Column(Float, nullable=False, default=0.0)
    last_calculated_at = Column(DateTime, nullable=False,
                                default=lambda: datetime.now(timezone.utc),
                                onupdate=lambda: datetime.now(timezone.utc))

    company = relationship("Company", back_populates="scores")