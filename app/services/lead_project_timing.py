"""
Resolve sales-lead project timing from signals, CRM extraction, and inference dossiers.

Replaces static tier defaults (e.g. every HOT lead → "60 to 90 days") with
evidence-backed windows when the corpus mentions quarters, months, RFPs, or go-live dates.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence

from app.services.crm_extractor import _extract_timing

_RE_WITHIN_MONTHS = re.compile(
    r"(?i)\b(?:within|in|over)\s+(?:the\s+)?(?:next\s+)?(\d{1,2})\s+months?\b",
)
_RE_WITHIN_WEEKS = re.compile(
    r"(?i)\b(?:within|in|over)\s+(?:the\s+)?(?:next\s+)?(\d{1,2})\s+weeks?\b",
)
_RE_DAYS = re.compile(r"(?i)\b(\d{1,3})\s*(?:-|to)\s*(\d{1,3})?\s*days?\b")
_RE_THIS_NEXT = re.compile(r"(?i)\b(this|next)\s+(quarter|year|fiscal\s+year|half)\b")
_RE_Q = re.compile(r"\b(Q[1-4])\s*(20\d{2})?\b", re.I)
_RE_YEAR = re.compile(r"\b(20\d{2})\b")

# Sales outreach: ignore calendar mentions more than ~24 months out.
_MAX_TIMING_YEAR_OFFSET = 2


def _current_year() -> int:
    return datetime.now(timezone.utc).year


def _timing_horizon_acceptable(label: str) -> bool:
    """Reject bare or embedded years too far out for rep outreach windows."""
    lab = (label or "").strip()
    if not lab:
        return False
    if re.fullmatch(r"20\d{2}", lab, re.I):
        return int(lab) <= _current_year() + _MAX_TIMING_YEAR_OFFSET
    m = _RE_YEAR.search(lab)
    if m:
        return int(m.group(1)) <= _current_year() + _MAX_TIMING_YEAR_OFFSET
    return True


def _days_for_year_reference(year: int) -> tuple[Optional[int], Optional[int]]:
    """Map a near-term calendar year to an outreach day range from today."""
    now = datetime.now(timezone.utc)
    if year < now.year:
        return 30, 120
    if year == now.year:
        end = datetime(year, 12, 31, tzinfo=timezone.utc)
        days_left = max(30, (end - now).days)
        return max(14, days_left // 3), days_left
    if year == now.year + 1:
        return 120, 365
    if year == now.year + 2:
        return 240, 540
    return None, None


@dataclass
class ProjectTiming:
    label: str
    display_phrase: str
    source: str  # extracted | inference | estimated
    confidence: float
    day_min: Optional[int] = None
    day_max: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _timing_from_extracted_label(label: str, *, confidence: float = 0.85) -> ProjectTiming:
    lab = (label or "").strip()
    low = lab.lower()
    day_min: Optional[int] = None
    day_max: Optional[int] = None

    if re.fullmatch(r"20\d{2}", lab, re.I):
        year = int(lab)
        day_min, day_max = _days_for_year_reference(year)
        phrase_year = f"targeting {year}"
        if day_min and day_max:
            return ProjectTiming(
                label=phrase_year,
                display_phrase=f"Outreach window aligns with {phrase_year} (roughly {day_min}–{day_max} days).",
                source="extracted",
                confidence=confidence,
                day_min=day_min,
                day_max=day_max,
            )

    m = _RE_WITHIN_MONTHS.search(lab)
    if m:
        months = int(m.group(1))
        day_min = max(14, months * 25)
        day_max = months * 31
    else:
        m = _RE_WITHIN_WEEKS.search(lab)
        if m:
            weeks = int(m.group(1))
            day_min = max(7, weeks * 5)
            day_max = weeks * 7
        elif "this quarter" in low or "next quarter" in low:
            day_min, day_max = 30, 120
        elif "this year" in low or "next year" in low:
            day_min, day_max = 90, 365
        elif _RE_Q.search(lab):
            day_min, day_max = 60, 180
        else:
            ym = _RE_YEAR.search(lab)
            if ym:
                day_min, day_max = _days_for_year_reference(int(ym.group(1)))

    phrase = f"Outreach window looks like {lab}."
    if day_min and day_max:
        phrase = f"Outreach window is {lab} (roughly {day_min}–{day_max} days)."

    return ProjectTiming(
        label=lab,
        display_phrase=phrase,
        source="extracted",
        confidence=confidence,
        day_min=day_min,
        day_max=day_max,
    )


def _estimate_from_signals(
    signal_blob: str,
    signal_types: Sequence[str],
    *,
    tier: str,
    procurement_hints: Sequence[str],
    intent_score: float = 0,
    procurement_strength: float = 0,
) -> ProjectTiming:
    """Tier + signal-type heuristic when no explicit calendar language exists."""
    st = {t.lower() for t in signal_types if t}
    hints = {h.lower() for h in procurement_hints if h}

    if hints & {"rfp_procurement"} or st & {"rfp", "procurement"}:
        day_min, day_max = 30, 75
        label = "active procurement (est. 30–75 days)"
    elif hints & {"go_live_milestone", "near_term_horizon"}:
        day_min, day_max = 45, 120
        label = "near-term rollout (est. 45–120 days)"
    elif hints & {"quarter_fy_window"}:
        day_min, day_max = 60, 150
        label = "fiscal-quarter window (est. 60–150 days)"
    elif st & {"robot_installation", "pilot", "deployment"}:
        day_min, day_max = 60, 120
        label = "deployment in progress (est. 60–120 days)"
    elif st & {"capex", "funding_round", "expansion", "scale_expansion"}:
        day_min, day_max = 90, 210
        label = "capital program phase (est. 90–210 days)"
    elif st & {"strategic_hire", "automation_hiring"}:
        day_min, day_max = 120, 240
        label = "build-out phase (est. 120–240 days)"
    elif intent_score >= 85 or (tier or "").upper() == "HOT":
        day_min, day_max = 45, 120
        label = "high-intent window (est. 45–120 days)"
    elif intent_score >= 70 or (tier or "").upper() == "WARM":
        day_min, day_max = 90, 180
        label = "evaluation window (est. 90–180 days)"
    else:
        day_min, day_max = 120, 270
        label = "early exploration (est. 120–270 days)"

    if procurement_strength >= 0.55 and day_max > 90:
        day_max = min(day_max, 150)

    return ProjectTiming(
        label=label,
        display_phrase=f"The timing of the project is {day_min} to {day_max} days ({label}).",
        source="estimated",
        confidence=0.45 + min(0.25, procurement_strength * 0.3),
        day_min=day_min,
        day_max=day_max,
    )


def resolve_project_timing(
    *,
    tier: str = "COLD",
    crm_metadata: Optional[dict] = None,
    lead_inference: Optional[dict] = None,
    signal_blob: str = "",
    signal_types: Optional[Sequence[str]] = None,
    procurement_hints: Optional[Sequence[str]] = None,
    intent_score: float = 0,
    procurement_strength: float = 0,
) -> ProjectTiming:
    """
    Best available project timing for sales copy and API payloads.
    Priority: CRM top_window → inference timetable → regex on signals → estimate.
    """
    meta = crm_metadata if isinstance(crm_metadata, dict) else {}
    inf = lead_inference if isinstance(lead_inference, dict) else {}

    timing_block = meta.get("timing") if isinstance(meta.get("timing"), dict) else {}
    top = (timing_block.get("top_window") or "").strip()
    if top:
        return _timing_from_extracted_label(top, confidence=0.88)

    stored = meta.get("project_timing")
    if isinstance(stored, dict) and stored.get("label"):
        return ProjectTiming(
            label=str(stored["label"]),
            display_phrase=str(stored.get("display_phrase") or f"The timing of the project is {stored['label']}."),
            source=str(stored.get("source") or "inference"),
            confidence=float(stored.get("confidence") or 0.7),
            day_min=stored.get("day_min"),
            day_max=stored.get("day_max"),
        )

    tt = inf.get("timetable") if isinstance(inf.get("timetable"), dict) else {}
    window = (tt.get("window") or "").strip()
    if window:
        return _timing_from_extracted_label(window, confidence=0.82)

    sigs = tt.get("signals") if isinstance(tt.get("signals"), list) else []
    if sigs and isinstance(sigs[0], dict) and sigs[0].get("label"):
        return _timing_from_extracted_label(str(sigs[0]["label"]), confidence=0.78)

    blob = (signal_blob or "").strip()
    if blob:
        extracted = _extract_timing([(blob, "")])
        for hit in extracted:
            if not _timing_horizon_acceptable(hit.label):
                continue
            return _timing_from_extracted_label(hit.label, confidence=hit.confidence)

        m = _RE_DAYS.search(blob)
        if m:
            lo = int(m.group(1))
            hi = int(m.group(2)) if m.group(2) else lo
            return ProjectTiming(
                label=f"{lo}–{hi} days",
                display_phrase=f"The timing of the project is {lo} to {hi} days.",
                source="extracted",
                confidence=0.75,
                day_min=lo,
                day_max=hi,
            )

    return _estimate_from_signals(
        blob,
        signal_types or [],
        tier=tier,
        procurement_hints=procurement_hints or [],
        intent_score=intent_score,
        procurement_strength=procurement_strength,
    )


def merge_project_timing_into_crm_metadata(
    meta: dict,
    timing: ProjectTiming,
    *,
    lead_inference: Optional[dict] = None,
) -> dict:
    """Persist timing on crm_metadata without wiping other keys."""
    out = dict(meta or {})
    out["project_timing"] = timing.to_dict()
    tblock = dict(out.get("timing") or {})
    if timing.label and not tblock.get("top_window"):
        tblock["top_window"] = timing.label
    out["timing"] = tblock
    if lead_inference:
        out["lead_inference"] = lead_inference
    return out
