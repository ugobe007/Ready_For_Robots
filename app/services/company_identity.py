"""Company identity: is this string a company, and which company is it?

Two jobs, used at ingest (scrapers) and at scoring (buyer ranking):

1. ``junk_name_reason(name)`` — headline fragments, place names, encoded strings
   and empty names are never companies. Checked before any INSERT.
2. ``canonical_company_key(name)`` / ``find_existing_company(db, name, domain)`` —
   "Target", "Target Corp.", "TARGET CORPORATION" and "Target Stores" are one
   company. Scrapers reuse the existing row instead of inserting a duplicate;
   ranking pools evidence across rows that already exist.

Conservative on purpose: only legal/corporate suffixes are stripped, so
"JW Marriott Las Vegas" (a property) and "Marriott International" stay distinct,
and "Bank of America" never collapses to "bank".
"""
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable, Optional

# ─── Junk names ──────────────────────────────────────────────────────────────

_COUNTRIES_REGIONS = frozenset({
    "usa", "us", "uk", "europe", "asia", "africa", "latin america", "middle east", "north america",
    "south america", "southeast asia", "silicon valley", "bay area", "midwest", "gulf coast",
})
# Bare place names that are also well-known buyer brands (Providence health system, …).
_PLACE_NAME_BRANDS = frozenset({
    "providence", "columbia", "toyota", "burlington", "hershey", "kohler", "corning", "dell", "nordstrom",
    "marion", "aurora", "mobile", "orange", "victoria", "florence", "sterling", "lincoln", "hudson",
})

_HEADLINE_RE = re.compile(
    r"^(?:how|why|what|when|where|who|which|is|are|can|will|this|these|top|best|inside|watch|video|report)\b"
    r"|\b(?:are|is|was|were|will|says?|said|could|would|announces?|reveals?|launch(?:es)?|plans?)\b.*\b\w+\b"
    r"|\bto (?:open|build|deploy|add|launch|use|test|buy|invest|expand|hire|cut|replace|roll)\b",
    re.I,
)
# Long official names are fine: "Port Authority of New York and New Jersey".
_ORG_NAME_RE = re.compile(
    r"\b(?:authority|department|district|county|city of|town of|state of|university|college|hospital|"
    r"health ?(?:system|plan)|medical center|school|agency|commission|administration|bureau|board of|"
    r"international airport|airport authority|port of|council)\b",
    re.I,
)
_ENCODED_RE = re.compile(r"^[A-Za-z0-9+/=_-]{20,}$")


@lru_cache(maxsize=1)
def _place_names() -> frozenset[str]:
    """US cities ≥15k, world cities ≥100k, US states, countries (app/data/place_names.txt)."""
    path = Path(__file__).resolve().parents[1] / "data" / "place_names.txt"
    try:
        with open(path, encoding="utf-8") as fh:
            return frozenset(line.strip() for line in fh if line.strip() and not line.startswith("#"))
    except OSError:
        return frozenset()


def is_place_name(name: str) -> bool:
    """Exact match only: 'Hoboken' is a place; 'City of Hoboken' / 'Hoboken Hospital' are not."""
    low = re.sub(r",\s*[a-z]{2}$", "", (name or "").lower().strip(" .,")).strip()  # 'hoboken, nj' → 'hoboken'
    if not low or low in _PLACE_NAME_BRANDS:
        return False
    if low not in _COUNTRIES_REGIONS and low not in _place_names():
        return False
    try:
        from app.services.known_brands import is_allowlisted_company_name

        return not is_allowlisted_company_name(low)
    except Exception:
        return True


