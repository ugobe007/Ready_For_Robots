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

# Industries where automation robots have the strongest fit
_HIGH_FIT_INDUSTRIES = {
    "hospitality", "hotel", "hotel & hospitality",
    "logistics", "supply chain", "3pl", "distribution",
    "healthcare", "hospital", "senior living", "assisted living",
    "food service", "food & beverage", "restaurant", "catering",
    "warehouse", "fulfillment",
}

# Signal types — exported for SQL rollups (leads API) so summary/homepage match classify_lead.
# HOT  → budget / mandate / deployment — priority outreach
# WARM → pain, expansion, exploration — nurture & watch
# API still emits tier COLD internally; product copy calls it "Emerging" (all have potential).
SIGNAL_TYPES_HOT = frozenset({
    "funding_round",
    "strategic_hire",
    "capex",
    "ma_activity",
    "labor_pain",
    "automation_intent",       # internal / job-board style
    "quality_bottleneck",
    "safety_incident",
    "production_capacity",
    "warehouse_throughput",
    "packaging_automation",
    "repetitive_process",
    # Deployment & procurement (often missing before — same deals always surfaced)
    "robot_installation",
    "pilot_success",
    "scale_expansion",
    "vendor_selection",
    "roi_documented",
    "economics_driven",
    "competitive_response",
    "problem_solution",
    "government_contract",
    "rfp_posted",
})
SIGNAL_TYPES_WARM = frozenset({
    "expansion",
    "job_posting",
    "labor_shortage",
    "news",
    "service_consistency",
    "equipment_integration",
    "material_handling",
    # Classifier emits automation_interest widely — treat as explore/nurture, not max HOT
    "automation_interest",
})

# Aliases for membership checks in priority_tier (frozenset supports `in`)
_HOT_SIGNAL_TYPES = SIGNAL_TYPES_HOT
_WARM_SIGNAL_TYPES = SIGNAL_TYPES_WARM

# One strong deployment/procurement hit can justify HOT with moderate ML score
_DEPLOYMENT_SIGNAL_TYPES = frozenset({
    "robot_installation", "pilot_success", "scale_expansion", "vendor_selection", "rfp_posted",
})


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


def _hot_signal_boost(hot_types: List[str]) -> float:
    """
    Cap how much raw signal *count* can inflate the tier. Previously every row in
    `signals` repeated the same type (e.g. many `news` mis-tagged as hot bucket
    in SQL rollups) and added +5 each → composite pegged at 100 and HOT flooded.
    """
    if not hot_types:
        return 0.0
    n = len(hot_types)
    u = len(set(hot_types))
    # Diversity: up to +10 for 2+ distinct hot types; volume: sublinear, capped
    diversity = min(10.0, 5.0 * min(2, u))
    extra_same = max(0, n - u)
    volume = min(8.0, 1.2 * min(6, extra_same) + 0.8 * min(3, u))
    return min(16.0, diversity + volume)


