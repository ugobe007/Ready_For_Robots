"""
Heuristic validation: is this string a plausible **operating company** name for buyer leads?

Used at the end of the pipeline (with `lead_filter.is_junk`) to drop:
  - News / broadcast brands (CBS News, not "CBS automation buyer")
  - Street / campus / section labels (Hotel Drive)
  - ALL CAPS headline scrapes (LUCAS SYSTEM FETCH)
  - Generic multi-word + RESTAURANT in shout-case (listicle / category lines)
  - Government / municipal entities (Daviess County — not a robot buyer)
  - Non-profit / trade associations (NRA, AHLA — advocate orgs, not buyers)
  - Automation vendor names inferred from naming patterns (RobosizeME, AutoBot)
"""
from __future__ import annotations

import re
from typing import Optional, Tuple

from app.services.known_brands import is_allowlisted_company_name

# ── Major news / broadcast (whole "company" is the outlet, not a buyer record) ──
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

# Last word is a road type; first token is a generic place/section (not "Acme Industrial Drive" with brand)
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

# ── Government / municipal entity inference ───────────────────────────────────
# "[Name] County", "[Name] Parish", "City of [X]", "Department of [X]", etc.
# These are government entities — not buyers of commercial service robots.
_GOV_SUFFIX = re.compile(
    r"(?i)\b("
    r"county|parish|township|borough|municipality|municipalities|"
    r"school\s+district|unified\s+school\s+district|"
    r"port\s+authority|transit\s+authority|housing\s+authority|"
    r"water\s+authority|power\s+authority|"
    r"county\s+commission|county\s+council|county\s+board|"
    r"public\s+schools|public\s+library|public\s+utilities|"
    r"fire\s+district|sanitation\s+district|irrigation\s+district"
    r")\s*$",
    re.IGNORECASE,
)

_GOV_PREFIX = re.compile(
    r"(?i)^("
    r"city\s+of\s|town\s+of\s|village\s+of\s|county\s+of\s|"
    r"state\s+of\s|province\s+of\s|district\s+of\s|"
    r"department\s+of\s|dept\.\s+of\s|bureau\s+of\s|"
    r"office\s+of\s|board\s+of\s|division\s+of\s|"
    r"ministry\s+of\s|agency\s+of\s|authority\s+of\s|"
    r"port\s+of\s|government\s+of\s|republic\s+of\s|"
    r"u\.s\.\s+|us\s+army\s|us\s+navy\s|us\s+air\s+force\s"
    r")"
)

# ── Non-profit / trade association / advocacy org ─────────────────────────────
# These orgs advocate for industries — they don't buy service robots for operations.
# CAUTION: keep conservative. "American Airlines" starts with "American" — don't over-fire.
_NONPROFIT_EXACT_SUFFIX = re.compile(
    r"(?i)\b("
    r"association|trade\s+association|industry\s+association|"
    r"national\s+association|american\s+association|"
    r"foundation(?!\s+hotel|\s+inn|\s+resort|\s+properties|\s+house)|"  # "Foundation Hotel" is a hotel brand
    r"council(?!\s+bluffs|\s+oak|\s+grove|\s+rock|\s+fire)|"            # "Council Bluffs" is a city
    r"institute(?!\s+of\s+technology)|"                                   # MIT/Caltech are buyers
    r"coalition|consortium|confederation|federation|"
    r"chamber\s+of\s+commerce|trade\s+group|trade\s+council|"
    r"board\s+of\s+trade|industry\s+group|"
    r"bureau(?!\s+of\s+engraving|\s+national\s+laboratory)|"             # avoid "Bureau Veritas" etc.
    r"society(?!\s+hill|\s+hotel|\s+suites)"                              # "Society Hotel" is a hotel
    r")\s*$",
    re.IGNORECASE,
)

# Acronym + "Association" / "NRA", "AHLA", "NRF" — these are always trade bodies
_TRADE_ASSOC_ACRONYM = re.compile(
    r"(?i)^[A-Z]{2,6}$"   # pure uppercase acronym alone is ambiguous; handled by other rules
)

