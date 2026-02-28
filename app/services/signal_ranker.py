"""
Signal Ranker
=============
Computes a weighted score for each signal based on:
  - Base signal strength (0-1)
  - Signal type weight (strategic hires > news)
  - Age decay (fresh signals score higher)
  - Robot relevance boost
  - Problem/pain-point identification boost
  - ROI / quantified impact boost
"""
import re
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Signal type weights — how strongly each type predicts a robot purchase
# ---------------------------------------------------------------------------
SIGNAL_TYPE_WEIGHTS: dict[str, float] = {
    "strategic_hire": 1.00,  # SVP/Dir of Automation = highest direct intent
    "capex":          0.95,  # committed capital spend
    "labor_shortage": 0.90,  # primary pain point robots solve
    "expansion":      0.85,  # new facility = new equipment opportunity
    "funding_round":  0.80,  # has capital + growth phase
    "ma_activity":    0.75,  # integration disruption creates openings
    "job_posting":    0.65,  # indirect but ongoing need
    "news":           0.45,  # awareness only
}
DEFAULT_TYPE_WEIGHT = 0.50

# ---------------------------------------------------------------------------
# Keyword regexes
# ---------------------------------------------------------------------------
ROBOT_RE = re.compile(
    r"\b(robot(?:ic)?s?|automat(?:e|ion|ing)|AGV|AMR|autonomous(?: mobile)?|"
    r"cobot|collaborative robot|conveyor|sortation|pick.to.light|"
    r"goods.to.person|AS[/]?RS|smart factory|industry 4\.0|"
    r"warehouse automat|fulfillment automat|machine vision|computer vision|"
    r"palletiz|depalletiz|pick.and.place|end.of.line|wearable exoskeleton)\b",
    re.IGNORECASE,
)

PROBLEM_RE = re.compile(
    r"\b(labor shortage|can.?t find|understaffed|turnover|vacancy|attrition|"
    r"overtime|absenteeism|temp worker|staffing crisis|scheduling gap|"
    r"wage inflation|workforce gap|high.*injury|worker.*injur)\b",
    re.IGNORECASE,
)

ROI_RE = re.compile(
    r"(\$\d+[\s]?[MBK]|million|billion|\d+\s*%\s*cost|cost\s*reduc|"
    r"\bROI\b|payback|efficiency gain|productivity.*increas|"
    r"\d+[\s-]year.*return|save.*per.*year|break.?even)",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Age decay table  (days → multiplier)
# ---------------------------------------------------------------------------
def _age_factor(created_at) -> float:
    if not created_at:
        return 0.75  # unknown age — moderate penalty
    now = datetime.now(timezone.utc)
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    age_days = max((now - created_at).days, 0)
    if age_days <= 7:
        return 1.00
    elif age_days <= 30:
        return 0.85
    elif age_days <= 90:
        return 0.70
    elif age_days <= 180:
        return 0.55
    else:
        return 0.40


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def compute_weighted_score(signal) -> float:
    """
    Returns a weighted score 0-100 for the given Signal ORM object.

    Formula
    -------
    weighted = base * type_weight * age_factor * robot_boost * problem_boost * roi_boost
    final    = min(weighted * 100, 100)
    """
    base = float(getattr(signal, "signal_strength", 0) or 0)
    signal_type = getattr(signal, "signal_type", None) or ""
    type_w = SIGNAL_TYPE_WEIGHTS.get(signal_type.lower(), DEFAULT_TYPE_WEIGHT)

    created_at = getattr(signal, "created_at", None)
    age_w = _age_factor(created_at)

    text = getattr(signal, "signal_text", "") or ""
    robot_boost   = 1.15 if ROBOT_RE.search(text) else 1.0
    problem_boost = 1.10 if PROBLEM_RE.search(text) else 1.0
    roi_boost     = 1.08 if ROI_RE.search(text) else 1.0

    weighted = base * type_w * age_w * robot_boost * problem_boost * roi_boost
    return round(min(weighted * 100, 100.0), 1)
