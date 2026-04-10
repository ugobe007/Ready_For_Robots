"""Rep feedback on pipeline leads (thumbs + optional reason / note)."""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from app.database import Base


class LeadRepFeedback(Base):
    __tablename__ = "lead_rep_feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    vote = Column(String(16), nullable=False)  # up | down
    reason_code = Column(String(32), nullable=True)
    note = Column(Text, nullable=True)
    user_id = Column(String(36), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
