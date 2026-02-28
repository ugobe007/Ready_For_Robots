"""
NLP Classifier
==============
Thin wrapper around SemanticParser that exposes a simple classify() API
used by scrapers and API endpoints.
"""
from typing import Dict, List
from app.services.semantic_parser import SemanticParser, ParseResult

_parser = SemanticParser()  # singleton


def classify(text: str) -> Dict[str, float]:
    """
    Classify a single text string.
    Returns domain scores in [0, 1] range.

    Example output:
        {
          "automation_intent": 0.72,
          "labor_pain":        0.65,
          "expansion_intent":  0.30,
          "industry_fit":      0.85,
          "overall":           0.63
        }
    """
    result = _parser.parse(text)
    return _to_scores(result)


def classify_multi(texts: List[str]) -> Dict[str, float]:
    """Classify multiple text blobs merged together."""
    result = _parser.parse_multi(texts)
    return _to_scores(result)


def explain(text: str) -> Dict:
    """Return scores plus top activated concepts for explainability."""
    result = _parser.parse(text)
    scores = _to_scores(result)
    top = [
        {"concept": a.concept_name, "domain": a.domain,
         "confidence": a.confidence, "matched_by": a.matched_by,
         "propagated": a.propagated}
        for a in result.top_concepts(8)
    ]
    return {"scores": scores, "activated_concepts": top}


def _to_scores(result: ParseResult) -> Dict[str, float]:
    a = result.domain_score("automation")
    l = result.domain_score("labor_pain")
    e = result.domain_score("expansion")
    i = result.domain_score("industry_fit")
    overall = round(a * 0.30 + l * 0.25 + e * 0.20 + i * 0.25, 4)
    return {
        "automation_intent": round(a, 4),
        "labor_pain":        round(l, 4),
        "expansion_intent":  round(e, 4),
        "industry_fit":      round(i, 4),
        "overall":           overall,
    }