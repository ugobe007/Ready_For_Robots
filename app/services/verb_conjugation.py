"""
verb_conjugation.py
===================
Lightweight verb conjugation engine for news headline parsing.

Implements the linguistic model described by the user:
  - Person & Number: he/she/it → 3rd-person singular (-s/-es)
  - Tense: simple past (-ed), simple present, simple future (will + base)
  - Mood: indicative (most headlines), imperative (commands), progressive (-ing)
  - Regular vs Irregular: standard patterns plus an explicit irregular table

Primary use: find the VERB PHRASE in a headline so the subject (actor) can be
correctly separated from the predicate — regardless of tense or conjugation.

    "Walmart's Distribution Centers Turn Automated"
      → verb phrase: "Turn" (simple present, 3rd-person plural)
      → subject:     "Walmart's Distribution Centers"
      → actor:       "Walmart"  (possessive owner)

    "Hilton Hotels Is Targeting Automation"
      → verb phrase: "Is Targeting" (present progressive, 3rd-person singular)
      → subject:     "Hilton Hotels"
      → actor:       "Hilton Hotels"

    "Amazon Had Been Expanding Its Robotics Fleet"
      → verb phrase: "Had Been Expanding" (past perfect progressive)
      → subject:     "Amazon"
      → actor:       "Amazon"

Public API
----------
  lemmatize(word)               -> infinitive form of any conjugated verb
  is_auxiliary(word)            -> True if word is a pure auxiliary
  is_news_verb(word)            -> True if word is any form of a news-relevant verb
  find_verb_phrase(text)        -> (start, end, lemma) of first verb phrase, or None
"""
from __future__ import annotations

import re
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1 — AUXILIARY VERBS
# These do NOT carry the main action — they help form tense and mood.
# ─────────────────────────────────────────────────────────────────────────────

#  Copular / tense auxiliaries
_BE_FORMS: FrozenSet[str] = frozenset({
    "be", "am", "is", "are", "was", "were", "been", "being",
})
_HAVE_FORMS: FrozenSet[str] = frozenset({
    "have", "has", "had", "having",
})
_DO_FORMS: FrozenSet[str] = frozenset({
    "do", "does", "did", "doing",
})
# Modal auxiliaries — followed by bare infinitive
_MODALS: FrozenSet[str] = frozenset({
    "will", "would", "shall", "should",
    "can", "could", "may", "might", "must",
    "ought",  # "ought to"
})
# All auxiliaries combined
AUXILIARIES: FrozenSet[str] = _BE_FORMS | _HAVE_FORMS | _DO_FORMS | _MODALS


def is_auxiliary(word: str) -> bool:
    """Return True if word is a pure auxiliary verb."""
    return word.lower() in AUXILIARIES


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2 — IRREGULAR VERB TABLE
#
# Format: infinitive → frozenset of all irregular conjugated forms.
# Regular conjugated forms (+ -s, -ed, -ing) are handled by the rule engine.
# Only forms that DEVIATE from the regular rules need to appear here.
# ─────────────────────────────────────────────────────────────────────────────

