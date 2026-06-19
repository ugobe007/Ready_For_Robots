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


def signals_predominantly_rss_html(signals: Sequence[object], *, min_ratio: float = 0.6) -> bool:
    """True when most signal rows are RSS/HTML aggregator blobs (not one noisy outlier)."""
    texts = [str(getattr(s, "signal_text", None) or "") for s in signals or []]
    if not texts:
        return False
    hits = sum(1 for t in texts if _GOOGLE_RSS_HTML_RE.search(t))
    return hits / len(texts) >= min_ratio


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
    Narrow delete gate for Unknown-industry headline garbage.

    RSS/HTML signal storage format is NOT a delete criterion — use
    ``pipeline_delete_policy.unknown_industry_delete_allowed``.
    """
    from app.services.pipeline_delete_policy import unknown_industry_delete_allowed

    return unknown_industry_delete_allowed(
        company_name,
        industry,
        signals,
        from_is_junk=from_is_junk,
    )
