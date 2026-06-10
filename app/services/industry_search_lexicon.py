"""
Industry / vertical search lexicon — sector sub-ontologies for pipeline search,
API filters, and scraper keyword expansion.

Source of truth: app/data/industry_sector_ontology.json (via industry_sector_ontology.py)
"""
from __future__ import annotations

import re
from typing import List

from app.services.industry_sector_ontology import (
    match_ontology_query,
    normalize_term,
    pipeline_diversity_industries,
    resolve_subject_refs,
    term_in_text,
    text_matches_subject_inference,
)

# Common search typos / shorthand → ontology lookup key
_QUERY_ALIASES = {
    "manufacting": "manufacturing",
    "package handing": "package handling",
    "intra logistic": "intra logistics",
    "micro logistic": "micro logistics",
    "light logistic": "light logistics",
    "warehouse logistic": "warehouse logistics",
    "grocery fulfilment": "grocery fulfillment",
    "grocery fulfilment automation": "grocery fulfillment automation",
    "janitorial": "janitorial automation",
    "housekeeping": "housekeeping automation",
    "hotel": "hotel automation",
    "out patient": "outpatient",
    "er": "emergency room",
    "ed": "emergency room",
    "datacenter": "data center",
    "qsr": "quick serve",
    "carwash": "car wash",
    "truckstop": "truck stop",
}


def normalize_search_query(query: str) -> str:
    return normalize_term(query)


def _resolve_query(query: str) -> str:
    q = normalize_search_query(query)
    return _QUERY_ALIASES.get(q, q)


def expand_search_terms(query: str) -> List[str]:
    """Return query + sector sub-ontology aliases for substring matching."""
    q = _resolve_query(query)
    if not q:
        return []
    match = match_ontology_query(q)
    terms = [q]
    if query.strip().lower() != q:
        terms.append(normalize_search_query(query))
    terms.extend(match.expansion_terms)
    terms.extend(normalize_term(ind) for ind in match.canonical_industries)
    return _dedupe(terms)


def canonical_industries_for_query(query: str) -> List[str]:
    q = _resolve_query(query)
    if not q:
        return []
    return match_ontology_query(q).canonical_industries


def industry_label_matches_query(industry: str, query: str) -> bool:
    """True if stored industry matches user search via sector ontology."""
    if not query:
        return True
    ind_l = (industry or "").lower()
    q = _resolve_query(query)
    if q in ind_l:
        return True
    for canonical in canonical_industries_for_query(q):
        c = canonical.lower()
        if c in ind_l or ind_l in c:
            return True
    for term in expand_search_terms(q):
        if term in ind_l:
            return True
    return False


def text_matches_industry_search(text: str, query: str) -> bool:
    """Match query against free text (signals, company name) using ontology."""
    if not query:
        return True
    hay = normalize_term(text)
    q = _resolve_query(query)
    if not hay:
        return False
    if term_in_text(q, hay):
        return True
    subject_refs = resolve_subject_refs(q)
    if subject_refs and text_matches_subject_inference(hay, q):
        return True
    match = match_ontology_query(q)
    for term in match.expansion_terms:
        if term_in_text(term, hay):
            if subject_refs:
                return text_matches_subject_inference(hay, q)
            return True
    if subject_refs:
        return False
    return text_matches_subject_inference(hay, q)


def lead_matches_search(
    query: str,
    *,
    industry: str = "",
    company_name: str = "",
    signal_text: str = "",
    location: str = "",
) -> bool:
    q = _resolve_query(query)
    if not q:
        return True
    if industry_label_matches_query(industry, q):
        return True
    blob = " ".join([company_name, signal_text, location]).lower()
    return text_matches_industry_search(blob, q)


PIPELINE_DIVERSITY_INDUSTRIES = pipeline_diversity_industries()


def _dedupe(items: List[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for raw in items:
        t = normalize_term(raw)
        if not t or t in seen:
            continue
        seen.add(t)
        out.append(t)
    return out
