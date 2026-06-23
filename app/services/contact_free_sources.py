"""
Free contact discovery — alternatives to paid Apollo People Search.

Waterfall slots (after CRM, before role inbox):
  1. Emails embedded in press-release / signal text
  2. first.last@domain from CRM decision makers or named contacts
  3. mailto: links on company homepage
"""
from __future__ import annotations

import logging
import os
import re
from typing import Any, Optional, Sequence

import requests

from app.services.outreach_email_inference import person_email_candidates

logger = logging.getLogger(__name__)

_EMAIL_IN_TEXT_RE = re.compile(
    r"\b([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})\b"
)
_MAILTO_RE = re.compile(
    r"mailto:([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})",
    re.IGNORECASE,
)

_BLOCKED_LOCALS = frozenset(
    {
        "noreply",
        "no-reply",
        "donotreply",
        "postmaster",
        "abuse",
        "unsubscribe",
        "bounce",
        "mailer-daemon",
    }
)
_LOW_VALUE_LOCALS = frozenset(
    {
        "media",
        "press",
        "pr",
        "newsroom",
        "investor",
        "investors",
        "ir",
        "careers",
        "jobs",
        "recruiting",
        "hr",
        "privacy",
        "legal",
        "compliance",
        "webmaster",
    }
)
_PREFERRED_LOCALS = frozenset(
    {
        "operations",
        "automation",
        "engineering",
        "facilities",
        "procurement",
        "plantmanager",
        "warehouse",
        "distribution",
        "innovation",
        "partnerships",
        "sales",
        "info",
        "contact",
        "hello",
    }
)


def apollo_contact_enabled() -> bool:
    """
    Apollo is opt-in: requires APOLLO_API_KEY and CONTACT_USE_APOLLO=true.
    Avoids accidental spend when a key is present but renewal is declined.
    """
    key = (os.getenv("APOLLO_API_KEY") or os.getenv("Apollo_API_Key") or "").strip()
    if not key:
        return False
    flag = (os.getenv("CONTACT_USE_APOLLO") or "").strip().lower()
    return flag in ("1", "true", "yes", "on")


def _normalize_email(raw: str) -> str:
    return raw.strip().lower().strip("<>").strip(".,;:")


def _email_score(email: str, domain: Optional[str]) -> int:
    local = email.split("@", 1)[0]
    score = 0
    if domain and email.endswith(f"@{domain.lower()}"):
        score += 40
    if local in _PREFERRED_LOCALS:
        score += 30
    if local in _LOW_VALUE_LOCALS:
        score -= 25
    if "." in local and local.replace(".", "").replace("-", "").isalpha():
        score += 15
    return score


def _is_usable_outreach_email(email: str) -> bool:
    normalized = _normalize_email(email)
    if "@" not in normalized:
        return False
    local = normalized.split("@", 1)[0]
    if local in _BLOCKED_LOCALS:
        return False
    return True


def extract_emails_from_text(text: str, *, domain: Optional[str] = None) -> list[str]:
    """Return deduped outreach-suitable emails found in free text."""
    if not text:
        return []
    found: list[str] = []
    seen: set[str] = set()
    for match in _EMAIL_IN_TEXT_RE.finditer(text):
        email = _normalize_email(match.group(1))
        if not _is_usable_outreach_email(email) or email in seen:
            continue
        seen.add(email)
        found.append(email)
    found.sort(key=lambda e: _email_score(e, domain), reverse=True)
    return found


def pick_signal_outreach_email(texts: Sequence[str], domain: Optional[str]) -> Optional[str]:
    """Best email from signal / press-release bodies."""
    combined = "\n".join(t for t in texts if t)
    emails = extract_emails_from_text(combined, domain=domain)
    return emails[0] if emails else None


def decision_maker_records(
    company: Any,
    contacts: Sequence[Any] | None,
) -> list[dict[str, Any]]:
    """Named contacts / CRM decision makers without verified email."""
    records: list[dict[str, Any]] = []
    meta = getattr(company, "crm_metadata", None) or {}
    for dm in meta.get("decision_makers") or []:
        if isinstance(dm, dict):
            records.append(dm)
    inf = meta.get("lead_inference") or {}
    if isinstance(inf, dict):
        for dm in inf.get("decision_makers") or inf.get("contacts") or []:
            if isinstance(dm, dict):
                records.append(dm)
    for contact in contacts or []:
        first = (getattr(contact, "first_name", None) or "").strip()
        last = (getattr(contact, "last_name", None) or "").strip()
        email = (getattr(contact, "email", None) or "").strip()
        if first and last and not email:
            records.append(
                {
                    "first_name": first,
                    "last_name": last,
                    "title": getattr(contact, "title", None),
                }
            )
    return records


def infer_person_email_from_decision_makers(
    company: Any,
    contacts: Sequence[Any] | None,
    domain: Optional[str],
) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Guess corporate email from named decision makers (first.last@domain).
    Returns (email, pattern_name, title).
    """
    if not domain:
        return None, None, None
    for dm in decision_maker_records(company, contacts):
        first = (dm.get("first_name") or dm.get("first") or "").strip()
        last = (dm.get("last_name") or dm.get("last") or "").strip()
        if not first or not last:
            continue
        title = (dm.get("title") or "").strip() or None
        for email, pattern_name in person_email_candidates(first, last, domain):
            return email, pattern_name, title
    return None, None, None


def fetch_website_mailto_email(domain: str, *, timeout: float = 2.0) -> Optional[str]:
    """Lightweight homepage scrape for mailto: links on the company domain."""
    if not domain:
        return None
    url = f"https://{domain.strip().lower()}/"
    try:
        response = requests.get(
            url,
            headers={"User-Agent": "ReadyForRobots/1.0 (contact research)"},
            timeout=timeout,
            allow_redirects=True,
        )
    except requests.RequestException as exc:
        logger.debug("Website mailto fetch failed for %s: %s", domain, exc)
        return None
    if response.status_code >= 400:
        return None
    html = response.text[:150_000]
    candidates: list[str] = []
    seen: set[str] = set()
    for match in _MAILTO_RE.finditer(html):
        email = _normalize_email(match.group(1))
        if not _is_usable_outreach_email(email) or email in seen:
            continue
        if not email.endswith(f"@{domain.lower()}"):
            continue
        seen.add(email)
        candidates.append(email)
    for email in extract_emails_from_text(html, domain=domain):
        if email not in seen:
            candidates.append(email)
    if not candidates:
        return None
    candidates.sort(key=lambda e: _email_score(e, domain), reverse=True)
    return candidates[0]
