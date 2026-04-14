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
# PRONOUN / DEMONSTRATIVE SUBJECTS
# When the subject of the main clause is a pronoun, there is no company actor.
#
#   "This is the most awesome way to automate frying potatoes."
#    └─ subject = "This"  → pronoun → no actor extractable
#
#   "It is becoming the standard in packaging automation."
#    └─ subject = "It"    → pronoun → no actor
#
#   "Here's how to automate your warehouse."
#    └─ subject = "Here"  → placeholder → no actor
# ─────────────────────────────────────────────────────────────────────────────
_PRONOUN_SUBJECTS: frozenset = frozenset({
    # Personal pronouns
    "i", "we", "you", "he", "she", "it", "they",
    # Demonstrative pronouns
    "this", "that", "these", "those",
    # Existential / placeholder
    "here", "there", "everything", "something", "nothing", "anything",
    # Indefinite
    "one", "someone", "anyone", "everyone", "nobody", "somebody",
    # Interrogative openers
    "what", "why", "how", "when", "where", "who", "which",
})

# ─────────────────────────────────────────────────────────────────────────────
# INFINITIVE AUTOMATION TRAP
# "automate" (and similar) appearing ONLY in an infinitive phrase ("to automate X")
# is NOT a genuine buyer signal — it's a descriptor of a method/way/solution.
#
#   "This is the most awesome way to automate frying potatoes."
#    └─ "automate" is part of "to automate" → infinitive → NOT a buyer verb
#
#   "Hilton Hotels Is Deploying Automation Technology"
#    └─ "automate/automation" is the OBJECT — the company is the actor ✓
#
# We flag text that contains automation words ONLY in infinitive position so the
# signal ranker can discount the score appropriately.
# ─────────────────────────────────────────────────────────────────────────────
_INFINITIVE_AUTOMATION_RE = re.compile(
    r"\bto\s+(?:automate|deploy|implement|adopt|use|leverage|integrate|"
    r"digitize|optimize|modernize|streamline|transform)\b",
    re.IGNORECASE,
)

# Editorial / how-to / listicle openers — headline is content, not a buyer signal
_EDITORIAL_OPENER_RE = re.compile(
    r"^(?:"
    r"here(?:'s|\s+is|\s+are)?\s+(?:how|why|what)|"       # "Here's how to..."
    r"how\s+to\s+|"                                         # "How to automate..."
    r"why\s+(?:you\s+)?(?:should|need|must|want)|"         # "Why you should automate"
    r"\d+\s+(?:ways?|tips?|steps?|reasons?|things?)\s+to|" # "5 ways to automate"
    r"the\s+(?:best|ultimate|complete|definitive|top)\s+(?:guide|way|ways?|method|approach)|"
    r"what\s+(?:is|are|you\s+need)|"                       # "What is automation?"
    r"(?:a|the)\s+(?:beginner'?s?|complete|quick)\s+guide|"
    r"(?:is|are|can|will|should|does|do)\s+"               # "Is automation right for...?"
    r"(?:automation|robots?|ai|technology|the\s+future)"
    r")",
    re.IGNORECASE,
)

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

    # ── Pronoun subject guard ────────────────────────────────────────────────
    # "This is the most awesome way to automate..." → subject = "This" → no actor
    if raw_subject.strip().lower() in _PRONOUN_SUBJECTS:
        return None

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


# ─────────────────────────────────────────────────────────────────────────────
# FALSE-SIGNAL CONTEXT DETECTORS
# Used by the signal ranker to avoid boosting scores for editorial/hyperbole.
# ─────────────────────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────────────────────
# COMPARATIVE SENTENCE MARKERS
# Companies mentioned AFTER these phrases are benchmarks, not buyers.
#
#   "McDonald's Big Mac will be the most efficient compared to Wendy's"
#    → "Wendy's" is a comparison target, not an actor
#
#   "if Lowe's improves automation … they will surpass Home Depot's goals"
#    → "Home Depot's goals" is a comparison target
# ─────────────────────────────────────────────────────────────────────────────
_COMPARATIVE_PHRASE_RE = re.compile(
    r"\b(?:"
    r"compared\s+to|"
    r"versus|vs\.?|"
    r"unlike|"
    r"relative\s+to|"
    r"surpass(?:ing|es|ed)?|"
    r"outperform(?:ing|s|ed)?|"
    r"ahead\s+of|"
    r"behind\s+(?:its|their|the)?|"
    r"better\s+than|"
    r"worse\s+than|"
    r"more\s+(?:efficient|competitive|productive)\s+than|"
    r"over\s+(?:its\s+)?(?:rivals?|competitors?|peers?)"
    r")\b",
    re.IGNORECASE,
)

