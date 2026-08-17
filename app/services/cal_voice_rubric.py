"""Cal voice rubric — Stage 1 scoring for Research → Draft → Evaluate.

Scores Human / Insight / Relevance / Reasoning / Restraint / Conversation (1–5).
Accuracy is a separate pass/fail. Spec: docs/CAL_LEARNING_SYSTEM.md

Heuristic judge for Stage 1 (manual loop). Stage 2 may add LLM judge behind this API.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field

VOICE_DIMENSIONS = (
    "human",
    "insight",
    "relevance",
    "reasoning",
    "restraint",
    "conversation",
)

DEFAULT_VOICE_THRESHOLD = 24  # of 30


@dataclass
class CalRubricResult:
    human: int
    insight: int
    relevance: int
    reasoning: int
    restraint: int
    conversation: int
    accuracy_pass: bool
    accuracy_notes: list[str] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)
    suggested_rules: list[str] = field(default_factory=list)

    @property
    def voice_total(self) -> int:
        return (
            self.human
            + self.insight
            + self.relevance
            + self.reasoning
            + self.restraint
            + self.conversation
        )

    @property
    def voice_pass(self) -> bool:
        return self.voice_total >= DEFAULT_VOICE_THRESHOLD

    @property
    def approved(self) -> bool:
        return self.voice_pass and self.accuracy_pass

    def to_dict(self) -> dict:
        d = asdict(self)
        d["voice_total"] = self.voice_total
        d["voice_pass"] = self.voice_pass
        d["approved"] = self.approved
        d["threshold"] = DEFAULT_VOICE_THRESHOLD
        return d


_LABEL_STACK_RE = re.compile(
    r"(?m)^(?:[A-Z][A-Za-z0-9 /-]{2,40}\.\s*){3,}$"
)
_BILLBOARD_OPEN_RE = re.compile(
    r"(?i)^(in|across)\s+[\w\s/&-]{3,40},\s+(operational pressure|teams |the hours )"
)
_SLOGAN_MARKERS = (
    "quick field pattern",
    "vendor-neutral either way",
    "rings true",
    "if that rings true",
    "curiosity peer",
    "game changer",
    "unlock massive value",
)
_PRESCRIBE_EARLY = (
    "before recommending a platform",
    "before i'd recommend a platform",
    "i would recommend",
    "you should buy",
    "book a demo",
    "worth a quick call",
    "hand this to robert",
)
_INTRO_MARKERS = (
    "i'm cal with readyforrobots",
    "i am cal with readyforrobots",
    "this is cal",
    "i'm cal,",
    "i am cal,",
)
_RESEARCH_FRAME = (
    "i've been looking",
    "i keep noticing",
    "i noticed",
    "in my research",
    "while researching",
)
_CONVERSATION_MARKERS = (
    "i'm curious",
    "i'd be interested",
    "where do you see",
    "does that",
    "would it",
    "is it still",
    "what would you",
)
_CONNECTIVE_REASONING = (
    "involve",
    "create work",
    "filling the gaps",
    "fill the gaps",
    "because",
    "which means",
    "that usually",
    "those are often",
    "pressure seems",
    "day-to-day",
)


def _clamp(n: int) -> int:
    return max(1, min(5, int(n)))


def _body_only(draft: str) -> str:
    text = (draft or "").strip()
    if text.lower().startswith("subject:"):
        parts = text.split("\n\n", 1)
        return parts[1].strip() if len(parts) > 1 else text
    return text


def score_cal_draft(draft: str | None, *, company_hint: str | None = None) -> CalRubricResult:
    """Heuristic rubric score for a Cal draft (Stage 1 Evaluate)."""
    body = _body_only(draft or "")
    low = body.lower()
    issues: list[str] = []
    rules: list[str] = []
    accuracy_notes: list[str] = []

    # --- Human ---
    human = 3
    if any(m in low for m in _INTRO_MARKERS):
        human += 1
    else:
        human -= 1
        issues.append("Missing Cal introduction / familiarity assumed")
        rules.append("Cal establishes who he is before asking for attention.")
    if any(m in low for m in _RESEARCH_FRAME):
        human += 1
    if _BILLBOARD_OPEN_RE.search(body.split("\n\n")[1] if "\n\n" in body else body):
        human -= 2
        issues.append("Billboard industry opener")
        rules.append("No billboard openers — lead with research framing.")
    if any(m in low for m in _SLOGAN_MARKERS):
        human -= 2
        issues.append("Slogan / curiosity-theater phrasing")
        rules.append("No slogan fragments or curiosity theater.")
    if "deployment advisor" in low and "ready for robots" in low and "i'm cal with readyforrobots" not in low:
        # Old title-heavy close without plain identity is ok but not preferred for first touch
        human = min(human, 4)

    # --- Insight / Reasoning (label stacks kill both) ---
    insight = 3
    reasoning = 3
    if _LABEL_STACK_RE.search(body) or _looks_like_label_stack(body):
        insight -= 2
        reasoning -= 2
        issues.append("Label stack without relationships")
        rules.append("Cal connects observations; he does not stack labels.")
    connective = sum(1 for m in _CONNECTIVE_REASONING if m in low)
    if connective >= 2:
        insight += 1
        reasoning += 1
    elif connective == 0 and len(body) > 200:
        reasoning -= 1
        issues.append("Little connective reasoning between observations")

    # --- Relevance ---
    relevance = 3
    if company_hint and company_hint.strip():
        hint = company_hint.strip()
        try:
            from app.services.agent_messaging import _KNOWN_TEAM_SHORT, _short_label

            short = _KNOWN_TEAM_SHORT.get(hint.lower()) or _short_label(hint)
        except Exception:
            short = hint.split()[0]
        if (
            hint.lower() in low
            or (short and short.lower() in low)
            or (len(hint.split()) >= 1 and hint.split()[0].lower() in low)
        ):
            relevance += 1
        else:
            relevance -= 1
            issues.append("Company name/short label missing from body")
            rules.append("Cal researches the company/sector before discussing automation.")
    sectorish = any(
        k in low
        for k in (
            "distribution",
            "warehouse",
            "hospital",
            "hotel",
            "manufactur",
            "kitchen",
            "retail",
            "fulfillment",
            "picking",
            "receiving",
        )
    )
    if sectorish:
        relevance += 1
    else:
        relevance -= 1
        issues.append("Weak industry/operational specificity")

    # --- Restraint ---
    restraint = 4
    if any(m in low for m in _PRESCRIBE_EARLY):
        restraint -= 2
        issues.append("Premature prescription / meeting ask")
        rules.append("Cal earns the right to diagnose before prescribing.")
    if "rfq" in low or "book a demo" in low:
        restraint -= 1

    # --- Conversation ---
    conversation = 2
    if any(m in low for m in _CONVERSATION_MARKERS):
        conversation += 2
    if "?" in body:
        conversation += 1
    else:
        issues.append("No question for the reader")
        conversation -= 1
    if "i'd be interested in your perspective" in low or "i'm curious if that's true" in low:
        conversation = max(conversation, 4)

    # --- Accuracy (heuristic: flag inventy absolute claims) ---
    accuracy_pass = True
    if re.search(r"(?i)\byou are (definitely|clearly) (ready|overstaffed|understaffed)\b", low):
        accuracy_pass = False
        accuracy_notes.append("Absolute claim about the company without sourced evidence")
    if re.search(r"(?i)\$\d[\d,]*\s*(million|k\b|roi)", low) and "if" not in low:
        accuracy_notes.append("Numeric ROI-like claim — verify sourcing")
        # soft fail: note only unless clearly inventing
    if "we monitored" in low or "scraped list" in low:
        accuracy_pass = False
        accuracy_notes.append("Surveillance / list-broker framing")

    # Deduplicate rules
    seen: set[str] = set()
    unique_rules: list[str] = []
    for r in rules:
        if r not in seen:
            seen.add(r)
            unique_rules.append(r)

    return CalRubricResult(
        human=_clamp(human),
        insight=_clamp(insight),
        relevance=_clamp(relevance),
        reasoning=_clamp(reasoning),
        restraint=_clamp(restraint),
        conversation=_clamp(conversation),
        accuracy_pass=accuracy_pass,
        accuracy_notes=accuracy_notes,
        issues=issues,
        suggested_rules=unique_rules,
    )


def _looks_like_label_stack(body: str) -> bool:
    """Detect 'Receiving. Replenishment. Returns.' style paragraphs."""
    for para in body.split("\n\n"):
        p = para.strip()
        if not p or len(p) > 220:
            continue
        sentences = [s.strip() for s in re.split(r"(?<=\.)\s+", p) if s.strip()]
        if len(sentences) < 3:
            continue
        short = sum(1 for s in sentences if 2 <= len(s.split()) <= 5 and s.endswith("."))
        if short >= 3 and short >= len(sentences) - 1:
            return True
    return False


def format_rubric_report(result: CalRubricResult, *, title: str = "Cal voice rubric") -> str:
    lines = [
        f"{title}",
        f"  Voice total: {result.voice_total}/30  "
        f"{'PASS' if result.voice_pass else 'FAIL'} (need ≥{DEFAULT_VOICE_THRESHOLD})",
        f"  Accuracy:    {'PASS' if result.accuracy_pass else 'FAIL'}",
        f"  Approved:    {'YES' if result.approved else 'NO'}",
        "",
        "  Scores:",
    ]
    for dim in VOICE_DIMENSIONS:
        lines.append(f"    {dim:14} {getattr(result, dim)}/5")
    if result.issues:
        lines.append("")
        lines.append("  Issues:")
        for issue in result.issues:
            lines.append(f"    - {issue}")
    if result.accuracy_notes:
        lines.append("")
        lines.append("  Accuracy notes:")
        for note in result.accuracy_notes:
            lines.append(f"    - {note}")
    if result.suggested_rules:
        lines.append("")
        lines.append("  Suggested Cal rules:")
        for rule in result.suggested_rules:
            lines.append(f"    - {rule}")
    return "\n".join(lines)
