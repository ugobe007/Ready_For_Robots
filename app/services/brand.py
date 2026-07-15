"""
Brand isolation — Cal serves two separate businesses from one codebase:

  * ``ready_for_robots`` — readyforrobots.com buyer-match / vendor-signup outreach
  * ``stagegate``        — onstage.bot trade-show logistics (bonded warehousing,
                            staging, on-site show support)

These must NEVER cross. Cal may work either brand, but a message written in one
brand's voice must only ever be sent from that brand's sending identity, and the
Ready For Robots buyer loop must never read/act on StageGate accounts (and vice
versa). This module is the single source of truth for detecting brand from
content, from a sender address, and from a company/CRM account.

Root cause this guards against: Cal, running in Ready For Robots mode, drafted
and sent "Cal with StageGate · onstage.bot" logistics copy to robot OEMs from
readyforrobots.com (a policy violation).
"""
from __future__ import annotations

from typing import Any, Optional

BRAND_RFR = "ready_for_robots"
BRAND_STAGEGATE = "stagegate"

# Phrases that unambiguously belong to the StageGate logistics persona. If any
# appear in a subject/body/from-name, the content brand is StageGate.
STAGEGATE_CONTENT_MARKERS = (
    "onstage.bot",
    "stagegate",
    "bonded warehous",
    "show logistics",
    "on-site tech support during demos",
)

# Email domains that belong to each brand's sending identity.
STAGEGATE_SENDER_DOMAINS = ("onstage.bot", "stagegate.com", "stagegate.io")
RFR_SENDER_DOMAINS = ("readyforrobots.com", "reply.readyforrobots.com")


class BrandViolation(Exception):
    """Raised when a message's content brand does not match its sender brand."""


def content_brand(*parts: Optional[str]) -> str:
    """Brand implied by the text of a message. Defaults to Ready For Robots."""
    haystack = " ".join(p for p in parts if p).lower()
    if any(marker in haystack for marker in STAGEGATE_CONTENT_MARKERS):
        return BRAND_STAGEGATE
    return BRAND_RFR


def _domain_of(email: Optional[str]) -> str:
    raw = (email or "").strip().lower()
    if "<" in raw and ">" in raw:
        raw = raw[raw.rfind("<") + 1 : raw.rfind(">")]
    if "@" in raw:
        return raw.rsplit("@", 1)[1].strip()
    return raw


def sender_brand(from_email: Optional[str]) -> Optional[str]:
    """Brand of a sending address by domain. None if the domain is unrecognized."""
    domain = _domain_of(from_email)
    if not domain:
        return None
    if any(domain == d or domain.endswith("." + d) for d in STAGEGATE_SENDER_DOMAINS):
        return BRAND_STAGEGATE
    if any(domain == d or domain.endswith("." + d) for d in RFR_SENDER_DOMAINS):
        return BRAND_RFR
    return None


def is_stagegate_branded(company: Any = None, acct: Any = None) -> bool:
    """True when this company/account belongs to the StageGate pipeline."""
    return company_brand(company, acct) == BRAND_STAGEGATE


def company_brand(company: Any = None, acct: Any = None) -> str:
    """Brand a company/CRM account belongs to. Defaults to Ready For Robots."""
    for obj in (acct, company):
        if obj is None:
            continue
        meta = getattr(obj, "crm_metadata", None)
        if isinstance(meta, dict) and meta.get("outreach_pipeline") == BRAND_STAGEGATE:
            return BRAND_STAGEGATE
        data_source = (getattr(obj, "data_source", None) or "")
        if isinstance(data_source, str) and data_source.lower().startswith("stagegate"):
            return BRAND_STAGEGATE
        mi = getattr(obj, "market_intelligence", None)
        if isinstance(mi, dict) and "stagegate_oem" in mi:
            return BRAND_STAGEGATE
    return BRAND_RFR


def assert_send_brand_consistent(
    *,
    from_email: Optional[str],
    subject: Optional[str],
    body_text: Optional[str],
    from_display_name: Optional[str] = None,
) -> None:
    """
    Enforce that a message's content brand matches its sending identity.

    Raises ``BrandViolation`` on any cross-brand send, e.g. StageGate logistics
    copy going out from readyforrobots.com, or Ready For Robots copy from an
    onstage.bot address. An unrecognized sender domain is treated as Ready For
    Robots (the default identity), so StageGate content from an unknown/unset
    sender is still blocked.
    """
    cbrand = content_brand(subject, body_text, from_display_name)
    sbrand = sender_brand(from_email) or BRAND_RFR
    if cbrand != sbrand:
        raise BrandViolation(
            f"Cross-brand send blocked: content brand={cbrand!r} but sender brand={sbrand!r} "
            f"(from={from_email!r}). StageGate/onstage.bot copy must only be sent from a "
            f"StageGate address, and Ready For Robots copy only from readyforrobots.com. "
            f"See app/services/brand.py."
        )
