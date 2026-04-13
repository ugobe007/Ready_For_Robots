"""
Company Validator — Logic Engine
=================================
Answers: "Is this string the name of a real company that could be a
robot/automation buyer?"

Pipeline (in order — fastest gates first):
  1. is_junk(name)                → reject known noise/headlines
  2. has_legal_suffix(name)       → accept immediately (Inc, LLC, Corp…)
  3. has_distinctive_proper_noun  → reject if ALL words are generic
                                    category terms (e.g. "Restaurant Robotics")
  4. is_structure_valid(name)     → reject structural headline patterns
                                    that escape the junk filter

Called from intelligence_news_scraper._accept_company() BEFORE the company
is written to the database, replacing the ad-hoc _is_valid_company_name check.
"""
from __future__ import annotations

import re
from typing import Tuple

from app.services.lead_filter import is_junk
from app.services.robot_vendor_names import is_known_robotics_vendor_name
from app.services.news_publications import is_known_publication_name

# ─────────────────────────────────────────────────────────────────────────────
# GATE 2 — Legal suffix fast-pass
# A name with a recognised legal entity suffix is almost certainly a real company.
# ─────────────────────────────────────────────────────────────────────────────
_LEGAL_SUFFIX = re.compile(
    r"\b(inc\.?|llc\.?|ltd\.?|corp\.?|co\.?|plc\.?|llp\.?|lp\.?|gmbh|bv|nv|ag|"
    r"s\.a\.?|s\.r\.l\.?|pty\.?|pte\.?|holdings?|group|enterprises?|"
    r"international|industries|ventures?|partners?|associates?)\s*$",
    re.IGNORECASE,
)


def _has_legal_suffix(name: str) -> bool:
    return bool(_LEGAL_SUFFIX.search(name))


# ─────────────────────────────────────────────────────────────────────────────
# GATE 3 — Distinctive proper noun check
#
# Generic words on their own are NOT company names — they are industry
# category descriptors.  A valid company name must contain at least ONE
# word that is NOT in this generic set (i.e. a real proper noun like a
# surname, invented word, place name used as brand, etc.)
#
# "Restaurant Robotics"  → restaurant=generic, robotics=generic  → REJECT
# "Tyson Foods"          → Tyson=distinctive                     → PASS
# "Boston Dynamics"      → Boston=distinctive                    → PASS
# "Amazon"               → Amazon=distinctive                    → PASS
# "Kraft Heinz"          → Kraft=distinctive                     → PASS
# ─────────────────────────────────────────────────────────────────────────────
_GENERIC_WORDS: frozenset[str] = frozenset({
    # Industry verticals
    "restaurant", "restaurants", "hospitality", "hotel", "hotels", "lodging",
    "logistics", "warehouse", "warehousing", "distribution", "fulfillment",
    "healthcare", "health", "medical", "clinical", "hospital", "hospitals",
    "pharmaceutical", "pharma", "pharmacy",
    "retail", "retailer", "retailers",
    "manufacturing", "manufacturer", "manufacturers", "industrial", "industry",
    "food", "beverage", "beverages", "agriculture", "agri", "dairy", "meat",
    "packaging", "package", "packing", "packager",
    "construction", "building", "buildings", "real", "estate",
    "automotive", "auto", "aerospace", "aviation", "transportation",
    "energy", "utilities", "utility", "power",
    "education", "government",
    "ecommerce", "commerce",
    # Technology categories
    "robotics", "robots", "robot", "automation", "automate",
    "technology", "technologies", "tech",
    "software", "hardware", "platform", "platforms",
    "solutions", "solution", "services", "service",
    "systems", "system", "analytics", "intelligence",
    "digital", "artificial", "machine", "computer", "cloud",
    "data", "network", "cyber", "ai",
    # Generic business descriptors
    "global", "national", "regional", "international", "american", "european",
    "enterprise", "commercial",
    "advanced", "smart", "integrated", "connected", "innovative", "next",
    "modern", "new", "future",
    "supply", "chain", "value", "demand",
    # Common filler words that appear at title-case in headlines
    "the", "a", "an", "and", "or", "of", "in", "at", "by", "for",
    "on", "with", "from", "to", "into", "as", "its", "their",
    # Report/article words
    "report", "survey", "study", "analysis", "outlook", "forecast",
    "trends", "trend", "insights", "insight", "review", "news",
    "weekly", "monthly", "annual", "quarterly",
    # Generic plural suffixes used as categories (user-reported)
    "chains", "brands", "groups", "networks", "systems", "operators",
    "providers", "vendors", "suppliers", "dealers", "distributors",
})

