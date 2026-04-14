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
    Main API.  Returns the FIRST validated company actor found in `headline`, or None.

    For headlines with multiple actors (compound sentences), use extract_actors().

    Processing pipeline — in priority order:
      1. Possessive:  "Walmart's Distribution Centers Turn" → "Walmart"
      2. Clause structure (sentence_parser):
           Complex:   "Because costs rose, Hilton Hotels deploys robots"
                       → skip subordinate, extract from independent → "Hilton Hotels"
           Compound:  "Amazon expands, but Walmart scales back"
                       → returns first actor: "Amazon"
           Simple:    "Hilton Hotels Is Targeting Automation"
                       → SVO extraction → subject = "Hilton Hotels"
      3. Raw verb-phrase fallback (single clause, no structure detected)
      4. Validate whole text as bare company name
    """
    from app.services.company_validator import is_valid_lead

    text = headline.strip()
    if not text or len(text) < 6:
        return None

    # ── Rule 1: Possessive ──────────────────────────────────────────────────
    poss_m = _POSSESSIVE.match(text)
    if poss_m:
        owner = poss_m.group(1).strip().rstrip("'")
        valid, _ = is_valid_lead(owner)
        if valid:
            return owner

    # ── Rule 2: Full clause-structure parse ─────────────────────────────────
    # Handles complex ("Because X, Company does Y"), compound ("A does X, but B does Y"),
    # and compound-complex sentences. Strips subordinate clauses, splits on FANBOYS,
    # and extracts SVO from each independent clause.
    from app.services.sentence_parser import parse_headline as _parse
    parsed = _parse(text)
    if parsed.actors:
        return parsed.actors[0]      # first validated actor

    # ── Rule 3: Verb phrase fallback for single-clause with no actor found ──
    # (e.g. generic subject before verb — already handled by sentence_parser,
    # but catch edge cases where clause splitting may have changed the text)
    vp = find_verb_phrase(text)
    if vp is not None:
        vp_start, _vp_end, _lemma = vp
        subject_phrase = _clean_subject(text[:vp_start])
        if not subject_phrase:
            return None
        # Pronoun subjects are never company actors ("They are disrupting…")
        from app.services.sentence_parser import _PRONOUN_SUBJECTS
        if subject_phrase.strip().lower() in _PRONOUN_SUBJECTS:
            return None
        valid, _ = is_valid_lead(subject_phrase)
        if valid:
            return subject_phrase
        return None   # generic subject → no actor; do NOT fall back to full title

    # ── Rule 4: No verb phrase — validate whole text as a bare company name ─
    valid, _ = is_valid_lead(text)
    return text if valid else None


def extract_actors(headline: str) -> list:
    """
    Returns ALL validated company actors from a headline.
    Useful for compound sentences: "Amazon expands, but Walmart struggles"
    → ["Amazon", "Walmart"]
    """
    from app.services.sentence_parser import extract_actors as _ea
    # Also check possessive as first-pass
    poss_m = _POSSESSIVE.match(headline.strip())
    if poss_m:
        from app.services.company_validator import is_valid_lead
        owner = poss_m.group(1).strip().rstrip("'")
        valid, _ = is_valid_lead(owner)
        if valid:
            return [owner]
    return _ea(headline)


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
