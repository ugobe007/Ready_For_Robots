"""Map company industry strings onto taxonomy keys and store the result.

Reads company fields the caller already has. Writes only
`company_taxonomy_industries`. Does not update, delete, or alter `companies`.
"""
from __future__ import annotations

from typing import Any, Iterable

from sqlalchemy.orm import Session

from app.models.company_taxonomy_industry import CompanyTaxonomyIndustry
from app.services.taxonomy_industry_synonyms import (
    classify_industry,
    taxonomy_function_keys,
)


def map_company_industries(companies: Iterable[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Split companies into exact synonym hits and an unmapped list.

    Each company dict needs `name` and `industry`. `id` is kept when present
    so a later write can point at the existing company row.
    """
    mapped: list[dict[str, Any]] = []
    unmapped: list[dict[str, Any]] = []
    allowed_functions = taxonomy_function_keys()
    for company in companies:
        name = str(company.get("name") or company.get("company_name") or "").strip()
        industry_text = str(company.get("industry") or company.get("industry_text") or "").strip()
        key = classify_industry(industry_text)
        row = {
            "company_id": company.get("id") if company.get("id") is not None else company.get("company_id"),
            "company_name": name,
            "industry_text": industry_text,
            "source_industry": industry_text,
            "readiness": company.get("readiness"),
            "source_kind": company.get("source_kind"),
            "functions": [
                fn
                for fn in (company.get("functions") or [])
                if fn in allowed_functions
            ],
        }
        if key is None:
            unmapped.append(row)
            continue
        row["taxonomy_industry"] = key
        mapped.append(row)
    return {"mapped": mapped, "unmapped": unmapped}


def write_taxonomy_industries(session: Session, mapped_rows: Iterable[dict[str, Any]]) -> int:
    """Insert mapped rows. Skips rows that are already stored. Does not touch companies."""
    written = 0
    for row in mapped_rows:
        company_id = row.get("company_id")
        industry = row.get("taxonomy_industry")
        if company_id is None or not industry:
            continue
        existing = (
            session.query(CompanyTaxonomyIndustry)
            .filter_by(company_id=company_id, taxonomy_industry=industry)
            .one_or_none()
        )
        if existing is not None:
            continue
        session.add(
            CompanyTaxonomyIndustry(
                company_id=company_id,
                company_name=row.get("company_name") or "",
                source_industry=row.get("source_industry") or row.get("industry_text") or "",
                taxonomy_industry=industry,
                readiness=row.get("readiness"),
                source_kind=row.get("source_kind"),
                functions=list(row.get("functions") or []) or None,
            )
        )
        written += 1
    session.flush()
    return written


def buyers_from_taxonomy_table(session: Session) -> list[dict[str, Any]]:
    """Read the new table only. Does not read or write `companies`."""
    rows = session.query(CompanyTaxonomyIndustry).order_by(CompanyTaxonomyIndustry.id).all()
    return [
        {
            "company_id": row.company_id,
            "company_name": row.company_name,
            "industry_text": row.source_industry,
            "taxonomy_industries": [row.taxonomy_industry],
            "functions": list(row.functions or []),
            "readiness": row.readiness,
            "source_kind": row.source_kind,
        }
        for row in rows
    ]
