"""
Detect Google RSS / market-research scraper noise stored as buyer leads.

Used by Phase 4 cleanup to purge headline fragments and HTML aggregator rows
without touching real accounts that happen to have Unknown industry.
"""
from __future__ import annotations

import re
from typing import Iterable, Optional, Sequence, Tuple

from app.services.text_classifier import EntityType, classify as classify_entity

_UNKNOWN_INDUSTRIES = frozenset({"", "unknown", "other", "new"})

_GOOGLE_RSS_HTML_RE = re.compile(
    r"news\.google\.com/rss|news\.google\.com/|"
    r"<a\s+href=|target=[\"']_blank[\"']|"
    r"&nbsp;|<font\s+color=|googlenews",
    re.IGNORECASE,
)

_MARKET_REPORT_RE = re.compile(
    r"(?i)\bmarket\s+(analysis|size|forecast|to\s+reach|report)\b|"
    r"\bforecast,?\s+size|indexbox\b|future\s+market\s+insights\b|"
    r"\bindustry\s+outlook\b|\bfast\s+facts\b",
)

_DELETE_ENTITY_TYPES = frozenset({
    EntityType.ARTICLE_HEADLINE,
    EntityType.DESCRIPTION,
    EntityType.MARKET_FRAGMENT,
    EntityType.SECTOR_DESCRIPTOR,
    EntityType.FACILITY_DESCRIPTOR,
    EntityType.POPULATION_GROUP,
    EntityType.DESCRIPTOR_ONLY,
    EntityType.EQUIPMENT_CAT,
})


def is_unknown_industry(industry: Optional[str]) -> bool:
    return (industry or "").strip().lower() in _UNKNOWN_INDUSTRIES


def signals_contain_google_rss_html(signals: Sequence[object]) -> bool:
    """True when signal text looks like Google News RSS HTML blobs."""
    texts = [str(getattr(s, "signal_text", None) or "") for s in signals or []]
    if not texts:
        return False
    hits = sum(1 for t in texts if _GOOGLE_RSS_HTML_RE.search(t))
    return hits >= max(1, int(len(texts) * 0.34))


def signals_are_market_research_noise(signals: Sequence[object]) -> bool:
    texts = [str(getattr(s, "signal_text", None) or "") for s in signals or []]
    if not texts:
        return False
    blob = " ".join(texts)
    return bool(_MARKET_REPORT_RE.search(blob))


def entity_is_noise_headline(name: str, *, min_confidence: float = 0.65) -> Tuple[bool, str]:
    tc = classify_entity(name or "")
    if tc.entity_type in _DELETE_ENTITY_TYPES and tc.confidence >= min_confidence:
        return True, f"entity={tc.entity_type.value} ({tc.confidence:.2f})"
    return False, ""


def is_rss_noise_delete_candidate(
    company_name: Optional[str],
    industry: Optional[str],
    signals: Sequence[object],
    *,
    from_is_junk: Optional[Tuple[bool, str]] = None,
) -> Tuple[bool, str, str]:
    """
    Conservative delete gate for Unknown-industry RSS / headline garbage.

    Returns (should_delete, reason, bucket).
    """
    name = (company_name or "").strip()
    if not is_unknown_industry(industry):
        return False, "", ""

    if from_is_junk is not None:
        junk, reason = from_is_junk
    else:
        from app.services.lead_filter import is_junk

        junk, reason = is_junk(name)

    if junk:
        return True, reason, "fast_junk"

    if signals_contain_google_rss_html(signals):
        return True, "google RSS HTML aggregator noise in signals", "rss_html_noise"

    if signals_are_market_research_noise(signals):
        ent_ok, ent_reason = entity_is_noise_headline(name, min_confidence=0.55)
        if ent_ok or len(name) >= 40:
            return True, "market research / industry report headline", "market_report_noise"

    ent_ok, ent_reason = entity_is_noise_headline(name, min_confidence=0.78)
    if ent_ok:
        return True, ent_reason, "headline_entity"

    return False, "", ""
