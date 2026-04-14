"""
headline_parser.py
==================
Extracts the ACTOR (the company that owns or performs an action) from a
news headline by applying three linguistic rules backed by a proper verb
conjugation engine (verb_conjugation.py):

  RULE 1 — Possessive → actor
      "Walmart's Distribution Centers Turn Automated"
       └─ possessive owner = "Walmart"  →  actor = "Walmart"

      "Hilton Hotels' restaurants are deploying robots"
       └─ possessive owner = "Hilton Hotels"  →  actor = "Hilton Hotels"

  RULE 2 — Verb phrase as anchor → subject / descriptor split
      Use find_verb_phrase() to locate the FIRST verb phrase regardless of:
        • Tense:    simple past/present/future
        • Person:   1st / 2nd / 3rd singular or plural
        • Number:   singular ("launches") or plural ("launch")
        • Mood:     indicative, progressive, perfect, perfect-progressive
        • Irregular: "went", "built", "had been expanding", "is targeting"

      Subject = text[:verb_phrase_start]

      Validate the subject:
        • Valid company name → return as actor
        • Generic phrase ("Distribution Centers", "German Companies") → None

  RULE 3 — No verb phrase found
      Validate whole text as a company name.  If it passes, return it.
      Otherwise return None.

  WHY CONJUGATION MATTERS HERE
      The old approach used regex stem-matching (deploy\w{0,6}) which:
        - Missed irregular past tenses: "went", "built", "had been expanding"
        - Incorrectly included auxiliary verbs in the subject span
          ("Marriott International Is [deploying]" → subject = "Marriott International Is")
        - Could not distinguish "is" (auxiliary in "is targeting") from "is"
          appearing as part of a company name

      The conjugation engine:
        - Maps any form to its infinitive: "went"→"go", "built"→"build",
          "securing"→"secure", "had been expanding"→"expand"
        - Understands auxiliary chains: "has been building" = aux+aux+main
        - Returns the START of the full verb phrase (including leading auxiliary)
          so the subject slice is clean

Public API
----------
  extract_actor(headline: str) -> Optional[str]
      Returns the company name of the actor, or None if none identified.

  possessive_owner(text: str) -> Optional[str]
      Extract the possessive owner from a text fragment, or None.
"""
from __future__ import annotations

import re
from typing import Optional

from app.services.verb_conjugation import find_verb_phrase, AUXILIARIES

# ─────────────────────────────────────────────────────────────────────────────
# Possessive patterns
# "Walmart's X"        → owner = "Walmart"
# "Hilton Hotels' X"   → owner = "Hilton Hotels"
# ─────────────────────────────────────────────────────────────────────────────
_POSSESSIVE = re.compile(
    r"^([A-Z][A-Za-z0-9\s&\.\-]{1,60}?)'\s*s?\s+",
)

# Small words that legitimately follow an owner in a possessive construction
# but should be stripped from the end of the subject phrase if they bleed in
_TRAILING_FUNCTION_WORDS = re.compile(
    r"\s+\b(is|are|was|were|has|have|had|will|would|can|could|should|"
    r"in|at|of|and|or|the|a|an|by|for|on|with|to|into|as|"
    r"now|also|still|already|just|recently|today|yesterday|"
    r"its|their|his|her|our|your)\b\s*$",
    re.IGNORECASE,
)


# Trailing prepositional phrase: "Distribution Centers in the Middle East [Are Facing…]"
# The core noun phrase is before the preposition — strip location/direction prep phrases.
_TRAILING_PREP_PHRASE = re.compile(
    r"\s+\b(in|at|of|across|throughout|within|near|from|between|among|"
    r"around|through|over|under|beyond|behind|above|below|along|"
    r"inside|outside|into|onto|upon)\b\s+.+$",
    re.IGNORECASE,
)


def _clean_subject(phrase: str) -> str:
    """
    Strip trailing function words / auxiliaries that bled into the subject
    because the verb phrase finder started at the main verb (not the aux).
    Also strips trailing prepositional phrases ("in the Middle East") so
    that "Distribution Centers in the Middle East" reduces to "Distribution Centers"
    before the is_valid_lead check.

    Applied iteratively until no more trailing words are removed.
    """
    prev = None
    text = phrase.strip().rstrip(",;:-—")
    while text != prev:
        prev = text
        text = _TRAILING_FUNCTION_WORDS.sub("", text).strip()
        text = _TRAILING_PREP_PHRASE.sub("", text).strip()
    return text


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
    # Must run BEFORE verb detection — the possessive 's is not a verb.
    poss_m = _POSSESSIVE.match(text)
    if poss_m:
        owner = poss_m.group(1).strip().rstrip("'")
        valid, _ = is_valid_lead(owner)
        if valid:
            return owner
        # Owner itself is generic ("Industry's X") → fall through to verb logic

    # ── Rule 2: Verb phrase anchor ─────────────────────────────────────────
    # find_verb_phrase understands all tenses, persons, numbers, moods.
    #
    # Example verb phrases and what they return:
    #   "Is Targeting"        → (start_of_Is, end_of_Targeting, "target")
    #   "Had Been Expanding"  → (start_of_Had, end_of_Expanding, "expand")
    #   "Announces"           → (start, end, "announce")
    #   "Went"                → (start, end, "go")       ← irregular past
    #   "Built"               → (start, end, "build")    ← irregular past
    vp = find_verb_phrase(text)
    if vp is not None:
        vp_start, _vp_end, _lemma = vp
        subject_phrase = text[:vp_start]
        subject_phrase = _clean_subject(subject_phrase)

        if not subject_phrase:
            # Verb phrase at very start ("Announces record results…") → no subject
            return None

        valid, _ = is_valid_lead(subject_phrase)
        if valid:
            return subject_phrase

        # Subject is generic (e.g. "Distribution Centers", "German Companies") →
        # this headline describes a category event, not a company action.
        # Return None explicitly — do NOT fall back to grabbing the title.
        return None

    # ── Rule 3: No verb phrase found ───────────────────────────────────────
    # Might be a bare company name, an appositive, or a title fragment.
    # Validate the whole text — return it only if it's a real company.
    valid, _ = is_valid_lead(text)
    if valid:
        return text
    return None


def possessive_owner(text: str) -> Optional[str]:
    """
    Extract just the possessive owner from a text fragment.
    "Hilton Hotels' automation strategy" → "Hilton Hotels"
    Returns None if no possessive found or owner fails validation.
    """
    from app.services.company_validator import is_valid_lead
    m = _POSSESSIVE.match(text.strip())
    if not m:
        return None
    owner = m.group(1).strip().rstrip("'")
    valid, _ = is_valid_lead(owner)
    return owner if valid else None