IRREGULAR_VERBS: Dict[str, FrozenSet[str]] = {
    # Core irregulars
    "be":         frozenset({"am", "is", "are", "was", "were", "been", "being"}),
    "have":       frozenset({"has", "had", "having"}),
    "do":         frozenset({"does", "did", "done"}),
    "go":         frozenset({"goes", "went", "gone"}),
    "say":        frozenset({"says", "said"}),
    "make":       frozenset({"makes", "made"}),
    "take":       frozenset({"takes", "took", "taken"}),
    "come":       frozenset({"comes", "came"}),
    "give":       frozenset({"gives", "gave", "given"}),
    "know":       frozenset({"knows", "knew", "known"}),
    "think":      frozenset({"thinks", "thought"}),
    "become":     frozenset({"becomes", "became"}),
    "grow":       frozenset({"grows", "grew", "grown"}),
    "bring":      frozenset({"brings", "brought"}),
    "buy":        frozenset({"buys", "bought"}),
    "build":      frozenset({"builds", "built"}),
    "sell":       frozenset({"sells", "sold"}),
    "send":       frozenset({"sends", "sent"}),
    "begin":      frozenset({"begins", "began", "begun"}),
    "run":        frozenset({"runs", "ran"}),
    "hold":       frozenset({"holds", "held"}),
    "lead":       frozenset({"leads", "led"}),
    "lose":       frozenset({"loses", "lost"}),
    "fall":       frozenset({"falls", "fell", "fallen"}),
    "win":        frozenset({"wins", "won"}),
    "meet":       frozenset({"meets", "met"}),
    "rise":       frozenset({"rises", "rose", "risen"}),
    "speak":      frozenset({"speaks", "spoke", "spoken"}),
    "spend":      frozenset({"spends", "spent"}),
    "stand":      frozenset({"stands", "stood"}),
    "tell":       frozenset({"tells", "told"}),
    "write":      frozenset({"writes", "wrote", "written"}),
    "drive":      frozenset({"drives", "drove", "driven"}),
    "feel":       frozenset({"feels", "felt"}),
    "fight":      frozenset({"fights", "fought"}),
    "find":       frozenset({"finds", "found"}),
    "leave":      frozenset({"leaves", "left"}),
    "pay":        frozenset({"pays", "paid"}),
    "seek":       frozenset({"seeks", "sought"}),
    "show":       frozenset({"shows", "showed", "shown"}),
    "keep":       frozenset({"keeps", "kept"}),
    "choose":     frozenset({"chooses", "chose", "chosen"}),
    "draw":       frozenset({"draws", "drew", "drawn"}),
    "eat":        frozenset({"eats", "ate", "eaten"}),
    "fly":        frozenset({"flies", "flew", "flown"}),
    "freeze":     frozenset({"freezes", "froze", "frozen"}),
    "give":       frozenset({"gives", "gave", "given"}),
    "hide":       frozenset({"hides", "hid", "hidden"}),
    "hit":        frozenset({"hits"}),                        # hit/hit/hit
    "put":        frozenset({"puts"}),                        # put/put/put
    "set":        frozenset({"sets"}),                        # set/set/set
    "cut":        frozenset({"cuts"}),                        # cut/cut/cut
    "let":        frozenset({"lets"}),                        # let/let/let
    "read":       frozenset({"reads"}),                       # read/read/read
    "shut":       frozenset({"shuts"}),                       # shut/shut/shut
    "sleep":      frozenset({"sleeps", "slept"}),
    "strike":     frozenset({"strikes", "struck", "stricken"}),
    "teach":      frozenset({"teaches", "taught"}),
    "understand": frozenset({"understands", "understood"}),
    "lay":        frozenset({"lays", "laid"}),
    "sit":        frozenset({"sits", "sat"}),
    "lie":        frozenset({"lies", "lay", "lain"}),
    "break":      frozenset({"breaks", "broke", "broken"}),
    "catch":      frozenset({"catches", "caught"}),
    "bite":       frozenset({"bites", "bit", "bitten"}),
    "blow":       frozenset({"blows", "blew", "blown"}),
    "bear":       frozenset({"bears", "bore", "borne"}),
    "bind":       frozenset({"binds", "bound"}),
    "bleed":      frozenset({"bleeds", "bled"}),
    "breed":      frozenset({"breeds", "bred"}),
    "burn":       frozenset({"burns", "burnt", "burned"}),
    "deal":       frozenset({"deals", "dealt"}),
    "dig":        frozenset({"digs", "dug"}),
    "feed":       frozenset({"feeds", "fed"}),
    "flee":       frozenset({"flees", "fled"}),
    "forbid":     frozenset({"forbids", "forbade", "forbidden"}),
    "forget":     frozenset({"forgets", "forgot", "forgotten"}),
    "forgive":    frozenset({"forgives", "forgave", "forgiven"}),
    "get":        frozenset({"gets", "got", "gotten"}),
    "grind":      frozenset({"grinds", "ground"}),
    "hang":       frozenset({"hangs", "hung"}),
    "hear":       frozenset({"hears", "heard"}),
    "mean":       frozenset({"means", "meant"}),
    "overcome":   frozenset({"overcomes", "overcame"}),
    "ring":       frozenset({"rings", "rang", "rung"}),
    "see":        frozenset({"sees", "saw", "seen"}),
    "shine":      frozenset({"shines", "shone"}),
    "shoot":      frozenset({"shoots", "shot"}),
    "sing":       frozenset({"sings", "sang", "sung"}),
    "sink":       frozenset({"sinks", "sank", "sunk"}),
    "slide":      frozenset({"slides", "slid"}),
    "steal":      frozenset({"steals", "stole", "stolen"}),
    "stick":      frozenset({"sticks", "stuck"}),
    "sting":      frozenset({"stings", "stung"}),
    "swear":      frozenset({"swears", "swore", "sworn"}),
    "sweep":      frozenset({"sweeps", "swept"}),
    "swim":       frozenset({"swims", "swam", "swum"}),
    "swing":      frozenset({"swings", "swung"}),
    "tear":       frozenset({"tears", "tore", "torn"}),
    "throw":      frozenset({"throws", "threw", "thrown"}),
    "wake":       frozenset({"wakes", "woke", "woken"}),
    "wear":       frozenset({"wears", "wore", "worn"}),
    "weep":       frozenset({"weeps", "wept"}),
    "wind":       frozenset({"winds", "wound"}),
    "withdraw":   frozenset({"withdraws", "withdrew", "withdrawn"}),
    "withhold":   frozenset({"withholds", "withheld"}),
    "withstand":  frozenset({"withstands", "withstood"}),
    "undergo":    frozenset({"undergoes", "underwent", "undergone"}),
    "undertake":  frozenset({"undertakes", "undertook", "undertaken"}),
    "oversee":    frozenset({"oversees", "oversaw", "overseen"}),
    "forecast":   frozenset({"forecasts", "forecast"}),      # forecast/forecast/forecast
    "broadcast":  frozenset({"broadcasts", "broadcast"}),
    "outperform": frozenset({"outperforms", "outperformed"}),
    "outgrow":    frozenset({"outgrows", "outgrew", "outgrown"}),
}

