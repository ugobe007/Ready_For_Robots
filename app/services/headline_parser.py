"""
headline_parser.py
==================
Extracts the ACTOR (the company that owns or performs an action) from a
news headline by applying three linguistic rules:

  RULE 1 — Possessive → actor
      "Walmart's Distribution Centers Turn Automated"
       └─ owner = "Walmart"  →  actor = "Walmart"

       "Hilton Hotels' restaurants are deploying robots"
        └─ owner = "Hilton Hotels"  →  actor = "Hilton Hotels"

  RULE 2 — Verb anchor → subject / descriptor split
      Find the first strong news verb.  Everything before it is the SUBJECT.
      Validate the subject:
        • Subject is a real company → return it as the actor.
        • Subject is a generic phrase ("Distribution Centers") → no actor, return None.

      "Hilton Hotels Targets Automation of Their Distribution Centers"
       └─ verb = "Targets"  subject = "Hilton Hotels"  → VALID → "Hilton Hotels"

      "Distribution Centers in the Middle East Are Facing a Crisis"
       └─ verb = "Are Facing"  subject = "Distribution Centers" → GENERIC → None

      "War Crisis Hits Warehousing Sector"
       └─ verb = "Hits"  subject = "War Crisis" → GENERIC → None

  RULE 3 — Pronoun ownership ("their", "its") signals a prior mention
      The actor is implied by context (pronoun), not extractable from the
      headline alone → return None and let other scraper patterns handle it.

Public API
----------
  extract_actor(headline: str) -> Optional[str]
      Returns the company name of the actor, or None if none can be identified.
"""
from __future__ import annotations

import re
from typing import Optional

# ─────────────────────────────────────────────────────────────────────────────
# News-headline verb list — the "anchor" used to split subject from predicate.
# Ordered from most to least specific.  Each alternation should match the STEM
# so that plurals / tenses (turns, turned, turning) are caught by \w* after.
# ─────────────────────────────────────────────────────────────────────────────
_VERB_STEMS = (
    # Announcement / corporate action
    "announc", "launch", "unveil", "reveal", "introduc", "present",
    "releas", "publish", "publish",
    # Acquisition / partnership
    "acquir", "merg", "partner", "team.*up", "joint.*ventur",
    "sign.*deal", "ink.*deal",
    # Investment / finance
    "rais", "secur", "clos.*fund", "land.*fund", "obtain.*fund",
    "invest", "fund", "back", "financ",
    # Hiring / leadership
    "appoint", "hire", "nam.*ceo", "promot", "onboard",
    # Expansion / construction
    "expand", "open", "build", "deploy", "install", "roll.*out",
    "break.*ground", "construct", "enabl",
    # Contraction / trouble
    "clos", "shut", "layoff", "lay.*off", "downsize", "restructur",
    "exit", "bankrupt", "fil.*chapter",
    # Reporting / stating
    "said", "report", "confirm", "stat", "acknowledg",
    # Change / direction verbs (user-identified: "Distribution Centers TURN")
    "turn", "shift", "pivot", "redefin", "reinvent", "overhaul",
    "transform", "reengineer", "moderniz", "upgrad",
    # Challenge / response verbs
    "navig", "tackl", "address", "combat", "fight", "brac",
    "struggl", "grappl", "face", "confront", "resist",
    # Market / financial movement
    "surge", "soar", "plunge", "spike", "slip", "drop", "rise",
    "fall", "gain", "lose", "climb", "slid",
    # Growth / momentum
    "grow", "scal", "accelerat", "boost", "spur", "lead",
    "outperform", "beat", "miss",
    # General corporate news
    "celebrat", "mark", "win", "award", "receiv",
    "plan", "aim", "target", "prioritiz",
    "hit", "reach", "achiev", "complet", "finish",
    # Strategic / operational verbs (user-identified)
    "deploy", "adopt", "integrat", "automat", "digitiz", "optimiz",
    "streamlin", "consolidat", "restructur", "reorganiz",
)

