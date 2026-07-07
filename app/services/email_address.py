"""Normalize and validate recipient emails before Resend / outreach send."""
from __future__ import annotations

import re
from typing import Optional

# Resend-compatible plain address (lowercase).
_RECIPIENT_RE = re.compile(
    r"^[a-z0-9._%+\-]+@[a-z0-9](?:[a-z0-9\-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9\-]{0,61}[a-z0-9])?)+$"
)

_NAMED_RE = re.compile(r"^([^<]+)<([^>]+)>$", re.IGNORECASE)


def normalize_recipient_email(raw: Optional[str]) -> Optional[str]:
    """
    Return a plain lowercase email or None.

    Accepts:
    - email@domain.com
    - Name <email@domain.com>
    - mailto:email@domain.com
    - first valid entry in comma/semicolon lists
    Rejects company names, bare domains, and malformed addresses.
    """
    if not raw:
        return None
    text = str(raw).strip().strip('"').strip("'")
    if not text:
        return None

    if "," in text or ";" in text:
        for part in re.split(r"[,;]", text):
            norm = normalize_recipient_email(part)
            if norm:
                return norm
        return None

    text = text.replace("mailto:", "", 1).strip()
    named = _NAMED_RE.match(text)
    if named:
        text = named.group(2).strip()

    text = text.strip("<>").strip()
    if "@" not in text or " " in text:
        return None

    local, _, domain = text.partition("@")
    if not local or not domain or "." not in domain:
        return None

    normalized = f"{local.lower()}@{domain.lower()}"
    if not _RECIPIENT_RE.match(normalized):
        return None
    return normalized


def recipient_email_error(raw: Optional[str]) -> Optional[str]:
    """Human-readable reason when normalize_recipient_email returns None."""
    if not raw or not str(raw).strip():
        return "Contact email is empty."
    if "@" not in str(raw):
        return (
            f"“{str(raw).strip()[:60]}” is not an email address — use name@company.com "
            "or Name <name@company.com>."
        )
    norm = normalize_recipient_email(raw)
    if norm:
        return None
    return (
        f"Invalid email format: “{str(raw).strip()[:80]}”. "
        "Use name@company.com (not a company name or bare domain)."
    )