# ─────────────────────────────────────────────────────────────────────────────
# CONDITIONAL / HYPOTHETICAL LANGUAGE
# The company is real but the action is speculative, not an actual deployment.
#
#   "if Lowe's improves their logistics automation … they will surpass …"
#    → conditional hypothesis, not a confirmed buyer signal
#
#   "Walmart could reduce labor costs by 30% through automation"
#    → modal verb = possibility, not committed action
#
#   "Home Depot's automation goals of 30%" — goal ≠ action
# ─────────────────────────────────────────────────────────────────────────────
_CONDITIONAL_OPENER_RE = re.compile(
    r"^if\s+\w",  # sentence starts with "if [word]"
    re.IGNORECASE,
)

_HYPOTHETICAL_LANGUAGE_RE = re.compile(
    r"(?:"
    # Sentence-opening "if <pronoun/generic> would/could…"
    r"\bif\s+(?:they|it|we|the\s+company|companies|retailers?)\s+(?:would|could|should)\b|"
    # Quantitative goals / targets — ends in %, so no trailing \b
    r"\bgoals?\s+of\s+\d+\s*%|"                  # "goals of 30%"
    r"\btargets?\s+(?:of\s+)?\d+\s*%|"           # "target of 50%"
    # Aims with numbers
    r"\baim(?:s|ing|ed)?\s+(?:to\s+)?(?:achieve|hit|reach)\s+\d|"
    # Modal verbs followed by competitive or cost-reduction verbs
    r"\b(?:would|could|might)\s+(?:surpass|outperform|exceed|beat|overtake|"
    r"reduce|save|cut|eliminate|lower|decrease|achieve|hit|reach)\b|"
    # Pure hypothetical markers
    r"\bhypothetical(?:ly)?\b|"
    r"\bin\s+theory\b"
    r")",
    re.IGNORECASE,
)


def has_comparative_context(text: str) -> bool:
    """
    Return True if the text contains comparison language that suggests companies
    are being used as benchmarks rather than as genuine automation buyers.

    Examples that return True:
      "McDonald's Big Mac will be most efficient compared to Wendy's and Burger King"
      "Lowe's wants to surpass Home Depot's automation rate"
      "Amazon's throughput vs. Walmart's logistics efficiency"

    Examples that return False (genuine buyer signals, no comparison):
      "Tyson Foods Deploys Robots Across 500 Plants"
      "Lowe's Is Expanding Its Automation Program"
    """
    return bool(_COMPARATIVE_PHRASE_RE.search(text))


def has_conditional_context(text: str) -> bool:
    """
    Return True if the text is a conditional / hypothetical sentence where the
    company action is speculative rather than confirmed.

    Examples that return True:
      "if Lowe's improves logistics automation … they will surpass Home Depot"
      "Walmart could reduce labor costs by 30% through automation"
      "The goals of 50% cost reduction through robotics"

    Examples that return False (confirmed actions):
      "Lowe's Is Expanding Its Automation Program"
      "Tyson Foods Plans to Automate Its Packaging Line"  ← planning is an action
    """
    if _CONDITIONAL_OPENER_RE.match(text):
        return True
    if _HYPOTHETICAL_LANGUAGE_RE.search(text):
        return True
    return False


def has_editorial_context(text: str) -> bool:
    """
    Return True if the text reads as editorial/how-to/listicle content rather
    than a genuine company action.  These texts may contain automation keywords
    but they describe methods, not buyer intent.

    Examples that return True:
      "This is the most awesome way to automate frying potatoes."
      "Here's how to automate your warehouse in 5 steps."
      "5 ways to use robots in food manufacturing."
      "The ultimate guide to packaging automation."
      "Why you should automate your distribution center."

    Examples that return False (real buyer signals):
      "Hilton Hotels Is Deploying Automation Technology."
      "Tyson Foods Seeks Automation Partners."
    """
    # Editorial opener patterns
    if _EDITORIAL_OPENER_RE.search(text):
        return True
    # Pronoun/demonstrative subject in the first clause
    first_words = text.strip().split()
    if first_words and first_words[0].lower().rstrip(",") in _PRONOUN_SUBJECTS:
        return True
    return False


def has_infinitive_only_automation(text: str) -> bool:
    """
    Return True if automation/robot keywords appear ONLY as part of infinitive
    phrases ("to automate X") rather than as the main predicate verb or object.

    "This is the most awesome way to automate frying potatoes."
      → "automate" is in "to automate" → True

    "Hilton Hotels Is Deploying Automation Technology"
      → "automation" is a noun in the direct object, not an infinitive → False

    "Tyson Foods Plans to Automate Its Packaging Line"
      → "to Automate" IS the infinitive, but "Tyson Foods" is the actor
        AND "plans" is the predicate → False (the company PLANS to automate)
    """
    # If there's a valid company actor and the automation is what they plan to do,
    # it IS a genuine buyer signal even if "to automate" appears.
    has_actor = bool(parse_headline(text).actors)
    has_infinitive_auto = bool(_INFINITIVE_AUTOMATION_RE.search(text))

    if not has_infinitive_auto:
        return False
    # If the text is editorial AND has infinitive automation → false signal
    if has_editorial_context(text):
        return True
    # If no company actor but has infinitive automation → likely descriptive
    if not has_actor and has_infinitive_auto:
        return True
    return False
