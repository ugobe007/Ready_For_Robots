"""
Known news / trade / B2B publication names — NOT buyer companies.

Used by:
  - intelligence_news_scraper: strip RSS attributions; never create leads for outlets
  - lead_filter.is_junk: hide legacy bad rows from the API
"""
from __future__ import annotations

import re
import unicodedata
from typing import Optional

# Lowercase, collapsed whitespace — match with normalize_publication_name()
KNOWN_TRADE_PUBLICATIONS = frozenset(
    {
        # User-reported + flagship B2B
        "textile today",
        "supply chain dive",
        "world economic forum",
        "the world economic forum",
        "wef",
        "smart brief",
        "smartbrief",
        # "Dive" network + siblings
        "retail dive",
        "healthcare dive",
        "education dive",
        "waste dive",
        "utility dive",
        "construction dive",
        "banking dive",
        "marketing dive",
        "higher ed dive",
        "k-12 dive",
        "restaurant dive",
        "food dive",
        "grocery dive",
        "hotel dive",
        "hospitality dive",
        "commercial dive",
        "multifamily dive",
        "hr dive",
        "cio dive",
        # Logistics / ops trade
        "dc velocity",
        "logistics management",
        "material handling 24/7",
        "mmh daily",
        "modern materials handling",
        "transport topics",
        "freightwaves",
        "freight waves",
        "inbound logistics",
        "outbound logistics",
        "logistics viewpoint",
        "supply chain brain",
        "supplychainbrain",
        "supply chain quarterly",
        "supply chain 247",
        "supply chain 24/7",
        "scmr",
        "supply chain management review",
        # Tech / business wires (often scraped as "company")
        "techcrunch",
        "the verge",
        "axios",
        "axios pro",
        "reuters",
        "bloomberg",
        "bloomberg news",
        "cnbc",
        "forbes",
        "fortune",
        "fortune magazine",
        "newsweek",
        "the atlantic",
        "atlantic",
        "time magazine",
        "time",
        "wired",
        "the wall street journal",
        "wall street journal",
        "wsj",
        "financial times",
        "the financial times",
        "ft.com",
        "economist",
        "the economist",
        "bbc news",
        "bbc",
        "the guardian",
        "guardian",
        "associated press",
        "the associated press",
        "npr",
        "pbs",
        "usa today",
        "los angeles times",
        "the new york times",
        "new york times",
        "washington post",
        "the washington post",
        "chicago tribune",
        "boston globe",
        "the boston globe",
        "miami herald",
        "denver post",
        "houston chronicle",
        "seattle times",
        "the seattle times",
        "atlanta journal-constitution",
        "ajc",
        # Hospitality / retail trade
        "hotel news resource",
        "hotel online",
        "hospitality net",
        "hospitalitynet",
        "skift",
        "tnooz",
        "chain store age",
        "nrf",
        "national retail federation",
        "progressive grocer",
        "supermarket news",
        "convenience store news",
        "restaurant business",
        "nrn",
        "nations restaurant news",
        "nation's restaurant news",
        "qsrmagazine",
        "qsr magazine",
        # Manufacturing / industry
        "industry week",
        "industryweek",
        "manufacturing net",
        "automation world",
        "plant services",
        "food processing",
        "food engineering",
        "packaging digest",
        "packaging world",
        # Already partially covered elsewhere in codebase
        "business insider",
        "marketwatch",
        "seeking alpha",
        "the motley fool",
        "motley fool",
        "barron's",
        "barrons",
        "barrons.com",
        "fox business",
        "fox news",
        "msnbc",
        "cnn",
        "cnet",
        "zdnet",
        "venturebeat",
        "venture beat",
        "the information",
        "protocol",
        "engadget",
        "ars technica",
        "wired",
        "fast company",
        "inc.",
        "inc magazine",
        "entrepreneur",
        "harvard business review",
        "hbr",
        "mckinsey",
        "mckinsey insights",
        "deloitte insights",
        "pwc",
        "ey",
        "kpmg",
        "accenture",
        "gartner",
        "idc",
        "statista",
        "grand view research",
        "verified market research",
        # Wires / distribution (scraped as “company name”)
        "pr newswire",
        "prnewswire",
        "globe newswire",
        "globenewswire",
        "business wire",
        "businesswire",
        "cision",
        "ein presswire",
        "einpresswire",
        "accesswire",
        "newmediawire",
        # Finance / news aggregators (headline attribution, not buyers)
        "yahoo finance",
        "google news",
        "msn money",
        "benzinga",
        "investing.com",
        "marketbeat",
        "zacks",
        "zacks investment research",
        "streetinsider",
        "tipranks",
        "simply wall st",
        "simplywallst",
        "gurufocus",
        "fintel",
        "stocktwits",
        # Meat / food processing trade publications
        "national provisioner",
        "the national provisioner",
        "meat+poultry",
        "meat and poultry",
        "food processing",
        "food manufacturing magazine",
        "processing magazine",
        "dairy foods",
        "baking business",
        "candy industry",
        "snack food & wholesale bakery",
        # Hospitality / foodservice trade
        "hotel management",
        "hotels magazine",
        "lodging magazine",
        "restaurant business",
        "foodservice equipment reports",
        "nation's restaurant news",
        "qsr magazine",
        "fsrmagazine",
        # Logistics / supply chain trade
        "dc velocity",
        "material handling & logistics",
        "modern materials handling",
        "inbound logistics",
        "supply chain management review",
        "logistics management",
        "freight waves",
        "freightwaves",
        "the load star",
        "loadstar",
        "air cargo news",
        # Manufacturing / automation trade
        "manufacturing tomorrow",
        "manufacturing engineering",
        "assembly magazine",
        "automation world",
        "control engineering",
        "machine design",
        "design news",
        "industryweek",
        "industry week",
        "plant engineering",
        "plant services",
    }
)

