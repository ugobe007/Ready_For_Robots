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
})


def is_allowlisted_company_name(name: str) -> bool:
    """True if the normalized name is a known brand we must never mark as junk."""
    s = (name or "").strip().lower()
    return s in ALLOWLISTED_COMPANY_NAMES
