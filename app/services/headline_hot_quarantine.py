"""Detect RSS/headline company names leaking into HOT/WARM pipeline tiers."""
from __future__ import annotations

import re
from typing import Any, Optional, Sequence

from app.services.company_name_validation import reject_as_non_company_name
from app.services.known_brands import is_allowlisted_company_name
from app.services.lead_filter import (
    _company_name_not_corroborated_by_signals,
    classify_lead,
    is_headline_fragment,
    is_junk,
)
from app.services.rss_noise_lead import entity_is_noise_headline, is_market_report_company_name
from app.services.unknown_industry_rescue import is_unknown_industry_headline_stub

_HEADLINE_LEAK_RES = [
    re.compile(r"(?i)^news\b"),
    re.compile(r"(?i)^new\s+(?!york\b|jersey\b|hampshire\b|mexico\b|zealand\b|balance\b|egg\b|ton\b)"),
    re.compile(r"(?i)^free\s+guide\b"),
    re.compile(r"(?i)^inside\b$"),
    re.compile(r"(?i)^meta\s+amazon\b"),
    re.compile(r"(?i)^passenger\s+assistance\b"),
    re.compile(r"(?i)^packaging\s+suction\b"),
    re.compile(r"(?i)^news\s+ai"),
    re.compile(r"(?i)^ice\s+begins\b"),
    re.compile(r"(?i)\b(begins|announces|highlights|approves|proves|locks)\s+(buying|that|the|a)\b"),
    re.compile(r"(?i)\bceo\s+highlights\b"),
    re.compile(r"(?i)\bstaff\s+using\b"),
    re.compile(r"(?i)\bwarehouse\s+benefits\b"),
    re.compile(r"(?i)\bmarket\s+(analysis|to\s+reach|forecast)\b"),
    re.compile(r"(?i):\s*\w"),  # event / trade-show headlines (NRF 2026: HPE)
    re.compile(r"(?i)\b\d{4}\s*:"),
    re.compile(r"(?i)^why\b"),
    re.compile(r"(?i)^how\b"),
    re.compile(r"(?i)^what\b"),
    re.compile(r"(?i)\s-\s+let\b"),
    re.compile(r"(?i)^all-inclusive\b"),
    re.compile(r"(?i)^faraway\b"),
    re.compile(r"(?i)^tavern\s+tap\b"),
    re.compile(r"(?i)\bBecomes\s+(?:First|Official|Certified)\b"),
    re.compile(r"(?i)\bFactory\s+Os\b"),
    re.compile(r"(?i)\bEngineering\s+Precision\b"),
    re.compile(r"(?i)^(?:Beverage|Food|Snack|Contract)\s+Co-?Packer\b"),
    re.compile(r"(?i)'s\s+(?:MedTech|Medtech)\s+startup\b"),
]
_SENTENCE_VERB = re.compile(
    r"(?i)\b(is|are|was|were|has|have|begins|announces|highlights|approves|proves|locks|using|demonstrates)\b"
)


def headline_hot_leak_reason(
    name: Optional[str],
    signals: Sequence[Any] | None = None,
    *,
    from_classify: tuple[bool, str, Any] | None = None,
) -> tuple[bool, str]:
    """
    True when an active company.name looks like a news headline, not a buyer entity.
    Used to quarantine HOT/WARM leaks that survived score-only gates.
    """
    raw = (name or "").strip()
    if not raw:
        return True, "empty name"
    if is_allowlisted_company_name(raw):
        return False, ""

    junk, reason = is_junk(raw)
    if junk:
        return True, reason

    hf, hr = is_headline_fragment(raw)
    if hf:
        return True, hr

    stub, sr = is_unknown_industry_headline_stub(raw)
    if stub:
        return True, sr

    bad, br = reject_as_non_company_name(raw)
    if bad:
        return True, br

    if is_market_report_company_name(raw):
        return True, "market research / industry report headline"

    noise, nr = entity_is_noise_headline(raw, min_confidence=0.68)
    if noise:
        return True, nr

    for rx in _HEADLINE_LEAK_RES:
        if rx.search(raw):
            return True, "headline hot leak (pattern)"

    words = raw.split()
    if len(words) >= 6 and _SENTENCE_VERB.search(raw):
        return True, "headline sentence (verb phrase)"

    if len(words) == 1 and len(raw) <= 8 and raw.lower() not in {"target", "motive", "moxie"}:
        if raw.lower() in {"inside", "costs", "home", "research", "news", "guide", "why", "how"}:
            return True, "single-word headline fragment"

    if signals:
        if _company_name_not_corroborated_by_signals(raw, signals):
            return True, "company name not found in signal text (mis-attributed headline fragment)"

    if from_classify is not None:
        junk_c, reason_c, _tier = from_classify
        if junk_c:
            return True, reason_c

    return False, ""


def headline_hot_leak_for_company(
    company: Any,
    signals: Sequence[Any] | None = None,
    scores: Any = None,
) -> tuple[bool, str, str]:
    """
    Returns (should_quarantine, reason, tier).
    Only quarantine when tier is HOT or WARM (caller may still apply broader rules).
    """
    sigs = signals if signals is not None else getattr(company, "signals", None) or []
    sc = scores if scores is not None else getattr(company, "scores", None)
    classify = classify_lead(company, sc, sigs)
    junk_c, reason_c, pri = classify
    tier = getattr(pri, "tier", "COLD") or "COLD"
    ok, reason = headline_hot_leak_reason(
        getattr(company, "name", None),
        sigs,
        from_classify=classify,
    )
    if not ok:
        return False, "", tier
    if junk_c:
        return True, reason_c, tier
    return True, reason, tier
