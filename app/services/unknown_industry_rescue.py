"""
Unknown-industry rescue: apply ontology-backed industry labels or quarantine headline stubs.

Used by ``scripts/rescue_unknown_industry_ontology.py`` after RSS/partnership cleanup.
"""
from __future__ import annotations

import re
from typing import Optional, Sequence, Tuple

from app.services.industry_inference import (
    effective_industry_for_lead,
    known_industry_for_company_name,
    should_skip_industry_reinfer_for_company_name,
)
from app.services.lead_filter import is_headline_fragment, is_junk
from app.services.rss_noise_lead import is_unknown_industry

_UNKNOWN_OUT = frozenset({"unknown", "new", "other", ""})

# RSS name-extraction stubs that pass ``is_junk`` but are not operating companies.
_HEADLINE_STUB_RES = (
    re.compile(r"(?i)\bceo\b.+\b(huang|musk|bezos|lecun|pichai|cook|zuckerberg|nadella)\b"),
    re.compile(r"(?i)^(moving beyond|islanders need|overtime as|overtime:|washington brings its)\b"),
    re.compile(r"(?i)\b(ot costs|spent \$|and welfare budget|sees softness|deep dive)\b"),
    re.compile(r"(?i)^(shanghai|federal|buddy|processors|convenience stores|medical devices?)\s*$"),
    re.compile(r"(?i)\bstock\)\s*$"),
    re.compile(r"(?i)^(europe artificial intelligence|medical device makers|hiring hotspots)\b"),
    re.compile(r"(?i)^(global capex|material handling drives demand|uv-c pharma robot rollout)\b"),
    re.compile(r"(?i)^(block shares jump|lucid \(lcid\)|digital budgets|record \$)\b"),
    re.compile(r"(?i)^(jobs: who|while wendy|future-proof|deflation bites)\b"),
    re.compile(r"(?i)^(new mexico quantum company|popular south jersey|north carolina treasurer)\b"),
    re.compile(r"(?i)^(key message update|food exec brief|scv news|techmediabreaks)\b"),
    re.compile(r"(?i)^(operators skipping|career moves|packaging machinery:)\b"),
)


def is_unknown_industry_headline_stub(name: Optional[str]) -> Tuple[bool, str]:
    raw = (name or "").strip()
    if not raw:
        return True, "empty name"
    hf, hr = is_headline_fragment(raw)
    if hf:
        return True, hr
    for rx in _HEADLINE_STUB_RES:
        if rx.search(raw):
            return True, "unknown-industry headline stub"
    return False, ""


def unknown_industry_rescue_action(
    company_name: Optional[str],
    industry: Optional[str],
    signals: Sequence[object],
) -> Tuple[str, str, str]:
    """
    Returns (action, value, reason).

    action:
      - ``apply`` — persist ``value`` as industry
      - ``quarantine`` — soft-hide (headline stub / junk name)
      - ``skip`` — leave unchanged
    """
    name = (company_name or "").strip()
    if not is_unknown_industry(industry):
        return "skip", "", "not unknown industry"

    junk, junk_reason = is_junk(name)
    if junk:
        return "quarantine", "", junk_reason

    stub, stub_reason = is_unknown_industry_headline_stub(name)
    if stub:
        return "quarantine", "", stub_reason

    if should_skip_industry_reinfer_for_company_name(name):
        return "quarantine", "", "non-company name (person/event/geo)"

    known = known_industry_for_company_name(name)
    if known:
        return "apply", known, f"known company map → {known}"

    inferred = effective_industry_for_lead(name, industry, signals)
    if inferred.strip().lower() not in _UNKNOWN_OUT:
        return "apply", inferred, f"inferred → {inferred}"

    return "skip", "", "still unknown after ontology inference"