# Build the reverse lookup: any_form → infinitive
_FORM_TO_LEMMA: Dict[str, str] = {}
for _inf, _forms in IRREGULAR_VERBS.items():
    _FORM_TO_LEMMA[_inf] = _inf          # infinitive maps to itself
    for _f in _forms:
        _FORM_TO_LEMMA[_f] = _inf


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3 — REGULAR CONJUGATION RULES
#
# Applied when the word is NOT in the irregular table.
# Rules follow English morphology:
#   Present 3rd-sg:  -s     (walks)     -es (watches)   -ies (flies)
#   Simple past:     -ed    (walked)    -ied (tried)     doubled consonant (stopped)
#   Present part.:   -ing   (walking)   doubled (running)   drop-e (making)
# ─────────────────────────────────────────────────────────────────────────────

def _try_candidates(*candidates: str) -> Optional[str]:
    """
    Return the first candidate that is a known news verb (infinitive in NEWS_VERBS).
    Falls back to the first candidate if none match (best-effort).
    NEWS_VERBS is referenced lazily to avoid forward-reference issues.
    """
    for c in candidates:
        if c and c in NEWS_VERBS:
            return c
    return candidates[0] if candidates else None


def _strip_regular_suffix(word: str) -> Optional[str]:
    """
    Given a word, attempt to strip a regular conjugation suffix and return the
    base (infinitive) form.  Returns None if no known suffix can be stripped.

    Core rules (English morphology):
      -ing  walk+ing  → walk  (simple)
            mak+e+ing → make  (drop-e: restore -e when consonant stem ≠ base)
            runn+ing  → run   (doubled consonant)
      -ed   walk+ed   → walk
            stopp+ed  → stop  (doubled consonant)
            announc+ed → announce  (restore -e)
            try+ied   → try   (-ied variant)
      -es   watch+es  → watch
            fly+ies   → fly   (-ies variant)
      -s    walk+s    → walk

    Key insight: try NEWS_VERBS lookup at each candidate to avoid adding
    spurious suffixes (e.g. "targeting" → stem="target" which IS in NEWS_VERBS,
    so return "target" directly — do NOT add "e" to get "targete").
    """
    w = word.lower()

    # ── -ing (present participle / gerund) ───────────────────────────────
    if w.endswith("ing") and len(w) > 5:
        stem = w[:-3]   # e.g. "targeting" → "target", "making" → "mak", "running" → "runn"

        # 1. Doubled consonant: running → run, planning → plan
        if (len(stem) >= 2 and stem[-1] == stem[-2]
                and stem[-1] not in "aeiou"):
            return stem[:-1]

        # 2. Stem is already a valid verb base: targeting → target ✓
        if stem in NEWS_VERBS or stem in _FORM_TO_LEMMA:
            return stem

        # 3. Drop-e restoration: making → mak+e = make
        #    Only add -e if stem ends in consonant and stem+e is a known verb.
        if stem and stem[-1] not in "aeiou":
            return _try_candidates(stem + "e", stem)

        return stem

    # ── -ied (past of -y verbs) ───────────────────────────────────────────
    if w.endswith("ied") and len(w) > 4:
        return w[:-3] + "y"      # tried → try, studied → study

    # ── -ed (simple past / past participle) ──────────────────────────────
    if w.endswith("ed") and len(w) > 4:
        stem = w[:-2]

        # 1. Doubled consonant: stopped → stop, planned → plan
        if (len(stem) >= 2 and stem[-1] == stem[-2]
                and stem[-1] not in "aeiou"):
            return stem[:-1]

        # 2. Stem already ends in -e (hoped → hope) or is a known verb
        if stem.endswith("e") or stem in NEWS_VERBS or stem in _FORM_TO_LEMMA:
            return stem

        # 3. Drop-e restoration: announced → announc → announce
        if stem and stem[-1] not in "aeiou":
            return _try_candidates(stem + "e", stem)

        return stem

    # ── -ies (3rd-person singular of -y verbs) ───────────────────────────
    if w.endswith("ies") and len(w) > 4:
        return w[:-3] + "y"      # flies → fly, tries → try

    # ── -es (3rd-person singular) ─────────────────────────────────────────
    if w.endswith("es") and len(w) > 4:
        stem_es = w[:-2]         # watches → watch, reaches → reach
        stem_s  = w[:-1]         # struggles → struggle (prefer -s strip if base is known verb)
        if stem_s in NEWS_VERBS or stem_s in _FORM_TO_LEMMA:
            return stem_s
        return stem_es

    # ── -s (3rd-person singular) ──────────────────────────────────────────
    if w.endswith("s") and len(w) > 3 and not w.endswith("ss"):
        return w[:-1]            # walks → walk, plans → plan

    return None


