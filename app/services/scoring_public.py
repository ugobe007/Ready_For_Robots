"""
Public snapshot of Hot/Warm scoring — for API + UI.
Single source of truth for numeric knobs: lead_filter + signal_ranker constants.
"""
from typing import Any, Dict, List

from app.services import lead_filter as lf
from app.services import signal_ranker as sr


def get_scoring_system_public() -> Dict[str, Any]:
    """Structured copy for homepage /docs; safe to cache (no DB)."""
    priority_constants = {
        k: getattr(lf, k)
        for k in (
            "PRIORITY_COMPOSITE_CAP",
            "PRIORITY_INDUSTRY_FIT_BOOST",
            "PRIORITY_SIGNAL_VOLUME_TIERS",
            "PRIORITY_ENTERPRISE_MIN_EMPLOYEES",
            "PRIORITY_ENTERPRISE_BOOST",
            "PRIORITY_MIDMARKET_MIN_EMPLOYEES",
            "PRIORITY_MIDMARKET_BOOST",
            "PRIORITY_HOT_COMPOSITE_MIN",
            "PRIORITY_HOT_COMPOSITE_WITH_HOT_SIGNALS",
            "PRIORITY_WARM_COMPOSITE_MIN",
            "PRIORITY_WARM_BASE_WITH_INDUSTRY",
            "PRIORITY_HOT_DISTINCT_TYPES_MIN",
            "PRIORITY_HOT_BASE_WITH_TWO_HITS",
            "PRIORITY_HOT_BASE_WITH_ONE_HIT",
            "PRIORITY_HOT_BASE_WITH_DEPLOYMENT",
            "HOT_SIGNAL_BOOST_CAP",
            "WARM_SIGNAL_BOOST_CAP",
        )
    }
    # Tuples → JSON-serializable
    vol = priority_constants.get("PRIORITY_SIGNAL_VOLUME_TIERS")
    if vol:
        priority_constants["PRIORITY_SIGNAL_VOLUME_TIERS"] = [
            {"min_signals": a, "boost": b, "notes_in_reasons": c} for a, b, c in vol
        ]

    age_rows: List[Dict[str, Any]] = []
    prev = 0
    for max_d, mult in sr.SIGNAL_AGE_DECAY_BRACKETS:
        age_rows.append(
            {
                "from_days": prev,
                "to_days": max_d,
                "multiplier": mult,
            }
        )
        prev = max_d + 1
    age_rows.append(
        {
            "from_days": prev,
            "to_days": None,
            "multiplier": sr.SIGNAL_AGE_DECAY_OLDEST_MULTIPLIER,
        }
    )

    return {
        "version": "1.1",
        "code_paths": {
            "priority_tier": "app/services/lead_filter.py",
            "per_signal_weight": "app/services/signal_ranker.py",
            "ml_base_score": "app/services/scoring_engine.py → inference_engine.analyze_signals",
        },
        "summary": (
            "Spotlight **tier** (Hot / Warm / Emerging) uses a **priority composite**: "
            "ML `overall_intent_score` (0–100) plus capped rule boosts (industry fit, hot/warm signal mix, "
            "signal count, company size). The **SCORE** on each card is the ML overall intent score from the DB, "
            "not the composite. **Weighted signal** scores (per row) use type weights, age decay, and text boosts."
        ),
        "priority_composite": {
            "formula": "composite = min(PRIORITY_COMPOSITE_CAP, ml_base + sum(boosts))",
            "ml_base_field": "overall_intent_score",
            "constants": priority_constants,
            "hot_tier_rules_plain": [
                f"HOT if composite ≥ {lf.PRIORITY_HOT_COMPOSITE_MIN}",
                (
                    f"OR composite ≥ {lf.PRIORITY_HOT_COMPOSITE_WITH_HOT_SIGNALS} AND "
                    "'hot_enough': ≥2 distinct hot-type signals, OR ≥2 hot hits with ML base ≥ "
                    f"{lf.PRIORITY_HOT_BASE_WITH_TWO_HITS}, OR ≥1 hot hit with base ≥ {lf.PRIORITY_HOT_BASE_WITH_ONE_HIT}, "
                    f"OR a deployment signal with ≥1 hot hit and base ≥ {lf.PRIORITY_HOT_BASE_WITH_DEPLOYMENT}"
                ),
            ],
            "warm_tier_rules_plain": [
                f"WARM if composite ≥ {lf.PRIORITY_WARM_COMPOSITE_MIN}",
                f"OR ML base ≥ {lf.PRIORITY_WARM_BASE_WITH_INDUSTRY} AND industry is high-fit",
            ],
            "emerging_tier": "Otherwise Emerging (shown as Emerging in UI; COLD in API).",
            "hot_signal_boost_note": (
                "Hot-type signal rows contribute a sublinear boost (diversity + volume), "
                f"capped at HOT_SIGNAL_BOOST_CAP so duplicate RSS rows do not max composite."
            ),
            "warm_signal_boost_note": (
                "Warm-type rows add a smaller capped boost (WARM_SIGNAL_BOOST_CAP)."
            ),
        },
        "signal_type_sets": {
            "hot_types": sorted(lf.SIGNAL_TYPES_HOT),
            "warm_types": sorted(lf.SIGNAL_TYPES_WARM),
            "deployment_escalation_types": sorted(lf.DEPLOYMENT_SIGNAL_TYPES),
        },
        "high_fit_industries": sorted(lf.HIGH_FIT_INDUSTRIES),
        "per_signal_weighting": {
            "formula": "weighted = signal_strength × type_weight × age × robot_boost × problem_boost × roi_boost; display = min(×100, 100)",
            "default_type_weight": sr.DEFAULT_TYPE_WEIGHT,
            "type_weights": dict(sorted(sr.SIGNAL_TYPE_WEIGHTS.items(), key=lambda x: (-x[1], x[0]))),
            "age_decay": {
                "unknown_age_multiplier": sr.SIGNAL_AGE_UNKNOWN_MULTIPLIER,
                "brackets": age_rows,
            },
            "text_pattern_multipliers": {
                "robot_automation_keywords": sr.SIGNAL_TEXT_BOOST_ROBOT,
                "labor_pain_keywords": sr.SIGNAL_TEXT_BOOST_PROBLEM,
                "roi_quant_keywords": sr.SIGNAL_TEXT_BOOST_ROI,
            },
        },
        "spotlight_selection": {
            "note": "Homepage picks 3 Hot + 2 Warm from eligible companies, sorted by newest signal time then composite; daily/hourly rotation avoids stale dominance.",
            "endpoint": "GET /api/leads/homepage",
        },
    }
