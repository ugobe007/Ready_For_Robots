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
    registrable_domain,
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
    """Employer website first. Job-board and press URLs are the wrong Hunter domain."""
    hosts: list[str] = []
    company_id = getattr(row, "company_id", None)
    if company_id and db is not None:
        from app.models.company import Company

        company = db.query(Company).filter(Company.id == company_id).first()
        if company:
            host = _host(str(getattr(company, "website", "") or ""))
            if host:
                hosts.append(host)
    for attr in ("contact_url", "apply_url"):
        host = _host(str(getattr(row, attr, "") or ""))
        if host:
            hosts.append(host)
    for host in hosts:
        cleaned = registrable_domain(host)
        if cleaned:
            return cleaned
    return None


def domain_from_people(people: list[dict[str, Any]] | None) -> Optional[str]:
    """Hunter company search often has no website on the job row. Use email hosts."""
    for person in people or []:
        if not isinstance(person, dict):
            continue
        host = registrable_domain(person.get("organization_domain"))
        if host:
            return host
        email = str(person.get("email") or "").strip().lower()
        if "@" in email:
            host = registrable_domain(email.split("@", 1)[1])
            if host:
                return host
    return None


def _page_contact_complete(row: Any) -> bool:
    name, _title = _page_name_title(row)
    contact = _contact_fields(row)
    source = str(_as_map(getattr(row, "provenance", None)).get("contact_source") or "")
    if not name or not contact.get("email"):
        return False
    if source.startswith("hunter") or source == "decision_maker_agent":
        return False
    return True


def _job_needs_hunter(
    row: Any, *, force: bool = False, scrape_pages: bool = False
) -> bool:
    if _page_contact_complete(row):
        return False
    name, _title = _page_name_title(row)
    contact = _contact_fields(row)
    blob = _as_map(getattr(row, "provenance", None))
    if name and contact.get("email") and not force:
        return False
    if not force and str(blob.get("hunter_checked_at") or "") == _today():
        # Domain-only miss (admin GET used to do this) must not skip the
        # leadership-page → Hunter finder pass.
        if scrape_pages and str(blob.get("hunter_leadership_at") or "") != _today():
            return True
        return False
    return True


def _company_search_names(employer: str, locality: str = "") -> list[str]:
    """Hunter company search uses the brand, not 'Westin Fort Lauderdale'."""
    raw = re.sub(r"\s+", " ", (employer or "").strip())
    names: list[str] = []
    seen: set[str] = set()

    def add(value: str) -> None:
        text = re.sub(r"\s+", " ", (value or "").strip(" -,."))
        key = text.lower()
        if len(text) < 3 or key in seen:
            return
        seen.add(key)
        names.append(text)

    add(raw)
    add(raw.replace(".", ""))
    add(re.sub(r"\s+by\s+.+$", "", raw, flags=re.I))
    add(re.sub(r"\s+of\s+[A-Z].*$", "", raw))
    add(
        re.sub(
            r",?\s+(inc|llc|ltd|corp|corporation|company|co|services|group|hotels|hotel|restaurants|restaurant)\.?$",
            "",
            raw,
            flags=re.I,
        )
    )
    city = (locality or "").split(",")[0].strip()
    if len(city) >= 4:
        for base in list(names):
            if base.lower().endswith(city.lower()):
                add(base[: -len(city)])
    return names


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


def _email_fits_employer(
    email: str, employer: str, locality: str = "", domain: str | None = None
) -> bool:
    """Reject Marin General for Mercy, NAPA Australia for a PA DC, Unical for Unifi."""
    raw = (email or "").strip().lower()
    if "@" not in raw:
        return False
    host = raw.split("@", 1)[1].lower()
    if _is_us_locality(locality) and any(host.endswith(tld) for tld in _FOREIGN_TLDS):
        return False
    want = registrable_domain(domain)
    got = registrable_domain(host)
    if want and got and (want == got or got.endswith("." + want) or want.endswith("." + got)):
        return True
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
    row: dict[str, Any],
    employer: str,
    locality: str = "",
    domain: str | None = None,
) -> bool:
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
    if not _email_fits_employer(email, employer, locality, domain=domain):
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


def _stamp_miss(
    row: Any,
    plan: DecisionMakerPlan | None = None,
    *,
    scrape_pages: bool = False,
) -> None:
    prov = dict(_as_map(getattr(row, "provenance", None)))
    prov["hunter_checked_at"] = _today()
    if scrape_pages:
        prov["hunter_leadership_at"] = _today()
    _stamp_plan(prov, plan)
    row.provenance = prov
    flag_modified(row, "provenance")


