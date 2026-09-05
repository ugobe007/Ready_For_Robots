"""Tag and rank humanoid pilot language in buyer signals."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Optional, Sequence

from app.services.lead_filter import SELLER_OR_PUBLISHER_CONTEXT_RE

_HUMANOID_RE = re.compile(
    r"(?i)\b(humanoid(?:s)?|biped(?:al)?\s+robot|android\s+robot|"
    r"mobile\s+manipulator|general.?purpose\s+robot)\b"
)

_ACTIVE_PILOT_RE = re.compile(
    r"(?i)\b("
    r"humanoid.*(?:pilot(?:s|ing|ed)?|trial|deploy(?:ment|ed|ing)?|rollout|"
    r"production\s+line|assembly\s+line|factory\s+floor|warehouse\s+floor|"
    r"went\s+live|go-live|workcell|workforce\s+deployment)|"
    r"(?:pilot(?:s|ing|ed)?|trial|deploy(?:ment|ed|ing)?|rollout).{0,80}humanoid|"
    r"deploy(?:ing|ed)?\s+(?:\d+\s+)?humanoid"
    r")\b"
)

_PILOT_INTENT_RE = re.compile(
    r"(?i)\b("
    r"humanoid.*(?:evaluat(?:e|ing|ion)|rfp|rfq|procurement|vendor\s+selection|"
    r"poc|proof\s+of\s+concept|pilot\s+program|feasibility)|"
    r"(?:evaluat(?:e|ing|ion)|rfp|rfq|procurement|vendor\s+selection|"
    r"poc|proof\s+of\s+concept).{0,80}humanoid"
    r")\b"
)

_OEM_HUMANOID_ANNOUNCE_RE = re.compile(
    r"(?i)(?:\b(?:unveil(?:s|ed)?|introduc(?:e|es|ed)|launch(?:es|ed)?|debut(?:s|ed)?|"
    r"announc(?:e|es|ed)|reveal(?:s|ed)?)\b.*\bhumanoid\b"
    r"|\bhumanoid\b.*\b(?:unveil(?:s|ed)?|introduc(?:e|es|ed)|launch(?:es|ed)?|"
    r"debut(?:s|ed)?|announc(?:e|es|ed)|reveal(?:s|ed)?)\b)"
)

_TIER_ORDER = {
    "ACTIVE_PILOT": 0,
    "PILOT_INTENT": 1,
    "HUMANOID_MENTION": 2,
    "NONE": 9,
}

_TIER_LABELS = {
    "ACTIVE_PILOT": "Humanoid pilot live",
    "PILOT_INTENT": "Humanoid pilot forming",
    "HUMANOID_MENTION": "Humanoid signal",
    "NONE": "",
}

_TIER_ACTIONS = {
    "ACTIVE_PILOT": "Lead with a narrow humanoid workcell pilot — confirm ops owner and success metrics.",
    "PILOT_INTENT": "Qualify humanoid pilot scope — ask timeline, integrator, and first workflow.",
    "HUMANOID_MENTION": "Probe for humanoid pilot interest — one workflow, one site, one metric.",
    "NONE": "",
}


@dataclass
class HumanoidPilotAssessment:
    tier: str = "NONE"
    score: float = 0.0
    label: str = ""
    action: str = ""
    matched_phrases: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "humanoid_pilot_tier": self.tier if self.tier != "NONE" else None,
            "humanoid_pilot_score": round(self.score, 1) if self.score > 0 else None,
            "humanoid_pilot_label": self.label or None,
            "humanoid_pilot_action": self.action or None,
        }


def _signal_texts(signals: Sequence[Any]) -> list[str]:
    texts: list[str] = []
    for sig in signals or []:
        if isinstance(sig, dict):
            raw = sig.get("raw_text") or sig.get("signal_text") or sig.get("display_text") or ""
        else:
            raw = getattr(sig, "signal_text", None) or getattr(sig, "display_text", None) or ""
        text = str(raw or "").strip()
        if text:
            texts.append(text)
    return texts


def _signal_types(signals: Sequence[Any]) -> list[str]:
    types: list[str] = []
    for sig in signals or []:
        if isinstance(sig, dict):
            typ = sig.get("signal_type")
        else:
            typ = getattr(sig, "signal_type", None)
        if typ:
            types.append(str(typ))
    return types


def _is_oem_humanoid_story(blob: str) -> bool:
    if _OEM_HUMANOID_ANNOUNCE_RE.search(blob):
        if not _ACTIVE_PILOT_RE.search(blob) and not _PILOT_INTENT_RE.search(blob):
            return True
    if SELLER_OR_PUBLISHER_CONTEXT_RE.search(blob) and not re.search(
        r"(?i)\b(our\s+(?:plant|factory|warehouse|facility|hotel|airport)|"
        r"we\s+(?:are|will|plan\s+to)\s+(?:pilot|deploy|trial|evaluate))\b",
        blob,
    ):
        return True
    return False


def assess_humanoid_pilot_language(
    signals: Sequence[Any],
    *,
    industry: Optional[str] = None,
) -> HumanoidPilotAssessment:
    """Score buyer-side humanoid pilot language from signal rows."""
    texts = _signal_texts(signals)
    if not texts:
        return HumanoidPilotAssessment()

    blob = " ".join(texts)
    if not _HUMANOID_RE.search(blob):
        return HumanoidPilotAssessment()

    if _is_oem_humanoid_story(blob):
        return HumanoidPilotAssessment(
            tier="HUMANOID_MENTION",
            score=25.0,
            label="Humanoid OEM/news (verify buyer)",
            action="Confirm end-buyer vs vendor PR before outreach.",
            matched_phrases=[texts[0][:120]],
        )

    types = _signal_types(signals)
    score = 35.0
    matched: list[str] = []

    if _ACTIVE_PILOT_RE.search(blob):
        tier = "ACTIVE_PILOT"
        score = 88.0
        for text in texts:
            if _ACTIVE_PILOT_RE.search(text):
                matched.append(text[:140])
                break
    elif _PILOT_INTENT_RE.search(blob):
        tier = "PILOT_INTENT"
        score = 72.0
        for text in texts:
            if _PILOT_INTENT_RE.search(text):
                matched.append(text[:140])
                break
    else:
        tier = "HUMANOID_MENTION"
        score = 48.0
        matched.append(texts[0][:140])

    if "robot_installation" in types or "pilot_success" in types:
        score = min(100.0, score + 8.0)
    if industry and any(k in industry.lower() for k in ("logistics", "hospitality", "manufacturing", "healthcare", "airport", "automotive")):
        score = min(100.0, score + 4.0)

    return HumanoidPilotAssessment(
        tier=tier,
        score=score,
        label=_TIER_LABELS[tier],
        action=_TIER_ACTIONS[tier],
        matched_phrases=matched[:2],
    )


def humanoid_pilot_sort_key(lead: dict[str, Any]) -> tuple[int, float, float]:
    """Sort key: humanoid tier first, then pilot score, then priority score."""
    tier = str(lead.get("humanoid_pilot_tier") or "NONE").upper()
    pilot_score = float(lead.get("humanoid_pilot_score") or 0)
    priority = lead.get("priority_score")
    if not isinstance(priority, (int, float)):
        raw = lead.get("score")
        if isinstance(raw, dict):
            priority = raw.get("overall_score") or 0
        else:
            priority = raw or 0
    return (_TIER_ORDER.get(tier, 9), -pilot_score, -float(priority or 0))