# Publications: "<anything> News / Times / Post / Journal …" is an outlet, not a buyer.
_OUTLET_RE = re.compile(
    r"\s(?:news|times|post|journal|herald|tribune|gazette|chronicle|daily|magazine|weekly|digest|insider|today|"
    r"review|register|observer|bulletin|dispatch|examiner|sentinel|telegraph|newswire|wire|press|reporter|"
    r"monthly|quarterly|blog|podcast|newsletter)$",
    re.I,
)
# Lowercase words allowed inside a real company name ("Bank of America", "Holiday Inn by Wyndham").
_NAME_CONNECTORS = frozenset({
    "of", "and", "the", "for", "at", "on", "in", "by", "de", "la", "le", "du", "des", "del", "da", "di", "van",
    "von", "der", "den", "y", "e", "et", "&", "a", "an", "to", "n", "s", "x", "plus", "co", "inc", "llc", "ltd",
})
# Phrases that are a sector or a topic, never a company.
_TOPIC_NAMES = frozenset({
    "health care", "healthcare", "home care", "senior care", "patient care", "child care", "food service",
    "foodservice", "hospitality", "retail", "logistics", "manufacturing", "warehousing", "supply chain",
    "coming soon", "now open", "grand opening", "press release", "breaking news", "case study", "white paper",
    "the future", "future of work", "artificial intelligence", "machine learning", "robotics", "automation",
    "smart city", "smart home", "smart factory", "industry", "technology", "innovation", "sustainability",
    "labor shortage", "workforce", "customer service", "public safety", "real estate", "higher education",
})
# Headline/topic endings: "Patient Testing Set", "Innovative Two-Step Treatment".
_TOPIC_TAIL_RE = re.compile(
    r"\s(?:set|treatment|treatments|soon|step|steps|approach|method|methods|program|initiative|study|"
    r"trial|trials|update|updates|overview|guide|tips|ideas|trends|outlook|strategy|strategies|breakthrough|"
    r"milestone|launch|debut|rollout|announcement|partnership|deal|opportunity|opportunities|challenge|"
    r"challenges|solution|revolution|era|age|wave|boom|surge|shift|push|race|crisis|shortage|gap)$",
    re.I,
)
_LEGAL_TAIL_RE = re.compile(r"\b(?:inc|llc|ltd|corp|corporation|co|company|plc|lp|llp|gmbh|group|holdings)\.?$", re.I)


def _phrase_reason(n: str) -> Optional[str]:
    """Topic phrases, sentence fragments and outlets that slip past headline checks."""
    low = n.lower().strip(" .,")
    if low in _TOPIC_NAMES:
        return "topic phrase, not a company"
    words = n.split()
    if len(words) < 2 or _LEGAL_TAIL_RE.search(n):
        return None
    if _OUTLET_RE.search(n):
        return "news outlet, not a buyer"
    # Sentence case: a lowercase word that isn't a connector ("Rewiring the future").
    # Only for names written in Title Case — all-lowercase rows ("best western hotels") are just unformatted.
    title_cased = words[0][:1].isupper()
    for w in (words[1:] if title_cased else []):
        core = re.sub(r"[^\w&]", "", w)
        if core and core[0].islower() and core.lower() not in _NAME_CONNECTORS and not core.isdigit():
            return "sentence fragment, not a company"
    if _TOPIC_TAIL_RE.search(n) and len(words) <= 5:
        return "topic phrase, not a company"
    return None


def junk_name_reason(name: Optional[str]) -> Optional[str]:
    """Why this string is not a company name (headline, place, encoded junk), or None."""
    n = (name or "").strip()
    if len(n) < 2:
        return "empty name"
    try:
        from app.services.known_brands import is_allowlisted_company_name

        if is_allowlisted_company_name(n):
            return None
    except Exception:
        pass
    if _ENCODED_RE.match(n) and (
        any(c.isdigit() for c in n) or (n != n.lower() and n != n.upper() and len(n) >= 24)
    ):
        return "encoded string, not a company"
    if is_place_name(n):
        return "place name, not a company"
    words = n.split()
    long_name = len(words) >= 6 and not _ORG_NAME_RE.search(n)
    if long_name or (len(words) >= 3 and _HEADLINE_RE.search(n)):
        return "headline fragment, not a company"
    if n.endswith(("?", "!")) or '"' in n or "|" in n or "“" in n or "”" in n:
        return "headline fragment, not a company"
    return _phrase_reason(n)


