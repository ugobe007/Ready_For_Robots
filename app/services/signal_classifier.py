"""
Signal Classifier — Ontology-based intent extraction
====================================================
Maps text to signal types using the robotics ontology.
Used by the intelligence news scraper to correlate and classify
automation opportunities with ontological meaning.
"""
import re
from typing import List, Optional
from app.services.ontology import CONCEPTS
from app.services.robot_signal_ontology import signal_types_from_ontology_matches
from app.services.semantic_parser import SemanticParser
from app.services.signal_rules_engine import infer_source_channel, rules_engine_signal_types

# Concept name → signal_type for DB storage (aligns with SIGNAL_PATTERNS)
CONCEPT_TO_SIGNAL: dict = {
    "robot_installation": "robot_installation",
    "humanoid_deployment": "robot_installation",
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


# Press headlines: COO/CEO stories often weak-trigger ontology "expansion" (growth_plan, etc.).
_CHIEF_OR_C_SUITE = re.compile(
    r"\bchief\s+(?:executive|operating|operations|financial|technology|marketing|information|people)\s+officer\b|"
    r"\b(?:ceo|coo|cfo|cto|cmo|chro)\b",
    re.I,
)
_EXEC_ACTION = re.compile(
    r"\b(?:appoint|appoints|appointed|names|named|elects|elects|hires|hired|joins|joined|"
    r"promotes|promoted|taps|tapped)\b",
    re.I,
)
_ANNOUNCE_C_SUITE = re.compile(
    r"\bannounces?\b.{0,140}\b(?:chief\s+(?:executive|operating|operations|financial|technology|marketing)\s+officer|"
    r"\b(?:ceo|coo|cfo|cto)\b)",
    re.I,
)
_STRONG_EXPANSION_CONTEXT = re.compile(
    r"\b(?:new|additional)\s+(?:facility|facilities|warehouse|distribution\s+center|dc\b|plant|hotel|property|properties|location|locations|acres)\b|"
    r"\b(?:breaking\s+ground|groundbreaking|ribbon\s+cutting|grand\s+opening)\b|"
    r"\b(?:square\s+feet|sq\.?\s*ft\.?)\b|"
    r"\b(?:capex|capital\s+expenditure|capital\s+investment)\b|"
    r"\b(?:opens?\s+\d+|opening\s+\d+\s+(?:stores?|locations?|hotels?|sites?))\b",
    re.I,
)


def text_indicates_executive_appointment(text: str) -> bool:
    """True when copy reads primarily as a named executive / C-suite move (not facility capex)."""
    t = (text or "").strip()
    if not t:
        return False
    if _CHIEF_OR_C_SUITE.search(t) and _EXEC_ACTION.search(t):
        return True
    if _ANNOUNCE_C_SUITE.search(t):
        return True
    if _CHIEF_OR_C_SUITE.search(t) and re.search(
        r"\b(?:svp|evp|senior\s+vice\s+president|vice\s+president|president)\b", t, re.I
    ):
        return True
    return False


def reconcile_signal_types_for_text(text: str, types: List[str]) -> List[str]:
    """
    Drop weak ``expansion`` / ``scale_expansion`` when the article is clearly an exec appointment
    without facility/capex anchors. Ensures ``strategic_hire`` is present for that shape.

    Call after ontology + rules + keyword merges (and after scraper keyword passes).
    """
    if not types:
        return types
    exec_appt = text_indicates_executive_appointment(text)
    strong_x = _STRONG_EXPANSION_CONTEXT.search(text or "") is not None
    if not exec_appt:
        return types

    filtered: List[str] = []
    for x in types:
        if x in ("expansion", "scale_expansion") and not strong_x:
            continue
        filtered.append(x)

    if "strategic_hire" not in filtered:
        filtered.insert(0, "strategic_hire")
    else:
        filtered = ["strategic_hire"] + [x for x in filtered if x != "strategic_hire"]

    if not filtered:
        return ["strategic_hire"]
    return filtered


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
    vocabulary_signals = signal_types_from_ontology_matches(text)
    channel = source_channel or infer_source_channel(article_url, rss_source_name)
    rules_signals = rules_engine_signal_types(text, source_channel=channel)

    merged: List[str] = []
    seen = set()
    for s in vocabulary_signals + ontology_signals + rules_signals:
        if s not in seen:
            seen.add(s)
            merged.append(s)
    if merged:
        return _filter_vendor_story_signals(text, reconcile_signal_types_for_text(text, merged))

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
    if any(
        kw in lower
        for kw in [
            "evaluate automation",
            "automation pilot",
            "proof of concept",
            "vendor selection",
            "rfp",
            "deploy robots",
            "robot deployment",
            "warehouse automation",
            "amr",
            "agv",
            "cobot",
        ]
    ):
        fallback.append("automation_interest")
    if fallback:
        return _filter_vendor_story_signals(text, reconcile_signal_types_for_text(text, fallback))
    return ["news"]


_VENDOR_CONCEPTS = frozenset({"robot_oem", "system_integrator", "robotics_distributor"})
_OEM_HUMANOID_ANNOUNCE_RE = re.compile(
    r"(?i)(?:\b(?:unveil(?:s|ed)?|introduc(?:e|es|ed)|launch(?:es|ed)?|debut(?:s|ed)?|"
    r"announc(?:e|es|ed)|reveal(?:s|ed)?)\b.*\bhumanoid\b"
    r"|\bhumanoid\b.*\b(?:unveil(?:s|ed)?|introduc(?:e|es|ed)|launch(?:es|ed)?|"
    r"debut(?:s|ed)?|announc(?:e|es|ed)|reveal(?:s|ed)?)\b)"
)
_BUYER_INTENT_CONCEPTS = frozenset({
    "labor_shortage", "high_turnover", "reduce_labor_costs", "vendor_selection", "rfq_rfp",
    "warehouse_expansion", "hotel_expansion", "capex_announcement", "strategic_automation_hire",
    "robot_installation", "pilot_success", "series_funding", "ma_activity", "new_construction",
    "humanoid_deployment",
})


def _filter_vendor_story_signals(text: str, signals: List[str]) -> List[str]:
    """Drop weak buyer tags when text is clearly vendor/funding PR, not end-buyer intent."""
    from app.services.lead_filter import SELLER_OR_PUBLISHER_CONTEXT_RE

    if not signals:
        return signals

    parse = _get_parser().parse(text)
    vendor_active = any(
        (act := parse.activations.get(name)) and act.confidence >= 0.45
        for name in _VENDOR_CONCEPTS
    )
    humanoid_oem_story = (
        _OEM_HUMANOID_ANNOUNCE_RE.search(text)
        or (
            (oem := parse.activations.get("humanoid_robot")) and oem.confidence >= 0.45
            and not (
                (dep := parse.activations.get("humanoid_deployment")) and dep.confidence >= 0.35
            )
        )
    )
    vendor_active = vendor_active or humanoid_oem_story
    buyer_intent_active = any(
        (act := parse.activations.get(name)) and act.confidence >= 0.35
        for name in _BUYER_INTENT_CONCEPTS
    )
    vendor_story = vendor_active and not buyer_intent_active

    if vendor_story:
        buyer_direct = {
            "vendor_selection",
            "pilot_success",
            "rfp_posted",
            "labor_shortage",
            "expansion",
            "capex",
            "strategic_hire",
            "robot_installation",
            "warehouse_throughput",
            "production_capacity",
        }
        if any(s in buyer_direct for s in signals):
            return [s for s in signals if s not in ("automation_interest", "automation_intent", "funding_round")]
        return ["news"]

    if not SELLER_OR_PUBLISHER_CONTEXT_RE.search(text):
        return signals
    buyer_direct = {
        "vendor_selection",
        "pilot_success",
        "rfp_posted",
        "labor_shortage",
        "expansion",
        "capex",
        "strategic_hire",
        "robot_installation",
        "warehouse_throughput",
        "production_capacity",
    }
    if any(s in buyer_direct for s in signals):
        return [s for s in signals if s not in ("automation_interest", "automation_intent", "funding_round")]
    return []


def primary_signal_type_for_text(
    text: str,
    *,
    source_channel: Optional[str] = None,
    article_url: str = "",
    rss_source_name: str = "",
) -> str:
    """
    Single signal type for callers that store one ``signal_type`` per row (e.g. SERP).

    Uses the same pipeline as RSS/intelligence scrapers: ontology (``SemanticParser`` +
    ``CONCEPTS``), ``signal_rules_engine``, then keyword fallback — not a parallel
    keyword-only map.
    """
    types = classify_signals_with_fallback(
        text,
        source_channel=source_channel,
        article_url=article_url,
        rss_source_name=rss_source_name,
    )
    if not types:
        return "news"
    return types[0]
