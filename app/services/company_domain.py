"""
Normalized website domain for entity resolution: merge duplicate CRM rows that
represent the same legal entity (same registrable domain, different company IDs).
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse

from app.services.lead_filter import pick_primary_score

_LEGAL_SUFFIX_RE = re.compile(
    r"(?i)(?:,?\s*(?:inc\.?|llc\.?|ltd\.?|corp\.?|corporation|co\.?|plc\.?|gmbh|bv|nv|ag|sa|srl))"
    r"|(?:\s+(?:international|holdings|group|enterprises))$"
)

# Registrable domain → canonical buyer name key (lowercase, collapsed)
_DOMAIN_ENTITY_NAME_KEYS: Dict[str, str] = {
    "jal.co.jp": "japan airlines",
    "choicehotels.com": "choice hotels",
}

# Alternate display names → canonical buyer name key
_NAME_ENTITY_ALIASES: Dict[str, str] = {
    "jal": "japan airlines",
    "japan airline": "japan airlines",
}


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


def normalize_company_name_key(name: Optional[str]) -> str:
    """Collapse legal suffixes and airline/airlines variants for entity dedupe."""
    s = (name or "").strip().lower()
    if not s:
        return ""
    s = re.sub(r"[^\w\s&'-]", " ", s)
    s = " ".join(s.split())
    s = _LEGAL_SUFFIX_RE.sub("", s).strip()
    s = re.sub(r"\bairline\b", "airlines", s)
    s = " ".join(s.split())
    return _NAME_ENTITY_ALIASES.get(s, s)


def company_entity_dedupe_keys(
    name: Optional[str],
    website: Optional[str] = None,
    *,
    website_domain: Optional[str] = None,
) -> Set[str]:
    """
    Stable keys for spotting the same buyer across duplicate DB rows.
    Matches exact domains, normalized names, and known brand domains (e.g. jal.co.jp).
    """
    keys: Set[str] = set()
    name_key = normalize_company_name_key(name)
    if name_key:
        keys.add(f"name:{name_key}")
    dom = normalize_website_domain(website) or (
        str(website_domain).strip().lower() if website_domain else None
    )
    if dom:
        keys.add(f"dom:{dom}")
        mapped = _DOMAIN_ENTITY_NAME_KEYS.get(dom)
        if mapped:
            keys.add(f"name:{mapped}")
    return keys


def _dedupe_by_entity_keys(items: List[Any], key_fn) -> List[Any]:
    seen: Set[str] = set()
    out: List[Any] = []
    for item in items:
        keys = key_fn(item)
        if keys and seen.intersection(keys):
            continue
        if keys:
            seen.update(keys)
        out.append(item)
    return out


def dedupe_companies_ordered(companies: List[Any]) -> List[Any]:
    """
    First occurrence wins (caller controls order — typically score/recency).
    Skips later rows that resolve to the same buyer entity (domain, name variants, brand aliases).
    """

    def _keys(c: Any) -> Set[str]:
        return company_entity_dedupe_keys(
            getattr(c, "name", None),
            getattr(c, "website", None),
            website_domain=getattr(c, "website_domain", None),
        )

    return _dedupe_by_entity_keys(companies, _keys)


def dedupe_staged_lead_tuples(
    staged: List[Tuple[Any, bool, str, Any]],
) -> List[Tuple[Any, bool, str, Any]]:
    """Same dedupe as dedupe_companies_ordered but keeps (company, junk, junk_reason, pri) rows."""

    def _keys(item: Tuple[Any, bool, str, Any]) -> Set[str]:
        c = item[0]
        return company_entity_dedupe_keys(
            getattr(c, "name", None),
            getattr(c, "website", None),
            website_domain=getattr(c, "website_domain", None),
        )

    return _dedupe_by_entity_keys(staged, _keys)


def dedupe_lead_payloads_ordered(leads: List[dict]) -> List[dict]:
    """Dedupe API-shaped lead dicts (homepage hotLeads, cached surfaces)."""

    def _keys(row: dict) -> Set[str]:
        if not isinstance(row, dict):
            return set()
        return company_entity_dedupe_keys(
            row.get("company_name"),
            row.get("website"),
            website_domain=row.get("website_domain"),
        )

    return _dedupe_by_entity_keys(leads, _keys)
