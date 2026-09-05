from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, func, ForeignKey
from sqlalchemy.orm import relationship, validates
from app.database import Base

class Company(Base):
    __tablename__ = 'companies'

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, index=True, nullable=True)
    name = Column(String, nullable=False, index=True)
    website = Column(String, nullable=True)
    # Normalized hostname (no scheme/www) for indexed domain-level entity resolution.
    website_domain = Column(String, nullable=True, index=True)
    industry = Column(String, nullable=True, index=True)
    sub_industry = Column(String, nullable=True)
    employee_estimate = Column(Integer, nullable=True)
    location_city = Column(String, nullable=True)
    location_state = Column(String, nullable=True)
    location_country = Column(String, nullable=True)
    source = Column(String, nullable=True)
    # Persisted robot/automation spec (rules_v1); refreshed when signals change (see app/db_events.py).
    automation_profile = Column(JSON, nullable=True)
    # CRM descriptors: budget, timing, automation_requirements, decision_makers, quality_flags.
    # Populated by crm_extractor after enrichment + rectification passes.
    crm_metadata = Column(JSON, nullable=True)
    is_internal = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    contacts = relationship("Contact", back_populates="company", cascade="all, delete-orphan")
    signals = relationship("Signal", back_populates="company", cascade="all, delete-orphan")
    # One-to-many: multiple score rows can exist after re-runs / sync; use pick_primary_score() when reading
    scores = relationship("Score", back_populates="company", cascade="all, delete-orphan")

    @validates("website")
    def _sync_website_domain(self, key, value):
        from app.services.company_domain import normalize_website_domain

        self.website_domain = normalize_website_domain(value) if value else None
        return value