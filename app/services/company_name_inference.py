"""
Infer a proper company name from news-style signal text when the DB `name` is a headline.

Heuristic: leading Title Case fragment before common reporting verbs ("to", "announces", "kick off", …).
"""
from __future__ import annotations

import re
from typing import List, Optional, Sequence

# Title-case subject (1–7 tokens) then a reporting verb — validated separately so "to" is never captured.
_SUBJECT_THEN_TOKEN = re.compile(
    r"^([A-Z0-9][\w.&'’-]*(?:\s+[A-Z0-9][\w.&'’-]*){0,6})\s+(\S+)",
    re.UNICODE,
)

_REPORTING_VERB_PREFIXES = frozenset(
    (
        "to",
        "will",
        "would",
        "has",
        "have",
        "had",
        "is",
        "are",
        "was",
        "were",
        "announced",
        "announces",
        "announce",
        "launch",
        "launches",
        "launched",
        "launching",
        "said",
        "says",
        "reported",
        "reports",
        "reporting",
        "unveil",
        "unveils",
        "unveiled",
        "unveiling",
        "expand",
        "expands",
        "expanded",
        "acquire",
        "acquired",
        "acquires",
        "partner",
        "partners",
        "partnered",
        "sign",
        "signs",
        "signed",
        "open",
        "opens",
        "opened",
        "kick",
        "kicks",
        "begin",
        "begins",
        "beginning",
        "raise",
        "raises",
        "raised",
        "invest",
        "invests",
        "invested",
        "plan",
        "plans",
        "planned",
        "planning",
        "expect",
        "expects",
        "expected",
        "introduce",
        "introduces",
        "introduced",
        "introducing",
        "debut",
        "debuts",
        "debuted",
        "start",
        "starts",
        "started",
        "by",
        "establishes",
        "establish",
        "establishing",
        "complete",
        "completes",
        "completed",
        "completing",
        "unveiled",
        "reveal",
        "reveals",
        "revealed",
        "seeking",
        "seeks",
        "file",
        "files",
        "filed",
    )
)

# "Company Name — Subtitle" or em dash
_EMDASH_SUBJECT = re.compile(
    r"^([A-Z0-9][\w.&'’-]*(?:\s+[A-Z0-9][\w.&'’-]*){0,6})\s*[-–—]{1,3}\s+\S",
    re.UNICODE,
)


def _valid_company_candidate(name: str) -> bool:
    if not name or len(name) < 2 or len(name) > 120:
        return False
    words = name.split()
    if len(words) > 8:
        return False
    if len(words) < 1:
        return False
    # Reject if mostly lowercase (not a cleaned headline subject)
    if name == name.lower() and len(words) > 1:
        return False
    from app.services.lead_filter import is_junk

    bad, _ = is_junk(name)
    if bad:
        return False
    # Reject obvious sentence starters
    low = name.lower()
    if low.startswith(("the ", "a ", "an ", "this ", "these ", "why ", "how ", "what ", "when ")):
        if len(words) <= 2:
            return False
    return True


def _token_starts_reporting_verb(token: str) -> bool:
    if not token:
        return False
    # Strip leading punctuation (quotes, bullets)
    tok = re.sub(r"^[^\w]+", "", token).lower()
    if not tok:
        return False
    base = re.split(r"[^\w]", tok, 1)[0]
    if base in _REPORTING_VERB_PREFIXES:
        return True
    # Multi-word verbs scanned as one token e.g. "kick" only — "Kick" + next word "Off" handled below
    if tok.startswith("kick ") or tok.startswith("by "):
        return True
    return False


def extract_company_name_from_headline(text: str) -> Optional[str]:
    """Return a candidate company name parsed from one signal/article string, or None."""
    if not text or not str(text).strip():
        return None
    t = re.sub(r"<[^>]+>", " ", str(text))
    t = re.sub(r"\s+", " ", t).strip()
    if len(t) < 14:
        return None
    t = t.lstrip("[").strip()

    m = _SUBJECT_THEN_TOKEN.match(t[:500])
    if m:
        cand = m.group(1).strip()
        verb_tok = m.group(2)
        if _token_starts_reporting_verb(verb_tok):
            cand = re.sub(r"[\s\-–—:]+$", "", cand)
            if _valid_company_candidate(cand):
                return cand

    m2 = _EMDASH_SUBJECT.match(t[:500])
    if m2:
        cand = m2.group(1).strip()
        if _valid_company_candidate(cand):
            return cand

    return None


def best_name_from_signals(signal_texts: Sequence[str]) -> Optional[str]:
    """
    Try each signal text (longest first — usually richest headline); return first valid candidate.
    """
    texts = sorted((x for x in signal_texts if x and str(x).strip()), key=lambda x: len(x), reverse=True)
    for txt in texts[:12]:
        c = extract_company_name_from_headline(txt)
        if c:
            return c
    return None


def should_attempt_name_fix(current_name: Optional[str]) -> bool:
    """True when stored name is likely a full headline / sentence, not a company label."""
    if not current_name or not str(current_name).strip():
        return False
    n = str(current_name).strip()
    words = n.split()
    if len(words) >= 10:
        return True
    if len(n) >= 95:
        return True
    # PR verbs mid-string often mean the whole thing is a headline
    if re.search(
        r"\b(announces|launch(?:es)?|unveil|expand|acquire[sd]?|kick\s+off|to\s+kick\s+off)\b",
        n,
        re.I,
    ):
        return True
    return False
