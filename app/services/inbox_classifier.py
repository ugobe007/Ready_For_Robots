"""Inbox Classifier — Filters out non-customer, test, newsletter, and internal ops emails."""
from __future__ import annotations

import re
from typing import Optional

NON_CUSTOMER_DOMAINS = (
    "pythh.ai",
    "sendfoxmail.com",
    "orbital-ai.com",
    "orbitalai.com",
    "sendfox.com",
)

NON_CUSTOMER_SUBJECT_PATTERNS = (
    r"pythh",
    r"sendfox",
    r"orbital\s*ai",
    r"portfolio\s+digest",
    r"learning\s+report",
    r"outreach\s+template\s+updated",
    r"circuit\s+breaker\s+tripped",
    r"watchdog",
    r"heartbeat",
    r"test_sent",
    r"test_email",
    r"\[test\]",
)

NON_CUSTOMER_FROM_PATTERNS = (
    r"hello@pythh\.ai",
    r"mail@sendfoxmail\.com",
    r"pythh",
    r"sendfox",
    r"orbital",
)


def classify_inbox_folder(
    from_email: Optional[str],
    subject: Optional[str],
    body_text: Optional[str] = None,
) -> str:
    """Return 'main' for genuine customer replies, or 'test' for internal/test/newsletter emails."""
    sender = (from_email or "").strip().lower()
    sub = (subject or "").strip().lower()

    if not sender and not sub:
        return "test"

    # Domain check
    if any(sender.endswith(f"@{domain}") or f"@{domain}" in sender for domain in NON_CUSTOMER_DOMAINS):
        return "test"

    # Pattern check on sender
    if any(re.search(pat, sender) for pat in NON_CUSTOMER_FROM_PATTERNS):
        return "test"

    # Pattern check on subject
    if any(re.search(pat, sub) for pat in NON_CUSTOMER_SUBJECT_PATTERNS):
        return "test"

    # Internal ops / watchdog alerts from readyforrobots.com
    if "readyforrobots.com" in sender and any(kw in sub for kw in ("learning report", "ops", "watchdog", "heartbeat", "template updated", "circuit breaker")):
        return "test"

    return "main"
