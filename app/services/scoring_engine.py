"""
Scoring Engine
==============
Computes robotics intent scores for a company using the ontological
InferenceEngine.  Falls back to legacy keyword scoring if no signals exist.
"""
from typing import Dict, List, Optional
from app.models.signal import Signal
from app.services.inference_engine import analyze_signals


def compute_scores(company, signals: List[Signal]) -> Dict:
    """
    Primary scoring function.
    Uses the full ontological inference pipeline when signals are present.
    Returns dict compatible with the Score ORM model (0–100 scale).
    """
    industry = getattr(company, "industry", "") or ""
    name = getattr(company, "name", "") or ""

    if signals:
        signal_texts = []
        signal_times: List[Optional[object]] = []
        for s in signals:
            if not hasattr(s, 'signal_type') or not hasattr(s, 'signal_text'):
                continue  # skip malformed/corrupt entries
            signal_texts.append(f"{s.signal_type or ''} {s.signal_text or ''}")
            signal_times.append(getattr(s, "created_at", None))
        result = analyze_signals(
            signal_texts,
            company_name=name,
            industry=industry,
            signal_times=signal_times if len(signal_times) == len(signal_texts) else None,
        )
        scores = result.to_score_dict()
    else:
        # No signals yet — use industry prior only
        from app.services.ontology import get_industry_prior
        prior = get_industry_prior(industry) * 100
        scores = {
            "automation_score":     0.0,
            "labor_pain_score":     0.0,
            "expansion_score":      0.0,
            "robotics_fit_score":   round(prior, 2),
            "overall_intent_score": round(prior * 0.25, 2),
        }

    return scores