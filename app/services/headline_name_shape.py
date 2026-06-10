"""
Headline name shape filter
==========================
Structural yes/no checks for strings extracted from news headlines.
Rejects fragments that *look* title-cased but are not legal entity names.

Used by ``lead_name_gate`` before ontological inference runs.
"""
from __future__ import annotations

import re
from typing import Tuple

# Shared with intelligence_news_scraper extraction heuristics
HEADLINE_NOISE_WORDS = frozenset({
    "the", "a", "an", "this", "that", "these", "those", "said", "says",
    "according to", "new york", "los angeles", "san francisco", "united states",
    "north america", "wall street", "main street", "industry", "company",
    "corporation", "inc", "llc", "ltd", "group", "international",
    "u.s. news", "world report", "& world", "& report", "criticize ",
    "discusses", "what ", "how ", "trends", "know about", "pleas for",
    "leaves door", "receives approval", "in stages", "in funding",
    "chicken restaurant chain", "fast food industry", "restaurant chain",
    "hotel group executive", "logistics park", "national park",
    "alumni", "reportedly", "predicts", "nixes", "cancels", "kicks", "amid",
    "women", "retailers", "nurses", "market", "outlook", "progress", "smoothies",
    "police", "start-ups", "experts", "robots", "momentum",
    "wildfires", "neuropsychology", "psychology",
})

_LEADING_ADVERBS = re.compile(
    r"^(significantly|rapidly|recently|officially|increasingly|reportedly|"
    r"nearly|currently|already|now|just|still|yet|also|only|even|further|"
    r"us-based|uk-based|china-based|japan-based|europe-based|"
    r"approximately|roughly|almost|over|more than|less than)\b",
    re.IGNORECASE,
)

_NOISE_PHRASES = frozenset({
    "& world", "& report", "u.s. news", "world report",
    "criticize", "discusses", " in funding", "in funding",
    "receives approval", "in stages", "leaves door",
    "chicken restaurant chain", "fast food industry",
    "logistics park", "national park",
    "market research", "market outlook", "market size",
    "labor shortage", "predicts a profit", "can you", "now it",
    "replacement route", "route 95", "route 9517",
    "launches ai and robotic", "launches ai and robot",
    "wildfires", "neuropsychology",
    "isin ", " isin", "stock isin",
    "earnings new", "earnings ",
    "distribution and",
    "leveraging ai",
    "automation lag",
    "pharmacy automation",
    "fill pharmacy",
    "healthcare access",
})

_SENTENCE_WORDS = frozenset({
    "to", "for", "in", "on", "at", "with", "from", "but",
    "receives", "approval", "stages", "funding", "staffing",
    "cuts", "leaves", "pleas", "trends", "know", "about",
    "criticize", "discusses", "what", "how", "through",
    "will", "nixes", "cancels", "kicks", "amid", "alumni",
    "reportedly", "predicts", "some", "it",
    "delivers", "delivery", "releases", "continues", "anticipates",
    "anticipate", "increase", "increases", "reveal", "reveals",
    "access", "policy", "act", "could", "brace", "braces",
    "lag", "lags", "industry",
    "here", "there", "five", "six", "seven", "eight", "nine", "ten",
})

_GENERIC_SINGLES = frozenset({
    "flexible", "scalable", "automated", "autonomous", "intelligent",
    "digital", "smart", "advanced", "integrated", "connected",
    "global", "local", "national", "regional", "international",
})

# Single-token headline extractions (verbs, wire tails, section labels)
_HEADLINE_FRAGMENT_SINGLES = frozenset({
    "steering", "shares", "quality", "recruiting", "workforce", "earnings",
    "reservations", "distribution", "leveraging", "emerges", "cracked",
    "special", "leading",
})

_GENERIC_PLURALS = frozenset({
    "retailers", "nurses", "women", "robots", "experts",
    "workers", "operators", "managers", "systems",
})