# ── Automation / robotics vendor name inference ───────────────────────────────
# Names that are clearly robot-makers, not robot-buyers.
# Pattern-based: catches startups not yet in the explicit vendor list.

# Starts with Robo/Robot in any casing = almost always a robotics vendor or tech co
_ROBO_PREFIX = re.compile(r"(?i)^robo(t(ic?s?|ize|size)?|tics?|t?ics?)?[a-z]")

# CamelCase or run-together name with "robot"/"robo"/"automat" baked in + tech suffix
_AUTOMATION_VENDOR_PATTERN = re.compile(
    r"(?i)^(robo|robot|autobot|automata|cobotic|cobot|mechatronic|"
    r"machina|synthbot|aibot|navbot|pickbot|sortbot|packbot|movebot|"
    r"swiftbot|anybot|smartbot)"
    r"[A-Za-z0-9]*$"  # rest of camelcase/alphanumeric (e.g. RobosizeME, AutoBot3000)
)

# Names explicitly ending in "robotics" or "robots" after a proper-noun prefix
# e.g. "Xyz Robotics", "Xyz Robots" (not already in the explicit vendor list)
_ROBOTICS_SUFFIX = re.compile(r"(?i)^[A-Z]\S+\s+(robotics?|robots?)\s*$")

# ── Hospitality / logistics tech SaaS vendor names ───────────────────────────
# Property management systems, revenue management, and similar tools sold TO hotels /
# restaurants / logistics operators — these companies are vendors, not buyers.
HOSPITALITY_TECH_VENDORS: frozenset = frozenset(
    {
        # Hotel PMS / RMS
        "mews",
        "cloudbeds",
        "apaleo",
        "clock pms",
        "protel",
        "maestro pms",
        "roomraccoon",
        "hotelogix",
        "webrezpro",
        "stayntouch",
        "guestline",
        "rezovation",
        "innroad",
        "frontdesk anywhere",
        "rmscloud",
        "rms cloud",
        "opera pms",
        "oracle hospitality",
        "oracle opera",
        "shiji",
        "infor hospitality",
        "agilysys",
        "hetras",
        "suitepads",
        "preno",
        "beds24",
        # Restaurant tech / POS
        "toast pos",
        "toast",
        "lightspeed restaurant",
        "lightspeed",
        "square for restaurants",
        "touchbistro",
        "upserve",
        "harbortouch",
        "revel systems",
        "aloha pos",
        "aloha",
        "micros pos",
        "micros",
        "positouch",
        "brink pos",
        "omnivore",
        "par technology",
        "popmenu",
        "otter",
        # Delivery / logistics SaaS
        "bringg",
        "routific",
        "onfleet",
        "shipbob",
        "flexe",
        "logiwa",
        "deposco",
        "increff",
        "körber supply chain",
        "korber supply chain",
        "bluestar",
        "warehouse anywhere",
        # Workforce / labor management SaaS (not hotel operators)
        "hotschedules",
        "fourth hospitality",
        "fourth",
        "workforce",
        "deputy",
        "sling app",
        "sling",
        "humanforce",
        "quinyx",
        "shiftboard",
        "when i work",
        # Revenue / rate management
        "duetto",
        "ideas revenue solutions",
        "ideas",
        "atomize",
        "beonprice",
        "rategain",
        "lodgiq",
        "roiback",
        # Channel managers / booking engines
        "siteminder",
        "cubilis",
        "channelrush",
        "wubook",
        "eviivo",
        "lodgify",
        "guesty",
        "hostaway",
        "hostfully",
        "tokeet",
        "rentals united",
        # Facility / building management SaaS
        "accruent",
        "trimble facility management",
        "archibus",
        "planon",
        "ioffice",
        "smartspace",
        # General automation / workflow SaaS (not robot buyers)
        "robosizeme",
        "robosize",
        "aethon",     # also in robot_vendor_names but belt-and-suspenders
        "pal robotics",
        "service max",
        "servicemax",
        "service channel",
        "servicechannel",
    }
)

