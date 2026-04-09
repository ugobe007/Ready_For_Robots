"""
Heuristic validation: is this string a plausible **operating company** name for buyer leads?

Used at the end of the pipeline (with `lead_filter.is_junk`) to drop:
  - News / broadcast brands (CBS News, not “CBS automation buyer”)
  - Street / campus / section labels (Hotel Drive)
  - ALL CAPS headline scrapes (LUCAS SYSTEM FETCH)
  - Generic multi-word + RESTAURANT in shout-case (listicle / category lines)

Conservative: prefer false negatives (rare real odd names) over showing embarrassing rows.
"""
from __future__ import annotations

import re
from typing import Optional, Tuple

# ── Major news / broadcast (whole “company” is the outlet, not a buyer record) ──
_NEWS_OUTLET_EXACT = frozenset(
    {
        "cbs news",
        "nbc news",
        "abc news",
        "fox news",
        "sky news",
        "bbc news",
        "msnbc",
        "cnn",
        "cnn news",
        "pbs newshour",
        "npr",
        "npr news",
        "al jazeera",
        "al jazeera english",
        "the new york times",
        "new york times",
        "washington post",
        "the washington post",
        "usa today",
        "associated press",
        "reuters",
        "bloomberg news",
        "financial times",
        "the financial times",
        "wall street journal",
        "the wall street journal",
        "los angeles times",
        "chicago tribune",
        "boston globe",
        "the boston globe",
        "miami herald",
        "houston chronicle",
        "denver post",
        "seattle times",
        "the seattle times",
        "atlanta journal-constitution",
        "san francisco chronicle",
        "sacramento bee",
        "dallas morning news",
        "star tribune",
        "twincities.com",
    }
)

# Last word is a road type; first token is a generic place/section (not “Acme Industrial Drive” with brand)
_ROAD_LAST = re.compile(
    r"(?i)^(.+?)\s+(drive|dr\.?|street|st\.?|road|rd\.?|boulevard|blvd\.?|avenue|ave\.?|"
    r"lane|ln\.?|way|circle|crescent|court|ct\.?|place|pl\.?|highway|hwy\.?|route|rte\.?)\s*$"
)

_GENERIC_ROAD_FIRST = frozenset(
    {
        "hotel",
        "motel",
        "airport",
        "industrial",
        "warehouse",
        "medical",
        "business",
        "campus",
        "downtown",
        "uptown",
        "midtown",
        "north",
        "south",
        "east",
        "west",
        "main",
        "park",
        "lake",
        "river",
        "grand",
        "mill",
        "factory",
        "plant",
        "distribution",
        "logistics",
    }
)

# ALL CAPS scrape: ends like a headline / wire verb
_HEADLINE_ALLCAPS_TAIL = re.compile(
    r"(?i)\s+(FETCH|REPORT|REPORTS|SAYS|SAID|ALERT|BREAKING|TODAY|UPDATE|EXCLUSIVE|BRIEF|WIRE)\s*$"
)

# Shout-case line ending in generic venue type (listicles / category rows)
_GENERIC_VENUE_TAIL = re.compile(
    r"(?i)\s+(RESTAURANT|CAFE|BAR\s*&\s*GRILL|BAR|GRILL|DINER|KITCHEN|TAVERN|PUB)\s*$"
)


def reject_as_non_company_name(name: Optional[str]) -> Tuple[bool, str]:
    """
    Returns (True, reason) if this should not be stored or shown as a lead company name.
    """
    if not name or not str(name).strip():
        return True, "empty name"

    raw = str(name).strip()
    low = raw.lower()
    words = raw.split()

    if low in _NEWS_OUTLET_EXACT:
        return True, "news or broadcast outlet (not a buyer company record)"

    # "CBS News", "Fox News" — two short tokens, second is NEWS
    if len(words) == 2 and words[1].lower() == "news":
        first = words[0].lower()
        if first in (
            "cbs",
            "nbc",
            "abc",
            "fox",
            "sky",
            "bbc",
            "cnn",
            "msnbc",
            "pbs",
            "npr",
        ):
            return True, "broadcast news brand (not a buyer company)"

    m = _ROAD_LAST.match(raw)
    if m and len(words) <= 5:
        first = m.group(1).strip().lower()
        first_token = first.split()[0] if first.split() else ""
        if first_token in _GENERIC_ROAD_FIRST or first in _GENERIC_ROAD_FIRST:
            return True, "address or section label (e.g. road/campus), not a company name"

    # ALL CAPS headline garbage (e.g. LUCAS SYSTEM FETCH)
    if raw == raw.upper() and len(raw) >= 10 and " " in raw:
        if _HEADLINE_ALLCAPS_TAIL.search(raw):
            return True, "ALL CAPS headline fragment (wire-style tail word)"
        if re.search(r"\bSYSTEM\s+FETCH\b", raw):
            return True, "headline scrape (SYSTEM FETCH)"
        if len(words) >= 3 and _GENERIC_VENUE_TAIL.search(raw):
            return True, "shout-case generic venue line (likely category/listicle, not a legal entity)"

    return False, ""


def is_plausible_company_name(name: Optional[str]) -> bool:
    """Inverse of reject_as_non_company_name for convenience."""
    bad, _ = reject_as_non_company_name(name)
    return not bad
