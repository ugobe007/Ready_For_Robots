"""
Lead Filter Service
===================
Two-stage pipeline applied to every lead before it surfaces in the API or dashboard:

  Stage 1 — JUNK FILTER: removes noise (scraped 404 pages, test artifacts, gibberish)
  Stage 2 — PRIORITY TIER: ranks clean leads as HOT / WARM / COLD

Usage
-----
  from app.services.lead_filter import classify_lead, is_junk, TIERS

  tier, reasons = classify_lead(company, score, signals)
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional

# ─── Junk detection ───────────────────────────────────────────────────────────

# Exact / partial strings that always mean the record is garbage
_JUNK_SUBSTRINGS = [
    "404", "not found", "page not found", "error", "access denied",
    "forbidden", "503 service", "502 bad gateway", "just a moment",
    "attention required", "cloudflare", "captcha", "enable javascript",
    "loading…", "loading...", "please wait", "robot check",
    "test company", "test lead", "sample company", "demo company",
    "n/a", "unknown", "unnamed", "placeholder", "no name",
    "untitled", "company name", "your company",
]

# Regex patterns on the raw name (lowercased)
_JUNK_PATTERNS = [
    r"^\s*$",                          # blank / whitespace only
    r"^[\W\d_]+$",                     # no letters at all
    r"^.{1,2}$",                       # too short (1-2 chars)
    r"^(inc|llc|corp|ltd|co|company)\.?$",   # generic legal suffixes alone
    r"https?://",                      # accidentally captured a URL
    r"<[^>]+>",                        # HTML tags leaked in
    r"^\d+$",                          # all digits
    r"[^\x00-\x7F]{3,}",              # more than 2 non-ASCII chars (encoding garbage)
]
_JUNK_RE = [re.compile(p, re.IGNORECASE) for p in _JUNK_PATTERNS]


def is_junk(name: Optional[str]) -> tuple[bool, str]:
    """
    Returns (True, reason) if the company name looks like scraper garbage.
    Returns (False, '') for clean names.
    """
    if not name:
        return True, "empty name"

    low = name.strip().lower()

    for sub in _JUNK_SUBSTRINGS:
        if sub in low:
            return True, f"junk substring: '{sub}'"

    for rx in _JUNK_RE:
        if rx.search(name.strip()):
            return True, f"junk pattern: {rx.pattern}"

    return False, ""


# ─── Priority tier ────────────────────────────────────────────────────────────

TIERS = ("HOT", "WARM", "COLD")

# Industries where Richtech robots have the strongest fit
_HIGH_FIT_INDUSTRIES = {
    "hospitality", "hotel", "hotel & hospitality",
    "logistics", "supply chain", "3pl", "distribution",
    "healthcare", "hospital", "senior living", "assisted living",
    "food service", "food & beverage", "restaurant", "catering",
    "warehouse", "fulfillment",
}

# Signal types that are strong buying-intent signals
# HOT  → company has budget + mandate → priority outreach
# WARM → confirmed pain or expansion → nurture / sequence
_HOT_SIGNAL_TYPES  = {
    "funding_round",   # money just raised
    "strategic_hire",  # ops decision-maker just hired
    "capex",           # active technology spend
    "ma_activity",     # M&A = new leadership + integration need
    "labor_pain",      # mass hiring of manual workers = pain to automate
    "automation_intent",  # company running lean / process-improvement programs
}
_WARM_SIGNAL_TYPES = {
    "expansion",         # new facility — needs equipment
    "job_posting",       # general ops posting
    "labor_shortage",    # urgency language in postings
    "news",              # general press mention
    "service_consistency",  # franchise / brand standard drive
    "equipment_integration", # WMS / ERP rollout — robot-ready infra
}


@dataclass
class PriorityResult:
    tier: str                        # HOT | WARM | COLD
    score: float                     # 0–100
    reasons: List[str] = field(default_factory=list)


def _industry_fits(industry: Optional[str]) -> bool:
    if not industry:
        return False
    low = industry.lower()
    return any(k in low for k in _HIGH_FIT_INDUSTRIES)


def priority_tier(
    overall_score: float,
    industry: Optional[str],
    signal_types: List[str],
    signal_count: int,
    employee_estimate: Optional[int] = None,
) -> PriorityResult:
    """
    Compute a priority tier independently of the inference engine score.
    Combines rule-based boosters with the overall ML score.
    """
    reasons: List[str] = []
    boost = 0.0

    # Base: ML inference score drives the tier
    base = overall_score

    # Industry fit boost
    if _industry_fits(industry):
        boost += 8.0
        reasons.append(f"high-fit industry ({industry})")

    # Signal type boosters
    hot_hits = [s for s in signal_types if s in _HOT_SIGNAL_TYPES]
    warm_hits = [s for s in signal_types if s in _WARM_SIGNAL_TYPES]
    if hot_hits:
        boost += 5.0 * len(hot_hits)
        reasons.append(f"intent signals: {', '.join(hot_hits)}")
    if warm_hits:
        boost += 2.0 * len(warm_hits)

    # Signal volume boost
    if signal_count >= 5:
        boost += 4.0
        reasons.append(f"{signal_count} signals")
    elif signal_count >= 3:
        boost += 2.0

    # Employee size boost (enterprise = more budget)
    if employee_estimate and employee_estimate >= 5000:
        boost += 5.0
        reasons.append(f"enterprise ({employee_estimate:,} employees)")
    elif employee_estimate and employee_estimate >= 1000:
        boost += 2.0

    composite = min(100.0, base + boost)

    if composite >= 75 or (base >= 65 and hot_hits):
        return PriorityResult("HOT", composite, reasons)
    if composite >= 50 or (base >= 40 and _industry_fits(industry)):
        return PriorityResult("WARM", composite, reasons)
    return PriorityResult("COLD", composite, reasons)


# ─── Convenience wrapper ──────────────────────────────────────────────────────

def classify_lead(company, score, signals) -> tuple[bool, str, PriorityResult]:
    """
    Full classification for a single lead.

    Returns:
        (junk: bool, junk_reason: str, priority: PriorityResult)

    If junk is True, priority tier will be 'COLD' with no reasons.
    """
    junk, junk_reason = is_junk(getattr(company, "name", None))
    if junk:
        return True, junk_reason, PriorityResult("COLD", 0.0, [junk_reason])

    overall = getattr(score, "overall_intent_score", 0.0) if score else 0.0
    sig_types = [s.signal_type for s in (signals or [])]
    sig_count = len(signals or [])
    emp = getattr(company, "employee_estimate", None)

    pri = priority_tier(overall, company.industry, sig_types, sig_count, emp)
    return False, "", pri
