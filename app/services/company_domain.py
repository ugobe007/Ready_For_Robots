"""
Normalized website domain for entity resolution: merge duplicate CRM rows that
represent the same legal entity (same registrable domain, different company IDs).
"""
from __future__ import annotations

from typing import Any, List, Optional, Tuple
from urllib.parse import urlparse

from app.services.lead_filter import pick_primary_score


def normalize_website_domain(website: Optional[str]) -> Optional[str]:
    """Hostname only, lowercased, no leading www — stable key for dedupe."""
    if not website or not str(website).strip():
        return None
    w = str(website).strip().lower()
    if "://" in w:
        try:
            netloc = urlparse(w).netloc or ""
        except Exception:
            netloc = w.split("://", 1)[-1]
    else:
        netloc = w
    netloc = netloc.split("/")[0].split("?")[0]
    if netloc.startswith("www."):
        netloc = netloc[4:]
    return netloc or None


def resolve_outreach_domain(
    company: Any | None = None,
    acct: Any | None = None,
    *,
    company_name: Optional[str] = None,
) -> Optional[str]:
    """
    Best domain for outreach email inference.

    Order: company/acct website URL → company.website_domain → brand slug from name
    (e.g. "Marriott International" → marriott.com).
    """
    dom = normalize_website_domain(
        (getattr(company, "website", None) if company else None)
        or (getattr(acct, "website", None) if acct else None)
    )
    if dom:
        return dom

    wd = getattr(company, "website_domain", None) if company else None
    if wd and str(wd).strip():
        return str(wd).strip().lower()

    name = company_name or (getattr(company, "name", None) if company else None) or ""
    from app.services.company_name_presence import infer_brand_domain_hosts

    hosts = infer_brand_domain_hosts(str(name))
    if not hosts:
        return None
    host = hosts[0]
    if host.startswith("www."):
        host = host[4:]
    return host or None


def persist_company_domain(company: Any, domain: str) -> None:
    """Write a resolved domain onto company when website is empty."""
    if not domain or not company:
        return
    if getattr(company, "website", None):
        return
    company.website = f"https://{domain}"
    if hasattr(company, "website_domain"):
        company.website_domain = domain


def company_rank_for_canonical(c: Any) -> tuple:
    """Higher tuple = stronger canonical candidate (intent, evidence, stable id)."""
    s = pick_primary_score(c.scores)
    ov = float(s.overall_intent_score) if s else 0.0
    n_sig = len(c.signals or [])
    return (ov, n_sig, -int(c.id or 0))


def pick_canonical_company(peers: List[Any]) -> Optional[Any]:
    if not peers:
        return None
    return max(peers, key=company_rank_for_canonical)


def dedupe_companies_ordered(companies: List[Any]) -> List[Any]:
    """
    First occurrence wins (caller controls order — typically score/recency).
    Skips later rows with the same normalized domain or same normalized display name.
    """
    seen_names: set[str] = set()
    seen_domains: set[str] = set()
    out: List[Any] = []
    for c in companies:
        raw = (c.name or "").strip()
        name_key = " ".join(raw.lower().split()) if raw else ""
        dom = normalize_website_domain(getattr(c, "website", None)) or getattr(
            c, "website_domain", None
        )
        if dom and dom in seen_domains:
            continue
        if name_key and name_key in seen_names:
            continue
        if dom:
            seen_domains.add(dom)
        if name_key:
            seen_names.add(name_key)
        out.append(c)
    return out


def dedupe_staged_lead_tuples(
    staged: List[Tuple[Company, bool, str, Any]],
) -> List[Tuple[Company, bool, str, Any]]:
    """Same dedupe as dedupe_companies_ordered but keeps (company, junk, junk_reason, pri) rows."""
    seen_names: set[str] = set()
    seen_domains: set[str] = set()
    out: List[Tuple[Company, bool, str, Any]] = []
    for item in staged:
        c = item[0]
        raw = (c.name or "").strip()
        name_key = " ".join(raw.lower().split()) if raw else ""
        dom = normalize_website_domain(getattr(c, "website", None)) or getattr(
            c, "website_domain", None
        )
        if dom and dom in seen_domains:
            continue
        if name_key and name_key in seen_names:
            continue
        if dom:
            seen_domains.add(dom)
        if name_key:
            seen_names.add(name_key)
        out.append(item)
    return out
