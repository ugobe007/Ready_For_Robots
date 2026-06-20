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
    "microsoft": "Datacenters",
    "corning": "Datacenters",
    "softbank": "Datacenters",
    # Casinos / hospitality (often mislabeled Healthcare from F&B/housekeeping signals)
    "caesars entertainment": "Casinos & Gaming",
    "boyd gaming": "Casinos & Gaming",
    "las vegas sands": "Hospitality",
    "wynn resorts": "Hospitality",
    "mgm resorts": "Casinos & Gaming",
    "penn entertainment": "Hospitality",
    "hard rock international": "Hospitality",
    "wyndham hotels": "Hospitality",
    "wyndham hotels & resorts": "Hospitality",
    "accor hotels": "Hospitality",
    "accor": "Hospitality",
    "marina bay sands": "Hospitality",
    "choice hotels": "Hospitality",
    "abm industries": "Real Estate & Facilities",
    "united airlines": "Airports & Aviation",
    "carnival corporation": "Cruise Lines",
    "norwegian cruise line": "Cruise Lines",
    # Food service / airline catering
    "gate gourmet": "Food Service",
    "lsg sky chefs": "Food Service",
    "hmshost": "Food Service",
    "compass group": "Food Service",
    "aramark": "Food Service",
    "sodexo": "Food Service",
    "yum! brands": "Food Service",
    "yum brands": "Food Service",
    "cracker barrel": "Food Service",
    "red lobster": "Food Service",
    "mcdonald's": "Food Service",
    "mcdonalds": "Food Service",
    "starbucks": "Food Service",
    "shake shack": "Food Service",
    "white castle": "Food Service",
    "chipotle": "Food Service",
    "sweetgreen": "Food Service",
    "chili's": "Food Service",
    "chilis": "Food Service",
    "brinker international": "Food Service",
    # Pharma / medtech
    "novartis": "Medical Technology",
    "becton dickinson": "Medical Technology",
    "becton, dickinson and company": "Medical Technology",
    # Logistics / parcel
    "ups": "Logistics",
    "united parcel service": "Logistics",
    "fedex": "Logistics",
    # Food / ag processing
    "aboitiz foods": "Food Processing & Manufacturing",
    "tyson foods": "Food Processing & Manufacturing",
    "cargill": "Food Processing & Manufacturing",
    # Contract / industrial manufacturing
    "prince manufacturing": "Contract Manufacturing",
    "foxconn": "Automotive & Manufacturing",
    # Healthcare / food buyers often stuck Unknown after RSS-heavy scrapes
    "hancock health": "Healthcare",
    "rwjbarnabas health": "Healthcare",
    "heineken": "Food Processing & Manufacturing",
    "denny's": "Food Service",
    "dennys": "Food Service",
    "associated wholesale grocers": "Retail",
    "rebellyous foods": "Food Processing & Manufacturing",
    "smashburger": "Food Service",
    "bazooka candy": "CPG & Consumer Goods",
    "ring pop maker bazooka": "CPG & Consumer Goods",
    "topps": "CPG & Consumer Goods",
    "shell": "Energy & Utilities",
    "volvo": "Automotive & Manufacturing",
    "makemytrip": "Airports & Aviation",
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
    # Airlines / aviation (signal text often mentions factory/manufacturing/robot deployment)
    "japan airlines": "Airports & Aviation",
    "all nippon airways": "Airports & Aviation",
    "ana holdings": "Airports & Aviation",
    "united airlines": "Airports & Aviation",
    "american airlines": "Airports & Aviation",
    "delta air lines": "Airports & Aviation",
    "southwest airlines": "Airports & Aviation",
    "jetblue airways": "Airports & Aviation",
    "british airways": "Airports & Aviation",
    "lufthansa": "Airports & Aviation",
    "emirates airline": "Airports & Aviation",
    "qantas airways": "Airports & Aviation",
    "singapore airlines": "Airports & Aviation",
    "cathay pacific": "Airports & Aviation",
    "air france": "Airports & Aviation",
    "klm royal dutch airlines": "Airports & Aviation",
    # Big-box / home improvement retail (signal noise often cites unrelated vendors)
    "home depot": "Retail",
    "the home depot": "Retail",
    "lowe's": "Retail",
    "lowes": "Retail",
    "walmart": "Retail",
    "costco": "Retail",
    "costco wholesale": "Retail",
    "novartis": "Medical Technology",
    "target corporation": "Retail",
}