_WS_RE = re.compile(r"\s+")


def normalize_publication_name(s: str) -> str:
    """Lowercase, strip, collapse internal whitespace, strip common unicode noise."""
    if not s:
        return ""
    t = unicodedata.normalize("NFKC", s).strip().lower()
    t = _WS_RE.sub(" ", t)
    # Strip paired quotes Google sometimes leaves in titles
    t = t.strip("\"'“”‘’")
    # Strip trailing punctuation RSS scrapers leave on names ("Modern Materials Handling.")
    t = t.rstrip(".,;:!?")
    return t


def is_known_publication_name(name: Optional[str]) -> bool:
    """
    True if this string is (almost certainly) a publisher / trade outlet, not an operating company.
    """
    if not name or not str(name).strip():
        return False
    n = normalize_publication_name(str(name))

    if n in KNOWN_TRADE_PUBLICATIONS:
        return True

    # City / regional business journals (outlet, not the subject company)
    if n.endswith(" business journal"):
        return True

    return False


def publication_matches_rss_source(candidate: str, rss_source: str) -> bool:
    """True if extracted `candidate` is the RSS <source> outlet (Google News, etc.)."""
    if not candidate or not rss_source:
        return False
    c = normalize_publication_name(candidate)
    s = normalize_publication_name(rss_source)
    if not c or not s:
        return False
    if c == s:
        return True
    # "CNN.com" vs "CNN", "Supply Chain Dive" vs "SupplyChainDive"
    c_compact = re.sub(r"[^\w]+", "", c)
    s_compact = re.sub(r"[^\w]+", "", s)
    if c_compact == s_compact and len(c_compact) >= 4:
        return True
    if len(s) >= 6 and (c.startswith(s) or s.startswith(c)):
        return True
    if len(c) >= 6 and (s.startswith(c) or c.startswith(s)):
        return True
    return False


_ATTRIB_TAIL = re.compile(r"\s*([-–—|])\s*([^\-–—|]+?)\s*$")


def strip_trailing_news_attribution(title: str, rss_source: str = "") -> str:
    """
    Remove trailing " - Publisher", " | Publisher" from RSS/aggregator titles when the tail
    is a known outlet or matches the feed's <source>.
    """
    t = (title or "").strip()
    if not t:
        return t
    guard = 0
    while guard < 8:
        guard += 1
        m = _ATTRIB_TAIL.search(t)
        if not m:
            break
        tail = m.group(2).strip()
        if not tail:
            break
        if is_known_publication_name(tail) or publication_matches_rss_source(tail, rss_source):
            t = t[: m.start()].strip()
            continue
        break
    return t