def passes_headline_name_shape(name: str) -> Tuple[bool, str]:
    """
    Boolean shape gate for headline-extracted candidate names.
    Returns (True, "") if the string has plausible company-name shape.
    """
    if not name or not str(name).strip():
        return False, "empty name"

    name = str(name).strip()
    name_lower = name.lower()
    words = name_lower.split()

    if len(name) < 3 or len(name) > 55:
        return False, "name length out of range (headline fragment)"

    if "?" in name:
        return False, "contains question mark (headline)"
    if re.search(r"\.{3,}", name) or "..." in name:
        return False, "truncated headline ellipsis"
    if re.match(r"(?i)^inside\s+[A-Z]\w+\s+[A-Z]", name):
        return False, "editorial deck opener"

    if not any(c.isupper() for c in name):
        return False, "no uppercase letter (not a proper noun)"

    if any(
        len(w.strip()) >= 3 and name_lower.startswith(w.strip())
        for w in HEADLINE_NOISE_WORDS
    ):
        return False, "starts with headline noise word"

    if _LEADING_ADVERBS.match(name_lower):
        return False, "starts with adverb (sentence fragment)"

    if re.search(r"'s?\s+\w+", name) and not re.search(
        r"(?i)'s?\s+(group|corp|inc|ltd|co\.?|holdings?|ventures?|partners?|labs?|"
        r"technologies|solutions|services|systems)$",
        name_lower,
    ):
        return False, "possessive headline fragment"

    if any(phrase in name_lower for phrase in _NOISE_PHRASES):
        return False, "contains headline noise phrase"

    if re.search(r"\bin funding\b.*\bthe robot\b$", name_lower):
        return False, "headline debris (in funding)"
    if "state leaders" in name_lower and "criticize" in name_lower:
        return False, "political headline fragment"

    if re.search(
        r"\s-\s+\w+[\w\s]*?(press|times|news|post|herald|tribune|journal|gazette|"
        r"review|report|daily|weekly|media|wire)\s*$",
        name_lower,
    ):
        return False, "news outlet attribution suffix"

    if re.search(r"\b[A-Z]{2}[A-Z0-9]{10}\b", name):
        return False, "embedded ISIN/ticker code"

    if name_lower in HEADLINE_NOISE_WORDS:
        return False, "noise word only"

    if re.search(r"\s(to|-\s*$|in|for|and|the|a|an|of|by)$", name_lower):
        return False, "truncated sentence fragment"

    if re.search(r"& (world|report)$|\s-\s*(u\.?s\.?|the)\b", name_lower):
        return False, "news org pattern"

    if any(
        re.search(r"\b" + re.escape(w) + r"\b", " " + name_lower + " ")
        for w in _SENTENCE_WORDS
    ):
        return False, "contains sentence word (headline grammar)"

    if re.search(
        r"\s(will|nixes|cancels|kicks\s|kicks off|predicts|releases?|delivers?|"
        r"continues?|brace|braces?|surge|surges?|lag|lags?|boosts?|gains?|adds?|"
        r"names?|serves?|cuts?|slashes?|opens?|closes?|shuts?|files?|wins?|"
        r"loses?|drops?|spikes?|surges?|plunges?|soars?|slips?|sheds?|"
        r"unveils?|launches?|announces?|reveals?|acquires?|hires?|expands?|"
        r"celebrates?|highlights?|appoints?|introduces?)\s*$",
        name_lower,
    ):
        return False, "trailing headline verb"

    if re.search(
        r"\s(revs?|heats?|ramps?|gears?|picks?|winds?|steps?|scales?|powers?)\s+(up|in|off|out|down)\s*$",
        name_lower,
    ):
        return False, "trailing phrasal verb"

    if re.match(r"^(here\s+(are|is)|there\s+(are|is))\s+", name_lower):
        return False, "list headline opener"

    if re.match(
        r"^(the\s+)?(future|state|rise|fall|history|evolution|dawn|end|era|age)\s+of\s+",
        name_lower,
    ):
        return False, "topic headline (future/state of X)"

    if re.match(
        r"^(supply chain|value chain|cold chain|warehouse|logistics|fulfillment|"
        r"distribution|manufacturing|packaging|retail|hospitality|healthcare|"
        r"food safety|food service|restaurant|automation|robotics)\s+"
        r"(technology|technologies|solutions?|management|services?|systems?|"
        r"analytics|platform|software|trends?)\s*$",
        name_lower,
    ):
        return False, "generic sector technology phrase"

    if re.search(
        r"\b(RELEASES|DELIVERS|ANNOUNCES|LAUNCHES|UNVEILS|OPENS|CLOSES|"
        r"REPORTS|NAMES|HIRES|ACQUIRES|SIGNS|WINS|LOSES)\s*$",
        name,
    ):
        return False, "ALL CAPS wire verb tail"

    if name_lower.startswith("new ") and len(words) >= 2 and (
        words[1].isdigit()
        or words[1]
        in {
            "surgical", "robot", "82", "mir", "software", "eastern", "western",
            "northern", "southern", "hub", "facility", "center",
        }
    ):
        return False, "New [product/descriptor] headline stub"

    if re.search(
        r"\s(ceo|robot|market|market research|market outlook|act|policy|"
        r"hub|center|facility|complex|campus|park|'s)\s*$",
        name_lower,
    ):
        return False, "ends with role/market/facility descriptor"

    if name_lower in _GENERIC_PLURALS:
        return False, "generic population/category plural"

    if len(words) == 1 and name_lower in _GENERIC_SINGLES:
        return False, "generic abstract single word"

    if len(words) == 1 and name_lower in _HEADLINE_FRAGMENT_SINGLES:
        return False, "single-word headline fragment"

    if re.search(r"\boks$", name_lower):
        return False, "headline verb conjugation (OKs)"

    if re.search(r"\b(plant|emerges|cracked|workforce|earnings)\s*$", name_lower):
        return False, "trailing headline noun/verb stub"

    if name_lower.startswith("some ") or name_lower.startswith("can "):
        return False, "question/list opener"

    if "," in name:
        return False, "comma (sentence fragment)"

    if " and " in name_lower and any(
        w in name_lower for w in ("cta", " and robot", " and robotic")
    ):
        return False, "headline conjunction fragment"

    if all(word in HEADLINE_NOISE_WORDS for word in words):
        return False, "all noise words"

    if len(words) > 7:
        return False, "too many words (likely headline sentence)"

    if name[0].islower():
        return False, "starts lowercase (mid-sentence fragment)"

    if re.match(r"^[a-z]{2}\.\s", name_lower) or name_lower.startswith("state "):
        return False, "location/state prefix"

    if re.search(
        r"\b(ont|que|b\.?c|alta?|sask|man|n\.?s|n\.?b|p\.?e\.?i|n\.?l)\b\.?\s*$",
        name_lower,
    ):
        return False, "city + province fragment"

    if re.search(r"\b(u\.s|u\.k|u\.s\.a)\s*\.?\s*$", name_lower):
        return False, "country abbreviation tail"

    return True, ""
