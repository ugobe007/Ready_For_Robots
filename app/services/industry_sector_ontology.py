"""
Sector sub-ontologies for industry search, inference, and scraper discovery.

Source of truth: app/data/industry_sector_ontology.json
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Set, Tuple

_ONTOLOGY_PATH = Path(__file__).resolve().parent.parent / "data" / "industry_sector_ontology.json"


def normalize_term(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


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
def _term_index() -> Dict[str, List[Tuple[str, str, str]]]:
    """
    normalized_term -> [(sector_id, sub_id, raw_term), ...]
    Indexes root aliases, sub-ontology terms, and sector labels.
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
            for term in sub.get("terms", []):
                _add(term, sid, sub_id)
    return index


def _term_matches_query(term: str, query: str) -> bool:
    if not term or not query:
        return False
    if term == query:
        return True
    if len(query) >= 4 and query in term:
        return True
    if len(term) >= 4 and term in query:
        return True
    return False


def _collect_sector_bundle(sector: dict) -> Tuple[List[str], List[str]]:
    """Return canonical labels (original case) + all sector expansion terms."""
    canonical: List[str] = list(sector.get("canonical_industries") or [])
    terms: List[str] = list(sector.get("root_aliases") or [])
    terms.append(sector.get("label", ""))

    subs = sector.get("sub_ontologies") or {}
    for sub in subs.values():
        terms.append(sub.get("label", ""))
        terms.extend(sub.get("terms") or [])
    return canonical, terms


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

    for sector_id in sector_full_match:
        matched_sector_subs.setdefault(sector_id, set())

    if not matched_sector_subs:
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
        canonical, terms = _collect_sector_bundle(sector)
        canonical_out.extend(canonical)
        terms_out.extend(terms)

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
    # Keep preview rotation focused on buyer verticals reps search most.
    priority = (
        "Food Service",
        "Hospitality",
        "Logistics",
        "Healthcare",
        "Manufacturing",
        "Retail",
        "Real Estate & Facilities",
    )
    ordered = [p for p in priority if p in seen]
    for ind in out:
        if ind not in ordered:
            ordered.append(ind)
    return tuple(ordered[:8])


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
