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
# Signal type weights — extended from Robot Automation Signal Ontology scoring guide.
# ---------------------------------------------------------------------------
SIGNAL_TYPE_WEIGHTS: dict[str, float] = {
    "automation_intent":   1.00,  # trigger expression / active automation decision
    "vendor_selection":    0.98,  # RFP/proposal/vendor-selection language
    "strategic_hire":      0.96,  # job title signal
    "capex":               0.92,  # CapEx / financial signal
    "expansion":           0.90,  # facility/expansion signal
    "quality_bottleneck":  0.88,  # quality issues = immediate automation need
    "safety_incident":     0.86,  # regulatory / safety pain
    "production_capacity": 0.84,  # maxed out capacity = automation to scale
    "warehouse_throughput":0.82,  # throughput constraints = clear ROI opportunity
    "job_posting":         0.80,  # active automation hiring
    "labor_shortage":      0.78,  # pain words with co-occurrence
    "packaging_automation":0.78,  # end-of-line packaging = proven robot use case
    "repetitive_process":  0.76,  # repetitive work = ideal for automation
    "material_handling":   0.75,  # forklift/logistics pain = AMR/AGV opportunity
    "funding_round":       0.72,  # has capital + growth phase
    "ma_activity":         0.75,  # integration disruption creates openings
    "automation_interest": 0.68,  # buying signal phrase / medium confidence
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
    r"palletiz|depalletiz|pick.and.place|end.of.line|wearable exoskeleton|"
    r"case packer|case.pack|shrink wrapper|labeler|filler|capper|sealer|"
    r"intralogistics|intra.logistics|pack.out|pack.in|pack.off|"
    r"packaging line|packaging automation|stretch wrapper|wrapping machine|"
    r"co.pack|contract pack|cartoner|case erector|tray packer|"
    r"cobotic|mobile robot|autonomous forklift|autonomous pallet)\b",
    re.IGNORECASE,
)

PROBLEM_RE = re.compile(
    r"\b(labor shortage|can.?t find|understaffed|turnover|vacancy|attrition|"
    r"overtime|absenteeism|temp worker|staffing crisis|scheduling gap|"
    r"wage inflation|workforce gap|high.*injury|worker.*injur|"
    r"throughput bottleneck|capacity constraint|running at capacity|maxed out|"
    r"repetitive strain|ergonomic risk|OSHA|lost.time|"
    r"scrap rate|defect rate|rework|quality issue|reject rate|"
    r"pack.out backlog|line speed|uptime issue|changeover time)\b",
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
    try:
        from app.services.robot_signal_ontology import ontology_signal_points
        from app.services.signal_rules_engine import infer_source_channel

        source_url = getattr(signal, "source_url", "") or ""
        source_channel = infer_source_channel(source_url)
        ontology_points = ontology_signal_points(text, signal_type=signal_type.lower(), source_channel=source_channel)
        if ontology_points:
            base = max(base, ontology_points / 100)
    except Exception:
        pass

    # ── Context guard: qualify the robot boost by sentence intent ─────────────
    # Three classes of false-positive automation context:
    #
    #   1. Editorial / how-to  ("Here's how to automate your warehouse")
    #      → automation keyword present, but no company action described
    #      → penalty: 0.85 (worse than neutral)
    #
    #   2. Comparative / benchmark  ("McDonald's vs. Wendy's automation goals")
    #      → companies are comparison targets, not confirmed buyers
    #      → penalty: 0.88
    #
    #   3. Conditional / hypothetical  ("if Lowe's improves automation by 50%...")
    #      → speculative action, not a committed deployment
    #      → penalty: 0.90  (less severe than editorial — company intent is real,
    #        but action is unconfirmed)
    #
    #   Real buyer signal  ("Tyson Foods Deploys Robots Across 500 Plants")
    #      → full ROBOT_RE boost: 1.15
    robot_boost = 1.0
    if ROBOT_RE.search(text):
        try:
            from app.services.sentence_parser import (
                has_editorial_context,
                has_infinitive_only_automation,
                has_comparative_context,
                has_conditional_context,
            )
            if has_editorial_context(text) or has_infinitive_only_automation(text):
                robot_boost = 0.85  # strongest penalty: pure editorial/how-to
            elif has_comparative_context(text):
                robot_boost = 0.88  # benchmark comparison, not a buyer
            elif has_conditional_context(text):
                robot_boost = 0.90  # speculative/hypothetical action
            else:
                robot_boost = SIGNAL_TEXT_BOOST_ROBOT  # 1.15 — confirmed buyer action
        except Exception:
            robot_boost = SIGNAL_TEXT_BOOST_ROBOT  # fail-open

    problem_boost = SIGNAL_TEXT_BOOST_PROBLEM if PROBLEM_RE.search(text) else 1.0
    roi_boost = SIGNAL_TEXT_BOOST_ROI if ROI_RE.search(text) else 1.0

    weighted = base * type_w * age_w * robot_boost * problem_boost * roi_boost
    return round(min(weighted * 100, 100.0), 1)


def compute_lead_aggregate_signal_score(signals) -> float:
    """
    Single 0–100 number per sales account: mean of the top 5 per-signal weighted scores
    (type weight × age decay × text boosts). Empty → 0.
    """
    if not signals:
        return 0.0
    scores = sorted((compute_weighted_score(s) for s in signals), reverse=True)
    top = scores[:5]
    return round(sum(top) / len(top), 1)
