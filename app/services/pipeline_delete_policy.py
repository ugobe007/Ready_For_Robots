"""
Central policy for hard-deleting ``companies`` rows.

Aligns destructive scripts with ``scripts/cleanup_leads.py`` phase 1:
only ``is_valid_lead(name)`` failures may be permanently removed.

Never hard-delete for:
  - ``is_internal=False`` (rectifier quarantine — already hidden from API)
  - Google RSS / HTML signal storage format
  - ``classify_lead`` buyer-opportunity gate failure (display-tier junk only)
  - thin / RSS-only signal corpora when the stored name still passes validation
"""
from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Sequence

from app.services.company_validator import is_valid_lead
from app.services.industry_inference import known_industry_for_company_name
from app.services.known_brands import is_allowlisted_company_name


def is_quarantined(company: object) -> bool:
    """Rectifier sets is_internal=False — soft-hide, not a delete signal."""
    return getattr(company, "is_internal", True) is False


def hard_delete_allowed(
    company: object,
    signals: Sequence[object] | None = None,
) -> tuple[bool, str, str]:
    """
    Returns (allowed, reason, bucket).

    ``signals`` is accepted for API symmetry but is not used for delete decisions.
    """
    _ = signals

    if is_quarantined(company):
        return False, "", ""

    name = (getattr(company, "name", None) or "").strip()
    if not name:
        return True, "empty name", "invalid_name"

    if is_allowlisted_company_name(name) or known_industry_for_company_name(name):
        return False, "", ""

    ok, reason = is_valid_lead(name, skip_external_checks=True)
    if not ok:
        return True, reason, "invalid_name"

    return False, "", ""


def unknown_industry_delete_allowed(
    company_name: str | None,
    industry: str | None,
    signals: Sequence[object] | None = None,
    *,
    from_is_junk: tuple[bool, str] | None = None,
) -> tuple[bool, str, str]:
    """
    Narrow delete gate for Unknown-industry cleanup scripts.

    Name must fail ``is_junk`` or high-confidence headline entity classification.
    RSS/HTML signal format alone is never sufficient.
    """
    from app.services.lead_filter import is_junk
    from app.services.rss_noise_lead import (
        entity_is_noise_headline,
        is_unknown_industry,
        signals_are_market_research_noise,
    )

    name = (company_name or "").strip()
    if not is_unknown_industry(industry):
        return False, "", ""

    if is_allowlisted_company_name(name) or known_industry_for_company_name(name):
        return False, "", ""

    if from_is_junk is not None:
        junk, reason = from_is_junk
    else:
        junk, reason = is_junk(name)

    if junk:
        return True, reason, "fast_junk"

    ent_ok, ent_reason = entity_is_noise_headline(name, min_confidence=0.78)
    if ent_ok:
        return True, ent_reason, "headline_entity"

    if signals_are_market_research_noise(signals or []) and len(name) >= 40:
        return True, "market research / industry report headline", "market_report_noise"

    return False, "", ""


def unknown_rss_noise_quarantine_allowed(
    company_name: str | None,
    industry: str | None,
    signals: Sequence[object] | None = None,
    *,
    from_is_junk: tuple[bool, str] | None = None,
    from_classify: tuple[bool, str, Any] | None = None,
) -> tuple[bool, str, str]:
    """
    Soft-hide gate for Unknown-industry RSS / report spam (rectifier quarantine).

    Quarantine when the name is junk or classify_lead marks display junk, but never
    when the name is a known brand or maps to a real industry via inference.
    """
    from app.services.lead_filter import classify_lead, is_junk
    from app.services.rss_noise_lead import (
        entity_is_noise_headline,
        is_market_report_company_name,
        is_unknown_industry,
        signals_are_market_research_noise,
        signals_predominantly_rss_html,
    )

    name = (company_name or "").strip()
    if not is_unknown_industry(industry):
        return False, "", ""

    if is_allowlisted_company_name(name):
        return False, "", ""

    if known_industry_for_company_name(name):
        return False, "", ""

    if from_is_junk is not None:
        junk, reason = from_is_junk
    else:
        junk, reason = is_junk(name)
    if junk:
        return True, reason, "junk_name"

    if is_market_report_company_name(name):
        return True, "market research / industry report headline", "market_report_name"

    if from_classify is not None:
        junk_c, reason_c, _tier = from_classify
    else:
        junk_c, reason_c, _tier = classify_lead(
            SimpleNamespace(
                name=name,
                industry=industry,
                is_internal=True,
                employee_estimate=None,
            ),
            None,
            signals or [],
        )
    if junk_c:
        return True, reason_c, "display_junk"

    if signals_predominantly_rss_html(signals or []) and signals_are_market_research_noise(
        signals or []
    ):
        ent_ok, ent_reason = entity_is_noise_headline(name, min_confidence=0.72)
        if ent_ok:
            return True, ent_reason, "market_report_rss"

    return False, "", ""
