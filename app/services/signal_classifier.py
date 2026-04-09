"""
Signal Classifier — Ontology-based intent extraction
====================================================
Maps text to signal types using the robotics ontology.
Used by the intelligence news scraper to correlate and classify
automation opportunities with ontological meaning.
"""
from typing import List, Optional
from app.services.ontology import CONCEPTS
from app.services.semantic_parser import SemanticParser
from app.services.signal_rules_engine import infer_source_channel, rules_engine_signal_types

# Concept name → signal_type for DB storage (aligns with SIGNAL_PATTERNS)
CONCEPT_TO_SIGNAL: dict = {
    "robot_installation": "robot_installation",
    "pilot_success": "pilot_success",
    "roi_documented": "roi_documented",
    "disinfection_robot": "robot_installation",
    "floor_scrubber_automation": "robot_installation",
    "vendor_selection": "vendor_selection",
    "strategic_automation_hire": "strategic_hire",
    "operations_technology_hire": "strategic_hire",
    "labor_shortage": "labor_shortage",
    "high_turnover": "labor_shortage",
    "reduce_labor_costs": "labor_shortage",
    "warehouse_expansion": "expansion",
    "hotel_expansion": "expansion",
    "funding_announcement": "funding_round",
    "series_funding": "funding_round",
    "capex_announcement": "capex",
    "ma_activity": "ma_activity",
    "acquisition": "ma_activity",
    "new_construction": "expansion",
    "growth_plan": "expansion",
    "operational_scale": "expansion",
    "warehouse_automation": "automation_interest",
    "amr_agv": "automation_interest",
    "service_robot": "automation_interest",
    "cobots": "automation_interest",
    "automation_intent": "automation_interest",
    "pick_place": "automation_interest",
    "wms_integration": "automation_interest",
    "computer_vision": "automation_interest",
    "ai_operations": "automation_interest",
    "equipment_integration": "automation_interest",
    "service_consistency": "automation_interest",
}

_parser: Optional[SemanticParser] = None


def _get_parser() -> SemanticParser:
    global _parser
    if _parser is None:
        _parser = SemanticParser()
    return _parser


def classify_signals_from_ontology(text: str, min_confidence: float = 0.2) -> List[str]:
    """
    Use ontology to extract signal types from text.
    Returns list of signal_type strings for DB storage.
    """
    parser = _get_parser()
    parse = parser.parse(text)

    signals = []
    for name, act in parse.activations.items():
        if act.confidence < min_confidence:
            continue
        sig = CONCEPT_TO_SIGNAL.get(name)
        if sig and sig not in signals:
            signals.append(sig)

    return signals


def classify_signals_with_fallback(
    text: str,
    *,
    source_channel: Optional[str] = None,
    article_url: str = "",
    rss_source_name: str = "",
) -> List[str]:
    """
    Ontology + Pythh-style rules engine + keyword fallback.
    Rules add modality/negation/costly-action structure; ontology stays primary for robotics concepts.

    ``source_channel`` overrides inference; otherwise use ``article_url`` and ``rss_source_name``
    (RSS ``<source>``) — see ``infer_source_channel`` in ``signal_rules_engine``.
    """
    ontology_signals = classify_signals_from_ontology(text, min_confidence=0.2)
    channel = source_channel or infer_source_channel(article_url, rss_source_name)
    rules_signals = rules_engine_signal_types(text, source_channel=channel)

    merged: List[str] = []
    seen = set()
    for s in ontology_signals + rules_signals:
        if s not in seen:
            seen.add(s)
            merged.append(s)
    if merged:
        return merged

    # Fallback: high-value keyword triggers
    lower = text.lower()
    fallback = []
    if any(kw in lower for kw in ["series a", "series b", "funding round", "raised $", "venture capital"]):
        fallback.append("funding_round")
    if any(kw in lower for kw in ["acqui", "merger", "buyout"]):
        fallback.append("ma_activity")
    if any(kw in lower for kw in ["capex", "capital expenditure", "capital investment"]):
        fallback.append("capex")
    if any(kw in lower for kw in ["labor shortage", "staff shortage", "worker shortage", "hiring difficult"]):
        fallback.append("labor_shortage")
    if any(kw in lower for kw in ["expansion", "new facility", "new warehouse", "opening"]):
        fallback.append("expansion")
    if any(kw in lower for kw in ["robot", "automation", "AMR", "AGV", "cobot"]):
        fallback.append("automation_interest")
    if fallback:
        return fallback
    return ["news"]
