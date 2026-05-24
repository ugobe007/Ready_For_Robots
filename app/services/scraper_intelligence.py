"""
Unified scraper intelligence stack.

Wires Markdown + Python ontologies, signal classifier, junk filter, logic engine
(is_valid_lead), lead inference dossier, inference-engine scoring, and website
enrichment for all ingestion scrapers — not only the intelligence news scraper.
"""
from __future__ import annotations

import logging
from typing import Any, List, Optional, Tuple

logger = logging.getLogger(__name__)


def classify_article_signals(
    text: str,
    *,
    article_url: str = "",
    rss_source_name: str = "",
) -> List[str]:
    """Ontology + rules-engine signal typing (Markdown vocab + Python CONCEPTS)."""
    from app.services.signal_classifier import classify_signals_with_fallback

    try:
        return classify_signals_with_fallback(
            text,
            article_url=article_url or None,
            rss_source_name=rss_source_name or None,
        )
    except Exception as exc:
        logger.warning("classify_article_signals failed, using ['news']: %s", exc)
        return ["news"]


def primary_signal_type(
    text: str,
    *,
    article_url: str = "",
    rss_source_name: str = "",
) -> str:
    """Best signal type for DB storage — ontology-first, keyword fallback."""
    from app.services.signal_classifier import primary_signal_type_for_text

    types = classify_article_signals(
        text, article_url=article_url, rss_source_name=rss_source_name
    )
    if types:
        return types[0]
    try:
        return primary_signal_type_for_text(text, article_url=article_url or None)
    except Exception:
        return "news"


def gate_lead_candidate(
    company_name: str,
    context_text: str = "",
    *,
    article_url: str = "",
    industry: Optional[str] = None,
    signal_types: Optional[List[str]] = None,
) -> Tuple[bool, Any]:
    """
    Full lead inference gate: is_junk → text_classifier → is_valid_lead → buyer intent.
    Returns (accepted, dossier).
    """
    from app.services.lead_inference_engine import evaluate_lead_candidate

    dossier = evaluate_lead_candidate(
        company_name=company_name,
        context_text=context_text,
        article_url=article_url or None,
        signal_types=signal_types,
        industry=industry,
        is_new_company=True,
    )
    return dossier.is_lead, dossier


def score_intent_strength(
    text: str,
    *,
    company_name: str = "",
    industry: Optional[str] = None,
) -> float:
    """Inference-engine overall_intent (0–1) for signal strength."""
    from app.services.inference_engine import analyze

    combined = f"{company_name} {industry or ''} {text}".strip()
    result = analyze(combined[:3000], industry=industry or None)
    return round(min(result.overall_intent, 1.0), 4)


def enrich_new_company_website(company, *, sleep_s: float = 0.5) -> None:
    """OpenAI → DuckDuckGo → brand slug website waterfall."""
    if getattr(company, "website", None):
        return
    try:
        from app.services.lead_enrichment import enrich_company_website

        enrich_company_website(company, sleep_s=sleep_s)
    except Exception as exc:
        logger.debug("Website enrich failed for %r: %s", getattr(company, "name", ""), exc)


def persist_dossier(company, dossier, db) -> None:
    """Store lead inference dossier on company.crm_metadata."""
    from app.services.lead_inference_engine import persist_lead_inference

    if dossier and getattr(dossier, "is_lead", False):
        persist_lead_inference(company, dossier, db)