def lemmatize(word: str) -> str:
    """
    Convert any conjugated verb form to its infinitive.

    Priority:
      1. Irregular table lookup (exact match)
      2. Regular suffix stripping rules
      3. Return word as-is (already infinitive, or unknown)
    """
    w = word.lower().strip()
    if w in _FORM_TO_LEMMA:
        return _FORM_TO_LEMMA[w]
    stripped = _strip_regular_suffix(w)
    if stripped:
        return stripped
    return w


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4 — NEWS-RELEVANT VERB LEXICON
#
# The set of BASE (infinitive) verb forms that are meaningful in a business /
# news headline context.  Used to decide whether a given word (after
# lemmatization) is a "real" action word that anchors the sentence.
# ─────────────────────────────────────────────────────────────────────────────

NEWS_VERBS: FrozenSet[str] = frozenset({
    # Announcement / disclosure
    "announce", "launch", "unveil", "reveal", "introduce", "present",
    "release", "publish", "disclose", "confirm", "state", "acknowledge",
    "say", "report", "tell",

    # Corporate action
    "acquire", "merge", "partner", "invest", "fund", "back", "finance",
    "raise", "secure", "close", "land", "win", "sign", "ink",
    "sell", "divest", "exit", "spin", "spin-off",

    # Expansion / construction
    "expand", "open", "build", "deploy", "install", "roll", "launch",
    "break", "construct", "develop", "create", "establish",
    "grow", "scale", "accelerate",

    # Contraction / trouble
    "shut", "close", "cut", "slash", "trim", "downsize", "restructure",
    "layoff", "furlough", "freeze", "pause", "suspend", "cancel",
    "lose", "miss", "fall", "drop", "decline", "slip", "plunge",

    # Hiring / leadership
    "hire", "appoint", "name", "promote", "fire", "dismiss", "resign",

    # Strategy / change
    "target", "plan", "aim", "seek", "consider", "explore", "evaluate",
    "pilot", "test", "trial", "adopt", "integrate", "automate",
    "transform", "modernize", "digitize", "optimize", "upgrade",
    "pivot", "shift", "turn", "redefine", "reinvent", "overhaul",
    "navigate", "tackle", "address", "combat", "face", "brace",
    "struggle", "grapple", "confront",

    # Financial movement
    "surge", "soar", "spike", "climb", "rise", "gain",
    "plunge", "sink", "slide", "lose", "fall", "drop",
    "outperform", "beat", "exceed", "miss",

    # Operations
    "deploy", "install", "operate", "run", "manage", "lead",
    "deliver", "ship", "fulfill", "process", "produce", "manufacture",

    # Disruption / pressure
    "disrupt", "impact", "affect", "hit", "strain", "squeeze",
    "challenge", "threaten", "hamper", "hinder", "stall", "slow",
    # Regulation / compliance
    "fine", "sue", "file", "settle", "comply", "violate", "ban",

    # Partnership
    "partner", "collaborate", "team", "join", "engage", "work",

    # General news verbs
    "celebrate", "mark", "reach", "achieve", "complete", "finish",
    "begin", "start", "kick", "boost", "spur",
    "go", "come", "take", "make", "give", "get", "bring",
    "find", "understand", "become", "grow", "keep",
    "hit", "buy", "pay", "meet", "hold", "lead", "show",
    "draw", "drive", "feel", "fight", "leave", "seek",
})


