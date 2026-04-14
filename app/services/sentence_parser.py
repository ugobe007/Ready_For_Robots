"""
sentence_parser.py
==================
Parses news headlines using the full grammatical model:

  SENTENCE COMPONENTS
  ───────────────────
  Subject   — the performer of the action (the ACTOR / company)
  Predicate — the verb phrase (what the subject does)
  Direct Object  — the noun that receives the action (what is being deployed/bought/built)
  Indirect Object — the noun that receives the direct object (who benefits)
  Modifiers — adjectives/adverbs/phrases that describe, but are NOT actors

  CLAUSE TYPES
  ────────────
  Independent clause — complete sentence on its own; contains the ACTOR
  Dependent / subordinate clause — adds context; introduced by a subordinating
      conjunction (because, since, although, unless, while, when, after, …)
      A dependent clause has a subject and verb but CANNOT stand alone.

  SENTENCE STRUCTURE TYPES
  ────────────────────────
  Simple          : 1 independent clause
      "Hilton Hotels deploys robots."
       └─ actor = Hilton Hotels

  Compound        : 2+ independent clauses joined by FANBOYS (for, and, nor,
                    but, or, yet, so) or a semicolon
      "Amazon expands its fleet, but Walmart scales back."
       └─ actors = [Amazon, Walmart]

  Complex         : 1 independent + 1+ subordinate clauses
      "Because labor costs are rising, Hilton Hotels is deploying robots."
       └─ subordinate = "Because labor costs are rising"   (NOT the actor)
       └─ independent = "Hilton Hotels is deploying robots" → actor = Hilton Hotels

  Compound-Complex: 2+ independent + 1+ subordinate clauses
      "Although demand fell, Amazon expanded and Walmart restructured."
       └─ subordinate = "Although demand fell"
       └─ independent₁ = "Amazon expanded"   → actor = Amazon
       └─ independent₂ = "Walmart restructured" → actor = Walmart

  KEY RULE (Subject-Verb-Object order)
  ─────────────────────────────────────
  Standard English word order:  Subject → Verb → (Indirect Object) → Direct Object

  The parser:
    1. Strips leading dependent clauses (introduced by subordinating conjunctions)
    2. Splits on FANBOYS to separate independent clauses
    3. For each independent clause: uses find_verb_phrase() to locate the predicate,
       then extracts subject (before verb) and direct object (after verb)
    4. Validates subject as a real company via is_valid_lead()

Public API
──────────
  parse_headline(text) -> ParsedHeadline
      Full parse: returns subjects, predicates, direct objects, and sentence type.

  extract_actors(text) -> List[str]
      Returns all validated company actors found in the headline.

  extract_svo(clause) -> Optional[SVO]
      Extracts (Subject, Verb-lemma, DirectObject) from a single independent clause.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from app.services.verb_conjugation import find_verb_phrase, NEWS_VERBS, lemmatize

# ─────────────────────────────────────────────────────────────────────────────
# SUBORDINATING CONJUNCTIONS
# These introduce DEPENDENT clauses. A clause starting with one of these is
# NOT an independent clause and does NOT contain the primary actor.
# ─────────────────────────────────────────────────────────────────────────────
SUBORDINATING_CONJUNCTIONS: frozenset = frozenset({
    # Causal
    "because", "since", "as", "so that", "in order that",
    # Concessive
    "although", "though", "even though", "even if", "while", "whereas",
    "despite", "in spite of",
    # Conditional
    "if", "unless", "provided", "provided that", "as long as",
    "in case", "only if", "whether",
    # Temporal
    "when", "whenever", "while", "before", "after", "until", "till",
    "as soon as", "once", "since", "now that",
    # Comparative / relative
    "than", "as", "just as",
    # Additional
    "where", "wherever", "how", "however",
    # Multi-word openers common in headlines
    "amid", "following", "despite", "given", "due to", "thanks to",
    "in light of", "on the back of", "in the wake of",
    "as a result of", "in response to",
})

# Single-word subordinating conjunctions for fast first-word check
_SUBORD_FIRST_WORDS: frozenset = frozenset({
    "because", "since", "although", "though", "while", "whereas",
    "if", "unless", "when", "whenever", "before", "after", "until",
    "till", "once", "where", "wherever", "how", "amid", "following",
    "despite", "given", "provided", "whether", "than",
})

# ─────────────────────────────────────────────────────────────────────────────
# COORDINATING CONJUNCTIONS (FANBOYS)
# Join two INDEPENDENT clauses → each clause can have its own actor.
# ─────────────────────────────────────────────────────────────────────────────
COORDINATING_CONJUNCTIONS: frozenset = frozenset({
    "for", "and", "nor", "but", "or", "yet", "so",
})

# Regex to split on FANBOYS (preceded by comma or semicolon)
# "Amazon expands, but Walmart struggles" → ["Amazon expands", "Walmart struggles"]
_FANBOYS_SPLIT = re.compile(
    r"[;,]\s*(?:for|and|nor|but|or|yet|so)\s+",
    re.IGNORECASE,
)
# Split on bare coordinating conjunctions between clauses (no preceding comma)
# "Amazon Expanded and Walmart Restructured" → two clauses
# Only fires when the word after the conjunction is Title-Case (likely a new subject)
_BARE_FANBOYS_SPLIT = re.compile(
    r"\s+(?:and|but|nor|or|yet|so)\s+(?=[A-Z])",
)
# Also split on bare semicolons
_SEMICOLON_SPLIT = re.compile(r"\s*;\s*")

# ─────────────────────────────────────────────────────────────────────────────
# RELATIVE PRONOUNS — introduce relative (dependent) clauses
# "the distribution center, which Walmart owns, is automated"
# ─────────────────────────────────────────────────────────────────────────────
_RELATIVE_CLAUSE = re.compile(
    r",\s*(?:which|that|who|whom|whose|where|when)\b.*?,",
    re.IGNORECASE,
)
# Also handle non-restrictive relative clauses at end of string
_RELATIVE_CLAUSE_END = re.compile(
    r",\s*(?:which|that|who|whom|whose)\b.*$",
    re.IGNORECASE,
)

# ─────────────────────────────────────────────────────────────────────────────
# MODIFIER PATTERNS
# Adjective/adverb phrases that precede the subject in headlines:
#   "Giant hospitality firm Hilton Hotels deploys robots"
#   → modifier = "Giant hospitality firm", subject = "Hilton Hotels"
# ─────────────────────────────────────────────────────────────────────────────
_APPOSITIVE_DESCRIPTOR = re.compile(
    r"^(?:(?:giant|major|leading|top|global|national|regional|local|"
    r"struggling|growing|embattled|troubled|fast-growing|"
    r"publicly traded|privately held|family-owned|"
    r"new york-based|london-based|us-based|uk-based|china-based|"
    r"\w+-based)\s+)+"
    r"(?:company|firm|chain|corporation|group|operator|provider|"
    r"retailer|manufacturer|brand|startup|giant|conglomerate|"
    r"restaurant|hotel|airline|carrier|logistics|"
    r"player|leader|specialist|pioneer)\s+",
    re.IGNORECASE,
)

# ─────────────────────────────────────────────────────────────────────────────
# DATA CLASSES
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class SVO:
    """Subject-Verb-Object triple extracted from a single clause."""
    subject: str                     # raw subject phrase (before verb)
    verb_lemma: str                  # lemmatized main verb
    direct_object: Optional[str]     # raw phrase after the verb (the "what")
    clause_text: str                 # original clause text


@dataclass
class ParsedHeadline:
    """Full parse result for a news headline."""
    sentence_type: str               # simple / compound / complex / compound-complex
    independent_clauses: List[str]   # list of independent clause texts
    subordinate_clauses: List[str]   # list of dependent clause texts
    svo_triples: List[SVO]           # SVO extractions from each independent clause
    actors: List[str]                # validated company names (subjects that pass is_valid_lead)
    direct_objects: List[str]        # what the actors are acting on


# ─────────────────────────────────────────────────────────────────────────────
# CLAUSE SPLITTING
# ─────────────────────────────────────────────────────────────────────────────

def _is_subordinate_opener(text: str) -> bool:
    """True if the clause begins with a subordinating conjunction."""
    first = text.strip().split()[0].lower().rstrip(",") if text.strip() else ""
    return first in _SUBORD_FIRST_WORDS


def _split_leading_subordinate(text: str) -> Tuple[Optional[str], str]:
    """
    If the headline leads with a dependent clause ("Because X, Y happens"),
    split at the first comma after the subordinate clause.

    Returns (dependent_clause, remainder) or (None, original_text).

    Examples
    --------
    "Because labor costs are rising, Hilton Hotels is deploying robots."
        → ("Because labor costs are rising", "Hilton Hotels is deploying robots.")

    "Although demand fell, Amazon expanded and Walmart restructured."
        → ("Although demand fell", "Amazon expanded and Walmart restructured.")

    "Hilton Hotels is deploying robots."
        → (None, "Hilton Hotels is deploying robots.")
    """
    text = text.strip()
    if not _is_subordinate_opener(text):
        return None, text

    # Find the comma that closes the subordinate clause
    comma_m = re.search(r",\s*", text)
    if not comma_m:
        return None, text  # No comma → can't split cleanly

    dep = text[:comma_m.start()].strip()
    main = text[comma_m.end():].strip()
    return dep, main


def _strip_relative_clauses(text: str) -> str:
    """
    Remove embedded relative clauses to simplify the sentence.
    "The center, which Amazon owns, is automated." → "The center is automated."
    """
    text = _RELATIVE_CLAUSE.sub(",", text)
    text = _RELATIVE_CLAUSE_END.sub("", text)
    return text.strip()


def _strip_leading_modifier(text: str) -> str:
    """
    Remove appositive descriptor phrases preceding the subject.
    "Leading logistics firm Amazon expands its fleet"
    → "Amazon expands its fleet"
    """
    m = _APPOSITIVE_DESCRIPTOR.match(text)
    if m:
        return text[m.end():].strip()
    return text


def split_into_clauses(text: str) -> Tuple[List[str], List[str]]:
    """
    Split a headline into independent and subordinate clauses.

    Returns (independent_clauses, subordinate_clauses).

    Handles:
      Simple:          ["Hilton Hotels deploys robots"]
      Compound:        ["Amazon expands", "Walmart contracts"]
      Complex:         sub=["Because costs rose"], ind=["Hilton Hotels deploys robots"]
      Compound-complex: sub=["Although demand fell"],
                        ind=["Amazon expanded", "Walmart restructured"]
    """
    text = text.strip().rstrip(".")
    subordinates: List[str] = []
    independents: List[str] = []

    # Step 1: Peel off leading subordinate clause
    dep, remainder = _split_leading_subordinate(text)
    if dep:
        subordinates.append(dep)
        text = remainder

    # Step 2: Strip embedded relative clauses from the remainder
    text = _strip_relative_clauses(text)

    # Step 3: Split remainder on FANBOYS or semicolons → multiple independent clauses
    parts = _FANBOYS_SPLIT.split(text)
    if len(parts) == 1:
        parts = _SEMICOLON_SPLIT.split(text)
    # Step 3b: If still one part, try bare conjunction split (no preceding comma)
    # "Amazon Expanded and Walmart Restructured" → verify both halves have verb phrases
    if len(parts) == 1:
        bare_parts = _BARE_FANBOYS_SPLIT.split(text)
        if len(bare_parts) > 1:
            # Only accept if each part contains a verb phrase (avoids splitting "VP and NP" objects)
            all_have_vp = all(find_verb_phrase(p.strip()) is not None for p in bare_parts if p.strip())
            if all_have_vp:
                parts = bare_parts

    for part in parts:
        part = part.strip()
        if not part:
            continue
        # Each part may itself be a subordinate (rare, but possible)
        if _is_subordinate_opener(part):
            subordinates.append(part)
        else:
            part = _strip_leading_modifier(part)
            if part:
                independents.append(part)

    if not independents and text:
        independents = [text]

    return independents, subordinates


# ─────────────────────────────────────────────────────────────────────────────
# SVO EXTRACTION
# ─────────────────────────────────────────────────────────────────────────────

def extract_svo(clause: str) -> Optional[SVO]:
    """
    Extract the Subject-Verb-Object triple from a single independent clause.

    Subject    = text before the verb phrase start
    Verb       = lemmatized main verb from find_verb_phrase()
    DirectObject = text after the verb phrase end (what's being acted on)

    Returns None if no verb phrase found.
    """
    from app.services.headline_parser import _clean_subject  # avoid circular at module level

    text = clause.strip()
    vp = find_verb_phrase(text)
    if vp is None:
        return None

    vp_start, vp_end, lemma = vp

    raw_subject = text[:vp_start]
    raw_subject = _clean_subject(raw_subject)

    raw_object = text[vp_end:].strip().lstrip(",;:-— ")
    # Stop at coordinating conjunction — "Expanded and Walmart Restructured"
    # The object is only the first noun phrase, not the rest of the sentence
    raw_object = re.split(
        r"\s+(?:and|but|nor|or|yet|so)\s+(?=[A-Z])",
        raw_object,
    )[0].strip()
    # Trim leading "to", "of", "its", "their", "a", "the" from object
    raw_object = re.sub(
        r"^(?:to|of|its|their|his|her|a|an|the|into|for|with|by)\s+",
        "",
        raw_object,
        flags=re.IGNORECASE,
    ).strip()

    return SVO(
        subject=raw_subject,
        verb_lemma=lemma,
        direct_object=raw_object if raw_object else None,
        clause_text=text,
    )


# ─────────────────────────────────────────────────────────────────────────────
# MAIN PARSE FUNCTION
# ─────────────────────────────────────────────────────────────────────────────

def parse_headline(text: str) -> ParsedHeadline:
    """
    Full parse of a news headline.

    1. Detect and separate dependent clauses.
    2. Split independent clauses (FANBOYS / semicolons).
    3. For each independent clause, extract SVO.
    4. Validate subjects as real companies.
    5. Determine sentence structure type.
    """
    from app.services.company_validator import is_valid_lead

    independents, subordinates = split_into_clauses(text)

    svo_triples: List[SVO] = []
    actors: List[str] = []
    direct_objects: List[str] = []

    for clause in independents:
        svo = extract_svo(clause)
        if svo is None:
            continue
        svo_triples.append(svo)
        if svo.subject:
            valid, _ = is_valid_lead(svo.subject)
            if valid:
                actors.append(svo.subject)
        if svo.direct_object:
            direct_objects.append(svo.direct_object)

    # Determine sentence structure type
    n_ind = len(independents)
    n_sub = len(subordinates)
    if n_sub == 0 and n_ind <= 1:
        sentence_type = "simple"
    elif n_sub == 0 and n_ind > 1:
        sentence_type = "compound"
    elif n_sub > 0 and n_ind <= 1:
        sentence_type = "complex"
    else:
        sentence_type = "compound-complex"

    return ParsedHeadline(
        sentence_type=sentence_type,
        independent_clauses=independents,
        subordinate_clauses=subordinates,
        svo_triples=svo_triples,
        actors=actors,
        direct_objects=direct_objects,
    )


def extract_actors(text: str) -> List[str]:
    """
    Convenience wrapper — returns all validated company actors from a headline.
    Handles simple, compound, complex, and compound-complex sentences.
    """
    result = parse_headline(text)
    return result.actors