# Company name looks like a passenger airline (not an automaker).
_AIRLINE_NAME_RE = re.compile(
    r"(?i)\b(airlines?|airways|air\s+lines?)\b"
)

# When two industries have the same raw keyword score, pick the higher-priority one first.
INDUSTRY_TIE_PRIORITY: Tuple[str, ...] = (
    "Automotive & Manufacturing",
    "Medical Technology",
    "Pharmaceuticals & Life Sciences",
    "Healthcare",
    "Defense",
    "Oil & Gas & Petrochemical",
    "Energy & Utilities",
    "Ports & Maritime",
    "Rail & Transit",
    "Logistics",
    "Construction & Building",
    "Mining & Extraction",
    "Agriculture & Agribusiness",
    "Food Processing & Manufacturing",
    "CPG & Consumer Goods",
    "Contract Manufacturing",
    "Manufacturing",
    "Food & Beverage",
    "Food Service",
    "Retail",
    "Software & IT",
    "Datacenters",
    "Telecom",
    "Financial Services",
    "Airports & Aviation",
    "Hospitality",
    "Education",
    "Government & Public Sector",
    "Real Estate & Facilities",
    "Waste & Environmental",
    "Sports & Stadiums",
    "Apparel & Textiles",
    "Automotive Dealerships",
    "Casinos & Gaming",
    "Cruise Lines",
    "Theme Parks & Entertainment",
    "Car Wash",
    "Laundry & Linen Services",
    "Media & Publishing",
)


