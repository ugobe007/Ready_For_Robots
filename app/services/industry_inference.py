"""
Shared industry inference from text (signal text, company name, article context).
Used by reclassify-unknown and can be used by scrapers.

Tie-breaking: when keyword scores tie, prefer industries earlier in INDUSTRY_TIE_PRIORITY
(stronger verticals / less noisy than e.g. Hospitality from STR headlines).
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional, Sequence, Tuple

# Normalized company name -> canonical industry (OEMs / frequent mislabels from signal text alone).
KNOWN_COMPANY_INDUSTRY: Dict[str, str] = {
    # Automotive / EV
    "faraday future": "Automotive & Manufacturing",
    "tesla": "Automotive & Manufacturing",
    "tesla inc": "Automotive & Manufacturing",
    "rivian": "Automotive & Manufacturing",
    "lucid motors": "Automotive & Manufacturing",
    "lucid group": "Automotive & Manufacturing",
    "nio inc": "Automotive & Manufacturing",
    "xpeng": "Automotive & Manufacturing",
    "fisker": "Automotive & Manufacturing",
    "general motors": "Automotive & Manufacturing",
    "ford motor": "Automotive & Manufacturing",
    "stellantis": "Automotive & Manufacturing",
    "sumitomo": "Automotive & Manufacturing",
    "duravant": "Automotive & Manufacturing",
    # Robotics / technology
    "brain corp": "Datacenters",
    "brain corp.": "Datacenters",
    "dexterity": "Automotive & Manufacturing",
    "opentrons global robotics": "Medical Technology",
    "hesai technology": "Automotive & Manufacturing",
    "seagull software": "Datacenters",
    "blinkops": "Datacenters",
    "velaris": "Datacenters",
    # Healthcare / senior living
    "cedarhurst": "Healthcare",
    "lifespire": "Healthcare",
    "novant health": "Healthcare",
    "marshall medical": "Healthcare",
    # Logistics / food distribution
    "performance food group": "Logistics",
    "core-mark": "Logistics",
    "dp world antwerp": "Logistics",
    "forward air acquisition": "Logistics",
    # Entertainment / gaming
    "mgm springfield": "Casinos & Gaming",
}

# When two industries have the same raw keyword score, pick the higher-priority one first.
INDUSTRY_TIE_PRIORITY: Tuple[str, ...] = (
    "Automotive & Manufacturing",
    "Medical Technology",
    "Healthcare",
    "Logistics",
    "Food Processing & Manufacturing",
    "CPG & Consumer Goods",
    "Contract Manufacturing",
    "Manufacturing",
    "Food & Beverage",
    "Retail",
    "Datacenters",
    "Airports & Aviation",
    "Hospitality",
    "Food Service",
    "Real Estate & Facilities",
    "Media & Publishing",
)


INDUSTRY_KEYWORDS: Dict[str, list] = {
    "Logistics": [
        "warehouse", "logistics", "fulfillment", "distribution", "supply chain",
        "3pl", "third party logistics", "fulfillment center", "fulfillment centre",
        "cold storage", "freight", "shipping",
        # Omit bare "delivery" — matches almost any supply-chain headline and pollutes other verticals.
    ],
    # Do not use generic "property management" — STR/Airbnb robot deployments often mention it
    # and mislabel automotive OEMs (e.g. Faraday Future delivering robots to vacation rentals).
    "Hospitality": [
        "hotel", "resort", "hospitality", "lodging", "motel", "inn",
        "housekeeping", "guest services",
    ],
    "Food Service": [
        "restaurant", "food service", "kitchen", "dining", "qsr",
        "fast food", "cafe", "chain restaurant", "franchise"
    ],
    "Healthcare": [
        "hospital", "healthcare", "health system", "clinic", "patient",
        "senior living", "nursing home", "assisted living", "medical center",
        "skilled nursing", "memory care", "long-term care", "ltc",
        "elder care", "home health", "home care", "palliative care",
        "cedarhurst", "lifespire", "brookdale", "sunrise senior",
        "brightspring", "encompass health",
    ],
    "Medical Technology": [
        "laboratory", "lab automation", "clinical lab", "diagnostics lab",
        "pharmacy", "hospital pharmacy", "surgical robot", "surgical suite",
        "patient care", "specimen processing", "pathology", "iv compounding",
        "medication dispensing", "robotic surgery", "da vinci", "telepresence",
        "telehealth", "phlebotomy", "surgical", "surgery robot", "korea biomed",
        "vitestro", "roen surgical", "surgerii"
    ],
    "Food Processing & Manufacturing": [
        "food processing", "food manufacturing", "meat processing",
        "bakery", "produce processing", "food packaging", "food safety",
        "food sorting", "food preparation", "cooking automation",
        "robotic chef", "robotic kitchen",
        "food plant", "food factory", "food production", "poultry processing",
        "seafood processing", "dairy processing", "cheese plant", "meat packing",
        "beverage manufacturing", "bottling plant", "canning", "brewing",
        "snack food", "baked goods", "confectionery", "cereal manufacturing",
    ],
    "CPG & Consumer Goods": [
        "consumer packaged goods", "cpg", "consumer goods", "fmcg",
        "fast moving consumer goods", "household products", "personal care",
        "packaged food", "packaged beverage", "brand manufacturer",
        "co-manufacturer", "co-packer", "co packer", "contract packer",
        "bottler", "bottling line", "canning line", "filling line",
        "kraft", "mondelez", "unilever", "procter", "colgate", "nestle",
        "general mills", "campbell", "conagra", "kellogg", "hershey",
        "anheuser", "molson", "constellation brands", "pepsi", "coca-cola",
        "tyson", "jbs usa", "smithfield", "hormel",
        "packaging line", "shrink wrap", "stretch wrap", "case packing",
        "palletizer", "depalletizer", "end of line", "end-of-line",
        "pack out", "pack in", "pack-out", "pack-in",
    ],
    "Contract Manufacturing": [
        "contract manufacturer", "contract manufacturing", "contract packager",
        "contract packaging", "cmo", "cdmo", "toll manufacturer",
        "toll processing", "toll packaging", "third party manufacturing",
        "white label", "private label manufacturer", "oem manufacturer",
        "custom manufacturer", "job shop", "make to order",
        "co-manufacturer", "flexible manufacturing", "small batch",
        "multi-sku", "rapid changeover", "high mix low volume",
    ],
    "Datacenters": [
        "datacenter", "data center", "hyperscale", "cloud infrastructure",
        "colocation", "server farm", "datacenter operations", "datacenter maintenance",
        # Omit bare "server" — substring-matches "food server", unrelated IT mentions.
    ],
    "Airports & Aviation": [
        "airport", "terminal", "aviation", "baggage handling", "boarding gate",
        "airport operations", "airport security", "airport shuttle",
        "airlines", "airline",
        # Omit generic "metro", "transit", "transportation" — label city-mobility and unrelated articles.
    ],
    "Retail": [
        "retail", "shopping", "e-commerce", "grocery", "supermarket",
        "shelf scanning", "inventory robot", "click-and-collect", "micro-fulfillment",
        "retail fulfillment", "retail automation", "cashier", "checkout",
        "brick and mortar", "big box",
        # Omit bare "store" — substring false positives ("restore", "bookstore" as noise, etc.).
    ],
    "Apparel & Textiles": [
        "garment", "apparel", "clothing", "fashion", "textile",
        "sewing", "fabric cutting", "apparel factory", "apparel warehouse",
        "clothing distribution", "fashion logistics", "garment sorting"
    ],
    "Casinos & Gaming": [
        "casino", "gaming", "resort casino", "slot", "table games",
        "integrated resort", "tribal gaming"
    ],
    "Cruise Lines": [
        "cruise", "cruise line", "cruise ship", "vessel", "onboard"
    ],
    "Theme Parks & Entertainment": [
        "theme park", "amusement park", "roller coaster", "attractions",
        "entertainment venue", "water park", "six flags", "ski resort", "stevens pass",
        # Major operators & resorts (prefer phrases — bare "disney" hits non-park news)
        "walt disney world", "disneyland", "disney parks", "disney resort",
        "universal studios", "universal orlando", "universal hollywood", "universal beijing",
        "seaworld", "sea world", "legoland", "cedar point", "busch gardens",
        "knott's berry farm", "hersheypark", "cedar fair", "merlin entertainments",
        "madame tussauds", "safari park", "zoo exhibit", "public aquarium",
        # Venue & experience types
        "family entertainment center", "indoor amusement", "dark ride", "haunted attraction",
        "seasonal park", "fairground", "carnival ride", "observation wheel",
    ],
    "Real Estate & Facilities": [
        "facilities management", "property management", "commercial real estate",
        "building services", "janitorial", "facility services",
        "corporate office", "corporate offices", "office building", "headquarters",
        "office campus", "office tower", "corporate campus",
        # Omit bare "enterprise" — matches generic B2B / software copy unrelated to facilities.
    ],
    "Automotive Dealerships": [
        "dealership", "auto dealer", "car dealer", "automotive retail"
    ],
    "Automotive & Manufacturing": [
        "automotive", "automaker", "auto manufacturer", "car company", "vehicle manufacturer",
        "electric vehicle", " ev ", "e.v.", "oem",
        "manufacturing", "factory", "assembly", "motor group",
        "semiconductor", "cobot", "industrial automation", "hyundai motor",
        "bmw group", "teradyne", "rockwell", "omron", "stmicroelectronics",
        "humanoid robots", "deploy humanoid", "factory from", "assembly line",
        "faraday future", "faraday",
        "robot and vehicle", "robot & vehicle", "vehicle deliveries", "eai robotics",
        "nvidia drive", "autonomous driving", "adas",
    ],
    "Media & Publishing": [
        "manufacturing dive", "motley fool", "new york times", "reuters",
        "business wire", "pr newswire", "financial times", "investing.com",
        "wirecutter", "magazine", "post.", "times.", "dive."
    ],
    "Laundry & Linen Services": [
        "laundry", "linen", "commercial laundry", "industrial laundry",
        "uniform cleaning", "linen service", "laundry service", "laundromat",
        "textile cleaning", "flatwork", "wash dry fold"
    ],
    "Car Wash": [
        "car wash", "carwash", "express wash", "tunnel wash", "conveyor wash",
        "automated car wash", "car wash chain", "quick wash"
    ],
}


def should_skip_industry_reinfer_for_company_name(name: Optional[str]) -> bool:
    """
    True when `name` looks like a person, event, geography fragment, or headline — not
    an operating company. Cleanup scripts should not persist `infer_industry_from_text`
    for these rows (keyword scoring mislabels e.g. Jeff Bezos → Media, South Korea. → Manufacturing).
    """
    if not name or not str(name).strip():
        return True
    raw = str(name).strip()
    low = raw.lower()

    # Country / region standing alone
    if re.match(r"(?i)^(south|north)\s+korea\.?$", raw):
        return True

    # Tech / celebrity figures mis-scraped as company names
    for pat in (
        r"(?i)^jeff\s+bezos\b",
        r"(?i)^elon\s+musk\b",
        r"(?i)^mark\s+zuckerberg\b",
        r"(?i)^tim\s+cook\b",
        r"(?i)^satya\s+nadella\b",
        r"(?i)^sundar\s+pichai\b",
    ):
        if re.match(pat, raw):
            return True

    # Conference / trade-show / week-style headlines
    if re.search(r"(?i)\b(national|international)\s+\w+\s+week\b", raw):
        return True
    if re.search(
        r"(?i)\b(ces|gtc|mach|modex|logimat|nrf|uscap|shoptalk)\b.*\b20\d\d",
        raw,
    ):
        return True
    if re.match(r"(?i)^nvidia\s+gtc\.?$", raw):
        return True
    if re.match(r"(?i)^mach\s+20\d\d", raw):
        return True

    # Product / meme headlines
    if re.match(r"(?i)^tesla'?s\s+optimus\b", raw):
        return True

    return False


def infer_industry_from_text(text: str) -> str:
    """Infer industry from combined text (e.g. company name + all signal texts)."""
    if not (text and text.strip()):
        return "Unknown"
    text_lower = text.lower()

    # Longest key first so "faraday future" wins over "faraday" if both exist.
    for key in sorted(KNOWN_COMPANY_INDUSTRY.keys(), key=len, reverse=True):
        if key in text_lower:
            return KNOWN_COMPANY_INDUSTRY[key]

    scores: Dict[str, int] = {}
    for industry, keywords in INDUSTRY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            scores[industry] = score
    if not scores:
        return "Unknown"

    best = max(scores.values())
    tied = [ind for ind, sc in scores.items() if sc == best]

    def _tie_key(ind: str) -> Tuple[int, int]:
        try:
            pri = INDUSTRY_TIE_PRIORITY.index(ind)
        except ValueError:
            pri = len(INDUSTRY_TIE_PRIORITY)
        return (-best, pri)

    tied.sort(key=_tie_key)
    return tied[0]


def effective_industry_for_lead(
    company_name: Optional[str],
    stored_industry: Optional[str],
    signals: Sequence[object],
) -> str:
    """
    Industry for UI and share copy: infer from name + signal text; fall back to stored.
    Prefer inference when it resolves (fixes bad Hospitality labels from STR-only keywords).
    """
    parts: List[str] = [company_name or ""]
    for s in signals or []:
        parts.append(getattr(s, "signal_text", None) or "")
    parts.append(stored_industry or "")
    blob = " ".join(parts)
    inferred = infer_industry_from_text(blob)
    if inferred != "Unknown":
        return inferred
    raw = (stored_industry or "").strip()
    if raw and raw.lower() not in ("unknown", "other"):
        return raw
    return "New"