def _stamp_hit(
    row: Any,
    prospect: dict[str, Any],
    plan: DecisionMakerPlan | None = None,
    *,
    scrape_pages: bool = False,
    domain: str | None = None,
) -> None:
    email = str(prospect.get("email") or "").strip().lower()
    if "email_not_unlocked" in email:
        email = ""
    name = str(prospect.get("name") or "").strip()
    title = str(prospect.get("title") or prospect.get("position") or "").strip()
    employer = str(getattr(row, "company_name", "") or "").strip()
    existing_name, _existing_title = _page_name_title(row)
    existing_email = str(getattr(row, "employer_email", "") or "").strip()
    if existing_email and _is_invented_ops_email(existing_email, employer):
        existing_email = ""
        row.employer_email = None
    prov = dict(_as_map(getattr(row, "provenance", None)))
    existing_source = str(prov.get("contact_source") or "")
    page_owned = bool(
        existing_name
        and existing_email
        and not existing_source.startswith("hunter")
        and existing_source != "decision_maker_agent"
    )
    if page_owned:
        _stamp_plan(prov, plan)
        prov["hunter_checked_at"] = _today()
        if scrape_pages:
            prov["hunter_leadership_at"] = _today()
        row.provenance = prov
        flag_modified(row, "provenance")
        return
    if email and _usable_hunter_row(
        prospect,
        employer,
        str(getattr(row, "locality", "") or ""),
        domain=domain,
    ):
        row.employer_email = email
    if name:
        prov["contact_name"] = name
    if title:
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
    if prospect.get("source") == "leadership_page" or scrape_pages:
        prov["hunter_leadership_at"] = _today()
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
    row: dict[str, Any],
    employer: str,
    locality: str = "",
    domain: str | None = None,
) -> bool:
    name = str(row.get("name") or "").strip()
    title = str(row.get("title") or row.get("position") or "").strip()
    if not name or not title:
        return False
    email = str(row.get("email") or "").strip().lower()
    if email and "@" in email:
        if _is_invented_ops_email(email, employer):
            return False
        if (row.get("verification_status") or "").lower() == "invalid":
            return False
        local = email.split("@", 1)[0]
        if local in _ROLE_LOCALS:
            return False
        if not row.get("from_company_search") and domain:
            if not _email_fits_employer(email, employer, locality, domain=domain):
                return False
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
            queries.append({"domain": domain, "department": departments})
        for name in _company_search_names(employer, locality):
            queries.append({"company": name, "department": departments})
        seen: set[str] = set()
        for query in queries:
            try:
                search = client.domain_search(**query)
            except (HunterAPIError, HunterConfigError) as exc:
                logger.warning("Hunter domain search failed for %r: %s", employer, exc)
                continue
            discovered = registrable_domain(search.get("domain"))
            company_hit = bool(query.get("company") and not query.get("domain"))
            if discovered:
                for person in search.get("emails") or []:
                    if isinstance(person, dict) and not person.get("organization_domain"):
                        person["organization_domain"] = discovered
            for person in search.get("emails") or []:
                if not isinstance(person, dict):
                    continue
                email = str(person.get("email") or "").strip().lower()
                marker = email or str(person.get("name") or "").strip().lower()
                if not marker or marker in seen:
                    continue
                seen.add(marker)
                row = dict(person)
                if company_hit:
                    row["from_company_search"] = True
                people.append(row)
        cache[key] = people
    return [
        person
        for person in cache[key]
        if _rankable_hunter_person(person, employer, locality, domain=domain)
    ]


def _finder_attempts(domain: Optional[str], employer: str) -> list[dict[str, str]]:
    """Leadership name + employer site first. Company-only if that domain is wrong."""
    attempts: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    clean = (registrable_domain(domain) or "").strip()
    company = (employer or "").strip()
    for domain_value, company_value in (
        (clean, company),
        ("", company),
    ):
        if not domain_value and not company_value:
            continue
        key = (domain_value.lower(), company_value.lower())
        if key in seen:
            continue
        seen.add(key)
        query: dict[str, str] = {}
        if domain_value:
            query["domain"] = domain_value
        if company_value:
            query["company"] = company_value
        attempts.append(query)
    return attempts


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
    if email and _usable_hunter_row(merged, employer, locality, domain=domain):
        return merged
    first, last = _name_bits(merged)
    if not first or not last:
        return merged if merged.get("name") else None
    for query in _finder_attempts(domain, employer):
        try:
            found = client.find_email(
                first_name=first,
                last_name=last,
                **query,
            )
        except (HunterAPIError, HunterConfigError) as exc:
            logger.warning(
                "Hunter finder failed for %r %s %s: %s", employer, first, last, exc
            )
            continue
        if found and _usable_hunter_row(found, employer, locality, domain=domain):
            merged.update({k: v for k, v in found.items() if v})
            merged["source"] = found.get("source") or "hunter_finder"
            return merged
    return merged if merged.get("name") else None