INDUSTRY_KEYWORDS: Dict[str, list] = {
    "Logistics": [
        "warehouse", "logistics", "fulfillment", "distribution", "supply chain",
        "3pl", "third party logistics", "fulfillment center", "fulfillment centre",
        "cold storage", "freight", "shipping",
        "warehouse automation", "warehouse logistics", "intra logistics", "intralogistics",
        "micro logistics", "light logistics", "package handling", "package automation",
        "parcel sorting", "sortation", "goods to person", "goods-to-person", "cross dock",
        "grocery logistics", "grocery distribution", "grocery fulfillment",
        "trucking", "trucking company", "fleet operator", "fleet management",
        "last mile delivery", "courier", "parcel carrier", "ltl carrier", "ftl carrier",
        "cold chain", "cold chain logistics", "refrigerated transport",
        # Omit bare "delivery" / "fleet" alone — too generic in headlines.
    ],
    # Do not use generic "property management" — STR/Airbnb robot deployments often mention it
    # and mislabel automotive OEMs (e.g. Faraday Future delivering robots to vacation rentals).
    "Hospitality": [
        "hotel", "resort", "hospitality", "lodging", "motel", "inn",
        "housekeeping", "guest services",
        "hospitality automation", "hotel automation", "front desk automation",
        "room service automation", "house cleaning automation", "housekeeping automation",
        "concierge robot", "check-in automation", "linen delivery",
    ],
    "Food Service": [
        "restaurant", "restaurants", "food service", "foodservice", "kitchen", "dining", "qsr",
        "fast food", "fast casual", "cafe", "chain restaurant", "franchise",
        "food prep", "food preparation", "food delivery", "food robot", "food robotics",
        "quick serve", "quick serve automation", "qsr automation",
        "kitchen robot", "kitchen automation", "server robot", "serving robot",
        "ghost kitchen", "dark kitchen", "commercial kitchen", "back of house",
        "cafeteria", "catering", "dining room", "table service", "drive-thru",
        "drive through", "mcdonald", "starbucks", "chipotle", "yum brands",
        "compass group", "aramark", "sodexo", "darden", "dine brands",
        "truck stop", "truckstop", "travel center", "travel plaza",
        "steakhouse", "steak house", "steak chain", "pizzeria", "pizza chain",
        "pizza restaurant", "bar and grill", "bar & grill", "brewpub", "tavern",
        "buffet restaurant", "family dining", "full service restaurant",
    ],
    "Healthcare": [
        "hospital", "healthcare", "health system", "clinic", "patient",
        "senior living", "senior care", "nursing home", "assisted living", "medical center",
        "skilled nursing", "memory care", "long-term care", "ltc",
        "elder care", "home health", "home care", "palliative care",
        "cedarhurst", "lifespire", "brookdale", "sunrise senior",
        "brightspring", "encompass health",
        "hospital automation", "healthcare automation", "hospital resupply",
        "hospital logistics", "outpatient", "out patient", "emergency room",
        "icu", "intensive care", "rehabilitation", "rehab",
    ],
    "Medical Technology": [
        "laboratory", "lab automation", "clinical lab", "diagnostics lab",
        "pharmacy", "hospital pharmacy", "surgical robot", "surgical suite",
        "patient care", "specimen processing", "pathology", "iv compounding",
        "medication dispensing", "robotic surgery", "da vinci", "telepresence",
        "telehealth", "phlebotomy", "surgical", "surgery robot", "korea biomed",
        "vitestro", "roen surgical", "surgerii",
        "lab delivery", "pharmacy automation", "surgery center", "surgery automation",
        "biomedical", "radiotherapy", "bulk medication", "medication picking",
    ],
    "Defense": [
        "defense", "defence", "military", "dod", "department of defense",
        "army", "navy", "air force", "warfighter", "national defense",
        "defense automation", "defense logistics", "military logistics",
        "defense robotics", "autonomous logistics", "ugv", "unmanned ground",
    ],
    "Energy & Utilities": [
        "energy storage", "battery storage", "bess", "grid scale storage",
        "grid automation", "power grid", "smart grid", "substation",
        "utility", "utilities", "energy automation", "transmission automation",
        "electric utility", "power utility", "water utility", "wastewater utility",
    ],
    "Oil & Gas & Petrochemical": [
        "oil and gas", "oil & gas", "petrochemical", "petrochemical plant",
        "refinery", "oil refinery", "natural gas", "lng terminal", "lng plant",
        "pipeline operator", "midstream", "upstream", "downstream", "drilling",
        "offshore platform", "oilfield", "gas processing",
    ],
    "Food Processing & Manufacturing": [
        "food processing", "food manufacturing", "food processing automation",
        "meat processing",
        "bakery", "produce processing", "food packaging", "food safety",
        "food sorting", "food preparation", "cooking automation",
        "robotic chef", "robotic kitchen",
        "food plant", "food factory", "food production", "poultry processing",
        "seafood processing", "dairy processing", "cheese plant", "meat packing",
        "cheese factory", "dairy processor", "dairy processors", "meat packer",
        "poultry plant", "meat processing plant",
        "beverage manufacturing", "bottling plant", "canning", "brewing",
        "snack food", "baked goods", "confectionery", "cereal manufacturing",
        "farm automation", "agriculture automation", "agtech", "ag tech",
        "crop processing", "harvest automation", "greenhouse automation",
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
        "end of line automation", "pack out", "pack in", "pack-out", "pack-in",
        "package handling", "package automation", "packaging automation",
    ],
    "Contract Manufacturing": [
        "contract manufacturer", "contract manufacturing", "contract packager",
        "contract packaging", "cmo", "cdmo", "toll manufacturer",
        "toll processing", "toll packaging", "third party manufacturing",
        "white label", "private label manufacturer", "oem manufacturer",
        "custom manufacturer", "job shop", "make to order",
        "co-manufacturer", "flexible manufacturing", "small batch",
        "multi-sku", "rapid changeover", "high mix low volume",
        "system integrator", "robotics integrator", "automation integrator",
        "integration partner", "robotics integration services",
    ],
    "Datacenters": [
        "datacenter", "data center", "hyperscale", "cloud infrastructure",
        "colocation", "server farm", "datacenter operations", "datacenter maintenance",
        "data center automation", "datacenter automation", "datacenter robot",
        # Omit bare "server" — substring-matches "food server", unrelated IT mentions.
    ],
    "Airports & Aviation": [
        "airport", "terminal", "aviation", "baggage handling", "boarding gate",
        "airport operations", "airport security", "airport shuttle",
        "airlines", "airline",
        "airport automation", "airport cleaning", "airport resupply",
        "airport service", "food court", "wheelchair", "tsa", "baggage",
        # Omit generic "metro", "transit", "transportation" — label city-mobility and unrelated articles.
    ],
    "Retail": [
        "retail", "shopping", "e-commerce", "grocery", "supermarket",
        "shelf scanning", "inventory robot", "click-and-collect", "micro-fulfillment",
        "retail fulfillment", "retail automation", "cashier", "checkout",
        "brick and mortar", "big box",
        "grocery pick and pack", "grocery fulfillment automation", "food picking",
        "order picking", "automated picking", "dark store",
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
        "janitorial automation", "commercial cleaning automation", "cleaning robot",
        "floor scrubber", "autonomous cleaning", "building automation",
        "building maintenance automation", "landscape automation", "grounds maintenance",
        "mowing robot", "facilities automation",
        # Omit bare "enterprise" — matches generic B2B / software copy unrelated to facilities.
    ],
    "Manufacturing": [
        "discrete manufacturing", "production plant", "manufacturing plant",
        "industrial plant", "production facility", "fabrication plant",
        "machine shop", "metal fabrication", "sheet metal", "injection molding",
        "plastics manufacturing", "foundry", "die casting", "stampings",
        "cnc machining", "precision machining", "tool and die",
        "production automation", "factory automation", "plant automation",
        # Omit bare "manufacturing", "factory", "assembly" — false positives in hospitality/CPG copy.
    ],
    "Food & Beverage": [
        "food and beverage", "food & beverage", "f&b company", "beverage company",
        "brewery", "brewing company", "distillery", "winery", "viticulture",
        "soft drink", "beverage bottling", "spirits company", "wine producer",
        "non-alcoholic beverage", "drink manufacturer",
    ],
    "Ports & Maritime": [
        "port of", "seaport", "container port", "container terminal",
        "maritime terminal", "shipping terminal", "port authority", "harbor",
        "stevedoring", "maritime logistics", "shipping line", "container ship",
        "port automation", "terminal automation", "crane automation",
        # Omit bare "port" — matches "airport", "support", "export".
    ],
    "Rail & Transit": [
        "railroad", "railway", "freight rail", "passenger rail", "commuter rail",
        "light rail", "metro rail", "subway", "transit agency", "transit authority",
        "rail yard", "intermodal rail", "rail automation", "train maintenance",
    ],
    "Construction & Building": [
        "general contractor", "construction company", "construction firm",
        "commercial construction", "infrastructure contractor", "builder",
        "construction site", "building contractor", "civil contractor",
        "construction automation", "construction robotics", "jobsite automation",
    ],
    "Mining & Extraction": [
        "mining company", "mining operation", "open pit mine", "underground mine",
        "quarry", "mineral extraction", "mining automation", "mine automation",
        "autonomous haul", "autonomous hauling", "ore processing",
    ],
    "Pharmaceuticals & Life Sciences": [
        "pharmaceutical", "pharma company", "biotech", "biotechnology",
        "life sciences", "drug manufacturer", "biologics", "biopharma",
        "pharmaceutical manufacturing", "api manufacturing", "fill finish",
        "clinical manufacturing", "cell therapy", "gene therapy",
        # cdmo overlaps Contract Manufacturing — prefer pharma-specific phrases here.
        "pharma cdmo", "biologics cdmo", "drug discovery",
    ],
    "Agriculture & Agribusiness": [
        "agribusiness", "agricultural cooperative", "crop production", "grower",
        "farm operator", "farming operation", "vertical farm", "vertical farming",
        "greenhouse grower", "hydroponic", "livestock operation", "dairy farm",
        "poultry farm", "orchard", "vineyard operation", "grain elevator",
    ],
    "Government & Public Sector": [
        "municipal", "city of", "county of", "state government", "federal agency",
        "public sector", "government agency", "correctional facility", "prison",
        "detention center", "public works", "municipal services",
    ],
    "Education": [
        "university", "college campus", "school district", "k-12", "higher education",
        "community college", "campus facilities", "education institution",
    ],
    "Financial Services": [
        "bank", "banking", "insurance company", "insurer", "financial services",
        "asset management", "investment firm", "credit union", "mortgage lender",
    ],
    "Telecom": [
        "telecom", "telecommunications", "wireless carrier", "mobile network",
        "broadband provider", "fiber network", "telco", "communications provider",
    ],
    "Software & IT": [
        "software company", "saas", "software as a service", "cloud software",
        "enterprise software", "erp vendor", "cloud erp", "business software",
        "it services", "managed services provider", "systems integrator software",
        # Omit bare "software", "cloud", "erp" — too generic in automation headlines.
    ],
    "Waste & Environmental": [
        "waste management", "recycling facility", "material recovery", "landfill",
        "environmental services", "sanitation", "waste hauling", "mrf facility",
    ],
    "Sports & Stadiums": [
        "stadium", "arena", "ballpark", "sports venue", "sports complex",
        "athletic facility", "convention center", "event venue",
    ],
    "Automotive Dealerships": [
        "dealership", "auto dealer", "car dealer", "automotive retail",
        "auto dealership automation", "dealership automation", "car dealership robot",
    ],
    "Automotive & Manufacturing": [
        "automotive", "automaker", "auto manufacturer", "car company", "vehicle manufacturer",
        "vehicle manufacturing", "automotive plant", "auto plant",
        "electric vehicle", " ev ", "e.v.", "oem",
        # Omit bare "manufacturing", "factory", "assembly" — they appear in hospitality supply-chain
        # and CPG copy ("central kitchen manufacturing") and falsely beat Hospitality.
        "motor group",
        "semiconductor", "cobot", "industrial automation", "hyundai motor",
        "bmw group", "teradyne", "rockwell", "omron", "stmicroelectronics",
        "humanoid robots", "deploy humanoid", "factory from", "assembly line",
        "faraday future", "faraday",
        "robot and vehicle", "robot & vehicle", "vehicle deliveries", "eai robotics",
        "nvidia drive", "autonomous driving", "adas",
        "automotive automation", "parts assembly", "parts logistics",
        "parts resupply", "service automation", "service repair", "service logistics",
    ],
    "Media & Publishing": [
        "manufacturing dive", "motley fool", "new york times", "reuters",
        "business wire", "pr newswire", "financial times", "investing.com",
        "wirecutter", "magazine", "post.", "times.", "dive."
    ],
    "Laundry & Linen Services": [
        "laundry", "linen", "commercial laundry", "industrial laundry",
        "uniform cleaning", "linen service", "laundry service", "laundromat",
        "textile cleaning", "flatwork", "wash dry fold",
        "commercial laundry automation", "laundry automation", "linen automation",
    ],
    "Car Wash": [
        "car wash", "carwash", "express wash", "tunnel wash", "conveyor wash",
        "automated car wash", "car wash chain", "quick wash",
        "car wash automation", "carwash robot",
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



def _keyword_in_text(kw: str, text_lower: str) -> bool:
    from app.services.industry_sector_ontology import term_in_text

    return term_in_text(kw, text_lower)


def _normalize_company_name_for_lookup(name: str) -> str:
    """Normalize unicode punctuation so KNOWN_COMPANY_INDUSTRY keys match scraped names."""
    n = name.strip().lower()
    return (
        n.replace("\u2019", "'")
        .replace("\u2018", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
    )


def known_industry_for_company_name(company_name: Optional[str]) -> Optional[str]:
    """Map company name to curated industry — never scan unrelated signal text."""
    low = _normalize_company_name_for_lookup(company_name or "")
    if not low:
        return None
    for key in sorted(KNOWN_COMPANY_INDUSTRY.keys(), key=len, reverse=True):
        if key in low:
            return KNOWN_COMPANY_INDUSTRY[key]
    return None


def infer_industry_scores(text: str, *, company_name: Optional[str] = None) -> Dict[str, int]:
    """
    Keyword hit counts per industry label (used by infer + disambiguation).

    When ``company_name`` is set, KNOWN_COMPANY_INDUSTRY applies to the name only
    (prevents e.g. SoftBank mentions in Home Depot headlines → Datacenters).
    """
    if not (text and text.strip()):
        return {}
    text_lower = text.lower()
    if company_name:
        known = known_industry_for_company_name(company_name)
        if known:
            return {known: 10**6}
    else:
        for key in sorted(KNOWN_COMPANY_INDUSTRY.keys(), key=len, reverse=True):
            if key in text_lower:
                ind = KNOWN_COMPANY_INDUSTRY[key]
                return {ind: 10**6}
    scores: Dict[str, int] = {}
    for industry, keywords in INDUSTRY_KEYWORDS.items():
        score = sum(1 for kw in keywords if _keyword_in_text(kw, text_lower))
        if score > 0:
            scores[industry] = score
    try:
        from app.services.industry_sector_ontology import infer_industries_from_subject_automation

        for industry, pts in infer_industries_from_subject_automation(text).items():
            scores[industry] = scores.get(industry, 0) + pts
    except Exception:
        pass
    return scores


def _pick_industry_from_scores(scores: Dict[str, int]) -> str:
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


def infer_industry_from_text(text: str) -> str:
    """Infer industry from combined text (e.g. company name + all signal texts)."""
    scores = infer_industry_scores(text)
    if not scores:
        return "Unknown"
    return _pick_industry_from_scores(scores)


def _keyword_hits(text_lower: str, industry: str) -> int:
    kws = INDUSTRY_KEYWORDS.get(industry, [])
    return sum(1 for kw in kws if kw in text_lower)


def _name_suggests_airline(name: str) -> bool:
    low = (name or "").strip().lower()
    if not low:
        return False
    return bool(_AIRLINE_NAME_RE.search(low))


def _stored_suggests_aviation(stored: str) -> bool:
    low = (stored or "").lower()
    if not low.strip():
        return False
    return any(
        tok in low
        for tok in (
            "airport",
            "aviation",
            "airline",
            "airlines",
        )
    )


def _stored_suggests_hospitality(stored: str) -> bool:
    low = (stored or "").lower()
    if not low.strip():
        return False
    return any(
        tok in low
        for tok in (
            "hospitality",
            "hotel",
            "hotels",
            "lodging",
            "resort",
            "travel",
            "leisure",
            "accommodation",
            "guest",
        )
    )


def effective_industry_for_lead(
    company_name: Optional[str],
    stored_industry: Optional[str],
    signals: Sequence[object],
) -> str:
    """
    Industry for UI and share copy: infer from name + signal text; fall back to stored.

    Disambiguation: generic industrial vocabulary in headlines must not override clear
    hospitality/hotel or airline context (fixes mislabels like Marriott or Japan Airlines → Automotive).
    Still prefers OEM/automotive inference when signal copy is vehicle-centric (Faraday, etc.).
    """
    name = (company_name or "").strip()
    from app.services.signal_text_normalize import strip_signal_html

    signal_blob = " ".join(
        strip_signal_html(getattr(s, "signal_text", None) or "") for s in signals or []
    )
    stored = (stored_industry or "").strip()
    blob = " ".join([name, signal_blob, stored])

    known = known_industry_for_company_name(name)
    if known:
        return known

    scores = infer_industry_scores(blob, company_name=name)
    inferred = _pick_industry_from_scores(scores)

    tl_all = blob.lower()
    tl_sig = signal_blob.lower()
    tl_name = name.lower()

    hosp_hits_all = _keyword_hits(tl_all, "Hospitality")
    hosp_hits_sig = _keyword_hits(tl_sig, "Hospitality")
    food_hits_all = _keyword_hits(tl_all, "Food Service")
    aviation_hits_all = _keyword_hits(tl_all, "Airports & Aviation")
    aviation_hits_sig = _keyword_hits(tl_sig, "Airports & Aviation")
    airline_name = _name_suggests_airline(name)

    hotel_brand_tokens = (
        "marriott", "hilton", "hyatt", "ihg", "accor", "wyndham", "choice hotels",
        "holiday inn", "sheraton", "westin", "omni hotels", "four seasons", "ritz-carlton",
        "rosewood", "langham", "peninsula", "w hotels", "aloft", "courtyard", "fairfield inn",
        "hampton inn", "doubletree", "embassy suites", "residence inn", "springhill suites",
    )
    brand_context = any(tok in tl_name for tok in hotel_brand_tokens)

    # Strong hospitality evidence should not lose to Automotive & Manufacturing tie priority.
    if inferred == "Automotive & Manufacturing":
        hosp_sc = scores.get("Hospitality", 0)
        auto_sc = scores.get("Automotive & Manufacturing", 0)
        if brand_context or hosp_hits_all >= 2 or hosp_hits_sig >= 2:
            inferred = "Hospitality"
        elif _stored_suggests_hospitality(stored) and hosp_hits_sig >= 1 and hosp_sc >= 1:
            inferred = "Hospitality"
        elif hosp_sc >= 2 and hosp_sc + 1 >= auto_sc:
            inferred = "Hospitality"
        elif airline_name or aviation_hits_sig >= 2 or (
            _stored_suggests_aviation(stored) and aviation_hits_sig >= 1
        ):
            inferred = "Airports & Aviation"

    # Food-forward venues vs industrial tie
    if inferred == "Automotive & Manufacturing" and food_hits_all >= 2 and hosp_hits_all < 2:
        fs = scores.get("Food Service", 0)
        if fs >= scores.get("Automotive & Manufacturing", 0):
            inferred = "Food Service"

    if inferred != "Unknown":
        return inferred
    raw = (stored_industry or "").strip()
    if raw and raw.lower() not in ("unknown", "other"):
        return raw
    return "New"
