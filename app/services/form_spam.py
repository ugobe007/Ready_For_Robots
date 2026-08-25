"""Form-spam gates for public capture endpoints (report download, etc.).

Pipeline ``lead_filter`` is for scraped company names. This module is for
typed web forms: honeypots, disposable inboxes, and generated mash strings
like ``NLexdStETPSyhfSDp`` / ``Qpjgved LLC``.
"""

from __future__ import annotations

import re
from typing import Optional

_LEGAL_SUFFIX = re.compile(
    r"\b(llc|inc|ltd|corp|co|gmbh|plc|llp|sa|ag|bv|oy|ab|pty|limited|incorporated)\.?\b",
    re.I,
)
_TOKEN_RE = re.compile(r"[A-Za-z]+")
_VOWELS = set("aeiouy")

DISPOSABLE_EMAIL_DOMAINS = frozenset(
    {
        "mailinator.com",
        "guerrillamail.com",
        "guerrillamailblock.com",
        "sharklasers.com",
        "grr.la",
        "10minutemail.com",
        "tempmail.com",
        "temp-mail.org",
        "throwaway.email",
        "yopmail.com",
        "trashmail.com",
        "discard.email",
        "getnada.com",
        "mailnesia.com",
        "maildrop.cc",
        "fakeinbox.com",
        "tempail.com",
        "emailondeck.com",
        "pokemail.net",
        "spam4.me",
        "example.com",
        "example.net",
        "example.org",
    }
)


def _max_consonant_run(token: str) -> int:
    run = best = 0
    for char in token:
        if not char.isalpha():
            run = 0
            continue
        if char.lower() in _VOWELS:
            run = 0
            continue
        run += 1
        if run > best:
            best = run
    return best


def _case_switches(token: str) -> int:
    switches = 0
    for left, right in zip(token, token[1:]):
        if left.isalpha() and right.isalpha() and left.islower() != right.islower():
            switches += 1
    return switches


def token_looks_generated(token: str) -> bool:
    letters = [c for c in token if c.isalpha()]
    n = len(letters)
    if n < 6:
        return False
    switches = _case_switches(token)
    if n >= 12 and switches >= 4:
        return True
    if n >= 16 and switches >= 3:
        return True
    if n >= 7 and _max_consonant_run(token) >= 5:
        return True
    return False


def field_looks_generated(text: Optional[str]) -> bool:
    cleaned = _LEGAL_SUFFIX.sub(" ", text or "")
    return any(token_looks_generated(token) for token in _TOKEN_RE.findall(cleaned))


def email_domain(email: str) -> str:
    return (email or "").strip().lower().rsplit("@", 1)[-1]


def is_disposable_email(email: str) -> bool:
    return email_domain(email) in DISPOSABLE_EMAIL_DOMAINS


def report_download_spam_reason(
    *,
    email: str,
    name: Optional[str] = None,
    company: Optional[str] = None,
    robot_category: Optional[str] = None,
    honeypot: Optional[str] = None,
) -> Optional[str]:
    if (honeypot or "").strip():
        return "honeypot"
    if is_disposable_email(email):
        return "disposable_email"
    generated = sum(
        1
        for value in (name, company, robot_category)
        if field_looks_generated(value)
    )
    if generated >= 2:
        return "generated_fields"
    return None
