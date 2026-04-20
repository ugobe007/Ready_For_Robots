"""
Short / ticker-style names that are real companies but fail naive heuristics
(e.g. 1–2 character names, all-caps “airport code” lookalikes).

Used by:
  - company_validator.is_valid_lead (fast-pass before junk filter)
  - lead_filter.is_junk (early allowlist so cleanup / API match the logic engine)
"""
from __future__ import annotations

# Keep in sync with product expectations: these are globally recognized brands/tickers
# stored as single-field “company names” by scrapers.
ALLOWLISTED_COMPANY_NAMES: frozenset[str] = frozenset({
    "ups", "dhl", "ibm", "3m", "sap", "bmw", "kfc", "cvs", "gm",
    "ge", "hp", "lg", "bp", "ab inbev", "jbs", "mcd",
    # "Best X" companies — real brands that trigger the Best-listicle junk pattern
    "best buy", "best western", "best western hotels", "best western international",
    "best western plus",
    # Founder-named companies — person-name classifier fires on these (false positive)
    # They are real companies; always allowlist.
    "john deere", "tim hortons", "henry schein", "ben & jerry's",
    "bob evans", "bob's red mill", "dave's hot chicken", "jack in the box",
    "jack's family restaurants", "bob evans farms",
    # Possessive brand names — single-word possessives that are real QSR chains
    "wendy's", "mcdonald's", "denny's", "arby's", "hardee's", "carl's jr",
    "popeyes", "chili's", "applebee's", "shari's", "friendly's", "steak 'n shake",
    # Health plan / insurance companies that look like noun phrases
    "partnership health plan", "health plan of san joaquin",
    "health plan of the redwoods", "molina healthcare",
})


def is_allowlisted_company_name(name: str) -> bool:
    """True if the normalized name is a known brand we must never mark as junk."""
    s = (name or "").strip().lower()
    return s in ALLOWLISTED_COMPANY_NAMES
