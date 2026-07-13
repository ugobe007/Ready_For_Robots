"""
Normalized website domain for entity resolution: merge duplicate CRM rows that
represent the same legal entity (same registrable domain, different company IDs).
"""
from __future__ import annotations

import os
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
    "qcasinoandresort.com": "q casino",
}

# Alternate display names → canonical buyer name key
_NAME_ENTITY_ALIASES: Dict[str, str] = {
    "jal": "japan airlines",
    "japan airline": "japan airlines",
    "q casino resort": "q casino",
    "q casino + resort": "q casino",
}

# Curated official domains for short/ambiguous names (avoid casino.com-style false positives).
_KNOWN_BRAND_DOMAINS: Dict[str, str] = {
    "q casino": "qcasinoandresort.com",
}

# Registrable domains that are generic nouns — never infer outreach from these.
_UNTRUSTED_GENERIC_DOMAINS: frozenset[str] = frozenset({
    "casino.com",
    "hotel.com",
    "hotels.com",
    "resort.com",
    "resorts.com",
    "shop.com",
    "store.com",
    "company.com",
    "business.com",
    "travel.com",
    "food.com",
    "mail.com",
    "email.com",
    "group.com",
    "global.com",
    "international.com",
})

# Single-token slugs that map to generic .com domains (not buyer-specific brands).
_GENERIC_SLUG_NOUNS: frozenset[str] = frozenset({
    "casino",
    "hotel",
    "hotels",
    "resort",
    "resorts",
    "shop",
    "store",
    "mall",
    "food",
    "travel",
    "company",
    "business",
    "group",
    "global",
    "national",
    "regional",
    "local",
    "market",
    "media",
    "news",
    "tech",
    "digital",
    "smart",
    "auto",
    "bank",
    "finance",
    "health",
    "care",
    "home",
    "house",
    "land",
    "city",
    "town",
    "county",
    "state",
    "energy",
    "power",
    "water",
    "steel",
    "metal",
    "wood",
    "glass",
    "paper",
    "plastic",
    "robot",
    "robots",
})


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


def is_trusted_outreach_domain(domain: Optional[str]) -> bool:
    """False for generic registrable domains (e.g. casino.com) unlinked to a specific buyer."""
    dom = normalize_website_domain(domain)
    if not dom:
        return False
    if dom in _UNTRUSTED_GENERIC_DOMAINS:
        return False
    label = dom.split(".", 1)[0]
    if label in _GENERIC_SLUG_NOUNS and dom.endswith(".com"):
        return False
    return True


def known_brand_domain(name: Optional[str]) -> Optional[str]:
    key = normalize_company_name_key(name)
    if not key:
        return None
    return _KNOWN_BRAND_DOMAINS.get(key)


def resolve_outreach_domain(
    company: Any | None = None,
    acct: Any | None = None,
    *,
    company_name: Optional[str] = None,
) -> Optional[str]:
    """
    Best domain for outreach email inference.

    Order: known brand map → company/acct website URL → company.website_domain → brand slug from name
    (e.g. "Marriott International" → marriott.com). Generic domains like casino.com are rejected.
    """
    name = company_name or (getattr(company, "name", None) if company else None) or ""

    curated = known_brand_domain(name)
    if curated:
        return curated

    dom = normalize_website_domain(
        (getattr(company, "website", None) if company else None)
        or (getattr(acct, "website", None) if acct else None)
    )
    if dom and is_trusted_outreach_domain(dom):
        return dom

    wd = getattr(company, "website_domain", None) if company else None
    if wd and str(wd).strip():
        dom = str(wd).strip().lower()
        if is_trusted_outreach_domain(dom):
            return dom

    # Brand-slug inference (name → firstword.com, e.g. "Shake Shack" → shake.com) fabricates
    # domains that resolve in DNS but belong to someone else. They slip the dead-domain
    # quarantine and were the dominant hard-bounce class. A real website must come from a
    # source lookup (OpenAI/DuckDuckGo) or the record itself — never from the company name.
    # Disabled by default; set CAL_ALLOW_BRAND_SLUG_DOMAIN=1 only to temporarily re-enable.
    if (os.getenv("CAL_ALLOW_BRAND_SLUG_DOMAIN", "0") or "0").strip().lower() in ("1", "true", "yes"):
        from app.services.company_name_presence import infer_brand_domain_hosts

        hosts = infer_brand_domain_hosts(str(name))
        for host in hosts:
            candidate = host[4:] if host.startswith("www.") else host
            if is_trusted_outreach_domain(candidate):
                return candidate

    return curated


def persist_company_domain(company: Any, domain: str) -> None:
    """Write a resolved domain onto company when website is empty."""
    if not domain or not company or not is_trusted_outreach_domain(domain):
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
