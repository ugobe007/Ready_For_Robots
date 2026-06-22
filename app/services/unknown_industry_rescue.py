"""
Unknown-industry rescue: apply ontology-backed industry labels or quarantine headline stubs.

Used by ``scripts/rescue_unknown_industry_ontology.py`` after RSS/partnership cleanup.
"""
from __future__ import annotations

import re
from typing import Optional, Sequence, Tuple

from app.services.company_name_validation import is_inferred_automation_vendor
from app.services.industry_inference import (
    effective_industry_for_lead,
    known_industry_for_company_name,
    should_skip_industry_reinfer_for_company_name,
)
from app.services.lead_filter import is_headline_fragment, is_junk
from app.services.robot_vendor_names import is_known_robotics_vendor_name
from app.services.rss_noise_lead import (
    entity_is_noise_headline,
    is_market_report_company_name,
    is_unknown_industry,
    signals_are_market_research_noise,
)

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
    re.compile(r"(?i)^(block shares jump|lucid \(lcid\)|lucid \(lcid\) stock|digital budgets|record \$)\b"),
    re.compile(r"(?i)^(jobs: who|while wendy|future-proof|deflation bites)\b"),
    re.compile(r"(?i)^(new mexico quantum company|popular south jersey|north carolina treasurer)\b"),
    re.compile(r"(?i)^(key message update|food exec brief|scv news|techmediabreaks)\b"),
    re.compile(r"(?i)^(operators skipping|career moves|packaging machinery:)\b"),
    re.compile(r"(?i)^(labor pains|fired nps|kerala ahead|2025:\s*the year)\b"),
    re.compile(r"(?i)^(overtime:\s*as|uk firm|wsu'?s)\b"),
    re.compile(r"(?i)\b(strategic business|disinfection product|port infrastructure)\b"),
    re.compile(r"(?i)^(drum dollies|guide rings|uvc disinfection)\b"),
    re.compile(r"(?i)^(oracle q2|invivoscribe|yann lecun)\b"),
    re.compile(r"(?i)\b(apple-picker|inflatable robotic)\b"),
    re.compile(r"(?i)^(redevelopment commission|otc welcomes|faa approves|eu pressures)\b"),
    re.compile(r"(?i)^(food dairy corn|fish freezing plant|major european tissue|rok profitable)\b"),
    re.compile(r"(?i)^(sweetwater expansion|rethinking india|global solar capex|hplc 2025)\b"),
    re.compile(r"(?i)^(ai use after|new major tn survey|arizona dps|low snow|billionaire brad)\b"),
    re.compile(r"(?i)^(michigan nurses|rochester police|lift off together|interpack 2026)\b"),
    re.compile(r"(?i)my voice matters"),
    re.compile(r"(?i)^(india full-truck-load|world material handling)\b"),
    re.compile(r"(?i)^(hanbit unit|standar|ioa championship|porter)\s*$"),
    re.compile(r"(?i)\bvc cultivate\b"),
)

# Product / vendor PR names scraped as buyer rows (not in OEM blocklist yet).
_VENDOR_PR_NAMES = frozenset(
    {
        "flippy",
        "mbody ai",
        "miso robotics",
        "miso robot",
        "chef robotics",
        "picoclaw ai",
        "world labs",
    }
)


def _is_vendor_oem_pr_entity(name: str) -> Tuple[bool, str]:
    low = name.strip().lower()
    low_base = re.sub(r"\s+(inc|corp|corporation|llc|ltd)\.?$", "", low, flags=re.I)
    if low in _VENDOR_PR_NAMES or low_base in _VENDOR_PR_NAMES:
        return True, "robotics vendor / OEM PR (not a buyer opportunity)"
    if is_known_robotics_vendor_name(name):
        return True, "robotics vendor / OEM (not a buyer opportunity)"
    if is_inferred_automation_vendor(name):
        return True, "name pattern matches automation/robotics vendor"
    return False, ""


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

    vendor, vendor_reason = _is_vendor_oem_pr_entity(name)
    if vendor:
        return "quarantine", "", vendor_reason

    if is_market_report_company_name(name):
        return "quarantine", "", "market research / industry report headline"

    noise, noise_reason = entity_is_noise_headline(name)
    if noise:
        return "quarantine", "", noise_reason

    known = known_industry_for_company_name(name)
    if known:
        return "apply", known, f"known company map → {known}"

    inferred = effective_industry_for_lead(name, industry, signals)
    if inferred.strip().lower() not in _UNKNOWN_OUT:
        return "apply", inferred, f"inferred → {inferred}"

    if signals_are_market_research_noise(signals):
        return "quarantine", "", "market research signal noise"

    return "skip", "", "still unknown after ontology inference"
