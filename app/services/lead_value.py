"""
Lead value (deal quality) — distinct from raw intent / tier status.

Customers are multi-dimensional: large accounts with concrete specs, schedules, and
buying signals should outrank smaller accounts that are only "considering" automation.

This module **does not** score robot vendors (product-centric, comparatively 1-D).

Inputs are designed to **sound-test** against the same artifacts the CRM uses:
- ML scores (`Score` / overall_intent)
- `automation_profile` rules_v1 (deployment contexts, robot categories, applications, confidence)
- Firmographics (`employee_estimate`)
- Signal freshness (time decay weights aligned with `signal_quality.time_weight_for_signal`)
- **Procurement / timeline** cues in signal text (RFP, go-live, fiscal/quarter windows, near-term milestones)

Optional CRM copy: pass `extra_timeline_text` (e.g. notes synced from your CRM) into `compute_lead_value`
when you add a field later — same scorer, no schema migration required.

Tune weights in LEAD_VALUE_WEIGHTS after reviewing pipeline outcomes.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Set, Tuple

from app.services.signal_quality import time_weight_for_signal

# Intent + spec matter, but procurement clarity is its own axis (pythh-style decomposition).
LEAD_VALUE_WEIGHTS: Dict[str, float] = {
    "intent": 0.28,
    "firmographic": 0.18,
    "spec_richness": 0.28,
    "timing_freshness": 0.12,
    "procurement_timeline": 0.14,
}

# ── Procurement / schedule language (signal_text + optional CRM notes) ───────
_RE_RFP = re.compile(
    r"(?i)\b(rfp|rfq|rfi|request for (proposal|quote|information)|invitation to bid|itb\b|"
    r"solicitation|bid deadline|proposal due|submission deadline|vendor selection|award (date|timeline))\b",
)
_RE_GO_LIVE = re.compile(
    r"(?i)\b(go-?live|go live|production rollout|full rollout|phase\s*[23]\s*(deploy|rollout)|"
    r"implementation (schedule|timeline|window)|pilot (complete|ends|concludes)|scale to (production|fleet))\b",
)
_RE_QUARTER = re.compile(
    r"(?i)\b(q[1-4])\s*(?:fy)?\s*(20\d{2}|'\d{2})\b|"
    r"\b(fy|fiscal year)\s*20\d{2}\b|"
    r"\bby (?:end of )?(?:q[1-4]|first half|second half|h[12])\s*(?:20\d{2})?\b",
)
_RE_NEAR_TERM = re.compile(
    r"(?i)\b(within|in|over)\s*(the\s*)?(next\s*)?(\d{1,2})\s*(month|week)s?\b|"
    r"\b(this|next)\s+(quarter|fiscal year)\b|"
    r"\bby\s+(january|february|march|april|may|june|july|august|september|october|november|december)\s+20\d{2}\b",
)
_RE_CAPEX_PROJECT = re.compile(
    r"(?i)\b(capex|capital project|approved budget|board approval|"
    r"multi-?year (investment|program)|committed \$\d)\b",
)


def _signal_text_blob(signals: Optional[List[Any]]) -> str:
    parts: List[str] = []
    for s in signals or []:
        t = getattr(s, "signal_text", None) or getattr(s, "raw_text", None)
        if isinstance(t, str) and t.strip():
            parts.append(t)
        elif isinstance(s, dict):
            t2 = (s.get("raw_text") or s.get("signal_text") or "") or ""
            if isinstance(t2, str) and t2.strip():
                parts.append(t2)
    return " ".join(parts)


def _procurement_timeline_strength(
    signals: Optional[List[Any]],
    extra_timeline_text: Optional[str] = None,
) -> Tuple[float, List[str]]:
    """
    0–1 from explicit procurement / schedule language. Returns (score, hint tags).
    """
    blob = _signal_text_blob(signals)
    if extra_timeline_text and str(extra_timeline_text).strip():
        blob = f"{blob} {extra_timeline_text}".strip()

    if not blob.strip():
        return 0.42, []

    hints: Set[str] = set()
    score = 0.38

    if _RE_RFP.search(blob):
        hints.add("rfp_procurement")
        score += 0.24
    if _RE_GO_LIVE.search(blob):
        hints.add("go_live_milestone")
        score += 0.18
    if _RE_QUARTER.search(blob):
        hints.add("quarter_fy_window")
        score += 0.16
    if _RE_NEAR_TERM.search(blob):
        hints.add("near_term_horizon")
        score += 0.12
    if _RE_CAPEX_PROJECT.search(blob):
        hints.add("capex_committed")
        score += 0.10

    # Light bonus when several independent cues co-occur (structured buying motion)
    if len(hints) >= 3:
        score += 0.08
    elif len(hints) >= 2:
        score += 0.04

    return min(1.0, score), sorted(hints)


def _firmographic_strength(employee_estimate: Optional[int]) -> float:
    """0–1: larger operating entities often imply budget and project capacity."""
    if employee_estimate is None or employee_estimate <= 0:
        return 0.62
    e = int(employee_estimate)
    if e >= 10_000:
        return 0.98
    if e >= 5_000:
        return 0.92
    if e >= 1_000:
        return 0.82
    if e >= 200:
        return 0.68
    return 0.55


def _spec_richness(automation_profile: Optional[Dict[str, Any]]) -> float:
    """
    0–1 from rules_v1 profile: tag counts + confidence — proxies identified use-case / spec depth.
    """
    if not isinstance(automation_profile, dict):
        return 0.45
    dc = len(automation_profile.get("deployment_contexts") or [])
    rc = len(automation_profile.get("robot_categories") or [])
    aa = len(automation_profile.get("application_areas") or [])
    conf = (automation_profile.get("confidence") or "low").strip().lower()
    conf_map = {"high": 1.0, "medium": 0.74, "low": 0.48}
    base = conf_map.get(conf, 0.48)
    # Marginal value per tag; cap so industry-only seeds do not max the scale alone
    tag_score = min(1.0, 0.07 * float(dc + rc + aa))
    return min(1.0, 0.45 * base + 0.55 * max(base, tag_score))


def _timing_freshness(signals: Optional[List[Any]]) -> float:
    """0–1 mean time-decay weight across signal rows (missing created_at → full weight)."""
    sigs = list(signals or [])
    if not sigs:
        return 0.72
    weights = []
    for s in sigs:
        ts = getattr(s, "created_at", None)
        weights.append(time_weight_for_signal(ts))
    return sum(weights) / float(len(weights))


def compute_lead_value(
    overall_intent_0_100: float,
    employee_estimate: Optional[int],
    automation_profile: Optional[Dict[str, Any]],
    signals: Optional[List[Any]],
    extra_timeline_text: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Returns `lead_value_score` (0–100) and a `components` dict for CRM / debugging.

    overall_intent_0_100: stored ML score (already noise/time adjusted at inference).
    extra_timeline_text: optional free text (e.g. CRM opportunity notes) merged into procurement detection.
    """
    w = LEAD_VALUE_WEIGHTS
    intent_u = max(0.0, min(1.0, float(overall_intent_0_100) / 100.0))
    firm_u = _firmographic_strength(employee_estimate)
    spec_u = _spec_richness(automation_profile)
    time_u = _timing_freshness(signals)
    proc_u, proc_hints = _procurement_timeline_strength(signals, extra_timeline_text=extra_timeline_text)

    combined_0_1 = (
        w["intent"] * intent_u
        + w["firmographic"] * firm_u
        + w["spec_richness"] * spec_u
        + w["timing_freshness"] * time_u
        + w["procurement_timeline"] * proc_u
    )
    lv = max(0.0, min(100.0, round(combined_0_1 * 100.0, 1)))

    return {
        "lead_value_score": lv,
        "components": {
            "intent_strength": round(intent_u, 4),
            "firmographic_strength": round(firm_u, 4),
            "spec_richness": round(spec_u, 4),
            "timing_freshness": round(time_u, 4),
            "procurement_timeline": round(proc_u, 4),
        },
        "procurement_hints": proc_hints,
        "weights": dict(w),
    }
