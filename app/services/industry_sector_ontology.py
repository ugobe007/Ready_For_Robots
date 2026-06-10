"""
Sector sub-ontologies for industry search, inference, and scraper discovery.

Source of truth: app/data/industry_sector_ontology.json

Subject + inference pattern: sub-ontologies may declare a primary ``subject`` (lab, patient,
airport, …). Matching does not require the exact phrase "lab automation" — text containing
the subject plus an inference anchor (automation, robot, AMR, …) is enough.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

_ONTOLOGY_PATH = Path(__file__).resolve().parent.parent / "data" / "industry_sector_ontology.json"

_DEFAULT_INFERENCE_ANCHORS: Tuple[str, ...] = (
    "automation",
    "automated",
    "robot",
    "robotics",
    "autonomous",
    "amr",
    "agv",
    "cobot",
    "deployment",
    "deploys",
    "deployed",
    "pilot",
    "pilots",
)


def normalize_term(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


@dataclass
class SubjectRef:
    sector_id: str
    sub_id: str
    subject: str
    modifiers: List[str]
    canonical_industries: List[str]
    terms: List[str]


@dataclass
class OntologyMatch:
    canonical_industries: List[str] = field(default_factory=list)
    expansion_terms: List[str] = field(default_factory=list)
    sector_ids: List[str] = field(default_factory=list)
    sub_ontology_ids: List[str] = field(default_factory=list)


@lru_cache(maxsize=1)
def load_sector_ontology() -> dict:
    with _ONTOLOGY_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


@lru_cache(maxsize=1)
def inference_anchors() -> Tuple[str, ...]:
    raw = load_sector_ontology().get("inference_anchors") or []
    anchors = [normalize_term(a) for a in raw if normalize_term(a)]
    return tuple(anchors or _DEFAULT_INFERENCE_ANCHORS)


@lru_cache(maxsize=1)
def _subject_refs() -> List[SubjectRef]:
    refs: List[SubjectRef] = []
    for sector in load_sector_ontology().get("sectors", []):
        sid = sector["id"]
        canonical = list(sector.get("canonical_industries") or [])
        for sub_id, sub in (sector.get("sub_ontologies") or {}).items():
            subject = normalize_term(sub.get("subject") or "")
            if not subject:
                continue
            refs.append(
                SubjectRef(
                    sector_id=sid,
                    sub_id=sub_id,
                    subject=subject,
                    modifiers=[normalize_term(m) for m in (sub.get("modifiers") or []) if normalize_term(m)],
                    canonical_industries=canonical,
                    terms=[normalize_term(t) for t in (sub.get("terms") or []) if normalize_term(t)],
                )
            )
    refs.sort(key=lambda r: len(r.subject), reverse=True)
    return refs


@lru_cache(maxsize=1)
def _term_index() -> Dict[str, List[Tuple[str, str, str]]]:
    """
    normalized_term -> [(sector_id, sub_id, raw_term), ...]
    Indexes root aliases, sub-ontology terms, subjects, and sector labels.
    """
    index: Dict[str, List[Tuple[str, str, str]]] = {}
    data = load_sector_ontology()

    def _add(term: str, sector_id: str, sub_id: str) -> None:
        key = normalize_term(term)
        if not key:
            return
        index.setdefault(key, []).append((sector_id, sub_id, term))

    for sector in data.get("sectors", []):
        sid = sector["id"]
        _add(sector.get("label", ""), sid, "__sector__")
        for alias in sector.get("root_aliases", []):
            _add(alias, sid, "__root__")
        for canonical in sector.get("canonical_industries", []):
            _add(canonical, sid, "__canonical__")
        for sub_id, sub in (sector.get("sub_ontologies") or {}).items():
            _add(sub.get("label", ""), sid, sub_id)
            if sub.get("subject"):
                _add(sub["subject"], sid, sub_id)
            for term in sub.get("terms", []):
                _add(term, sid, sub_id)
    return index


def _term_matches_query(term: str, query: str) -> bool:
    if not term or not query:
        return False
    if term == query:
        return True
    # Very short ontology keys must match exactly (avoids "er" ⊂ "center", "ed" ⊂ "red").
    if len(term) <= 3 or len(query) <= 3:
        return False
    if len(query) >= 4 and query in term:
        return True
    if len(term) >= 4 and term in query:
        return True
    return False


def term_in_text(term: str, hay: str) -> bool:
    """Match expansion term in haystack without short-token substring false positives."""
    t = normalize_term(term)
    h = normalize_term(hay)
    if not t or not h:
        return False
    if t in h and " " in t:
        return True
    if len(t) <= 4:
        return re.search(rf"\b{re.escape(t)}\b", h) is not None
    if len(t) >= 8:
        return t in h
    return re.search(rf"\b{re.escape(t)}\b", h) is not None


def _subject_in_text(subject: str, hay: str) -> bool:
    if not subject or not hay:
        return False
    if " " in subject:
        return subject in hay
    if len(subject) <= 4:
        return re.search(rf"\b{re.escape(subject)}\b", hay) is not None
    return subject in hay


def _has_inference_anchor(hay: str) -> bool:
    return any(anchor in hay for anchor in inference_anchors())


def _strip_inference_suffix(query: str) -> str:
    """Drop trailing inference anchor only when the prefix is a known subject or multi-word."""
    q = normalize_term(query)
    subjects = {ref.subject for ref in _subject_refs()}
    for anchor in inference_anchors():
        suffix = f" {anchor}"
        if not q.endswith(suffix) or len(q) <= len(suffix):
            continue
        prefix = q[: -len(suffix)].strip()
        if prefix in subjects or " " in prefix:
            return prefix
    return q


def resolve_subject_refs(query: str) -> List[SubjectRef]:
    """Map a user query to subject-based sub-ontologies (longest subject wins)."""
    q = _strip_inference_suffix(query)
    if not q:
        return []
    matched: List[SubjectRef] = []
    for ref in _subject_refs():
        if _term_matches_query(ref.subject, q) or _term_matches_query(q, ref.subject):
            matched.append(ref)
    return matched


def subject_inference_terms(query: str) -> List[str]:
    """Expansion terms derived from subject + modifiers + anchors."""
    refs = resolve_subject_refs(query)
    if not refs:
        return []
    terms: List[str] = []
    anchors = list(inference_anchors())
    for ref in refs:
        terms.append(ref.subject)
        terms.extend(ref.modifiers)
        terms.extend(ref.terms)
        for mod in ref.modifiers:
            terms.append(f"{ref.subject} {mod}")
            for anchor in anchors:
                terms.append(f"{ref.subject} {anchor}")
                if mod:
                    terms.append(f"{ref.subject} {mod} {anchor}")
    return _dedupe_terms(terms)


def text_matches_subject_inference(text: str, query: str) -> bool:
    """
    True when text contains a known subject from the query and an inference anchor
    (automation, robot, AMR, …) — exact phrase like "lab automation" not required.
    """
    hay = normalize_term(text)
    if not hay:
        return False
    refs = resolve_subject_refs(query)
    if not refs:
        return False
    if not _has_inference_anchor(hay):
        return False
    for ref in refs:
        if not _subject_in_text(ref.subject, hay):
            continue
        if ref.modifiers and any(mod in hay for mod in ref.modifiers):
            return True
        if any(term in hay for term in ref.terms):
            return True
        if _subject_in_text(ref.subject, hay):
            return True
    return False


def infer_industries_from_subject_automation(text: str) -> Dict[str, int]:
    """Boost canonical industries when subject + inference anchor appear in signal text."""
    hay = normalize_term(text)
    if not hay or not _has_inference_anchor(hay):
        return {}
    boosts: Dict[str, int] = {}
    for ref in _subject_refs():
        if not _subject_in_text(ref.subject, hay):
            continue
        weight = 2 if ref.modifiers and any(m in hay for m in ref.modifiers) else 1
        for ind in ref.canonical_industries:
            boosts[ind] = max(boosts.get(ind, 0), weight)
    return boosts


def _collect_sector_bundle(sector: dict) -> Tuple[List[str], List[str]]:
    """Return canonical labels (original case) + all sector expansion terms."""
    canonical: List[str] = list(sector.get("canonical_industries") or [])
    terms: List[str] = list(sector.get("root_aliases") or [])
    terms.append(sector.get("label", ""))

    subs = sector.get("sub_ontologies") or {}
    for sub in subs.values():
        terms.append(sub.get("label", ""))
        if sub.get("subject"):
            terms.append(sub["subject"])
            terms.extend(sub.get("modifiers") or [])
        terms.extend(sub.get("terms") or [])
    return canonical, terms


def _collect_matched_sub_terms(sector: dict, sub_ids: Set[str]) -> List[str]:
    """Terms from matched sub-ontologies only — avoids cross-sub-ontology bleed."""
    terms: List[str] = []
    subs = sector.get("sub_ontologies") or {}
    for sub_id in sub_ids:
        if sub_id in ("__root__", "__sector__", "__canonical__"):
            continue
        sub = subs.get(sub_id) or {}
        terms.append(sub.get("label", ""))
        if sub.get("subject"):
            terms.append(sub["subject"])
            terms.extend(sub.get("modifiers") or [])
        terms.extend(sub.get("terms") or [])
    return terms


def match_ontology_query(query: str) -> OntologyMatch:
    q = normalize_term(query)
    if not q:
        return OntologyMatch()

    index = _term_index()
    matched_sector_subs: Dict[str, Set[str]] = {}
    sector_full_match: Set[str] = set()
    direct_terms: List[str] = [q]

    for term_key, refs in index.items():
        if not _term_matches_query(term_key, q):
            continue
        direct_terms.append(term_key)
        for sector_id, sub_id, raw in refs:
            direct_terms.append(raw)
            if sub_id in ("__root__", "__sector__", "__canonical__"):
                sector_full_match.add(sector_id)
            else:
                matched_sector_subs.setdefault(sector_id, set()).add(sub_id)

    for ref in resolve_subject_refs(q):
        matched_sector_subs.setdefault(ref.sector_id, set()).add(ref.sub_id)
        direct_terms.append(ref.subject)
        direct_terms.extend(ref.modifiers)
        direct_terms.extend(ref.terms)

    for sector_id in sector_full_match:
        matched_sector_subs.setdefault(sector_id, set())

    if not matched_sector_subs:
        subject_terms = subject_inference_terms(q)
        if subject_terms:
            return OntologyMatch(expansion_terms=_dedupe_terms([q, *subject_terms]))
        return OntologyMatch(expansion_terms=_dedupe_terms(direct_terms))

    canonical_out: List[str] = []
    terms_out: List[str] = list(direct_terms)
    sector_ids: List[str] = []
    sub_ids_out: List[str] = []

    for sector in load_sector_ontology().get("sectors", []):
        sid = sector["id"]
        if sid not in matched_sector_subs:
            continue
        sector_ids.append(sid)
        sub_ids = matched_sector_subs[sid]
        sub_ids_out.extend(sorted(sub_ids))
        canonical, _all_terms = _collect_sector_bundle(sector)
        canonical_out.extend(canonical)
        specific_subs = {s for s in sub_ids if s not in ("__root__", "__sector__", "__canonical__")}
        if sid in sector_full_match or not specific_subs:
            terms_out.extend(_all_terms)
        else:
            terms_out.extend(_collect_matched_sub_terms(sector, sub_ids))
            terms_out.extend(sector.get("root_aliases") or [])

    terms_out.extend(subject_inference_terms(q))
    return OntologyMatch(
        canonical_industries=_dedupe_canonical(canonical_out),
        expansion_terms=_dedupe_terms(terms_out),
        sector_ids=_dedupe_terms(sector_ids),
        sub_ontology_ids=_dedupe_terms(sub_ids_out),
    )


def all_sector_expansion_terms() -> List[str]:
    terms: List[str] = []
    for sector in load_sector_ontology().get("sectors", []):
        _, bundle = _collect_sector_bundle(sector)
        terms.extend(bundle)
        terms.extend(sector.get("canonical_industries") or [])
    return _dedupe_terms(terms)


def pipeline_diversity_industries() -> Tuple[str, ...]:
    seen: Set[str] = set()
    out: List[str] = []
    for sector in load_sector_ontology().get("sectors", []):
        for ind in sector.get("canonical_industries") or []:
            if ind not in seen:
                seen.add(ind)
                out.append(ind)
    priority = (
        "Food Service",
        "Hospitality",
        "Logistics",
        "Healthcare",
        "Medical Technology",
        "Airports & Aviation",
        "Automotive & Manufacturing",
        "Datacenters",
        "Food Processing & Manufacturing",
        "Retail",
        "Real Estate & Facilities",
        "Defense",
        "Energy & Utilities",
    )
    ordered = [p for p in priority if p in seen]
    for ind in out:
        if ind not in ordered:
            ordered.append(ind)
    return tuple(ordered[:10])


def _dedupe_terms(items: List[str]) -> List[str]:
    seen: Set[str] = set()
    out: List[str] = []
    for raw in items:
        t = normalize_term(raw)
        if not t or t in seen:
            continue
        seen.add(t)
        out.append(t)
    return out


def _dedupe_canonical(items: List[str]) -> List[str]:
    seen: Set[str] = set()
    out: List[str] = []
    for raw in items:
        label = (raw or "").strip()
        key = label.lower()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(label)
    return out
