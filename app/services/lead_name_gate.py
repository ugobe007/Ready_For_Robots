"""
Lead Name Gate — boolean pre-filter before ontological inference
================================================================
Every candidate company string must pass this AND-chain before:
  - ``classify_signals_with_fallback`` / ontology signal typing
  - ``InferenceEngine.analyze`` / lead inference dossier
  - DB insert in news scrapers

Public API (yes/no):
  is_acceptable_lead_name(name) -> bool
  check_lead_name(name) -> (bool, reason)
  filter_name_candidates([(name, conf), ...]) -> filtered list
"""
from __future__ import annotations

import re
from typing import List, Optional, Tuple

from app.services.company_validator import is_valid_lead
from app.services.headline_name_shape import passes_headline_name_shape
from app.services.lead_filter import is_junk
from app.services.text_classifier import EntityType, TextClassification, classify

# Fast headline stubs — checked before heavier validators
_LISTICLE_RE = re.compile(
    r"(?i)^(\d+\s+)?(best|top|worst|review|reviews|guide to|ways to|things to|tips for)\b",
)
_JOB_SEO_RE = re.compile(r"(?i)^(your job|how to|what is|why you|can you)\b")
_INCOMPLETE_RE = re.compile(
    r"(?i)\s+(to|for|and|the|a|an|of|by|is|are|was|were)\s*$",
)

_HARD_REJECT_TYPES = frozenset({
    EntityType.PERSON_NAME,
    EntityType.CITY_OR_TOWN,
    EntityType.COUNTRY,
    EntityType.SECTOR_DESCRIPTOR,
    EntityType.FACILITY_DESCRIPTOR,
    EntityType.POPULATION_GROUP,
    EntityType.DESCRIPTOR_ONLY,
    EntityType.MALFORMED_ENTITY,
    EntityType.SAYING,
    EntityType.EQUIPMENT_CAT,
    EntityType.MARKET_FRAGMENT,
    EntityType.ARTICLE_HEADLINE,
    EntityType.DESCRIPTION,
})


def _classifier_rejects(tc: TextClassification) -> Optional[str]:
    if tc.entity_type in _HARD_REJECT_TYPES and tc.confidence >= 0.65:
        return (
            f"text_classifier:{tc.entity_type.value} "
            f"(conf={tc.confidence:.2f})"
        )
    if tc.entity_type == EntityType.UNKNOWN and tc.confidence < 0.40:
        return "text_classifier: insufficient company evidence"
    return None


def check_lead_name(
    name: str,
    *,
    entity_hint: Optional[TextClassification] = None,
) -> Tuple[bool, str]:
    """
    Boolean AND gate. Returns (True, "") only when the name may proceed to ontology.
    """
    name = (name or "").strip()
    if not name:
        return False, "empty name"

    if _LISTICLE_RE.search(name) or _JOB_SEO_RE.search(name):
        return False, "listicle or SEO headline stub"

    if _INCOMPLETE_RE.search(name):
        return False, "incomplete headline fragment"

    ok, reason = passes_headline_name_shape(name)
    if not ok:
        return False, f"headline shape: {reason}"

    junk, junk_reason = is_junk(name)
    if junk:
        return False, junk_reason or "junk filter"

    tc = entity_hint if entity_hint is not None else classify(name)
    cls_reason = _classifier_rejects(tc)
    if cls_reason:
        return False, cls_reason

    valid, vreason = is_valid_lead(name, entity_hint=tc, skip_junk_check=True)
    if not valid:
        return False, vreason or "logic engine rejected"

    return True, ""


def is_acceptable_lead_name(
    name: str,
    *,
    entity_hint: Optional[TextClassification] = None,
) -> bool:
    """Simple yes/no — use before running ontological parsers."""
    return check_lead_name(name, entity_hint=entity_hint)[0]


def filter_name_candidates(
    candidates: List[Tuple[str, float]],
) -> List[Tuple[str, float]]:
    """Drop headline junk; preserve confidence ordering."""
    kept: List[Tuple[str, float]] = []
    for name, confidence in candidates:
        if is_acceptable_lead_name(name):
            kept.append((name, confidence))
    kept.sort(key=lambda x: x[1], reverse=True)
    return kept


def check_oem_prospect_name(
    name: str,
    *,
    entity_hint: Optional[TextClassification] = None,
) -> Tuple[bool, str]:
    """
    Boolean gate for StageGate / robot_companies pipeline.
    Same headline-junk rejection as buyer gate, but allows robot OEMs through.
    """
    name = (name or "").strip()
    if not name:
        return False, "empty name"

    if _LISTICLE_RE.search(name) or _JOB_SEO_RE.search(name):
        return False, "listicle or SEO headline stub"

    if _INCOMPLETE_RE.search(name):
        return False, "incomplete headline fragment"

    ok, reason = passes_headline_name_shape(name)
    if not ok:
        return False, f"headline shape: {reason}"

    junk, junk_reason = is_junk(name, mode="oem_prospect")
    if junk:
        return False, junk_reason or "junk filter"

    tc = entity_hint if entity_hint is not None else classify(name)
    cls_reason = _classifier_rejects(tc)
    if cls_reason:
        return False, cls_reason

    valid, vreason = is_valid_lead(
        name,
        entity_hint=tc,
        skip_junk_check=True,
        mode="oem_prospect",
    )
    if not valid:
        return False, vreason or "logic engine rejected"

    return True, ""


def is_acceptable_oem_prospect_name(
    name: str,
    *,
    entity_hint: Optional[TextClassification] = None,
) -> bool:
    """Yes/no gate for robot OEM / partner names (robot_companies table)."""
    return check_oem_prospect_name(name, entity_hint=entity_hint)[0]