_HOSPITALITY_LEGAL_SUFFIX = re.compile(
    r"\s*(inc\.?|llc\.?|ltd\.?|corp\.?|corporation|company|co\.?|plc\.?|gmbh)\s*$",
    re.IGNORECASE,
)


_GENERIC_SUFFIX = re.compile(
    r"\s*(inc\.?|llc\.?|ltd\.?|corp\.?|corporation|company|co\.?|plc\.?|gmbh|"
    r"systems?|platform|solutions?|software|technologies|tech|labs?|group|global)\s*$",
    re.IGNORECASE,
)


def _normalize_saas(name: str) -> str:
    """Strip legal + common product-line suffixes before vendor lookup."""
    s = " ".join(name.strip().lower().split())
    s = _GENERIC_SUFFIX.sub("", s).strip()
    return s


def is_hospitality_tech_vendor(name: Optional[str]) -> bool:
    """True when the name is a known SaaS / tech platform sold TO hospitality/logistics operators."""
    if not name or not str(name).strip():
        return False
    return _normalize_saas(str(name)) in HOSPITALITY_TECH_VENDORS


def is_government_entity(name: Optional[str]) -> bool:
    """True when the name looks like a government / municipal body, not a private operator."""
    if not name or not str(name).strip():
        return False
    raw = str(name).strip()
    return bool(_GOV_SUFFIX.search(raw) or _GOV_PREFIX.match(raw))


def is_trade_org(name: Optional[str]) -> bool:
    """True when the name looks like a non-profit, trade association, or advocacy org."""
    if not name or not str(name).strip():
        return False
    raw = str(name).strip()
    return bool(_NONPROFIT_EXACT_SUFFIX.search(raw))


def is_inferred_automation_vendor(name: Optional[str]) -> bool:
    """
    True when the name pattern strongly implies this is an automation / robotics *vendor*
    (i.e. they build or sell robots) rather than a buyer deploying robots.

    Conservative: only fires on clear-cut patterns to avoid killing real companies
    (e.g. "Automate Inc." a general manufacturer is fine; "AutoBot" is not).
    """
    if not name or not str(name).strip():
        return False
    raw = str(name).strip()
    if _ROBO_PREFIX.match(raw):
        return True
    if _AUTOMATION_VENDOR_PATTERN.match(raw):
        return True
    if _ROBOTICS_SUFFIX.match(raw):
        return True
    return False


def reject_as_non_company_name(name: Optional[str]) -> Tuple[bool, str]:
    """
    Returns (True, reason) if this should not be stored or shown as a lead company name.
    """
    if not name or not str(name).strip():
        return True, "empty name"

    raw = str(name).strip()
    low = raw.lower()
    words = raw.split()

    if is_allowlisted_company_name(raw):
        return False, ""

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

    # Email / social handle leaked into name field
    if "@" in raw and re.search(r"@\s*\S+\.\S+", raw):
        return True, "email or handle pattern, not a company name"

    # Attribution prefix (article metadata, not a buyer)
    if re.match(r"(?i)^\s*(source|photo|image|credit|filed under)\s*:\s*\S", raw):
        return True, "article attribution prefix, not a company name"

    # Government / municipal entity
    if is_government_entity(raw):
        return True, "government or municipal entity (not a commercial robot buyer)"

    # Trade association / non-profit
    if is_trade_org(raw):
        return True, "trade association or non-profit (not an operating buyer)"

    # Automation vendor inferred from name pattern
    if is_inferred_automation_vendor(raw):
        return True, "name pattern matches automation/robotics vendor, not a buyer"

    # Hospitality or logistics tech SaaS vendor
    if is_hospitality_tech_vendor(raw):
        return True, "hospitality or logistics tech vendor (sells to operators, not a buyer)"

    return False, ""


def is_plausible_company_name(name: Optional[str]) -> bool:
    """Inverse of reject_as_non_company_name for convenience."""
    bad, _ = reject_as_non_company_name(name)
    return not bad