# Build compiled regex: match any verb stem at a word boundary.
# Suffixes: s, ed, es, ing, er, ers handled by \w{0,6}
_VERB_STEMS_PAT = "|".join(_VERB_STEMS)
_HEADLINE_VERB = re.compile(
    r"\b(?:" + _VERB_STEMS_PAT + r")\w{0,6}\b",
    re.IGNORECASE,
)

# ─────────────────────────────────────────────────────────────────────────────
# Possessive patterns
# ─────────────────────────────────────────────────────────────────────────────
# "Walmart's ..."  or  "Hilton Hotels' ..."
_POSSESSIVE = re.compile(
    r"^([A-Z][A-Za-z0-9\s&\.\-]{1,60}?)'\s*s?\s+",
)

# ─────────────────────────────────────────────────────────────────────────────
# Pronoun ownership signals — headline contains "their" or "its" early on,
# meaning the actor was referenced earlier in the article, not in the headline.
# ─────────────────────────────────────────────────────────────────────────────
_PRONOUN_LEAD = re.compile(r"\b(their|its|his|her)\b", re.IGNORECASE)


def extract_actor(headline: str) -> Optional[str]:
    """
    Main API.  Returns the company name of the actor in `headline`, or None.

    None means: "no specific company actor could be identified from this headline."
    Callers should either skip ingestion or fall through to other extraction patterns.
    """
    from app.services.company_validator import is_valid_lead

    text = headline.strip()
    if not text or len(text) < 6:
        return None

    # ── Rule 1: Possessive ──────────────────────────────────────────────────
    # "Walmart's Distribution Centers Turn" → owner = "Walmart"
    poss_m = _POSSESSIVE.match(text)
    if poss_m:
        owner = poss_m.group(1).strip().rstrip("'")
        valid, _ = is_valid_lead(owner)
        if valid:
            return owner
        # Owner itself is generic ("Industry's X") → fall through to verb logic

    # ── Rule 2: Verb anchor ─────────────────────────────────────────────────
    verb_m = _HEADLINE_VERB.search(text)
    if verb_m:
        subject_phrase = text[:verb_m.start()].strip().rstrip(",;:-—")

        if not subject_phrase:
            # Verb is at the very beginning ("Turns out …") → no extractable subject
            return None

        # Clean trailing auxiliary verbs and prepositions that bleed into subject.
        # "Marriott International Is [Deploying]" → strip trailing "Is" → "Marriott International"
        subject_phrase = re.sub(
            r"\s+\b(is|are|was|were|has|have|had|will|would|can|could|should|"
            r"in|at|of|and|or|the|a|an|by|for|on|with|to|into|as|now|also|still)\b\s*$",
            "",
            subject_phrase,
            flags=re.IGNORECASE,
        ).strip()
        # Apply iteratively — "Marriott International Is Now" needs two passes
        subject_phrase = re.sub(
            r"\s+\b(is|are|was|were|has|have|had|will|would|can|could|should|"
            r"in|at|of|and|or|the|a|an|by|for|on|with|to|into|as|now|also|still)\b\s*$",
            "",
            subject_phrase,
            flags=re.IGNORECASE,
        ).strip()

        valid, _ = is_valid_lead(subject_phrase)
        if valid:
            return subject_phrase

        # Subject is generic (e.g. "Distribution Centers", "War Crisis") →
        # this headline describes a category event, not a company action.
        # Return None: do NOT fall back to grabbing the full title.
        return None

    # ── Rule 3: No verb found ───────────────────────────────────────────────
    # Could be a fragment, a company name alone, or an appositive.
    # Validate the whole headline as-is: if it's a valid company name, return it;
    # otherwise return None and let structural patterns upstream handle it.
    valid, _ = is_valid_lead(text)
    if valid:
        return text
    return None


def possessive_owner(text: str) -> Optional[str]:
    """
    Extract just the possessive owner from a text fragment.
    "Hilton Hotels' automation strategy" → "Hilton Hotels"
    Returns None if no possessive found.
    """
    from app.services.company_validator import is_valid_lead
    m = _POSSESSIVE.match(text.strip())
    if not m:
        return None
    owner = m.group(1).strip().rstrip("'")
    valid, _ = is_valid_lead(owner)
    return owner if valid else None