def _warm_signal_boost(warm_types: List[str]) -> float:
    if not warm_types:
        return 0.0
    n = len(warm_types)
    u = len(set(warm_types))
    return min(8.0, 2.0 * min(3, u) + 0.6 * min(5, max(0, n - u)))


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

    # Industry fit boost (was 8 — too many WARM/HOT via industry alone)
    if _industry_fits(industry):
        boost += 5.0
        reasons.append(f"high-fit industry ({industry})")

    # Signal type boosters (capped — do not let N duplicate rows max out composite)
    hot_hits = [s for s in signal_types if s in _HOT_SIGNAL_TYPES]
    warm_hits = [s for s in signal_types if s in _WARM_SIGNAL_TYPES]
    if hot_hits:
        boost += _hot_signal_boost(hot_hits)
        unique_hot = list(dict.fromkeys(hot_hits))[:5]
        if len(hot_hits) > 5:
            reasons.append(f"{len(hot_hits)} hot-type signals ({', '.join(unique_hot)}, ...)")
        else:
            reasons.append(f"{len(hot_hits)} hot-type signals ({', '.join(unique_hot)})")
    if warm_hits:
        boost += _warm_signal_boost(warm_hits)

    # Signal volume boost (mild — type boosts already reflect volume somewhat)
    if signal_count >= 8:
        boost += 3.0
        reasons.append(f"{signal_count} signals")
    elif signal_count >= 5:
        boost += 2.0
    elif signal_count >= 3:
        boost += 1.0

    # Employee size boost (enterprise = more budget)
    if employee_estimate and employee_estimate >= 5000:
        boost += 5.0
        reasons.append(f"enterprise ({employee_estimate:,} employees)")
    elif employee_estimate and employee_estimate >= 1000:
        boost += 2.0

    composite = min(100.0, base + boost)

    # HOT: stricter. Duplicate rows of one hot type (e.g. RSS noise) must not
    # qualify on composite alone — need distinct intent types OR strong base score.
    distinct_hot = len(set(hot_hits))
    has_deployment_signal = any(s in _DEPLOYMENT_SIGNAL_TYPES for s in signal_types)
    hot_enough = (
        distinct_hot >= 2
        or (len(hot_hits) >= 2 and base >= 68)
        or (len(hot_hits) >= 1 and base >= 72)
        or (has_deployment_signal and len(hot_hits) >= 1 and base >= 52)
    )
    if composite >= 82 or (composite >= 76 and hot_enough):
        return PriorityResult("HOT", composite, reasons)
    if composite >= 52 or (base >= 44 and _industry_fits(industry)):
        return PriorityResult("WARM", composite, reasons)
    return PriorityResult("COLD", composite, reasons)


# "Target" as common word (goal/benchmark) — when signals are about xAI, Anthropic, etc. saying "exceeds target"
# "Target" as single word is almost always a false positive (common word in funding headlines)
# Real Target Corporation would typically have "Target Corporation" or "Target stores"
_TARGET_FALSE_POSITIVE_PHRASES = (
    "exceeds its target", "exceeding its target", "surpassing target", "surpassed target",
    "exceeds target", "exceeded target", "exceeding target", "xai", "anthropic",
    "elon musk", "billion target", "million target", "funding target", "revenue target",
    "exceeds its own target", "surpassing initial target", "exceeding its $",
)

def _is_target_false_positive(company_name: str, signals) -> bool:
    """Target Corp vs common-word 'target' in funding headlines (xAI, Anthropic, etc.)."""
    name_lower = (company_name or "").strip().lower()
    # Single-word "Target" only - "Target Corporation" stays
    if not name_lower or name_lower != "target":
        return False
    # Always filter single-word "Target" - nearly always false positive from "exceeds target" etc.
    # Keep only if signals clearly reference Target Corporation (stores, retail, etc.)
    sigs = signals or []
    target_corp_phrases = ("target corporation", "target corp", "target stores", "target retail", "target.com")
    for s in sigs:
        text = (getattr(s, "signal_text", None) or getattr(s, "raw_text", None) or "").lower()
        if any(phrase in text for phrase in target_corp_phrases):
            return False  # Real Target Corp - don't filter
    # Single-word "Target" with no Target Corp context = always block (false positive from "exceeds target" etc.)
    return True


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
    # Target false positive: "Target" from "exceeds its target" in xAI/Anthropic headlines
    if _is_target_false_positive(getattr(company, "name", ""), signals):
        return True, "target false positive (common-word in funding headlines)", PriorityResult("COLD", 0.0, ["target false positive"])

    overall = getattr(score, "overall_intent_score", 0.0) if score else 0.0
    sig_types = [s.signal_type for s in (signals or [])]
    sig_count = len(signals or [])
    emp = getattr(company, "employee_estimate", None)

    pri = priority_tier(overall, company.industry, sig_types, sig_count, emp)
    return False, "", pri
