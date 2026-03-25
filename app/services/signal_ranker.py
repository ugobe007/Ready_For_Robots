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
    "strategic_hire":      1.00,  # SVP/Dir of Automation = highest direct intent
    "capex":               0.95,  # committed capital spend
    "quality_bottleneck":  0.93,  # quality issues = immediate automation need
    "safety_incident":     0.92,  # safety problems = urgent automation driver
    "labor_shortage":      0.90,  # primary pain point robots solve
    "production_capacity": 0.88,  # maxed out capacity = automation to scale
    "warehouse_throughput":0.87,  # throughput constraints = clear ROI opportunity
    "packaging_automation":0.86,  # end-of-line packaging = proven robot use case
    "repetitive_process":  0.85,  # repetitive work = ideal for automation
    "expansion":           0.85,  # new facility = new equipment opportunity
    "material_handling":   0.83,  # forklift/logistics pain = AMR/AGV opportunity
    "funding_round":       0.80,  # has capital + growth phase
    "ma_activity":         0.75,  # integration disruption creates openings
    "job_posting":         0.65,  # indirect but ongoing need
    "news":                0.52,  # awareness — slightly less punishing for tiering context
}
DEFAULT_TYPE_WEIGHT = 0.55

# Age decay: (max_age_days_inclusive, multiplier). Gentler than before for older-but-valid signals.
SIGNAL_AGE_DECAY_BRACKETS = (
    (7, 1.00),
    (30, 0.88),
    (90, 0.75),
    (180, 0.60),
)
SIGNAL_AGE_DECAY_OLDEST_MULTIPLIER = 0.45
SIGNAL_AGE_UNKNOWN_MULTIPLIER = 0.80

# Multipliers when signal_text matches keyword patterns (stack multiplicatively)
SIGNAL_TEXT_BOOST_ROBOT = 1.15
SIGNAL_TEXT_BOOST_PROBLEM = 1.10
SIGNAL_TEXT_BOOST_ROI = 1.08

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
        return SIGNAL_AGE_UNKNOWN_MULTIPLIER
    now = datetime.now(timezone.utc)
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    age_days = max((now - created_at).days, 0)
    for max_days, mult in SIGNAL_AGE_DECAY_BRACKETS:
        if age_days <= max_days:
            return mult
    return SIGNAL_AGE_DECAY_OLDEST_MULTIPLIER


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
    robot_boost = SIGNAL_TEXT_BOOST_ROBOT if ROBOT_RE.search(text) else 1.0
    problem_boost = SIGNAL_TEXT_BOOST_PROBLEM if PROBLEM_RE.search(text) else 1.0
    roi_boost = SIGNAL_TEXT_BOOST_ROI if ROI_RE.search(text) else 1.0

    weighted = base * type_w * age_w * robot_boost * problem_boost * roi_boost
    return round(min(weighted * 100, 100.0), 1)