# ─── Canonical identity ──────────────────────────────────────────────────────

# Trailing tokens that never distinguish one company from another.
_SUFFIX_TOKENS = frozenset({
    "inc", "incorporated", "corp", "corporation", "co", "company", "companies", "llc", "l l c", "ltd", "limited",
    "plc", "lp", "llp", "pllc", "gmbh", "ag", "sa", "nv", "bv", "pty", "pte", "kk",
    "group", "holdings", "holding", "enterprises", "international", "intl", "worldwide", "global",
    "brands", "stores", "store", "usa", "us", "na", "n a",
})
# Trailing industry descriptors: "Kenco Logistics" is Kenco. Used only to attach a
# row to a company that already exists under the bare name (see group_companies).
_DESCRIPTOR_TOKENS = frozenset({
    "logistics", "foods", "food", "restaurants", "restaurant", "resorts", "hotels", "hospitality", "airlines",
    "health", "healthcare", "health system", "systems", "solutions", "services", "supply chain", "distribution",
    "industries", "manufacturing", "retail", "grocery", "markets", "supermarkets", "entertainment", "gaming",
    "transportation", "freight", "trucking", "warehousing", "fulfillment", "technologies", "technology",
})
# A key that is only one of these is too generic to merge on.
_GENERIC_KEYS = frozenset({
    "american", "national", "united", "general", "first", "global", "the", "new", "best", "smart", "city",
    "county", "state", "hospital", "university", "airport", "restaurant", "hotel", "logistics", "foods",
    "premier", "pacific", "atlantic", "southern", "northern", "western", "eastern", "central", "metro",
    "royal", "golden", "summit", "pinnacle", "apex", "elite", "prime", "star", "eagle", "phoenix",
})
# Domains that are not a company's own site.
_SHARED_DOMAINS = frozenset({
    "linkedin.com", "indeed.com", "google.com", "facebook.com", "twitter.com", "x.com", "youtube.com",
    "wikipedia.org", "glassdoor.com", "ziprecruiter.com", "simplyhired.com", "bloomberg.com", "reuters.com",
    "prnewswire.com", "businesswire.com", "globenewswire.com", "crunchbase.com", "yahoo.com", "zoominfo.com",
    "myworkdayjobs.com", "greenhouse.io", "lever.co", "ashbyhq.com", "smartrecruiters.com", "news.google.com",
})


def canonical_company_key(name: Optional[str]) -> str:
    """'Target Corporation' → 'target'; 'The Kroger Co.' → 'kroger'; 'AT&T Inc.' → 'at and t'."""
    s = (name or "").lower()
    s = re.sub(r"\(.*?\)", " ", s)                  # drop parentheticals
    s = re.sub(r"\.com\b", " ", s)
    s = s.replace("&", " and ").replace("+", " and ")
    s = re.sub(r"[^\w\s]", " ", s)                   # punctuation → space
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"^the ", "", s)
    toks = s.split()
    while len(toks) > 1:
        if toks[-1] in _SUFFIX_TOKENS:
            toks.pop()
        elif len(toks) > 2 and " ".join(toks[-2:]) in _SUFFIX_TOKENS:
            toks = toks[:-2]
        else:
            break
    # Trailing "and" left over from "X & Co." / "X and Company".
    while len(toks) > 1 and toks[-1] == "and":
        toks.pop()
    return "".join(toks)   # spaces dropped: 'wal mart' == 'walmart', 'h e b' == 'heb'


def _words(name: Optional[str]) -> list[str]:
    s = (name or "").lower()
    s = re.sub(r"\(.*?\)", " ", s).replace("&", " and ")
    return re.sub(r"[^\w\s]", " ", s).split()


