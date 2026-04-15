"""
Company Validator — Logic Engine
=================================
Answers: "Is this string the name of a real company that could be a
robot/automation buyer?"

Pipeline (in order — fastest gates first):
  0. text_classifier entity_hint  → fast-reject if caller already classified
                                    the name as a non-company entity type
  1. is_junk(name)                → reject known noise/headlines
  2. has_legal_suffix(name)       → accept immediately (Inc, LLC, Corp…)
  3. has_distinctive_proper_noun  → reject if ALL words are generic
                                    category terms (e.g. "Restaurant Robotics")
  4. is_structure_valid(name)     → reject structural headline artifacts
                                    that escape the junk filter

Called from intelligence_news_scraper:
  - ``_extract_companies`` / ``_accept_company`` (extraction pass; optional hint)
  - ``_get_or_create_company`` before **insert** (always pass classifier hint)

When the caller has already run text_classifier.classify(), pass the result
via the `entity_hint` parameter to skip redundant re-classification.
"""
from __future__ import annotations

import re
from typing import Optional, Tuple

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
    # Generic collective nouns — never a company name by themselves
    "companies", "firms", "businesses", "enterprises", "organizations",
    "corporations", "institutions", "agencies", "associations",
    "players", "stakeholders", "participants",
    # Nationality adjectives — describe origin, not identity
    "german", "french", "british", "chinese", "japanese", "korean",
    "italian", "spanish", "dutch", "swedish", "swiss", "australian",
    "canadian", "mexican", "brazilian", "indian", "russian",
    "american", "european", "asian", "african", "latin",
    # Abstract concept / innovation words (user-reported)
    "innovation", "innovations", "technological", "expertise", "expert", "experts",
    "intelligence", "intelligent", "insights", "insight",
    "knowledge", "learning", "thinking", "strategy", "strategic",
    "excellence", "quality", "performance", "efficiency",
    "transformation", "initiative", "initiatives",
    # Web / media / content stubs
    "site", "sites", "portal", "portals", "hub", "hubs", "page", "pages",
    "blog", "blogs", "media", "content", "channel", "channels",
    # Agriculture / food subcategories that read as generic topics
    "poultry", "livestock", "grain", "crop", "crops", "produce",
    "seafood", "aquaculture", "horticulture",
    # Plural / variant forms missed earlier
    "distributions", "facilities", "centres", "hubs",
    # Workforce / labor terms (concepts, not company identifiers)
    "labor", "labour", "workforce", "workers", "worker", "employees",
    "staffing", "hiring", "recruitment", "talent", "headcount",
    "challenge", "challenges", "issue", "issues", "problem", "problems",
    "risk", "risks", "concern", "concerns", "pressure", "pressures",
    "impact", "impacts", "trend", "trends", "shift", "shifts",
    # News event / geopolitical topics — never company names
    "war", "wars", "crisis", "crises", "conflict", "conflicts",
    "disaster", "disasters", "emergency", "emergencies",
    "outbreak", "pandemic", "recession", "inflation",
    "shortage", "shortages", "disruption", "disruptions",
    "scandal", "breach", "attack", "attacks", "threat", "threats",
    "uncertainty", "volatility", "downturn", "slowdown",
})

# Well-known individual people — never a company name
_KNOWN_INDIVIDUALS: frozenset[str] = frozenset({
    # Tech / business figures
    "elon musk", "jeff bezos", "bill gates", "mark zuckerberg", "tim cook",
    "sundar pichai", "satya nadella", "jensen huang", "sam altman", "larry page",
    "sergey brin", "jack dorsey", "reed hastings", "marc benioff", "andy jassy",
    "warren buffett", "charlie munger", "ray dalio", "jamie dimon",
    # Political / public figures likely to appear in news-scraped headlines
    "donald trump", "joe biden", "kamala harris", "barack obama", "joe biden",
    "ron desantis", "gavin newsom", "xi jinping", "vladimir putin",
    "angela merkel", "emmanuel macron", "rishi sunak", "justin trudeau",
    # Celebrities / sports that appear in business news
    "taylor swift", "lebron james", "oprah winfrey",
})

