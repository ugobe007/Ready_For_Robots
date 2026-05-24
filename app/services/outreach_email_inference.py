"""
Industry-aware default outreach emails when no CRM contact or Apollo match exists.

Role inboxes (not named executives) — ordered by likelihood for automation / robotics buyers.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

# General automation & robotics outreach (operational buyers first, not marketing).
DEFAULT_ROLE_LOCALS: tuple[str, ...] = (
    "operations",
    "automation",
    "engineering",
    "innovation",
    "facilities",
    "procurement",
    "sales",
    "info",
    "contact",
    "hello",
    "partnerships",
    "projects",
    "support",
)

LOGISTICS_MANUFACTURING_LOCALS: tuple[str, ...] = (
    "plantmanager",
    "warehouse",
    "distribution",
    "operations",
    "automation",
    "engineering",
    "facilities",
    "procurement",
    "sales",
    "info",
    "contact",
)

HOSPITALITY_LOCALS: tuple[str, ...] = (
    "operations",
    "facilities",
    "engineering",
    "innovation",
    "automation",
    "procurement",
    "sales",
    "info",
    "contact",
    "hello",
)

HEALTHCARE_LOCALS: tuple[str, ...] = (
    "operations",
    "facilities",
    "engineering",
    "procurement",
    "automation",
    "sales",
    "info",
    "contact",
)

RETAIL_LOCALS: tuple[str, ...] = (
    "operations",
    "innovation",
    "facilities",
    "procurement",
    "automation",
    "sales",
    "info",
    "contact",
)

# Secondary inboxes for CC when no explicit contact list is set.
CC_ROLE_LOCALS: tuple[str, ...] = ("info", "contact", "hello", "engineering")

# Named-person patterns (when first/last are known).
PERSON_EMAIL_PATTERNS: tuple[tuple[str, str], ...] = (
    ("{first}.{last}", "first.last"),
    ("{first}{last}", "firstlast"),
    ("{first_initial}{last}", "firstinitiallast"),
    ("{first_initial}.{last}", "firstinitial.last"),
    ("{first}{last_initial}", "firstlastinitial"),
    ("{last}{first_initial}", "lastfirstinitial"),
)


@dataclass(frozen=True)
class OutreachEmailGuess:
    primary: str
    cc: list[str]
    primary_local: str
    industry_bucket: str


def industry_bucket(industry: Optional[str]) -> str:
    raw = (industry or "").strip().lower()
    if any(x in raw for x in ("hospitality", "hotel", "casino", "gaming", "resort")):
        return "hospitality"
    if any(x in raw for x in (
        "logistics", "warehouse", "warehousing", "distribution", "manufacturing",
        "factory", "industrial", "supply chain",
    )):
        return "logistics_manufacturing"
    if any(x in raw for x in ("healthcare", "hospital", "medical", "clinical")):
        return "healthcare"
    if "retail" in raw or "store oper" in raw:
        return "retail"
    return "default"


def role_locals_for_industry(industry: Optional[str]) -> tuple[str, ...]:
    bucket = industry_bucket(industry)
    if bucket == "hospitality":
        return HOSPITALITY_LOCALS
    if bucket == "logistics_manufacturing":
        return LOGISTICS_MANUFACTURING_LOCALS
    if bucket == "healthcare":
        return HEALTHCARE_LOCALS
    if bucket == "retail":
        return RETAIL_LOCALS
    return DEFAULT_ROLE_LOCALS


def all_known_role_locals() -> frozenset[str]:
    """Union of role inbox local-parts (includes legacy sales/marketing defaults)."""
    parts: set[str] = set()
    for tup in (
        DEFAULT_ROLE_LOCALS,
        LOGISTICS_MANUFACTURING_LOCALS,
        HOSPITALITY_LOCALS,
        HEALTHCARE_LOCALS,
        RETAIL_LOCALS,
        CC_ROLE_LOCALS,
    ):
        parts.update(tup)
    parts.update(("sales", "marketing"))
    return frozenset(parts)


def looks_like_person_email(email: str) -> bool:
    """Heuristic: first.last@domain style addresses are not overwritten."""
    normalized = (email or "").strip().lower()
    if "@" not in normalized:
        return False
    local = normalized.split("@", 1)[0]
    if "." not in local:
        return False
    left, _, right = local.partition(".")
    return len(left) >= 1 and len(right) >= 2 and left.isalpha() and right.replace("-", "").isalpha()


def should_reinfer_stored_contact(email: Optional[str], domain: str) -> bool:
    """
    True when a CRM contact_email may be replaced with industry-aware inference.
    Skips person-style emails and addresses on a different domain.
    """
    if not domain:
        return False
    if not email or not email.strip():
        return True
    normalized = email.strip().lower()
    if looks_like_person_email(normalized):
        return False
    if not normalized.endswith(f"@{domain.lower()}"):
        return False
    local = normalized.split("@", 1)[0]
    return local in all_known_role_locals()


def _email(local: str, domain: str) -> str:
    return f"{local.strip().lower()}@{domain.strip().lower()}"


def infer_primary_outreach_email(domain: Optional[str], industry: Optional[str] = None) -> Optional[str]:
    """Best-guess TO address for buyer outreach."""
    if not domain:
        return None
    locals_ = role_locals_for_industry(industry)
    return _email(locals_[0], domain) if locals_ else None


def infer_sales_email(domain: Optional[str], industry: Optional[str] = None) -> Optional[str]:
    """Backward-compatible alias — prefer infer_primary_outreach_email."""
    return infer_primary_outreach_email(domain, industry)


def infer_cc_outreach_emails(
    domain: Optional[str],
    industry: Optional[str] = None,
    *,
    primary: Optional[str] = None,
    max_cc: int = 2,
) -> list[str]:
    """Secondary addresses for CC (info/contact/hello, then next operational inboxes)."""
    if not domain or max_cc <= 0:
        return []

    primary = (primary or infer_primary_outreach_email(domain, industry) or "").strip().lower()
    cc: list[str] = []

    for local in CC_ROLE_LOCALS:
        addr = _email(local, domain)
        if addr != primary and addr not in cc:
            cc.append(addr)
        if len(cc) >= max_cc:
            return cc

    for local in role_locals_for_industry(industry)[1:6]:
        addr = _email(local, domain)
        if addr != primary and addr not in cc:
            cc.append(addr)
        if len(cc) >= max_cc:
            break

    return cc


def infer_outreach_emails(domain: Optional[str], industry: Optional[str] = None) -> Optional[OutreachEmailGuess]:
    """Primary TO + CC list for a company domain."""
    if not domain:
        return None
    bucket = industry_bucket(industry)
    locals_ = role_locals_for_industry(industry)
    if not locals_:
        return None
    primary_local = locals_[0]
    primary = _email(primary_local, domain)
    cc = infer_cc_outreach_emails(domain, industry, primary=primary)
    return OutreachEmailGuess(
        primary=primary,
        cc=cc,
        primary_local=primary_local,
        industry_bucket=bucket,
    )


def person_email_candidates(
    first: str,
    last: str,
    domain: str,
) -> list[tuple[str, str]]:
    """Return (email, pattern_name) for common corporate naming conventions."""
    first = first.strip().lower()
    last = last.strip().lower()
    if not first or not last or not domain:
        return []
    fi = first[0]
    li = last[0]
    mapping = {
        "first": first,
        "last": last,
        "first_initial": fi,
        "last_initial": li,
    }
    out: list[tuple[str, str]] = []
    seen: set[str] = set()
    for pattern_tpl, pattern_name in PERSON_EMAIL_PATTERNS:
        local = pattern_tpl.format(**mapping)
        email = _email(local, domain)
        if email in seen:
            continue
        seen.add(email)
        out.append((email, pattern_name))
    return out
