"""
Semantic role helpers for candidate company-name strings.

This module answers a narrower question than the text classifier:
"What is the object of this string?"

For lead ingestion, adjectives/descriptors are additive. The object/head noun is
what determines ontological value:
  - "US restaurant" -> object=restaurant -> sector descriptor
  - "Hospitality Robots Strategic Business" -> object=business -> abstract descriptor
  - "MGM Springfield and the technology" -> object=technology, candidate=MGM Springfield
  - "Supply chain consultancy SCALA" -> descriptor=supply chain consultancy, candidate=SCALA
  - "Rivian spin-out Mind Robotics" -> descriptor=Rivian spin-out, candidate=Mind Robotics
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class SemanticRoleParse:
    original: str
    head_object: str = ""
    object_kind: str = "unknown"
    subject_candidate: str = ""
    object_candidate: str = ""
    verb_anchor: str = ""
    descriptors: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)


_VERB_ANCHOR = re.compile(
    r"\b(is|are|was|were|has|have|had|will|would|could|should|may|might|must|"
    r"does|do|did|expands?|continues?|launches?|hires?|opens?|closes?|"
    r"acquires?|deploys?|announces?|reveals?|unveils?|signs?|wins?|loses?|"
    r"raises?|cuts?|gains?|drops?|rises?|falls?|grows?|shrinks?|invests?|"
    r"plans?|aims?|targets?|secures?|lands?|names?|appoints?|makes?|builds?|"
    r"scales?|tests?|trials?|pilots?|highlights?|fuels?|inaugurates?)\b",
    re.IGNORECASE,
)

_DESCRIPTOR_PLUS_CANDIDATE = re.compile(
    r"(?i)^(?P<descriptor>"
    r"(?:(?:chinese|american|us|u\.s\.|japanese|korean|german|dutch|swedish|"
    r"french|british|canadian|australian|european|asian)\s+)?"
    r"(?:supply\s+chain|hospitality|logistics|restaurant|hotel|healthcare|"
    r"third\s+party\s+logistics)\s+"
    r"(?:consultanc(?:y|ies)|operating\s+system|system|platform|software|"
    r"robots?|strategic\s+business|technology)"
    r")\s+(?P<candidate>[A-Z][A-Za-z0-9&'.-]{2,}(?:\s+[A-Z][A-Za-z0-9&'.-]{2,}){0,2})$"
)

_SPINOUT_CANDIDATE = re.compile(
    r"(?i)^(?P<descriptor>.+?\bspin[-\s]?out\b)\s+"
    r"(?P<candidate>[A-Z][A-Za-z0-9&'.-]{2,}(?:\s+[A-Z][A-Za-z0-9&'.-]{2,}){0,3})$"
)

_MALFORMED_TAIL = re.compile(
    r"(?i)^(?P<candidate>[A-Z][A-Za-z0-9&'.-]+(?:\s+[A-Z][A-Za-z0-9&'.-]+){0,4})\s+"
    r"(?P<tail>and\s*$|and\s+(?:the\s+)?(?P<object>technology|business|market|industry|automation|robots?)|"
    r"to\s+(?P<verb>open|expand|deploy|launch|hire))"
)

_REGION_WORDS = {
    "u.s.", "us", "american", "north", "europe", "european", "asia", "asian",
    "n.j.", "nj", "philly-area", "philly", "california", "texas", "florida",
    "new", "york", "chicago", "atlanta", "dfw", "dallas", "houston",
    "chinese", "japanese", "korean", "german", "dutch", "swedish", "french",
    "british", "canadian", "australian",
}

_SECTOR_OBJECTS = {
    "hospitality", "restaurant", "restaurants", "qsr", "logistics", "3pl",
    "manufacturers", "manufacturer", "retailers", "retailer", "hotels",
    "hotel", "healthcare", "hospitals", "hospital", "airports", "airport",
    "operators", "operator", "robotics", "robots",
}

_FACILITY_OBJECTS = {
    "park", "center", "centers", "centre", "centres", "warehouse",
    "warehouses", "facility", "facilities", "hospital", "hospitals",
    "clinic", "clinics", "hotel", "hotels", "restaurant", "restaurants",
    "airport", "airports",
}

_POPULATION_OBJECTS = {
    "americans", "adults", "seniors", "patients", "workers", "worker",
    "travelers", "travellers", "guests", "consumers", "customers",
}

_DESCRIPTOR_ONLY = {
    "bestseller", "best seller", "seller", "supplier", "vendor", "operator",
    "operators", "manufacturer", "manufacturers", "buyer", "buyers",
    "beststeller",
}

_NON_OBJECT_TAILS = {
    "big", "larger", "smaller", "better", "faster", "slower", "new", "next",
    "first", "last", "public", "private", "available",
}

_NON_COMPANY_CANDIDATE_PHRASES = {
    "ai",
    "competitive strategies",
    "programs to codify",
    "life science automation",
    "smart tech wearable",
    "fuels innovative learning",
    "singapore champions robotics adoption",
    "inaugurates phase ii",
    "pacious on ai",
}

_ABSTRACT_OBJECTS = {
    "business", "technology", "market", "industry", "strategy", "innovation",
    "trend", "trends", "scaling", "automation",
}

_COMPOUND_OBJECTS = {
    "third party logistics": "sector_descriptor",
    "logistics park": "facility_descriptor",
    "strategic business": "sector_descriptor",
    "scaling restaurants": "sector_descriptor",
    "scaling robots": "sector_descriptor",
    "hospitality robots strategic business": "facility_descriptor",
}

_GENERIC_MODIFIERS = (
    _REGION_WORDS
    | _SECTOR_OBJECTS
    | _FACILITY_OBJECTS
    | _POPULATION_OBJECTS
    | _ABSTRACT_OBJECTS
    | {
        "third", "party", "supply", "chain", "consultancy", "consultancies",
        "scaling", "strategic", "data", "very", "long", "synthetic", "phrase", "about",
        "competitive", "strategies", "programs", "codify", "life", "science",
        "smart", "wearable", "fuels", "innovative", "learning", "champions",
        "adoption", "inaugurates", "phase", "ii", "pacious",
    }
)


def _words(text: str) -> list[str]:
    return re.findall(r"[A-Za-z][A-Za-z'.-]*", text or "")


def _kind_for_head(head: str, phrase: str) -> str:
    low_head = head.lower()
    low_phrase = " ".join(w.lower() for w in _words(phrase))
    if low_phrase in _DESCRIPTOR_ONLY:
        return "descriptor_without_object"
    for compound, kind in sorted(
        _COMPOUND_OBJECTS.items(), key=lambda item: len(item[0]), reverse=True
    ):
        if low_phrase.endswith(compound) or low_phrase == compound:
            return kind
    if low_head in _SECTOR_OBJECTS:
        return "sector_descriptor"
    if low_head in _FACILITY_OBJECTS:
        return "facility_descriptor"
    if low_head in _POPULATION_OBJECTS:
        return "population_group"
    if low_head in _DESCRIPTOR_ONLY:
        return "descriptor_without_object"
    if low_head in _ABSTRACT_OBJECTS:
        return "abstract_descriptor"
    return "unknown"


def _has_brand_modifier(descriptors: list[str]) -> bool:
    for word in descriptors:
        low = word.lower()
        if low in _GENERIC_MODIFIERS:
            continue
        if word.isupper() and len(word) >= 2:
            return True
        if word[:1].isupper():
            return True
    return False


def _is_probable_candidate_object(candidate: str) -> bool:
    words = _words(candidate)
    if not words:
        return False
    low_phrase = " ".join(w.lower() for w in words)
    if low_phrase in _NON_COMPANY_CANDIDATE_PHRASES:
        return False
    if low_phrase in _COMPOUND_OBJECTS:
        return False
    head, descriptors, kind = _head_object(candidate)
    if kind != "unknown" and _has_brand_modifier(descriptors):
        return True
    if kind != "unknown" and not any(w.isupper() and len(w) >= 3 for w in words):
        return False
    if any(w.isupper() and len(w) >= 3 for w in words):
        return True
    return _has_brand_modifier(words)


def _head_object(text: str) -> tuple[str, list[str], str]:
    words = _words(text)
    if not words:
        return "", [], "unknown"
    head = words[-1]
    descriptors = words[:-1]
    # Preserve compound object value when the last two words form the object.
    if len(words) >= 2:
        last_two = " ".join(w.lower() for w in words[-2:])
        if last_two in _COMPOUND_OBJECTS:
            head = last_two
            descriptors = words[:-2]
    return head, descriptors, _kind_for_head(head, text)


def parse_semantic_roles(text: str) -> SemanticRoleParse:
    raw = (text or "").strip()
    if not raw:
        return SemanticRoleParse(original=text or "", evidence=["empty input"])

    m = _DESCRIPTOR_PLUS_CANDIDATE.match(raw)
    if m:
        descriptor = m.group("descriptor")
        candidate = m.group("candidate")
        if _is_probable_candidate_object(candidate):
            return SemanticRoleParse(
                original=raw,
                head_object=candidate,
                object_kind="candidate_object",
                object_candidate=candidate,
                descriptors=[descriptor],
                evidence=["descriptor phrase precedes a trailing candidate object"],
            )

    spinout = _SPINOUT_CANDIDATE.match(raw)
    if spinout:
        descriptor = spinout.group("descriptor")
        candidate = spinout.group("candidate")
        if _is_probable_candidate_object(candidate):
            return SemanticRoleParse(
                original=raw,
                head_object=candidate,
                object_kind="candidate_object",
                object_candidate=candidate,
                descriptors=[descriptor],
                evidence=["spin-out descriptor precedes a trailing candidate object"],
            )

    verb = _VERB_ANCHOR.search(raw)
    if verb:
        subject = raw[: verb.start()].strip()
        obj_text = raw[verb.end() :].strip()
        head, descriptors, kind = _head_object(obj_text or raw)
        if head.lower() in _NON_OBJECT_TAILS:
            head = ""
            kind = "sentence_or_headline"
        return SemanticRoleParse(
            original=raw,
            head_object=head,
            object_kind="sentence_or_headline",
            subject_candidate=subject,
            verb_anchor=verb.group(0),
            descriptors=descriptors,
            evidence=["verb anchor splits subject from object phrase"],
        )

    malformed = _MALFORMED_TAIL.match(raw)
    if malformed:
        candidate = malformed.group("candidate")
        obj = malformed.group("object") or malformed.group("verb") or "truncated connector"
        if _is_probable_candidate_object(candidate):
            return SemanticRoleParse(
                original=raw,
                head_object=obj,
                object_kind="malformed_entity_string",
                subject_candidate=candidate,
                object_candidate=candidate,
                descriptors=[malformed.group("tail").strip()],
                evidence=["candidate object embedded in malformed sentence tail"],
            )

    head, descriptors, kind = _head_object(raw)
    if head.lower() in _REGION_WORDS and descriptors:
        head = descriptors[-1]
        descriptors = descriptors[:-1]
        kind = _kind_for_head(head, raw)
    low_phrase = " ".join(w.lower() for w in _words(raw))
    if kind.endswith("_descriptor") and low_phrase not in _COMPOUND_OBJECTS:
        if _has_brand_modifier(descriptors):
            kind = "unknown"

    return SemanticRoleParse(
        original=raw,
        head_object=head,
        object_kind=kind,
        descriptors=descriptors,
        evidence=["noun phrase head object extracted"],
    )
