"""
Pythh-style signal rules engine (v1) — deterministic pipeline over raw text.

Architecture (spec-aligned):
  Raw text → sentence split → trigger scan (with negation windows) → modality /
  intensity / time / source → strength & confidence → optional multi-clause split.

Maps internal “Pythh” action labels to existing RFR ``signal_type`` strings so DB and
scrapers stay compatible. Timeline builder + matching engine live downstream (scores,
CRM, dashboard).

This is intentionally **non-LLM**: rule tables + windows, easy to extend and audit.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple
from urllib.parse import parse_qs, unquote, urlparse

# ── Category A: phrase → (internal action, RFR signal_type) ─────────────────
# Longer phrases first for greedy match (sorted at runtime).
ACTION_TRIGGERS: Tuple[Tuple[str, str, str], ...] = (
    # Executive moves — match before short tokens like "expansion" / "launching"
    ("chief operations officer", "talent_signal", "strategic_hire"),
    ("chief operating officer", "talent_signal", "strategic_hire"),
    ("chief executive officer", "talent_signal", "strategic_hire"),
    ("chief financial officer", "talent_signal", "strategic_hire"),
    ("chief technology officer", "talent_signal", "strategic_hire"),
    ("chief marketing officer", "talent_signal", "strategic_hire"),
    ("closing round", "fundraising_signal", "funding_round"),
    ("close round", "fundraising_signal", "funding_round"),
    ("closed round", "fundraising_signal", "funding_round"),
    ("data room", "investor_signal", "funding_round"),
    ("evaluating vendors", "buyer_signal", "vendor_selection"),
    ("evaluating vendor", "buyer_signal", "vendor_selection"),
    ("request for proposal", "buyer_signal", "vendor_selection"),
    ("request for proposals", "buyer_signal", "vendor_selection"),
    ("rfp", "buyer_signal", "vendor_selection"),
    ("rfq", "buyer_signal", "vendor_selection"),
    ("running pilot", "buyer_signal", "pilot_success"),
    ("pilot program", "buyer_signal", "pilot_success"),
    ("pilot ", "buyer_signal", "pilot_success"),
    ("partnership", "partnership_signal", "ma_activity"),
    ("partnering with", "partnership_signal", "ma_activity"),
    ("partner with", "partnership_signal", "ma_activity"),
    ("restructuring", "distress_signal", "news"),
    ("layoffs", "distress_signal", "labor_shortage"),
    ("launching", "product_signal", "expansion"),
    ("launched", "product_signal", "expansion"),
    ("expanding", "expansion_signal", "expansion"),
    ("expansion", "expansion_signal", "expansion"),
    ("new facility", "expansion_signal", "expansion"),
    ("new warehouse", "expansion_signal", "expansion"),
    ("opening office", "expansion_signal", "expansion"),
    ("opening new location", "expansion_signal", "expansion"),
    ("raising", "fundraising_signal", "funding_round"),
    ("raised", "fundraising_signal", "funding_round"),
    ("series a", "fundraising_signal", "funding_round"),
    ("series b", "fundraising_signal", "funding_round"),
    ("series c", "fundraising_signal", "funding_round"),
    ("funding round", "fundraising_signal", "funding_round"),
    ("venture capital", "fundraising_signal", "funding_round"),
    ("are hiring", "talent_signal", "strategic_hire"),
    ("now hiring", "talent_signal", "labor_shortage"),
    ("hiring", "talent_signal", "labor_shortage"),
    ("acquisition", "partnership_signal", "ma_activity"),
    ("merger", "partnership_signal", "ma_activity"),
    ("acquires", "partnership_signal", "ma_activity"),
    ("warehouse automation", "buyer_signal", "automation_interest"),
    ("kitchen automation", "buyer_signal", "automation_interest"),
    ("evaluate automation", "buyer_signal", "automation_interest"),
    ("automation pilot", "buyer_signal", "pilot_success"),
    ("proof of concept", "buyer_signal", "pilot_success"),
    ("automation roadmap", "buyer_signal", "automation_interest"),
    ("deploy robots", "buyer_signal", "robot_installation"),
    ("robot deployment", "buyer_signal", "robot_installation"),
    ("automation", "buyer_signal", "automation_interest"),
    ("robot", "buyer_signal", "automation_interest"),
)

# Standalone tokens need procurement/costly-action or industry anchor context.
_WEAK_STANDALONE_TRIGGERS = frozenset({"robot", "automation"})
_PROCUREMENT_OR_DEPLOY_MARKERS: Tuple[str, ...] = (
    "rfp",
    "vendor",
    "procurement",
    "pilot",
    "deploy",
    "deployment",
    "implement",
    "install",
    "evaluate",
    "proof of concept",
    "warehouse",
    "hotel",
    "hospital",
    "airport",
    "manufacturing",
    "logistics",
    "fulfillment",
    "restaurant",
)

# Category B: modality → weight contribution (certainty)
MODALITY_WEIGHTS: Dict[str, float] = {
    "planned": 0.15,
    "probable": 0.12,
    "exploratory": 0.06,
    "speculative": 0.02,
    "actual": 0.22,
    "active": 0.18,
}

MODALITY_PATTERNS: Tuple[Tuple[str, str], ...] = (
    (r"\bwill\b|\bplan to\b|\bplans to\b", "planned"),
    (r"\bexpect to\b|\bexpected to\b", "probable"),
    (r"\blooking to\b|\bexploring\b|\bconsidering\b", "exploratory"),
    (r"\bmay\b|\bmight\b|\bcould\b", "speculative"),
    (r"\blaunched\b|\bclosed\b|\bhired\b|\bopened\b|\bcompleted\b", "actual"),
    (r"\bare hiring\b|\bnow hiring\b|\bactively hiring\b", "active"),
)

# Category C: negation — if within N tokens before trigger, suppress or invert
NEGATION_TOKENS = frozenset(
    {
        "not",
        "no",
        "never",
        "n't",
        "without",
        "paused",
        "stopped",
        "discontinued",
    }
)
NEGATION_PHRASES = (
    "no longer",
    "not currently",
    "not actively",
    "not any",
    "doesn't",
    "don't",
    "didn't",
    "won't",
)
NEGATION_LOOKBACK_TOKENS = 5

# Category D: intensity
INTENSITY_ADJ: Dict[str, float] = {
    "strong": 0.12,
    "cautious": -0.04,
    "stealth": -0.06,
    "weak": -0.10,
}

INTENSITY_PATTERNS: Tuple[Tuple[str, str], ...] = (
    (r"\baggressively\b|\brapidly\b|\bheavily\b|\bsignificantly\b", "strong"),
    (r"\bselectively\b|\bcarefully\b", "cautious"),
    (r"\bquietly\b", "stealth"),
    (r"\bslowly\b", "weak"),
)

# Category F: time → urgency weight
TIME_WEIGHTS: Dict[str, float] = {
    "immediate": 0.15,
    "near_term": 0.12,
    "medium": 0.08,
    "long": 0.04,
    "recent_past": 0.06,
}

TIME_PATTERNS: Tuple[Tuple[str, str], ...] = (
    (r"\bnow\b|\bimmediately\b|\bright now\b", "immediate"),
    (r"\bthis quarter\b|\bthis month\b|\bsoon\b|\bin the coming months\b", "near_term"),
    (r"\bthis year\b|\bwithin the year\b", "medium"),
    (r"\bnext year\b|\bnext fiscal\b", "long"),
    (r"\brecently\b|\bjust announced\b", "recent_past"),
)

# Category G: source channel → reliability [0,1]
SOURCE_RELIABILITY: Dict[str, float] = {
    "sec_filing": 1.0,
    "earnings_call": 0.95,
    "press_release": 0.9,
    "job_posting": 0.85,
    "linkedin_founder": 0.8,
    "linkedin_employee": 0.7,
    "news_article": 0.7,
    "blog_post": 0.6,
    "podcast": 0.6,
    "rumor": 0.4,
    "anonymous": 0.3,
}


def infer_source_channel(url: str = "", rss_source: str = "") -> str:
    """
    Map article URL + RSS ``<source>`` label to a ``SOURCE_RELIABILITY`` key.

    Google News RSS links often wrap the publisher URL in a ``url=`` query param; we
    unwrap that when present so host-based rules apply (Pythh-style provenance).
    """
    u_raw = (url or "").strip()
    rs = (rss_source or "").strip().lower()
    u = u_raw.lower()

    if "news.google.com" in u and "url=" in u_raw:
        try:
            qs = parse_qs(urlparse(u_raw).query)
            inner = (qs.get("url") or [None])[0]
            if inner:
                u_raw = unquote(inner)
                u = u_raw.lower()
        except Exception:
            pass

    try:
        parsed = urlparse(u_raw)
        host = (parsed.netloc or "").lower()
        path = (parsed.path or "").lower()
    except Exception:
        host, path = "", ""

    blob = f"{host} {path} {rs}"

    if "sec.gov" in host or "/archives/edgar" in path:
        return "sec_filing"
    if "earnings-call" in path or "earnings_call" in path or "transcript" in path:
        return "earnings_call"
    if any(d in host for d in ("seekingalpha.com", "fool.com", "gurufocus.com")) and (
        "earnings" in blob or "transcript" in blob or "call" in path
    ):
        return "earnings_call"
    if any(
        d in host
        for d in (
            "prnewswire.com",
            "businesswire.com",
            "globenewswire.com",
            "newswire.com",
        )
    ):
        return "press_release"
    if "linkedin.com" in host:
        if re.search(r"/(in|posts|feed|pulse)/", path):
            return "linkedin_founder"
        return "linkedin_employee"
    if any(
        d in host
        for d in (
            "indeed.com",
            "glassdoor.com",
            "ziprecruiter.com",
            "greenhouse.io",
            "lever.co",
            "workday.com",
        )
    ):
        return "job_posting"
    if any(d in host for d in ("medium.com", "substack.com")) or ".blog." in host or host.startswith(
        "blog."
    ):
        return "blog_post"
    if any(
        d in host
        for d in (
            "spotify.com",
            "podcasts.apple.com",
            "libsyn.com",
            "buzzsprout.com",
        )
    ):
        return "podcast"
    if any(x in rs for x in ("blind", "rumor mill", "unverified")):
        return "rumor"

    return "news_article"


# Costly-action bonus (substring match in clause)
COSTLY_ACTION_MARKERS: Tuple[str, ...] = (
    "hiring",
    "opening office",
    "new location",
    "pilot",
    "rfp",
    "request for proposal",
    "data room",
    "purchase",
    "equipment",
    "manufacturing",
    "migrate",
    "migration",
)

# Multi-signal splitters (clause boundaries)
CLAUSE_SPLIT_REGEX = re.compile(
    r"(?<=[\.\!\?])\s+|\s*,\s*after\s+|\s+after\s+|\s+while\s+|\s+as we\s+|\s+following\s+|\s+then\s+|\s+also\s+|\s+in addition\b|\s+;\s+",
    re.IGNORECASE,
)

_SENT_SPLIT = re.compile(r"(?<=[\.\!\?])\s+")


@dataclass
class SignalDraft:
    """One rule-engine hit (pre-DB)."""

    clause: str
    trigger_phrase: str
    internal_action: str
    rfr_signal_type: str
    strength: float
    confidence: float
    ui_tier: str
    negated: bool = False
    modality: Optional[str] = None
    negation_note: Optional[str] = None


def split_sentences(text: str) -> List[str]:
    """Lightweight sentence split (no NLTK)."""
    if not text or not text.strip():
        return []
    parts = _SENT_SPLIT.split(text.strip())
    return [p.strip() for p in parts if p.strip()]


def split_clauses(sentence: str) -> List[str]:
    """Secondary split for multi-signal sentences."""
    if not sentence.strip():
        return []
    bits = CLAUSE_SPLIT_REGEX.split(sentence)
    return [b.strip() for b in bits if b.strip()]


def _tokenize_with_spans(lower: str) -> Tuple[List[str], List[int]]:
    """Tokens (alphanumeric) + start index of each token in ``lower``."""
    tokens: List[str] = []
    spans: List[int] = []
    for m in re.finditer(r"[a-z0-9]+(?:'[a-z]+)?", lower):
        tokens.append(m.group(0))
        spans.append(m.start())
    return tokens, spans


def _negation_before(lower: str, trigger_start: int) -> Tuple[bool, Optional[str]]:
    """True if a negation token/phrase appears within lookback window before trigger."""
    before = lower[:trigger_start]
    for phrase in NEGATION_PHRASES:
        idx = before.rfind(phrase)
        if idx != -1 and trigger_start - idx <= 80:
            return True, phrase
    tokens, spans = _tokenize_with_spans(before)
    if not tokens:
        return False, None
    # Map trigger_start to token index
    cut = len(tokens)
    for i, sp in enumerate(spans):
        if sp >= trigger_start:
            cut = i
            break
    window_start = max(0, cut - NEGATION_LOOKBACK_TOKENS)
    for j in range(window_start, cut):
        if tokens[j] in NEGATION_TOKENS or tokens[j].endswith("n't"):
            return True, tokens[j]
    return False, None


def _modality_for(lower: str) -> Optional[str]:
    for pat, label in MODALITY_PATTERNS:
        if re.search(pat, lower):
            return label
    return None


def _intensity_delta(lower: str) -> float:
    d = 0.0
    for pat, lab in INTENSITY_PATTERNS:
        if re.search(pat, lower):
            d += INTENSITY_ADJ.get(lab, 0.0)
    return d


def _time_weight(lower: str) -> float:
    for pat, lab in TIME_PATTERNS:
        if re.search(pat, lower):
            return TIME_WEIGHTS.get(lab, 0.0)
    return 0.0


def _costly_bonus(lower: str) -> float:
    return 0.2 if any(m in lower for m in COSTLY_ACTION_MARKERS) else 0.0


def _ambiguity_penalty(lower: str) -> float:
    if re.search(r"\bmight have\b|\ballegedly\b|\brumor\b|\bunconfirmed\b", lower):
        return 0.2
    if re.search(r"\bgame.?changer\b|\brevolutionary\b|\bworld.?class\b", lower):
        return 0.15
    return 0.0


def _promotional_penalty(lower: str) -> float:
    return 0.15 if re.search(r"\bbest\s+ever\b|\b#1\b|\bmarket leader\b", lower) else 0.0


def _score_to_ui_tier(score: float) -> str:
    if score >= 0.8:
        return "confirmed"
    if score >= 0.6:
        return "likely"
    if score >= 0.4:
        return "possible"
    if score >= 0.2:
        return "weak"
    return "noise"


def _find_triggers(lower: str) -> List[Tuple[str, str, str, int]]:
    """Return list of (matched_phrase, internal, rfr_type, start_index)."""
    hits: List[Tuple[str, str, str, int]] = []
    sorted_triggers = sorted(ACTION_TRIGGERS, key=lambda x: len(x[0]), reverse=True)
    used_ranges: List[Tuple[int, int]] = []

    def overlaps(a: int, b: int) -> bool:
        for s, e in used_ranges:
            if not (b <= s or a >= e):
                return True
        return False

    for phrase, internal, rfr in sorted_triggers:
        p = phrase.strip().lower()
        if re.fullmatch(r"[a-z0-9]+", p):
            for m in re.finditer(rf"\b{re.escape(p)}\b", lower):
                a, b = m.start(), m.end()
                if not overlaps(a, b):
                    hits.append((phrase, internal, rfr, a))
                    used_ranges.append((a, b))
        else:
            idx = lower.find(p)
            while idx != -1:
                end = idx + len(p)
                if not overlaps(idx, end):
                    hits.append((phrase, internal, rfr, idx))
                    used_ranges.append((idx, end))
                idx = lower.find(p, idx + 1)
    hits.sort(key=lambda x: x[3])
    return hits


def _compute_strength_and_confidence(
    clause_lower: str,
    modality: Optional[str],
    negated: bool,
    source_channel: str,
    actor_resolved: bool,
    object_resolved: bool,
    base_action_weight: float = 0.45,
) -> Tuple[float, float]:
    if negated:
        return 0.0, 0.35

    modality_w = MODALITY_WEIGHTS.get(modality or "exploratory", 0.08)
    strength = base_action_weight + modality_w
    strength += _intensity_delta(clause_lower)
    strength += _time_weight(clause_lower)
    strength += _costly_bonus(clause_lower)
    strength -= _ambiguity_penalty(clause_lower)
    strength -= _promotional_penalty(clause_lower)
    strength = max(0.0, min(1.0, strength))

    rel = SOURCE_RELIABILITY.get(source_channel, SOURCE_RELIABILITY["news_article"])
    confidence = 0.2 if actor_resolved else 0.0
    confidence += 0.2 if object_resolved else -0.1
    confidence += rel * 0.3
    confidence += modality_w * 0.3
    if source_channel in ("rumor", "anonymous"):
        confidence -= 0.3
    confidence -= _promotional_penalty(clause_lower)
    confidence = max(0.0, min(1.0, confidence))

    return strength, confidence


def extract_drafts_from_clause(
    clause: str,
    *,
    source_channel: str = "news_article",
    actor_resolved: bool = False,
    object_resolved: bool = False,
) -> List[SignalDraft]:
    """
    Run trigger + negation + modality + scoring on one clause.
    ``actor_resolved`` / ``object_resolved`` may be wired later (NER / entity pass).
    """
    if not clause.strip():
        return []

    lower = clause.lower()
    modality = _modality_for(lower)
    drafts: List[SignalDraft] = []

    for matched, internal, rfr, start in _find_triggers(lower):
        token = matched.strip().lower()
        if token in _WEAK_STANDALONE_TRIGGERS:
            has_context = (
                _costly_bonus(lower) > 0
                or any(m in lower for m in _PROCUREMENT_OR_DEPLOY_MARKERS)
            )
            if not has_context:
                continue
        neg, neg_note = _negation_before(lower, start)
        if neg and internal == "fundraising_signal":
            drafts.append(
                SignalDraft(
                    clause=clause.strip(),
                    trigger_phrase=matched,
                    internal_action=internal,
                    rfr_signal_type="news",
                    strength=0.15,
                    confidence=0.45,
                    ui_tier="weak",
                    negated=True,
                    modality=modality,
                    negation_note=neg_note or "negation",
                )
            )
            continue
        if neg:
            continue

        st, cf = _compute_strength_and_confidence(
            lower,
            modality,
            negated=False,
            source_channel=source_channel,
            actor_resolved=actor_resolved,
            object_resolved=object_resolved,
        )
        drafts.append(
            SignalDraft(
                clause=clause.strip(),
                trigger_phrase=matched,
                internal_action=internal,
                rfr_signal_type=rfr,
                strength=st,
                confidence=cf,
                ui_tier=_score_to_ui_tier(st),
                negated=False,
                modality=modality,
            )
        )

    return drafts


def extract_signal_drafts(
    text: str,
    *,
    source_channel: str = "news_article",
    actor_resolved: bool = False,
    object_resolved: bool = False,
) -> List[SignalDraft]:
    """
    Full pipeline: sentences → clauses → triggers → drafts.
    """
    out: List[SignalDraft] = []
    for sent in split_sentences(text):
        for clause in split_clauses(sent):
            out.extend(
                extract_drafts_from_clause(
                    clause,
                    source_channel=source_channel,
                    actor_resolved=actor_resolved,
                    object_resolved=object_resolved,
                )
            )
    return out


def drafts_to_rfr_signal_types(
    drafts: Sequence[SignalDraft],
    *,
    min_strength: float = 0.18,
) -> List[str]:
    """Map drafts to RFR ``signal_type`` strings (deduped, order preserved)."""
    seen = set()
    ordered: List[str] = []
    for d in drafts:
        if d.negated and d.internal_action == "fundraising_signal" and d.rfr_signal_type == "news":
            continue
        if d.strength < min_strength:
            continue
        if d.rfr_signal_type not in seen:
            seen.add(d.rfr_signal_type)
            ordered.append(d.rfr_signal_type)
    return ordered


def rules_engine_signal_types(
    text: str,
    *,
    source_channel: str = "news_article",
    min_strength: float = 0.18,
) -> List[str]:
    """Convenience: text → RFR signal types for merge with ontology."""
    drafts = extract_signal_drafts(
        text,
        source_channel=source_channel,
        actor_resolved=False,
        object_resolved=False,
    )
    return drafts_to_rfr_signal_types(drafts, min_strength=min_strength)
