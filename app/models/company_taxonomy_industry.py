"""Company industry labels mapped onto the 29 taxonomy industries.

This table is written by the synonym map. It does not change `companies` or
any other existing table. Unmapped companies are not stored here.
"""
from __future__ import annotations

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.sql import func

from app.database import Base
from app.models.types import JSONB


class CompanyTaxonomyIndustry(Base):
    __tablename__ = "company_taxonomy_industries"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    company_name = Column(String(300), nullable=False)
    source_industry = Column(String(300), nullable=False)
    taxonomy_industry = Column(String(64), nullable=False, index=True)
    readiness = Column(String(32), nullable=True)
    source_kind = Column(String(64), nullable=True)
    functions = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "taxonomy_industry",
            name="uq_company_taxonomy_industry",
        ),
    )