def base_company_key(name: Optional[str]) -> Optional[str]:
    """'Kenco Logistics' → 'kenco' (descriptor dropped); None when nothing to drop."""
    toks = _words(name)
    if toks and toks[0] == "the":
        toks = toks[1:]
    while toks and toks[-1] in _SUFFIX_TOKENS:
        toks.pop()
    dropped = False
    while len(toks) > 1 and (toks[-1] in _DESCRIPTOR_TOKENS or " ".join(toks[-2:]) in _DESCRIPTOR_TOKENS):
        toks = toks[:-2] if " ".join(toks[-2:]) in _DESCRIPTOR_TOKENS else toks[:-1]
        dropped = True
        while toks and toks[-1] in _SUFFIX_TOKENS:
            toks.pop()
    return "".join(toks) if dropped and toks else None


def usable_domain(domain: Optional[str]) -> Optional[str]:
    d = (domain or "").lower().strip()
    d = re.sub(r"^https?://", "", d).split("/")[0]
    d = re.sub(r"^www\.", "", d)
    if not d or "." not in d or d in _SHARED_DOMAINS or any(d.endswith("." + s) for s in _SHARED_DOMAINS):
        return None
    return d


def mergeable_key(key: Optional[str]) -> bool:
    return bool(key) and len(key) >= 3 and key not in _GENERIC_KEYS


def find_existing_company(db, name: str, domain: Optional[str] = None) -> Any:
    """Existing row for this company (same domain, or same canonical name), else None."""
    from sqlalchemy import func

    from app.models.company import Company

    dom = usable_domain(domain)
    if dom:
        row = db.query(Company).filter(Company.website_domain == dom).order_by(Company.id.asc()).first()
        if row is not None:
            return row
    exact = db.query(Company).filter(func.lower(Company.name) == (name or "").strip().lower()).order_by(
        Company.id.asc()).first()
    if exact is not None:
        return exact
    key = canonical_company_key(name)
    if not mergeable_key(key):
        return None
    words = _words(name)
    first = next((w for w in words if w != "the"), key)[:12]
    # Narrow by the first word, compare canonical keys in Python.
    candidates = (
        db.query(Company)
        .filter(func.lower(Company.name).like(f"%{first}%"))
        .order_by(Company.id.asc())
        .limit(200)
        .all()
    )
    for row in candidates:
        if canonical_company_key(row.name) == key:
            return row
    base = base_company_key(name)
    if mergeable_key(base):
        for row in candidates:
            if canonical_company_key(row.name) == base:
                return row
    return None


# ─── Grouping existing rows (for ranking and the duplicates report) ──────────


class _UnionFind:
    def __init__(self) -> None:
        self.parent: dict[int, int] = {}

    def find(self, x: int) -> int:
        self.parent.setdefault(x, x)
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a: int, b: int) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[max(ra, rb)] = min(ra, rb)


def group_companies(rows: Iterable[tuple[int, str, Optional[str]]]) -> dict[int, int]:
    """[(id, name, website_domain)] → {id: group_root_id}. Same canonical name or same own domain."""
    uf = _UnionFind()
    by_key: dict[str, int] = {}
    by_domain: dict[str, int] = {}
    pending_base: list[tuple[int, str]] = []
    rows = list(rows)
    for cid, name, domain in rows:
        uf.find(cid)
        if junk_name_reason(name):
            continue
        key = canonical_company_key(name)
        if mergeable_key(key):
            if key in by_key:
                uf.union(by_key[key], cid)
            else:
                by_key[key] = cid
        base = base_company_key(name)
        if mergeable_key(base):
            pending_base.append((cid, base))
        dom = usable_domain(domain)
        if dom:
            if dom in by_domain:
                uf.union(by_domain[dom], cid)
            else:
                by_domain[dom] = cid
    # 'Kenco Logistics' joins 'Kenco Group' only because a bare 'kenco' company exists.
    for cid, base in pending_base:
        if base in by_key:
            uf.union(by_key[base], cid)
    return {cid: uf.find(cid) for cid in list(uf.parent)}