def enrich_daily_jobs_with_hunter(
    db: Session,
    *,
    limit: int = TOP_N,
    client: HunterClient | None = None,
    force: bool = False,
    scrape_pages: bool = False,
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
    hunter: HunterClient | None = None
    if hunter_contact_enabled():
        try:
            hunter = client or HunterClient()
        except HunterConfigError as exc:
            if not scrape_pages:
                out["reason"] = str(exc)
                return out
    elif not scrape_pages:
        out["reason"] = "hunter_disabled"
        return out

    rows = select_daily_report_rows(db, limit=limit)
    cache: dict[str, list[dict[str, Any]]] = {}

    def _fetch_hunter_people(
        *,
        employer: str,
        domain: Optional[str],
        departments: str,
        locality: str,
        leadership_person: Any = None,
    ) -> list[dict[str, Any]]:
        if hunter is None:
            return []
        if isinstance(leadership_person, dict) and leadership_person.get("name"):
            return []
        return _domain_people(
            hunter,
            employer=employer,
            domain=domain,
            departments=departments,
            locality=locality,
            cache=cache,
        )

    page_cache: dict[str, list[dict[str, Any]]] = {}

    def _fetch_leadership_pages(
        *,
        employer: str,
        domain: Optional[str],
    ) -> list[dict[str, Any]]:
        if not scrape_pages:
            return []
        from app.services.employer_leadership import fetch_leadership_pages

        key = (domain or employer or "").strip().lower()
        if key not in page_cache:
            page_cache[key] = fetch_leadership_pages(domain=domain, employer=employer)
        return page_cache[key]

    filled = 0
    missed = 0
    skipped = 0
    looked = 0
    for row in rows:
        if not _job_needs_hunter(row, force=force, scrape_pages=scrape_pages):
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
        if hunter is not None and not domain:
            preview = _domain_people(
                hunter,
                employer=employer,
                domain=None,
                departments=plan.departments,
                locality=locality,
                cache=cache,
            )
            domain = domain_from_people(preview)

        prospect = None
        try:
            from app.services.extract_dag.decision_maker import run_decision_maker_dag

            dag_out = run_decision_maker_dag(
                row,
                domain=domain,
                fetchers={
                    "hunter_people": _fetch_hunter_people,
                    "leadership_pages": _fetch_leadership_pages,
                },
            )
            if dag_out.get("job_function") and dag_out.get("target_titles"):
                plan.function = str(dag_out["job_function"])
                plan.titles = list(dag_out["target_titles"])
                plan.departments = str(dag_out.get("departments") or plan.departments)
            prospect = dag_out.get("decision_maker")
            if not isinstance(prospect, dict):
                prospect = None
        except Exception:
            logger.warning("extract DAG failed for %r", employer, exc_info=True)
            from app.services.employer_leadership import people_from_pages

            people = _fetch_hunter_people(
                employer=employer,
                domain=domain,
                departments=plan.departments,
                locality=locality,
            )
            leaders = people_from_pages(
                _fetch_leadership_pages(employer=employer, domain=domain)
            )
            prospect = pick_candidate(plan, leaders + people, locality=locality)
        if prospect and hunter is not None:
            prospect = _fill_email_via_finder(
                hunter,
                prospect,
                employer=employer,
                domain=domain,
                locality=locality,
            )
        has_mail = bool(
            prospect
            and _usable_hunter_row(prospect, employer, locality, domain=domain)
        )
        known_name, known_title = _page_name_title(row)
        if not has_mail and hunter is not None:
            first, last = _name_bits({"name": known_name})
            if first and last and score_candidate(
                plan, {"title": known_title or known_name}, locality=locality
            ):
                for query in _finder_attempts(domain, employer):
                    try:
                        found = hunter.find_email(
                            first_name=first,
                            last_name=last,
                            **query,
                        )
                    except (HunterAPIError, HunterConfigError) as exc:
                        logger.warning("Hunter finder failed for %r: %s", employer, exc)
                        found = None
                    if found and _usable_hunter_row(
                        found, employer, locality, domain=domain
                    ):
                        prospect = found
                        has_mail = True
                        break
        if has_mail:
            _stamp_hit(
                row, prospect, plan=plan, scrape_pages=scrape_pages, domain=domain
            )
            filled += 1
        elif prospect and prospect.get("name") and not known_name:
            _stamp_hit(
                row, prospect, plan=plan, scrape_pages=scrape_pages, domain=domain
            )
            filled += 1
        else:
            _stamp_miss(row, plan=plan, scrape_pages=scrape_pages)
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
