"""
text_classifier.py
==================
Semantic entity type classifier — "What is this text?"

Rather than matching words as tokens against a blocklist, we classify text
snippets by their *structural grammar template*:

  CONJUGATED_VERB   → finite verb in a subject position signals a sentence or
                       headline, never a company name
  POSSESSIVE        → possessive constructs ("X's Y") signal description fragments
  COMPARISON        → comparative constructs signal editorial content
  QUESTION          → interrogative openers signal article titles
  PERSON_NAME       → FirstName + LastName pattern (no corporate suffix)
  GEOGRAPHIC        → city / country / state identifiers
  SECTOR_DESCRIPTOR → industry or buyer-persona category, not a named account
  FACILITY_DESCRIPTOR → facility/location type, not a named account
  POPULATION_GROUP  → demographic/workforce group, not a named account
  MALFORMED_ENTITY  → real-looking name embedded in a broken headline fragment
  SAYING / QUOTE    → quoted text or proverbial patterns
  COMPANY_NAME      → proper noun, no finite verb, distinctive word present

Public API
----------
  classify(text: str) -> TextClassification
  is_company_name(text: str) -> bool          # convenience wrapper

  TextClassification.entity_type   : EntityType
  TextClassification.confidence    : float  (0–1)
  TextClassification.evidence      : List[str]
  TextClassification.is_valid_company : bool
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from app.services.semantic_roles import parse_semantic_roles


# ─────────────────────────────────────────────────────────────────────────────
# Entity types
# ─────────────────────────────────────────────────────────────────────────────

class EntityType(Enum):
    COMPANY_NAME     = "company_name"
    PERSON_NAME      = "person_name"
    CITY_OR_TOWN     = "city_or_town"
    COUNTRY          = "country"
    SECTOR_DESCRIPTOR = "sector_descriptor"
    FACILITY_DESCRIPTOR = "facility_descriptor"
    POPULATION_GROUP = "population_group"
    DESCRIPTOR_ONLY = "descriptor_without_object"
    MALFORMED_ENTITY = "malformed_entity_string"
    DESCRIPTION      = "description"
    SAYING           = "saying"
    ARTICLE_HEADLINE = "article_headline"
    EQUIPMENT_CAT    = "equipment_category"
    MARKET_FRAGMENT  = "market_fragment"
    UNKNOWN          = "unknown"


@dataclass
class TextClassification:
    entity_type: EntityType
    confidence: float               # 0–1
    evidence: List[str] = field(default_factory=list)
    is_valid_company: bool = False

    def __repr__(self) -> str:
        return (
            f"TextClassification(type={self.entity_type.value}, "
            f"conf={self.confidence:.2f}, valid_company={self.is_valid_company})"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Template: CONJUGATED VERB detection
#
# A company name does not contain finite verbs.  If the candidate string
# contains a conjugated verb in subject-verb position we have a sentence or
# headline fragment, not a company name.
# ─────────────────────────────────────────────────────────────────────────────

# Auxiliary verbs that attach to a subject → sentence pattern
_AUX_VERBS = re.compile(
    r"\b(is|are|was|were|has|have|had|will|would|could|should|may|might|must|"
    r"shall|does|do|did|'s\s+been|'ve\s+been|'re\s+going)\b",
    re.IGNORECASE,
)

# Strong action verbs in 3rd-person singular (common in news headlines)
# Ending: -s, -es, -ed — but NOT legitimate company name suffixes like "-ies"
_HEADLINE_VERBS = re.compile(
    r"\b(expands?|continues?|launches?|hires?|opens?|closes?|acquires?|deploys?|announces?|"
    r"reveals?|unveils?|signs?|wins?|loses?|raises?|cuts?|gains?|drops?|rises?|falls?|"
    r"grows?|shrinks?|invests?|plans?|aims?|targets?|secures?|lands?|names?|appoints?|"
    r"makes?|builds?|scales?|tests?|trials?|pilots?|"
    r"promotes?|retires?|resigns?|files?|sues?|settles?|recalls?|halts?|pauses?|"
    r"reports?|posts?|earns?|beats?|misses?|warns?|says?|stated?|confirmed?|denied?|"
    r"celebrated?|highlighted?|completed?|delivered?|implemented?|transformed?|"
    r"automated?|deployed?|installed?|integrated?|adopted?|modernized?|upgraded?|"
    r"partnered?|collaborated?|merged?|acquired?|divested?|spun?\s+off)\b",
    re.IGNORECASE,
)

# Past-tense -ed verbs preceded by a whitespace (sentence pattern)
_PAST_TENSE = re.compile(
    r"(?<!\w)(announced|expanded|launched|hired|opened|closed|acquired|deployed|"
    r"reported|completed|delivered|implemented|invested|raised|secured|partnered|"
    r"merged|divested|named|appointed|promoted|recalled|halted|filed|won|lost|"
    r"grew|shrunk|signed|revealed|unveiled|celebrated|achieved|transformed|"
    r"automated|installed|integrated|adopted|modernized|upgraded)\b",
    re.IGNORECASE,
)


def _has_conjugated_verb(text: str) -> Optional[str]:
    """Returns the matched verb string if a conjugated verb is found, else None."""
    m = _AUX_VERBS.search(text)
    if m:
        return m.group(0)
    m = _HEADLINE_VERBS.search(text)
    if m:
        return m.group(0)
    m = _PAST_TENSE.search(text)
    if m:
        return m.group(0)
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Template: POSSESSIVE fragment
# ─────────────────────────────────────────────────────────────────────────────

# "Company's new hub", "Delta's power cooling" — description fragment
_POSSESSIVE = re.compile(r"\b\w{2,}'s\s+\w", re.IGNORECASE)


# ─────────────────────────────────────────────────────────────────────────────
# Template: COMPARISON
# ─────────────────────────────────────────────────────────────────────────────

_COMPARISON = re.compile(
    r"\b(more\s+than|less\s+than|compared\s+to|versus|vs\.?|unlike|"
    r"better\s+than|worse\s+than|cheaper\s+than|faster\s+than|"
    r"as\s+\w+\s+as|than\s+ever|than\s+before)\b",
    re.IGNORECASE,
)


# ─────────────────────────────────────────────────────────────────────────────
# Template: QUESTION OPENER
# ─────────────────────────────────────────────────────────────────────────────

_QUESTION_OPENER = re.compile(
    r"^(how|why|what|when|where|who|which|can|could|should|will|would|is|are|"
    r"was|were|do|does|did)\b",
    re.IGNORECASE,
)


# ─────────────────────────────────────────────────────────────────────────────
# Template: SAYING / QUOTE
# ─────────────────────────────────────────────────────────────────────────────

_QUOTE_WRAP = re.compile(r'^["\u201c\u2018].+["\u201d\u2019]$')
_SAYING_OPENER = re.compile(
    r"^(as\s+(they|people|we|it)\s+say|the\s+saying\s+goes|"
    r"according\s+to|as\s+the\s+old\s+saying)",
    re.IGNORECASE,
)


# ─────────────────────────────────────────────────────────────────────────────
# Template: PERSON NAME
#
# Two or three title-case words where the first is a known first name
# and no corporate suffix is present.
# ─────────────────────────────────────────────────────────────────────────────

_COMMON_FIRST_NAMES: frozenset = frozenset({
    "james", "john", "robert", "michael", "william", "david", "richard",
    "joseph", "thomas", "charles", "christopher", "daniel", "matthew",
    "anthony", "donald", "mark", "paul", "steven", "andrew", "kenneth",
    "george", "joshua", "kevin", "brian", "edward", "ronald", "timothy",
    "jason", "jeffrey", "ryan", "jacob", "gary", "nicholas", "eric",
    "jonathan", "stephen", "larry", "justin", "scott", "brandon", "benjamin",
    "samuel", "frank", "gregory", "raymond", "frank", "patrick", "alexander",
    "jack", "dennis", "jerry", "tyler", "aaron", "jose", "henry", "adam",
    "douglas", "nathan", "peter", "zachary", "kyle", "walter", "harold",
    "mary", "patricia", "jennifer", "linda", "barbara", "elizabeth", "susan",
    "jessica", "sarah", "karen", "lisa", "nancy", "betty", "margaret",
    "sandra", "ashley", "emily", "donna", "michelle", "carol", "amanda",
    "melissa", "melonie", "melony", "deborah", "stephanie", "rebecca", "sharon", "laura", "cynthia",
    "kathleen", "amy", "angela", "shirley", "anna", "brenda", "pamela",
    "emma", "nicole", "helen", "samantha", "katherine", "christine", "virginia",
    # Well-known first names of public figures in business news
    "elon", "jeff", "sundar", "satya", "jensen", "oprah", "sheryl", "tim",
    "mark", "larry", "sergey", "reed", "marc", "sam", "andy",
})

_LEGAL_SUFFIX_RE = re.compile(
    r"\b(inc\.?|llc\.?|ltd\.?|corp\.?|corporations?|co\.?|plc\.?|llp\.?|lp\.?|gmbh|bv|nv|ag|"
    r"s\.a\.?|s\.r\.l\.?|pty\.?|pte\.?|holdings?|group|enterprises?|"
    r"international|industries|ventures?|partners?|associates?)\s*$",
    re.IGNORECASE,
)

# Job title words — if the second word of a 2-word string is a job title,
# it's a person + title combination, not a company name.
_JOB_TITLES: frozenset = frozenset({
    "ceo", "coo", "cfo", "cto", "vp", "president", "director", "manager",
    "chief", "head", "officer", "founder", "partner", "consultant",
    "chairman", "chairwoman", "chairperson", "executive", "analyst",
    "engineer", "scientist", "researcher", "advisor",
})


def _is_person_name(text: str) -> bool:
    """
    Returns True if text looks like a person's name:
    2–3 title-case words, first word is a known first name,
    no corporate suffix, no company-style numbers.
    """
    # Reject if it has a legal suffix (it's a company, not a person)
    if _LEGAL_SUFFIX_RE.search(text):
        return False
    words = text.strip().split()
    if len(words) < 2 or len(words) > 4:
        return False
    # First word must be a known first name (case-insensitive)
    if words[0].lower() not in _COMMON_FIRST_NAMES:
        return False
    # All words must be title-case (person names are title-cased)
    if not all(w[0].isupper() for w in words if w.isalpha()):
        return False
    # No digits (company names sometimes have numbers; people's names don't)
    if any(c.isdigit() for c in text):
        return False
    # Second word can be a last name OR a job title — both indicate person
    return True


# ─────────────────────────────────────────────────────────────────────────────
# Template: GEOGRAPHIC — city, town, country, state
# ─────────────────────────────────────────────────────────────────────────────

_COUNTRIES: frozenset = frozenset({
    "germany", "france", "japan", "china", "india", "brazil", "canada",
    "australia", "mexico", "italy", "spain", "south korea", "north korea",
    "russia", "ukraine", "turkey", "indonesia", "argentina", "netherlands",
    "switzerland", "sweden", "norway", "denmark", "finland", "poland",
    "singapore", "taiwan", "vietnam", "thailand", "malaysia", "philippines",
    "saudi arabia", "uae", "united arab emirates", "egypt", "nigeria",
    "south africa", "kenya", "israel", "pakistan", "bangladesh",
    "united states", "united kingdom", "great britain",
    "europe", "asia", "africa", "latin america", "middle east",
    "north america", "south america", "southeast asia",
})

_US_STATES: frozenset = frozenset({
    "alabama", "alaska", "arizona", "arkansas", "california", "colorado",
    "connecticut", "delaware", "florida", "georgia", "hawaii", "idaho",
    "illinois", "indiana", "iowa", "kansas", "kentucky", "louisiana",
    "maine", "maryland", "massachusetts", "michigan", "minnesota",
    "mississippi", "missouri", "montana", "nebraska", "nevada",
    "new hampshire", "new jersey", "new mexico", "new york", "north carolina",
    "north dakota", "ohio", "oklahoma", "oregon", "pennsylvania",
    "rhode island", "south carolina", "south dakota", "tennessee",
    "texas", "utah", "vermont", "virginia", "washington", "west virginia",
    "wisconsin", "wyoming",
})

# "City, ST" or "City, Country" pattern
_CITY_STATE_PATTERN = re.compile(
    r"^[A-Z][a-zA-Z\s]+,\s*([A-Z]{2}|[A-Za-z\s]{3,})$"
)

# Generic geographic words that alone indicate a place, not a company
_GEO_WORDS = re.compile(
    r"\b(city|town|village|municipality|county|province|state|region|"
    r"district|territory|capital|metropolitan|suburb)\b",
    re.IGNORECASE,
)


def _is_geographic(text: str) -> tuple[bool, EntityType]:
    """Returns (True, EntityType) if text is a geographic name."""
    low = text.strip().lower()
    if low in _COUNTRIES:
        return True, EntityType.COUNTRY
    if low in _US_STATES:
        return True, EntityType.CITY_OR_TOWN
    if _CITY_STATE_PATTERN.match(text.strip()):
        return True, EntityType.CITY_OR_TOWN
    if _GEO_WORDS.search(text):
        return True, EntityType.CITY_OR_TOWN
    return False, EntityType.UNKNOWN


# ─────────────────────────────────────────────────────────────────────────────
# Template: EQUIPMENT CATEGORY
# ─────────────────────────────────────────────────────────────────────────────

_EQUIPMENT_CAT = re.compile(
    r"\b(filling\s+machine|labeling\s+machine|wrapping\s+machine|sealing\s+machine|"
    r"packing\s+machine|capping\s+machine|palletizing\s+machine|conveyor\s+system|"
    r"sorter\s+system|pick\s+and\s+place|robotic\s+arm|servo\s+motor|stepper\s+motor|"
    r"linear\s+actuator|industrial\s+robot|collaborative\s+robot|mobile\s+robot|"
    r"autonomous\s+vehicle|automated\s+guided\s+vehicle|agv|amr)\b",
    re.IGNORECASE,
)


# ─────────────────────────────────────────────────────────────────────────────
# Template: MARKET FRAGMENT
# ─────────────────────────────────────────────────────────────────────────────

_MARKET_FRAGMENT = re.compile(
    r"\b(market\s+(size|share|forecast|report|outlook|analysis|overview|trends?)|"
    r"industry\s+(report|outlook|forecast|analysis|trends?)|"
    r"global\s+(market|industry|outlook|forecast)|"
    r"sector\s+(outlook|forecast|report)|"
    r"research\s+(report|study|findings?)|"
    r"cagr|compound\s+annual\s+growth)\b",
    re.IGNORECASE,
)


# ─────────────────────────────────────────────────────────────────────────────
# Template: ONTOLOGICAL NON-COMPANY DESCRIPTORS
# ─────────────────────────────────────────────────────────────────────────────

_REGION_MODIFIER = (
    r"(?:u\.s\.|us|american|north\s+american|europe|european|asia|asian|"
    r"n\.j\.|nj|philly(?:-area)?|california|texas|florida|new\s+york|"
    r"chicago|atlanta|dfw|dallas|houston|bay\s+area)"
)

_SECTOR_DESCRIPTOR = re.compile(
    rf"^(?:{_REGION_MODIFIER}\s+)?("
    r"hospitality|restaurants?|qsr|third\s+party\s+logistics|3pl|"
    r"logistics|supply\s+chain|manufacturers?|retailers?|hotels?|"
    r"healthcare|hospitals?|airports?|operators?|robotics?|robots?|"
    r"strategic\s+business|scaling\s+restaurants"
    r")\s*$",
    re.IGNORECASE,
)

_FACILITY_DESCRIPTOR = re.compile(
    rf"^(?:{_REGION_MODIFIER}\s+)?("
    r"logistics\s+park|industrial\s+park|business\s+park|warehouse\s+park|"
    r"distribution\s+centers?|fulfillment\s+centers?|warehouses?|"
    r"hospitals?|clinics?|hotels?|restaurants?|airports?|facilities|"
    r"hospitality\s+robots|hospitality\s+robots\s+strategic\s+business"
    r")\s*$",
    re.IGNORECASE,
)

_POPULATION_GROUP = re.compile(
    rf"^(?:{_REGION_MODIFIER}\s+)?("
    r"elderly\s+americans|older\s+adults|seniors?|patients?|"
    r"health\s+workers?|hospital\s+workers?|restaurant\s+workers?|"
    r"warehouse\s+workers?|factory\s+workers?|travelers?|guests?|"
    r"consumers?|customers?|operators?"
    r")\s*$",
    re.IGNORECASE,
)

_MALFORMED_ENTITY_STRING = re.compile(
    r"(?i)^([A-Z][A-Za-z0-9&'.-]+(?:\s+[A-Z][A-Za-z0-9&'.-]+){0,4})\s+"
    r"(and\s*$|and\s+(the\s+)?(technology|business|market|industry|automation|robots?)|"
    r"to\s+(open|expand|deploy|launch|hire))"
)


# ─────────────────────────────────────────────────────────────────────────────
# Template: COMPANY NAME positive signals
# ─────────────────────────────────────────────────────────────────────────────

# Words that are clearly not part of a company name (generic article words)
_ARTICLE_OPENER = re.compile(
    r"^(the\s+|a\s+|an\s+)(hotel|restaurant|company|firm|brand|chain|"
    r"store|warehouse|hospital|operator|retailer|business|sector|"
    r"market|industry|report|study|survey)\b",
    re.IGNORECASE,
)

# All-caps abbreviations with 2–3 letters are often ticker/airport codes
_SHORT_ALLCAPS = re.compile(r"^[A-Z]{2,3}(\d)?$")


def _has_legal_suffix(text: str) -> bool:
    return bool(_LEGAL_SUFFIX_RE.search(text))


def _word_count(text: str) -> int:
    return len(text.strip().split())


def _is_title_case(text: str) -> bool:
    """Returns True if most words start with a capital letter."""
    words = [w for w in text.strip().split() if w.isalpha() and len(w) > 2]
    if not words:
        return False
    caps = sum(1 for w in words if w[0].isupper())
    return caps / len(words) >= 0.6


# ─────────────────────────────────────────────────────────────────────────────
# Main classifier
# ─────────────────────────────────────────────────────────────────────────────

def classify(text: str) -> TextClassification:
    """
    Classify a text snippet by semantic entity type.

    Templates are checked in order of *disqualification strength* — the most
    reliable negative signals (conjugated verb, question opener) fire first,
    then progressively softer heuristics.

    Returns TextClassification with entity_type, confidence, evidence, and
    a is_valid_company convenience flag.
    """
    if not text or not text.strip():
        return TextClassification(
            EntityType.UNKNOWN, 0.0,
            ["empty input"], False,
        )

    raw = text.strip()
    low = raw.lower()
    evidence: List[str] = []
    confidence = 0.5  # default mid-confidence until a template fires
    roles = parse_semantic_roles(raw)

    # ── Hard headline / deck artefacts (before legal-suffix fast-pass) ─────────
    # Real operating names almost never end in "?" or use "Inside X" magazine decks.
    if raw.endswith("?"):
        evidence.append("ends with question mark (rhetorical headline / fragment)")
        return TextClassification(EntityType.ARTICLE_HEADLINE, 0.90, evidence, False)
    if re.search(r"\.{3,}", raw):
        evidence.append("ellipsis or truncated RSS/deck copy")
        return TextClassification(EntityType.ARTICLE_HEADLINE, 0.88, evidence, False)
    if re.match(r"(?i)^inside\s+[A-Z]\w+\s+[A-Z]", raw):
        evidence.append("editorial section kicker: 'Inside X Y …'")
        return TextClassification(EntityType.ARTICLE_HEADLINE, 0.90, evidence, False)
    # Same rule as lead_filter: only when the whole string is the stub (allows "… Stadium").
    _nordic_sport_headline_only = re.compile(
        r"(?i)(swedish|norwegian|danish|finnish|icelandic|estonian|latvian|lithuanian)\s+"
        r"(sport|sports)\s+(airline|airlines|carrier|retailer|retailers|chain|chains|"
        r"brand|brands|group)\s*[\s.?!…]*\Z",
    )
    if _nordic_sport_headline_only.fullmatch(raw):
        evidence.append("nationality + generic sector headline only (not 'descriptor + brand')")
        return TextClassification(EntityType.ARTICLE_HEADLINE, 0.88, evidence, False)

    # ── Fast-pass: legal suffix → almost certainly a company ─────────────────
    if _has_legal_suffix(raw):
        evidence.append("has legal entity suffix (Inc/LLC/Corp/Ltd/…)")
        return TextClassification(EntityType.COMPANY_NAME, 0.92, evidence, True)

    # ── DISQUALIFIERS (checked before positive signals) ───────────────────────

    # 1. Question opener
    if _QUESTION_OPENER.match(raw):
        evidence.append(f"question opener: {raw.split()[0]!r}")
        return TextClassification(EntityType.ARTICLE_HEADLINE, 0.92, evidence, False)

    # 2. Saying / quote
    if _QUOTE_WRAP.match(raw):
        evidence.append("surrounded by quotation marks")
        return TextClassification(EntityType.SAYING, 0.88, evidence, False)
    if _SAYING_OPENER.match(raw):
        evidence.append("starts with proverbial phrase")
        return TextClassification(EntityType.SAYING, 0.85, evidence, False)

    # 3. Geographic exact match
    geo, geo_type = _is_geographic(raw)
    if geo:
        evidence.append(f"geographic name ({geo_type.value})")
        return TextClassification(geo_type, 0.90, evidence, False)

    # 4. Market fragment
    mf = _MARKET_FRAGMENT.search(raw)
    if mf:
        evidence.append(f"market report fragment: {mf.group(0)!r}")
        return TextClassification(EntityType.MARKET_FRAGMENT, 0.87, evidence, False)

    # 5. Comparison operators. This must run before object-head parsing because
    # comparison sentences often end with population/facility objects.
    comp = _COMPARISON.search(raw)
    if comp:
        evidence.append(f"comparison construct: {comp.group(0)!r}")
        return TextClassification(EntityType.ARTICLE_HEADLINE, 0.82, evidence, False)

    # 6. Ontological non-company descriptors
    if roles.object_kind == "candidate_object":
        evidence.extend(roles.evidence)
        evidence.append(f"candidate object: {roles.object_candidate!r}")
        return TextClassification(EntityType.MALFORMED_ENTITY, 0.78, evidence, False)

    if roles.object_kind == "malformed_entity_string":
        evidence.extend(roles.evidence)
        evidence.append(f"candidate object: {roles.object_candidate!r}")
        return TextClassification(EntityType.MALFORMED_ENTITY, 0.84, evidence, False)

    malformed = _MALFORMED_ENTITY_STRING.search(raw)
    if malformed:
        evidence.append("proper-name span embedded in malformed headline fragment")
        evidence.append(f"candidate span: {malformed.group(1)!r}")
        return TextClassification(EntityType.MALFORMED_ENTITY, 0.84, evidence, False)

    if roles.object_kind == "sector_descriptor":
        evidence.extend(roles.evidence)
        evidence.append(f"head object: {roles.head_object!r}")
        return TextClassification(EntityType.SECTOR_DESCRIPTOR, 0.88, evidence, False)

    if roles.object_kind == "facility_descriptor":
        evidence.extend(roles.evidence)
        evidence.append(f"head object: {roles.head_object!r}")
        return TextClassification(EntityType.FACILITY_DESCRIPTOR, 0.88, evidence, False)

    if roles.object_kind == "population_group":
        evidence.extend(roles.evidence)
        evidence.append(f"head object: {roles.head_object!r}")
        return TextClassification(EntityType.POPULATION_GROUP, 0.88, evidence, False)

    if roles.object_kind == "descriptor_without_object":
        evidence.extend(roles.evidence)
        evidence.append("descriptor-only token has no buyer-account object")
        return TextClassification(EntityType.DESCRIPTOR_ONLY, 0.90, evidence, False)

    if roles.object_kind == "abstract_descriptor":
        evidence.extend(roles.evidence)
        evidence.append(f"head object: {roles.head_object!r}")
        return TextClassification(EntityType.DESCRIPTION, 0.78, evidence, False)

    sector = _SECTOR_DESCRIPTOR.search(raw)
    if sector:
        evidence.append(f"sector/category descriptor: {sector.group(1)!r}")
        return TextClassification(EntityType.SECTOR_DESCRIPTOR, 0.88, evidence, False)

    facility = _FACILITY_DESCRIPTOR.search(raw)
    if facility:
        evidence.append(f"facility/location descriptor: {facility.group(1)!r}")
        return TextClassification(EntityType.FACILITY_DESCRIPTOR, 0.88, evidence, False)

    population = _POPULATION_GROUP.search(raw)
    if population:
        evidence.append(f"population/workforce group: {population.group(1)!r}")
        return TextClassification(EntityType.POPULATION_GROUP, 0.88, evidence, False)

    # 7. Equipment category label
    eq = _EQUIPMENT_CAT.search(raw)
    if eq:
        evidence.append(f"equipment category label: {eq.group(0)!r}")
        return TextClassification(EntityType.EQUIPMENT_CAT, 0.85, evidence, False)

    # 8. Conjugated verb — strongest structural negative signal for company names
    verb = _has_conjugated_verb(raw)
    if verb:
        evidence.append(f"conjugated verb present: {verb!r}")
        # Possessive on top of verb → definite description
        if _POSSESSIVE.search(raw):
            evidence.append("possessive construct also present")
            return TextClassification(EntityType.DESCRIPTION, 0.91, evidence, False)
        return TextClassification(EntityType.ARTICLE_HEADLINE, 0.85, evidence, False)

    # 9. Possessive fragment (without verb — still a fragment, not a company name)
    if _POSSESSIVE.search(raw):
        # Allow: "O'Brien's", "McDonald's" — single possessive word = brand name
        words = raw.split()
        if len(words) >= 3:
            evidence.append("possessive fragment with multiple words")
            return TextClassification(EntityType.DESCRIPTION, 0.75, evidence, False)
        # 1–2 word possessives can be brand names ("McDonald's", "Wendy's") — continue

    # 10. Article/section opener ("the hotel", "a company", etc.)
    if _ARTICLE_OPENER.match(raw):
        evidence.append("starts with article + generic noun")
        return TextClassification(EntityType.DESCRIPTION, 0.80, evidence, False)

    # ── POSITIVE IDENTIFICATION ────────────────────────────────────────────────

    # 11. Person name
    if _is_person_name(raw):
        evidence.append(f"first-name pattern: {raw.split()[0]!r} is a common first name")
        return TextClassification(EntityType.PERSON_NAME, 0.78, evidence, False)

    # ── Soft scoring: accumulate positive company signals ─────────────────────
    # Philosophy: prove that the string IS a company name, don't just assume it.
    # Each signal adds or removes evidence. A name passes only when multiple
    # independent positive signals agree.

    company_score = 0.0
    word_count = _word_count(raw)

    # ── POSITIVE signals ──────────────────────────────────────────────────────

    # Title-case proper noun (+0.25)
    if _is_title_case(raw):
        company_score += 0.25
        evidence.append("title-case proper noun")

    # Starts with capital (+0.10)
    if raw[0].isupper():
        company_score += 0.10
        evidence.append("starts with capital letter")

    # Compact (1–4 words) — sweet spot for company names (+0.20)
    # 5-word names still plausible but less certain (+0.10)
    if 1 <= word_count <= 4:
        company_score += 0.20
        evidence.append(f"compact name ({word_count} word(s))")
    elif word_count == 5:
        company_score += 0.10
        evidence.append(f"5-word name (borderline compact)")
    elif word_count <= 7:
        company_score += 0.02
    else:
        company_score -= 0.25
        evidence.append(f"very long ({word_count} words) — likely a sentence")

    # No sentence punctuation (+0.10)
    if not re.search(r"[.!?,;:]", raw):
        company_score += 0.10
        evidence.append("no sentence-punctuation")

    # No all-lowercase word pair — not a mid-sentence fragment (+0.10)
    if not re.search(r"\b[a-z]{4,}\s+[a-z]{4,}", raw):
        company_score += 0.10
        evidence.append("no all-lowercase word pair (not mid-sentence)")

    # Contains at least one word that is NOT a generic industry category word.
    # Import the same _GENERIC_WORDS set used by company_validator so scoring
    # is consistent. A name with zero distinctive words is almost certainly a
    # topic label, not a legal entity (+0.20 / -0.30).
    try:
        from app.services.company_validator import _GENERIC_WORDS, _ALWAYS_DISTINCTIVE
        words_lower = [w.lower() for w in re.findall(r"[a-zA-Z&]+", raw)]
        distinctive = any(
            w in _ALWAYS_DISTINCTIVE or w not in _GENERIC_WORDS
            for w in words_lower
        )
        if distinctive:
            company_score += 0.20
            evidence.append("contains distinctive non-generic word")
        else:
            company_score -= 0.30
            evidence.append("all words are generic category terms — no proper noun")
    except Exception:
        pass  # never break if cross-import fails

    # Contains a number or symbol that real companies sometimes use (&, #, digits)
    # but this is a weak positive — small bonus only
    if re.search(r"[&\+\d]", raw):
        company_score += 0.05
        evidence.append("contains & / + / digit (brand formatting)")

    # ── NEGATIVE signals ──────────────────────────────────────────────────────

    # Short all-caps (2–3 letters) = ticker/airport code
    if _SHORT_ALLCAPS.match(raw):
        company_score -= 0.50
        evidence.append("short all-caps: likely ticker or airport code")

    # Generic noun phrase ending (e.g. "Network", "Expansion", "Sourcing" alone)
    _BARE_GENERIC_ENDING = re.compile(
        r"\b(network|expansion|sourcing|research|facility|plant|campus|"
        r"use|adoption|trends?|insights?|overview|strategy|safety|"
        r"management|solutions?|services?|technology)\s*$",
        re.IGNORECASE,
    )
    if _BARE_GENERIC_ENDING.search(raw) and word_count <= 4:
        company_score -= 0.20
        evidence.append("ends with bare generic noun (concept label, not company)")

    # All words are common English words found in a dictionary (not proper nouns)
    # Simple heuristic: if every word is all-lowercase letters (after strip), likely text
    if raw == raw.lower() and not re.search(r"\d|[&\+]", raw):
        company_score -= 0.20
        evidence.append("entirely lowercase — not a proper noun")

    # ── Decision ──────────────────────────────────────────────────────────────

    confidence = min(0.95, max(0.0, company_score))

    if confidence >= 0.45:
        return TextClassification(EntityType.COMPANY_NAME, confidence, evidence, True)

    if confidence >= 0.25:
        # Borderline — classify as UNKNOWN rather than asserting company.
        # The inference gate in company_validator will reject UNKNOWN < 0.40.
        evidence.append(f"borderline ({confidence:.2f}) — insufficient proof of company identity")
        return TextClassification(EntityType.UNKNOWN, confidence, evidence, False)

    evidence.append(f"insufficient positive signals (score={confidence:.2f})")
    return TextClassification(EntityType.DESCRIPTION, 0.60, evidence, False)


# ─────────────────────────────────────────────────────────────────────────────
# Convenience helpers
# ─────────────────────────────────────────────────────────────────────────────

def is_company_name(text: str, min_confidence: float = 0.45) -> bool:
    """Quick boolean check: is this text a company name?"""
    result = classify(text)
    return result.entity_type == EntityType.COMPANY_NAME and result.confidence >= min_confidence


def classify_batch(texts: List[str]) -> List[TextClassification]:
    """Classify a list of text snippets."""
    return [classify(t) for t in texts]
