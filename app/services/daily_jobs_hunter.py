"""Hunter.io company lookup for operator daily-job sales cards.

Look up the employer, pick the title that owns this job, then find that
person's email. FIND does not call Hunter. Apollo is not used here.
Never invent a name or mailbox.
"""
from __future__ import annotations

import logging
import re
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
    MIN_DOMAIN_CONFIDENCE,
    HunterAPIError,
    HunterClient,
    HunterConfigError,
    hunter_contact_enabled,
)
from app.services.job_decision_maker_agent import (
    DecisionMakerPlan,
    pick_candidate,
    plan_for_job,
    score_candidate,
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
_GENERIC_EMPLOYER_TOKENS = frozenset(
    {
        "hospital",
        "health",
        "medical",
        "center",
        "centre",
        "company",
        "companies",
        "technologies",
        "technology",
        "partners",
        "partner",
        "distribution",
        "auto",
        "parts",
        "metal",
        "supply",
        "candy",
        "university",
        "america",
        "mall",
        "energy",
        "group",
        "services",
        "service",
        "international",
        "global",
        "industries",
        "industry",
        "hygiene",
        "aviation",
        "airport",
        "floor",
        "tech",
        "general",
        "systems",
        "solutions",
        "incorporated",
        "inc",
        "llc",
        "ltd",
        "corp",
        "corporation",
        "the",
        "and",
        "for",
        "sd",
        "usa",
        "united",
        "states",
        "regional",
        "national",
    }
)
_US_STATE_ABBR = frozenset(
    {
        "AL",
        "AK",
        "AZ",
        "AR",
        "CA",
        "CO",
        "CT",
        "DC",
        "DE",
        "FL",
        "GA",
        "HI",
        "IA",
        "ID",
        "IL",
        "IN",
        "KS",
        "KY",
        "LA",
        "MA",
        "MD",
        "ME",
        "MI",
        "MN",
        "MO",
        "MS",
        "MT",
        "NC",
        "ND",
        "NE",
        "NH",
        "NJ",
        "NM",
        "NV",
        "NY",
        "OH",
        "OK",
        "OR",
        "PA",
        "RI",
        "SC",
        "SD",
        "TN",
        "TX",
        "UT",
        "VA",
        "VT",
        "WA",
        "WI",
        "WV",
        "WY",
    }
)
_CAREER_HOST_LABELS = frozenset(
    {
        "jobs",
        "careers",
        "career",
        "apply",
        "hiring",
        "recruiting",
        "talent",
    }
)
_ATS_HOSTS = frozenset(
    {
        "greenhouse.io",
        "lever.co",
        "workday.com",
        "myworkdayjobs.com",
        "smartrecruiters.com",
        "icims.com",
        "ultipro.com",
        "paycomonline.net",
        "breezy.hr",
        "bamboohr.com",
        "jobvite.com",
        "taleo.net",
        "successfactors.com",
        "workable.com",
        "fountain.com",
    }
)
_FOREIGN_TLDS = (
    ".com.au",
    ".co.uk",
    ".co.nz",
    ".com.br",
    ".co.za",
    ".co.jp",
    ".de",
    ".fr",
    ".it",
    ".es",
    ".nl",
    ".in",
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
    if any(host == d or host.endswith("." + d) for d in _ATS_HOSTS):
        return None
    label = host.split(".", 1)[0]
    if label in _CAREER_HOST_LABELS:
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


def _job_needs_hunter(row: Any, *, force: bool = False) -> bool:
    name, _title = _page_name_title(row)
    contact = _contact_fields(row)
    blob = _as_map(getattr(row, "provenance", None))
    source = str(blob.get("contact_source") or "")
    if not force and name and contact.get("email") and source.startswith("hunter"):
        return False
    if name and contact.get("email") and not force:
        return False
    if not force and source in {"hunter_domain", "hunter_finder", "decision_maker_agent"}:
        return False
    if not force and str(blob.get("hunter_checked_at") or "") == _today():
        return False
    return True


def _employer_tokens(employer: str) -> list[str]:
    return [
        tok
        for tok in re.findall(r"[a-z0-9]{3,}", (employer or "").lower())
        if tok not in _GENERIC_EMPLOYER_TOKENS
    ]


def _host_core(email: str) -> str:
    host = email.split("@", 1)[1].lower().removeprefix("www.")
    labels = [p for p in host.split(".") if p]
    if len(labels) >= 3 and labels[-1] in {"au", "uk", "nz", "br", "za", "jp"}:
        return labels[-3]
    return labels[-2] if len(labels) >= 2 else (labels[0] if labels else "")


def _is_us_locality(place: str) -> bool:
    """US workplace labels only. Do not treat 'Sydney, AU' or the word 'in' as US."""
    raw = (place or "").strip()
    if re.search(r"united states|\bUSA\b|\bU\.S\.A?\.?\b", raw, re.I):
        return True
    match = re.search(r",\s*([A-Z]{2})\b", raw)
    return bool(match and match.group(1) in _US_STATE_ABBR)


def _email_fits_employer(email: str, employer: str, locality: str = "") -> bool:
    """Reject Marin General for Mercy, NAPA Australia for a PA DC, Unical for Unifi."""
    raw = (email or "").strip().lower()
    if "@" not in raw:
        return False
    host = raw.split("@", 1)[1].lower()
    if _is_us_locality(locality) and any(host.endswith(tld) for tld in _FOREIGN_TLDS):
        return False
    core = re.sub(r"[^a-z0-9]", "", _host_core(raw))
    emp_slug = re.sub(r"[^a-z0-9]", "", employer.lower())
    if core and emp_slug and core == emp_slug:
        return True
    tokens = _employer_tokens(employer)
    if tokens:
        longest = max(tokens, key=len)
        if len(longest) >= 4 and (longest in core or core.startswith(longest)):
            return True
    acronym = "".join(
        tok[0]
        for tok in re.findall(r"[a-z0-9]+", employer.lower())
        if tok not in {"the", "and", "of", "for", "a", "an", "via"}
    )
    if len(acronym) >= 3 and acronym == core:
        return True
    return False


def _usable_hunter_row(
    row: dict[str, Any], employer: str, locality: str = ""
) -> bool:
    email = str(row.get("email") or "").strip().lower()
    name = str(row.get("name") or "").strip()
    if not email or "@" not in email:
        return False
    if _is_invented_ops_email(email, employer):
        return False
    if not _email_fits_employer(email, employer, locality):
        return False
    local = email.split("@", 1)[0]
    if local in _ROLE_LOCALS:
        return False
    if (row.get("verification_status") or "").lower() == "invalid":
        return False
    try:
        confidence = int(row.get("confidence") or 0)
    except (TypeError, ValueError):
        confidence = 0
    if confidence < MIN_DOMAIN_CONFIDENCE:
        return False
    if not name and "." not in local:
        return False
    return True


def _stamp_plan(prov: dict[str, Any], plan: DecisionMakerPlan | None) -> None:
    if not plan:
        return
    prov["dm_target_titles"] = list(plan.titles)
    prov["dm_job_function"] = plan.function


def _stamp_miss(row: Any, plan: DecisionMakerPlan | None = None) -> None:
    prov = dict(_as_map(getattr(row, "provenance", None)))
    prov["hunter_checked_at"] = _today()
    _stamp_plan(prov, plan)
    row.provenance = prov
    flag_modified(row, "provenance")


def _stamp_hit(
    row: Any,
    prospect: dict[str, Any],
    plan: DecisionMakerPlan | None = None,
) -> None:
    email = str(prospect.get("email") or "").strip().lower()
    if "email_not_unlocked" in email:
        email = ""
    name = str(prospect.get("name") or "").strip()
    title = str(prospect.get("title") or prospect.get("position") or "").strip()
    employer = str(getattr(row, "company_name", "") or "").strip()
    existing_email = str(getattr(row, "employer_email", "") or "").strip()
    if existing_email and _is_invented_ops_email(existing_email, employer):
        existing_email = ""
        row.employer_email = None
    existing_name, existing_title = _page_name_title(row)
    if email and not existing_email:
        row.employer_email = email
    prov = dict(_as_map(getattr(row, "provenance", None)))
    if name and not existing_name:
        prov["contact_name"] = name
    if title and not existing_title:
        prov["contact_title"] = title
    source = str(prospect.get("source") or "").strip() or "hunter_domain"
    prov["contact_source"] = source
    prov["hunter_checked_at"] = _today()
    if prospect.get("confidence") is not None:
        prov["hunter_confidence"] = prospect.get("confidence")
    if prospect.get("match_why"):
        prov["dm_match_why"] = prospect.get("match_why")
    _stamp_plan(prov, plan)
    if prospect.get("target_titles") and not plan:
        prov["dm_target_titles"] = list(prospect.get("target_titles") or [])
    row.provenance = prov
    flag_modified(row, "provenance")


def _name_bits(person: dict[str, Any]) -> tuple[str, str]:
    first = str(person.get("first_name") or "").strip()
    last = str(person.get("last_name") or "").strip()
    if first and last:
        return first, last
    parts = str(person.get("name") or "").split()
    if len(parts) >= 2:
        return parts[0], parts[-1]
    return "", ""


def _rankable_hunter_person(
    row: dict[str, Any], employer: str, locality: str = ""
) -> bool:
    name = str(row.get("name") or "").strip()
    title = str(row.get("title") or row.get("position") or "").strip()
    if not name or not title:
        return False
    email = str(row.get("email") or "").strip().lower()
    if email and "@" in email:
        return _usable_hunter_row(row, employer, locality)
    return True


def _domain_people(
    client: HunterClient,
    *,
    employer: str,
    domain: Optional[str],
    departments: str,
    locality: str,
    cache: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    key = f"{(domain or '').strip().lower()}|{employer.strip().lower()}|{departments}"
    if key not in cache:
        people: list[dict[str, Any]] = []
        queries: list[dict[str, Any]] = []
        if domain:
            queries.append({"domain": domain, "department": departments, "seniority": "executive,senior"})
        queries.append({"company": employer, "department": departments, "seniority": "executive,senior"})
        seen: set[str] = set()
        for query in queries:
            try:
                search = client.domain_search(**query)
            except (HunterAPIError, HunterConfigError) as exc:
                logger.warning("Hunter domain search failed for %r: %s", employer, exc)
                continue
            for person in search.get("emails") or []:
                if not isinstance(person, dict):
                    continue
                email = str(person.get("email") or "").strip().lower()
                marker = email or str(person.get("name") or "").strip().lower()
                if not marker or marker in seen:
                    continue
                seen.add(marker)
                people.append(person)
        cache[key] = people
    return [
        person
        for person in cache[key]
        if _rankable_hunter_person(person, employer, locality)
    ]


def _fill_email_via_finder(
    client: HunterClient,
    prospect: dict[str, Any],
    *,
    employer: str,
    domain: Optional[str],
    locality: str,
) -> dict[str, Any] | None:
    merged = dict(prospect)
    email = str(merged.get("email") or "").strip().lower()
    if email and _usable_hunter_row(merged, employer, locality):
        return merged
    first, last = _name_bits(merged)
    if not first or not last:
        return None
    try:
        found = client.find_email(
            domain=domain,
            company=employer,
            first_name=first,
            last_name=last,
        )
    except (HunterAPIError, HunterConfigError) as exc:
        logger.warning("Hunter finder failed for %r %s %s: %s", employer, first, last, exc)
        return None
    if not found or not _usable_hunter_row(found, employer, locality):
        return None
    merged.update({k: v for k, v in found.items() if v})
    merged["source"] = found.get("source") or "hunter_finder"
    return merged


def enrich_daily_jobs_with_hunter(
    db: Session,
    *,
    limit: int = TOP_N,
    client: HunterClient | None = None,
    force: bool = False,
) -> dict[str, Any]:
    """Look up the employer on Hunter.io, pick the title that owns this job, find email."""
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
    cache: dict[str, list[dict[str, Any]]] = {}
    filled = 0
    missed = 0
    skipped = 0
    looked = 0
    for row in rows:
        if not _job_needs_hunter(row, force=force):
            skipped += 1
            continue
        employer = str(getattr(row, "company_name", "") or "").strip()
        if not employer:
            skipped += 1
            continue
        looked += 1
        plan = plan_for_job(row)
        domain = domain_for_job(row, db)
        locality = str(getattr(row, "locality", "") or "").strip()
        people = _domain_people(
            hunter,
            employer=employer,
            domain=domain,
            departments=plan.departments,
            locality=locality,
            cache=cache,
        )
        prospect = pick_candidate(plan, people, locality=locality)
        if prospect:
            prospect = _fill_email_via_finder(
                hunter,
                prospect,
                employer=employer,
                domain=domain,
                locality=locality,
            )
        if not prospect:
            known_name, known_title = _page_name_title(row)
            bits = known_name.split()
            if len(bits) >= 2 and score_candidate(
                plan, {"title": known_title or known_name}, locality=locality
            ):
                try:
                    found = hunter.find_email(
                        domain=domain,
                        company=employer,
                        first_name=bits[0],
                        last_name=bits[-1],
                    )
                except (HunterAPIError, HunterConfigError) as exc:
                    logger.warning("Hunter finder failed for %r: %s", employer, exc)
                    found = None
                if found and _usable_hunter_row(found, employer, locality):
                    prospect = found
        if prospect and _usable_hunter_row(prospect, employer, locality):
            _stamp_hit(row, prospect, plan=plan)
            filled += 1
        else:
            _stamp_miss(row, plan=plan)
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