# Country and region names — never a company name on their own
_COUNTRIES_AND_REGIONS: frozenset[str] = frozenset({
    "germany", "france", "japan", "china", "india", "brazil", "canada",
    "australia", "mexico", "italy", "spain", "south korea", "north korea",
    "russia", "ukraine", "turkey", "indonesia", "argentina", "netherlands",
    "switzerland", "sweden", "norway", "denmark", "finland", "poland",
    "singapore", "taiwan", "vietnam", "thailand", "malaysia", "philippines",
    "saudi arabia", "uae", "united arab emirates", "egypt", "nigeria",
    "south africa", "kenya", "israel", "pakistan", "bangladesh",
    "europe", "asia", "africa", "latin america", "middle east",
    "north america", "south america", "southeast asia",
    "western europe", "eastern europe", "asia pacific",
    "the eu", "the uk", "the us",
})

# Words that look generic but are used as real brand/company identifiers.
# Whitelisting them prevents false-rejection.
_ALWAYS_DISTINCTIVE: frozenset[str] = frozenset({
    # Proper names / brands that happen to be common words
    "amazon", "apple", "target", "oracle", "delta", "united",
    # Kept here because they appear as PART of multi-word names where another
    # word carries the distinctiveness (General Mills, National Grid)
    "general", "national",
    "american",    # American Airlines, American Express
    "first",       # First Solar, First Data
    "new",         # New Balance, New York Times Company
    # Known 3-letter company tickers that look like airport codes
    "ups", "dhl", "ibm", "3m", "sap", "nxp",
})

# Add distribution to the generic set (missed earlier)
_GENERIC_WORDS = _GENERIC_WORDS | frozenset({
    "distribution", "distributor", "distributors",
    "operations", "operation",
    "group",           # used generically, but also in real names — borderline
    "network", "networks",
    "center", "centers", "centre", "centres",
})


def _has_distinctive_word(name: str) -> bool:
    """
    Returns True if the name contains at least one word that is NOT in
    the generic category set — i.e. a real proper noun / brand identifier.
    """
    words = re.findall(r"[a-zA-Z&]+", name)
    for word in words:
        w = word.lower()
        if w in _ALWAYS_DISTINCTIVE:
            return True
        if w not in _GENERIC_WORDS:
            return True
    return False


# ─────────────────────────────────────────────────────────────────────────────
# GATE 4 — Structural sanity check
# Catches edge-cases that escape the junk filter and generic-word check.
# ─────────────────────────────────────────────────────────────────────────────
_STRUCTURAL_REJECTS = [
    # Ends with a year (event/conference title)
    re.compile(r"\b20\d\d\s*$"),
    # Contains a period mid-name (sentence boundary leaked in)
    re.compile(r"\w\.\s+[A-Z]"),
    # "X and Y" where Y is a generic word (headline conjunction)
    re.compile(r"\s+and\s+\w+\s*$", re.IGNORECASE),
    # All words are 3 letters or fewer (likely an acronym chain or noise)
    re.compile(r"^([A-Z]{1,3}\s+){2,}[A-Z]{1,3}\s*$"),
]


def _is_structure_valid(name: str) -> bool:
    for rx in _STRUCTURAL_REJECTS:
        if rx.search(name):
            return False
    return True


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def is_valid_lead(name: str) -> Tuple[bool, str]:
    """
    Main gate.  Returns (True, "") if name should be ingested as a lead,
    or (False, reason) if it should be rejected.

    Pipeline:
      1. Junk filter   — catches known bad patterns (fast regex)
      2. Legal suffix  — fast-pass for Inc/LLC/Corp names
      3. Generic words — reject if no distinctive proper noun
      4. Structure     — reject structural headline artifacts
      5. Vendor check  — reject known robotics vendors (not buyers)
      6. Publication   — reject known news orgs
    """
    if not name or not name.strip():
        return False, "empty name"

    name = name.strip()

    # Stage 1a: fast-pass for universally-known companies (before junk filter
    # which can reject short all-caps names as airport codes)
    _KNOWN_COMPANIES: frozenset[str] = frozenset({
        "ups", "dhl", "ibm", "3m", "sap", "bmw", "kfc", "cvs", "gm",
        "ge", "hp", "lg", "bp", "ab inbev", "jbs", "mcd",
    })
    if name.strip().lower() in _KNOWN_COMPANIES:
        return True, ""

    # Stage 1: junk filter (existing regex-based)
    junk, reason = is_junk(name)
    if junk:
        return False, f"junk filter: {reason}"

    # Stage 2: legal suffix fast-pass
    if _has_legal_suffix(name):
        return True, ""

    # Stage 2b: country / region names are never companies
    if name.strip().lower() in _COUNTRIES_AND_REGIONS:
        return False, f"country or region name, not a company ({name!r})"

    # Stage 3: must contain a distinctive proper noun
    if not _has_distinctive_word(name):
        return False, (
            f"no distinctive proper noun — all words are generic category terms "
            f"({name!r} reads as a concept/phrase, not a company)"
        )

    # Stage 4: structural sanity
    if not _is_structure_valid(name):
        return False, "structural headline artifact"

    # Stage 5: robotics vendor (seller, not buyer)
    if is_known_robotics_vendor_name(name):
        return False, "known robotics vendor (not a buyer opportunity)"

    # Stage 6: news publication
    if is_known_publication_name(name):
        return False, "known news publication (not a company)"

    return True, ""
