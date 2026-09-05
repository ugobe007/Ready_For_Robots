"""Upgrade role-inbox outreach emails to named Hunter contacts when decision makers exist."""
from __future__ import annotations

import logging
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.contact import Contact
from app.services.company_domain import resolve_outreach_domain
from app.services.contact_free_sources import decision_maker_records
from app.services.hunter_client import HunterAPIError, HunterClient, hunter_contact_enabled
from app.services.lead_enrichment import persist_outreach_contact
from app.services.outreach_email_inference import looks_like_person_email, should_reinfer_stored_contact

logger = logging.getLogger(__name__)


def current_outreach_email(company: Company, contacts: list[Contact]) -> tuple[str | None, str | None]:
    meta = company.crm_metadata or {}
    email = (meta.get("outreach_email") or "").strip().lower()
    source = (meta.get("outreach_email_source") or "").strip().lower() or None
    if email:
        return email, source
    for c in contacts:
        addr = (c.email or "").strip().lower()
        if addr and "@" in addr:
            return addr, None
    return None, source


def hunter_upgrade_eligible(
    company: Company,
    contacts: list[Contact],
) -> tuple[bool, str]:
    if not hunter_contact_enabled():
        return False, "hunter disabled"
    domain = resolve_outreach_domain(company)
    if not domain:
        return False, "missing domain"
    dms = decision_maker_records(company, contacts)
    if not dms:
        return False, "no decision makers"
    email, source = current_outreach_email(company, contacts)
    if email and looks_like_person_email(email):
        return False, "already has person email"
    if email and not should_reinfer_stored_contact(email, domain):
        return False, "verified non-role contact"
    return True, "eligible"


def upgrade_company_contact_with_hunter(
    company: Company,
    db: Session,
    *,
    max_finder_calls: int = 2,
) -> dict[str, Any]:
    """Try Hunter Email Finder for named decision makers; persist first hit."""
    out: dict[str, Any] = {
        "company_id": company.id,
        "name": company.name,
        "upgraded": False,
        "email": None,
        "source": None,
        "reason": None,
    }
    contacts = db.query(Contact).filter(Contact.company_id == company.id).limit(10).all()
    eligible, reason = hunter_upgrade_eligible(company, contacts)
    if not eligible:
        out["reason"] = reason
        return out

    domain = resolve_outreach_domain(company)
    try:
        client = HunterClient()
    except Exception as exc:
        out["reason"] = str(exc)
        return out

    for dm in decision_maker_records(company, contacts)[: max(1, int(max_finder_calls))]:
        first = (dm.get("first_name") or dm.get("first") or "").strip()
        last = (dm.get("last_name") or dm.get("last") or "").strip()
        if not first or not last:
            continue
        try:
            prospect = client.find_email(
                domain=domain,
                company=company.name,
                first_name=first,
                last_name=last,
            )
        except HunterAPIError as exc:
            logger.warning("Hunter upgrade failed for %r: %s", company.name, exc)
            out["reason"] = str(exc)[:200]
            break
        if not prospect or not prospect.get("email"):
            continue
        email = prospect["email"].strip().lower()
        title = prospect.get("title") or dm.get("title")
        persist_outreach_contact(
            company,
            db,
            email=email,
            source="hunter",
            title=title,
        )
        db.commit()
        out.update(
            {
                "upgraded": True,
                "email": email,
                "source": "hunter",
                "reason": "hunter_finder",
                "title": title,
            }
        )
        return out

    if not out.get("reason"):
        out["reason"] = "no hunter match"
    return out


def select_hunter_upgrade_candidates(
    db: Session,
    *,
    limit: int = 30,
    tiers: Optional[set[str]] = None,
) -> list[Company]:
    from app.services.lead_filter import classify_lead, pick_primary_score

    tier_filter = {t.upper() for t in (tiers or {"HOT", "WARM"})}
    rows: list[tuple[float, Company]] = []
    q = (
        db.query(Company)
        .filter(Company.is_internal.is_(True))
        .order_by(Company.updated_at.desc())
        .limit(max(limit * 40, 400))
    )
    for company in q:
        contacts = db.query(Contact).filter(Contact.company_id == company.id).limit(10).all()
        if not hunter_upgrade_eligible(company, contacts)[0]:
            continue
        sigs = company.signals or []
        _junk, _reason, pri = classify_lead(company, company.scores, sigs)
        if pri.tier not in tier_filter:
            continue
        score = getattr(pick_primary_score(company.scores), "overall_score", 0) or 0
        rows.append((float(score), company))
    rows.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in rows[:limit]]


def run_hunter_upgrade_batch(
    db: Session,
    *,
    limit: int = 30,
    tiers: Optional[set[str]] = None,
) -> dict[str, Any]:
    candidates = select_hunter_upgrade_candidates(db, limit=limit, tiers=tiers)
    results: list[dict[str, Any]] = []
    upgraded = 0
    for company in candidates:
        row = upgrade_company_contact_with_hunter(company, db)
        results.append(row)
        if row.get("upgraded"):
            upgraded += 1
    return {
        "candidates": len(candidates),
        "upgraded": upgraded,
        "sample": results[:15],
    }