# Common first names — used as a supporting heuristic for person detection
_COMMON_FIRST_NAMES: frozenset[str] = frozenset({
    "james", "john", "robert", "michael", "william", "david", "richard",
    "joseph", "thomas", "charles", "christopher", "daniel", "matthew",
    "anthony", "donald", "mark", "paul", "steven", "andrew", "kenneth",
    "george", "joshua", "kevin", "brian", "edward", "ronald", "timothy",
    "jason", "jeffrey", "ryan", "jacob", "gary", "nicholas", "eric",
    "mary", "patricia", "jennifer", "linda", "barbara", "elizabeth",
    "susan", "jessica", "sarah", "karen", "lisa", "nancy", "betty",
    "margaret", "sandra", "ashley", "emily", "donna", "michelle", "carol",
    "elon", "jeff", "sundar", "satya", "jensen", "oprah",
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
    # "american" removed — now classified as nationality adjective in _GENERIC_WORDS
    # Real companies like "American Airlines" pass because "Airlines" is distinctive
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
    # PR / news headline: "[Brand] Strengthens Position|Presence|Leadership …"
    re.compile(r"(?i)\bstrengthens\s+(position|presence|leadership)\b"),
]


def _is_structure_valid(name: str) -> bool:
    for rx in _STRUCTURAL_REJECTS:
        if rx.search(name):
            return False
    return True


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def is_valid_lead(
    name: str,
    entity_hint: "Optional[object]" = None,
) -> Tuple[bool, str]:
    """
    Main gate.  Returns (True, "") if name should be ingested as a lead,
    or (False, reason) if it should be rejected.

    Pipeline:
      0. entity_hint   — if caller already ran text_classifier.classify(),
                         pass the TextClassification here to fast-reject
                         without re-running the classifier
      1. Junk filter   — catches known bad patterns (fast regex)
      2. Legal suffix  — fast-pass for Inc/LLC/Corp names
      3. Generic words — reject if no distinctive proper noun
      4. Structure     — reject structural headline artifacts
      5. Vendor check  — reject known robotics vendors (not buyers)
      6. Publication   — reject known news orgs

    Parameters
    ----------
    name        : candidate company name string
    entity_hint : optional TextClassification from text_classifier.classify()
                  — if provided, hard-reject types are applied immediately
                  without re-running the classifier
    """
    if not name or not name.strip():
        return False, "empty name"

    name = name.strip()

    # Stage 0: entity type hint from text_classifier (avoids re-classification)
    if entity_hint is not None:
        try:
            from app.services.text_classifier import EntityType
            hint_type = getattr(entity_hint, "entity_type", None)
            hint_conf = getattr(entity_hint, "confidence", 0.0)
            hint_evidence = getattr(entity_hint, "evidence", [])
            _HARD_REJECT = {
                EntityType.PERSON_NAME,
                EntityType.CITY_OR_TOWN,
                EntityType.COUNTRY,
                EntityType.SAYING,
                EntityType.EQUIPMENT_CAT,
                EntityType.MARKET_FRAGMENT,
            }
            if hint_type in _HARD_REJECT and hint_conf >= 0.65:
                reason = (
                    f"text_classifier: {hint_type.value} "
                    f"(conf={hint_conf:.2f}) — "
                    + "; ".join(hint_evidence[:2])
                )
                return False, reason
            if hint_type == EntityType.ARTICLE_HEADLINE and hint_conf >= 0.75:
                return False, (
                    f"text_classifier: article headline "
                    f"(conf={hint_conf:.2f}) — "
                    + "; ".join(hint_evidence[:2])
                )
        except Exception:
            pass  # never let hint processing break the validator

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

    # Stage 2c: known individual people are never companies
    # Using a curated list only — generic first-name heuristics cause false positives
    # on founder-named companies like "John Deere", "Tim Hortons", "Walt Disney".
    if name.strip().lower() in _KNOWN_INDIVIDUALS:
        return False, f"known individual person, not a company ({name!r})"

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