def is_news_verb(word: str) -> bool:
    """Return True if word (any conjugated form) is a news-relevant verb."""
    return lemmatize(word.lower()) in NEWS_VERBS


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 5 — VERB PHRASE FINDER
#
# Finds the first VERB PHRASE in a headline text and returns its span.
# A verb phrase may be:
#   Simple:           "announces"       (present, 3rd-sg)
#   Aux + main:       "is targeting"    (present progressive)
#   Modal + main:     "will expand"     (simple future)
#   Perfect:          "has launched"    (present perfect)
#   Perf. prog.:      "has been building" (present perfect progressive)
#   Past perfect:     "had announced"
#   Past perf. prog.: "had been expanding"
#
# Returns: (start_idx, end_idx, lemma_of_main_verb) or None
# ─────────────────────────────────────────────────────────────────────────────

# Tokeniser: split into (word, start, end) triples preserving positions
_TOKEN_RE = re.compile(r"[A-Za-z']+")


def _tokenize(text: str) -> List[Tuple[str, int, int]]:
    """Return [(token, start, end), ...] preserving character offsets."""
    return [(m.group(), m.start(), m.end()) for m in _TOKEN_RE.finditer(text)]


def find_verb_phrase(text: str) -> Optional[Tuple[int, int, str]]:
    """
    Find the first verb phrase in `text`.

    Returns (phrase_start, phrase_end, main_verb_lemma) or None.

    The phrase_start is the character index of the first word of the phrase
    (which may be an auxiliary).  The subject occupies text[:phrase_start].

    Examples
    --------
    "Hilton Hotels Is Targeting Automation"
        tokens: Hilton(0) Hotels(7) Is(14) Targeting(17) Automation(27)
        → aux "Is" at 14, main "Targeting" → lemma "target"
        → returns (14, 26, "target")
        subject = text[:14].strip() = "Hilton Hotels"

    "Distribution Centers Turn to Automation"
        tokens: Distribution(0) Centers(13) Turn(21) to(26) Automation(29)
        → main "Turn" → lemma "turn"
        → returns (21, 25, "turn")
        subject = text[:21].strip() = "Distribution Centers"
        → "Distribution Centers" fails is_valid_lead → no actor

    "Amazon Had Been Expanding Its Robotics Fleet"
        → aux chain: Had + Been → main: Expanding → lemma "expand"
        → subject: "Amazon" → valid → actor = "Amazon"
    """
    tokens = _tokenize(text)
    n = len(tokens)

    for i, (word, start, end) in enumerate(tokens):
        w = word.lower()

        # ── Case A: auxiliary chain → find main verb ──────────────────────
        if w in AUXILIARIES:
            # Walk forward through aux chain, find first non-aux content word
            j = i + 1
            phrase_end = end
            main_lemma = None
            while j < n:
                nw, ns, ne = tokens[j]
                nwl = nw.lower()
                if nwl in AUXILIARIES:
                    j += 1
                    phrase_end = ne
                    continue
                # First non-aux word: must be a news verb (participle or base)
                candidate_lemma = lemmatize(nwl)
                if candidate_lemma in NEWS_VERBS:
                    main_lemma = candidate_lemma
                    phrase_end = ne
                break
            if main_lemma:
                return (start, phrase_end, main_lemma)
            # Aux not followed by news verb — not a verb phrase, keep scanning
            continue

        # ── Case B: modal → bare infinitive ───────────────────────────────
        # (modals are a subset of AUXILIARIES, handled above)

        # ── Case C: simple conjugated news verb ───────────────────────────
        lemma = lemmatize(w)
        if lemma in NEWS_VERBS and w not in AUXILIARIES:
            return (start, end, lemma)

    return None
