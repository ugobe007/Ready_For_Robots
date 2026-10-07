"""Hunter.io fill for operator daily-job sales cards.

FIND does not call Hunter. This is the Admin / daily-email path only.
Verified domain-search people only — never invent a name or mailbox.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.parse import urlparse

from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.services.daily_jobs_report import (
    TOP_N,
    _as_map,
    _contact_fields,
    _is_invented_ops_email,
    _page_name_title,
    select_daily_report_rows,
)
from app.services.hunter_client import (
    HunterAPIError,
    HunterClient,
    HunterConfigError,
    hunter_contact_enabled,
    pick_best_domain_email,
)
from app.services.robot_job_extract import _is_board_host

logger = logging.getLogger(__name__)

_ROLE_LOCALS = frozenset(
    {
        "info",
        "hello",
        "contact",
        "careers",
        "jobs",
        "hr",
        "press",
        "media",
        "support",
        "sales",
        "admin",
        "office",
        "team",
        "operations",
    }
)


def _today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _host(url: str | None) -> Optional[str]:
    raw = (url or "").strip()
    if not raw:
        return None
    if "://" not in raw:
        raw = "https://" + raw
    host = (urlparse(raw).hostname or "").lower().removeprefix("www.")
    if not host or _is_board_host(host):
        return None
    return host


def domain_for_job(row: Any, db: Session) -> Optional[str]:
    for attr in ("contact_url", "apply_url"):
        host = _host(str(getattr(row, attr, "") or ""))
        if host:
            return host
    company_id = getattr(row, "company_id", None)
    if not company_id:
        return None
    from app.models.company import Company

    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        return None
    return _host(str(getattr(company, "website", "") or ""))


def _job_needs_hunter(row: Any) -> bool:
    name, _title = _page_name_title(row)
    contact = _contact_fields(row)
    if name and contact.get("email"):
        return False
    blob = _as_map(getattr(row, "provenance", None))
    if blob.get("contact_source") == "hunter_domain":
        return False
    if str(blob.get("hunter_checked_at") or "") == _today():
        return False
    return True


def _usable_hunter_row(row: dict[str, Any], employer: str) -> bool:
    email = str(row.get("email") or "").strip().lower()
    name = str(row.get("name") or "").strip()
    if not email or "@" not in email:
        return False
    if _is_invented_ops_email(email, employer):
        return False
    local = email.split("@", 1)[0]
    if local in _ROLE_LOCALS:
        return False
    if (row.get("verification_status") or "").lower() == "invalid":
        return False
    if not name and "." not in local:
        return False
    return True


def _stamp_miss(row: Any) -> None:
    prov = dict(_as_map(getattr(row, "provenance", None)))
    prov["hunter_checked_at"] = _today()
    row.provenance = prov
    flag_modified(row, "provenance")


def _stamp_hit(row: Any, prospect: dict[str, Any]) -> None:
    email = str(prospect.get("email") or "").strip().lower()
    name = str(prospect.get("name") or "").strip()
    title = str(prospect.get("title") or "").strip()
    employer = str(getattr(row, "company_name", "") or "").strip()
    existing_email = str(getattr(row, "employer_email", "") or "").strip()
    if existing_email and _is_invented_ops_email(existing_email, employer):
        existing_email = ""
    existing_name, existing_title = _page_name_title(row)
    if email and not existing_email:
        row.employer_email = email
    prov = dict(_as_map(getattr(row, "provenance", None)))
    if name and not existing_name:
        prov["contact_name"] = name
    if title and not existing_title:
        prov["contact_title"] = title
    prov["contact_source"] = "hunter_domain"
    prov["hunter_checked_at"] = _today()
    if prospect.get("confidence") is not None:
        prov["hunter_confidence"] = prospect.get("confidence")
    row.provenance = prov
    flag_modified(row, "provenance")


def _lookup(
    client: HunterClient,
    *,
    employer: str,
    domain: Optional[str],
    cache: dict[str, Optional[dict[str, Any]]],
) -> Optional[dict[str, Any]]:
    key = (domain or employer).strip().lower()
    if key in cache:
        return cache[key]
    try:
        search = client.domain_search(domain=domain, company=employer)
    except (HunterAPIError, HunterConfigError) as exc:
        logger.warning("Hunter domain search failed for %r: %s", employer, exc)
        cache[key] = None
        return None
    emails = [
        row
        for row in (search.get("emails") or [])
        if isinstance(row, dict) and _usable_hunter_row(row, employer)
    ]
    best = pick_best_domain_email(emails)
    if best and not _usable_hunter_row(best, employer):
        best = None
    cache[key] = best
    return best


def enrich_daily_jobs_with_hunter(
    db: Session,
    *,
    limit: int = TOP_N,
    client: HunterClient | None = None,
) -> dict[str, Any]:
    """Fill missing names/emails on the top-N cards via Hunter domain search."""
    out: dict[str, Any] = {
        "ok": False,
        "looked_up": 0,
        "filled": 0,
        "skipped": 0,
        "missed": 0,
        "reason": None,
        "enabled": hunter_contact_enabled(),
    }
    if not hunter_contact_enabled():
        out["reason"] = "hunter_disabled"
        return out
    try:
        hunter = client or HunterClient()
    except HunterConfigError as exc:
        out["reason"] = str(exc)
        return out

    rows = select_daily_report_rows(db, limit=limit)
    cache: dict[str, Optional[dict[str, Any]]] = {}
    filled = 0
    missed = 0
    skipped = 0
    looked = 0
    for row in rows:
        if not _job_needs_hunter(row):
            skipped += 1
            continue
        employer = str(getattr(row, "company_name", "") or "").strip()
        if not employer:
            skipped += 1
            continue
        looked += 1
        domain = domain_for_job(row, db)
        prospect = None
        known_name, _ = _page_name_title(row)
        bits = known_name.split()
        if len(bits) >= 2:
            try:
                found = hunter.find_email(
                    domain=domain,
                    company=employer,
                    first_name=bits[0],
                    last_name=bits[-1],
                )
                if found and _usable_hunter_row(found, employer):
                    prospect = found
            except (HunterAPIError, HunterConfigError) as exc:
                logger.warning("Hunter finder failed for %r: %s", employer, exc)
        if not prospect:
            prospect = _lookup(hunter, employer=employer, domain=domain, cache=cache)
        if prospect and prospect.get("email"):
            _stamp_hit(row, prospect)
            filled += 1
        else:
            _stamp_miss(row)
            missed += 1
    if looked:
        db.commit()
    out.update(
        {
            "ok": True,
            "looked_up": looked,
            "filled": filled,
            "skipped": skipped,
            "missed": missed,
        }
    )
    return out
