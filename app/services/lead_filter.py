"""
Lead Filter Service
===================
Two-stage pipeline applied to every lead before it surfaces in the API or dashboard:

  Stage 1 — JUNK FILTER: removes noise (scraped 404 pages, test artifacts, gibberish)
  Stage 2 — PRIORITY TIER: ranks clean leads as HOT / WARM / COLD
  Stage 3 — HOT QUALIFICATION: for HOT leads, determines buying window, intent
             confidence, and recommended outreach action.

Usage
-----
  from app.services.lead_filter import classify_lead, is_junk, qualify_hot_lead, TIERS

  tier, reasons = classify_lead(company, score, signals)
  qual = qualify_hot_lead(signals)
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

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


# ─── Signal-text junk detection ───────────────────────────────────────────────

# Listicle / advice-article patterns that should never inflate a lead score
_JUNK_SIGNAL_PATTERNS = [
    r"^\d+\s+(?:ways?|strategies?|tips?|tricks?|ideas?|steps?|reasons?|mistakes?|secrets?|things?|questions?|examples?|factors?|hacks?|methods?|tactics?)\s+(?:to|for|that|you|on|about|every|when)",
    r"^top\s+\d+",
    r"^\d+\s+(?:best|great|key|simple|easy|proven|powerful|effective)",
    r"^how\s+to\b",
    r"^why\s+(?:you|your|every|hotels?|restaurants?|companies)",
    r"^what\s+(?:is|are|hotel|restaurant)\b",
    r"^the\s+(?:ultimate|complete|definitive|best|top)\s+guide",
    r"^(?:a\s+)?guide\s+to\b",
    r"combat\s+(?:restaurant|labor|wage|cost|inflation)",
    r"^(?:everything|all)\s+you\s+(?:need|should|must|want)",
]
_JUNK_SIGNAL_RE = [re.compile(p, re.IGNORECASE) for p in _JUNK_SIGNAL_PATTERNS]


def is_junk_signal_text(text: Optional[str]) -> tuple[bool, str]:
    """
    Returns (True, reason) if the signal text looks like a listicle/editorial,
    NOT a real company-event signal.
    """
    if not text:
        return False, ""
    # Only check the first 200 chars (the title portion)
    head = text.strip()[:200]
    for rx in _JUNK_SIGNAL_RE:
        if rx.search(head):
            return True, f"junk headline pattern: {rx.pattern}"
    return False, ""


def clean_signals(signals) -> list:
    """Return only signals whose text does not match junk patterns."""
    return [s for s in (signals or []) if not is_junk_signal_text(getattr(s, "signal_text", ""))[0]]


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
    hot_hits  = [s for s in signal_types if s in _HOT_SIGNAL_TYPES]
    warm_hits = [s for s in signal_types if s in _WARM_SIGNAL_TYPES]
    if hot_hits:
        boost += 5.0 * len(hot_hits)
        # Show unique types only (e.g. 3x funding_round → "funding_round x3")
        from collections import Counter
        hit_counts = Counter(hot_hits)
        hit_labels = [f"{t} x{n}" if n > 1 else t for t, n in hit_counts.items()]
        reasons.append(f"intent signals: {', '.join(hit_labels)}")
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
    # Strip listicle / advice-article signals before scoring
    clean_sigs = clean_signals(signals)
    sig_types = [s.signal_type for s in clean_sigs]
    sig_count = len(clean_sigs)
    emp = getattr(company, "employee_estimate", None)

    pri = priority_tier(overall, company.industry, sig_types, sig_count, emp)
    return False, "", pri


# ─── HOT Lead Qualification ───────────────────────────────────────────────────
# For leads already classified as HOT, this layer answers the sales question:
#   "When should we reach out, how confident are we, and what do we say?"

# ── Buying-window pattern sets ────────────────────────────────────────────────
# NOW  (0-30 days)   — active, committed, real-time urgency
_NOW_PATTERNS = [
    r"\b(breaking ground|opened today|opens today|now open|just opened|'grand opening)\b",
    r"\b(immediately|urgent(?:ly)?|asap|right now|this week|this month)\b",
    r"\b(approved budget|budget approved|committed \$|signed contract|contract signed)\b",
    r"\b(deployed|deploying|gone live|go.?live|launching now|just launch)\b",
    r"\bQ1 20(?:25|26)\b",                    # Q1 2026 = current quarter
    r"\b(March|February|January) 20(?:25|26)\b",
    r"\b(effective immediately|effective today|starting today|start(?:ing)? now)\b",
    r"\bopen(?:ing)? for business\b",
    r"\blabor shortage.*critical\b|\bcritical.*labor shortage\b",
    r"\b(staff shortage|staffing crisis).*now\b|\bnow.*(staff shortage|staffing crisis)\b",
    r"\bhired.*(?:VP|Director|Head of|SVP).*automat\b",
    r"\bnew.*(?:VP|Director).*appoint",
]

# NEAR (30-90 days)  — near-term milestone visible
_NEAR_PATTERNS = [
    r"\bQ2 20(?:25|26)\b",
    r"\b(April|May|June) 20(?:25|26)\b",
    r"\b(this (?:spring|summer|quarter)|next quarter|coming (?:weeks|months))\b",
    r"\bwithin (?:\d+ )?(?:weeks|days|month)\b",
    r"\b(just closed|recently (closed|raised|secured|acquired|merged))\b",
    r"\bintegration (?:underway|in progress|ongoing|phase)\b",
    r"\b(opening|expansion) (?:planned|scheduled|set) for\b",
    r"\b(new facility|new hotel|new center|new warehouse).{0,40}(open|complete|finish)\b",
    r"\braising \$|\bseries [A-E]\b|\bfunding round\b",
    r"\b(renovation|remodel).{0,30}(planned|scheduled|underway)\b",
    r"\bnewly (?:appointed|hired|named)\b",
]

# PIPELINE (90-180 days) — longer horizon but confirmed forward motion
_PIPELINE_PATTERNS = [
    r"\bQ[34] 20(?:25|26)\b",
    r"\b(July|August|September|October|November|December) 20(?:25|26)\b",
    r"\b(by end of year|end of 2026|later this year|later in 2026)\b",
    r"\b(2026 (?:plan|initiative|roadmap|strategy|budget)|strategic (?:plan|initiative|roadmap))\b",
    r"\b(announced|planning|intend(?:ing)?|plan(?:ning)? to) (?:open|expand|automat|deploy|invest)\b",
    r"\bnew (?:facility|warehouse|hotel|campus|location).{0,50}(break ground|planned|announce)\b",
    r"\b(multi.?year|long.?term|3.year|5.year) (?:plan|investment|partnership|contract)\b",
]

_NOW_RE      = [re.compile(p, re.IGNORECASE) for p in _NOW_PATTERNS]
_NEAR_RE     = [re.compile(p, re.IGNORECASE) for p in _NEAR_PATTERNS]
_PIPELINE_RE = [re.compile(p, re.IGNORECASE) for p in _PIPELINE_PATTERNS]


# ── Intent confidence signal-type mapping ─────────────────────────────────────
_HIGH_CONFIDENCE_TYPES = {
    "funding_round", "capex", "strategic_hire", "ma_activity", "automation_intent"
}
_MEDIUM_CONFIDENCE_TYPES = {
    "expansion", "labor_pain", "labor_shortage", "job_posting"
}

# ── Recommended action lookup [window][confidence] ───────────────────────────
_ACTION_MATRIX: Dict[str, Dict[str, str]] = {
    "NOW": {
        "HIGH":   "Immediate outreach — decision in progress. Call/email same day. Demo ready.",
        "MEDIUM": "Same-week outreach — active pain. Lead with ROI on labor cost.",
        "LOW":    "Reach out within 3 days. Validate urgency via discovery call.",
    },
    "NEAR": {
        "HIGH":   "Schedule discovery call this week. Budget window 30–90 days.",
        "MEDIUM": "Prioritize in 30-day sequence. Proposal by next week.",
        "LOW":    "Add to 2-week follow-up sequence. Share case study first.",
    },
    "PIPELINE": {
        "HIGH":   "Intro call + send ROI brief now. Proposal in 60 days.",
        "MEDIUM": "Add to 45-day nurture. Check back at Q3 budget cycle.",
        "LOW":    "Monthly nurture. Flag for Q4 budget push.",
    },
    "UNCLEAR": {
        "HIGH":   "Research + timed intro within 2 weeks. Strong signals but timing unknown.",
        "MEDIUM": "Monthly cadence. Monitor for timing triggers.",
        "LOW":    "Low touch nurture. Re-score when new signals arrive.",
    },
}


_HTML_TAG_RE    = re.compile(r"<[^>]+>", re.IGNORECASE)
_MULTI_SPACE_RE = re.compile(r"\s{2,}")


def _strip_html(text: str) -> str:
    """Remove HTML tags and collapse whitespace."""
    text = _HTML_TAG_RE.sub(" ", text)
    text = text.replace("&amp;", "&").replace("&nbsp;", " ").replace("&lt;", "<").replace("&gt;", ">")
    return _MULTI_SPACE_RE.sub(" ", text).strip()


def _extract_evidence(text: str, patterns: list) -> Optional[str]:
    """Return first matching sentence fragment for a pattern list (HTML stripped)."""
    clean = _strip_html(text)
    for rx in patterns:
        m = rx.search(clean)
        if m:
            # Return up to 120 chars centred on the match
            start = max(0, m.start() - 40)
            end   = min(len(clean), m.end() + 80)
            return clean[start:end].strip().replace("\n", " ")
    return None


@dataclass
class HotQualification:
    buying_window:      str             # NOW | NEAR | PIPELINE | UNCLEAR
    intent_confidence:  str             # HIGH | MEDIUM | LOW
    recommended_action: str             # plain-English outreach instruction
    window_evidence:    List[str] = field(default_factory=list)   # quotes from signals
    confidence_drivers: List[str] = field(default_factory=list)   # signal types driving confidence
    freshest_signal_days: Optional[int] = None                    # age of most recent signal


def qualify_hot_lead(signals) -> HotQualification:
    """
    Deep-qualify a HOT lead by analysing signal texts for:
      - Buying window (NOW / NEAR / PIPELINE / UNCLEAR)
      - Intent confidence (HIGH / MEDIUM / LOW)
      - Recommended outreach action
      - Quoted evidence from signal text
    """
    from datetime import datetime, timezone

    clean = clean_signals(signals or [])
    if not clean:
        return HotQualification(
            buying_window="UNCLEAR",
            intent_confidence="LOW",
            recommended_action=_ACTION_MATRIX["UNCLEAR"]["LOW"],
        )

    # ── Age of freshest signal ──────────────────────────────────────────────
    now = datetime.now(timezone.utc)
    ages = []
    for s in clean:
        ca = getattr(s, "created_at", None)
        if ca:
            if ca.tzinfo is None:
                ca = ca.replace(tzinfo=timezone.utc)
            ages.append((now - ca).days)
    freshest = min(ages) if ages else None

    # ── Intent confidence — from signal types ──────────────────────────────
    sig_types = [getattr(s, "signal_type", "") or "" for s in clean]
    high_drivers  = [t for t in sig_types if t in _HIGH_CONFIDENCE_TYPES]
    med_drivers   = [t for t in sig_types if t in _MEDIUM_CONFIDENCE_TYPES]

    if high_drivers:
        confidence = "HIGH"
        conf_drivers = list(dict.fromkeys(high_drivers))   # unique, ordered
    elif med_drivers:
        confidence = "MEDIUM"
        conf_drivers = list(dict.fromkeys(med_drivers))
    else:
        confidence = "LOW"
        conf_drivers = list(dict.fromkeys(sig_types))

    # ── Buying window — from signal text ───────────────────────────────────
    all_text = " ".join(
        (getattr(s, "signal_text", "") or "") for s in clean
    )

    now_evidence      = []
    near_evidence     = []
    pipeline_evidence = []

    for rx in _NOW_RE:
        ev = _extract_evidence(all_text, [rx])
        if ev:
            now_evidence.append(ev)

    for rx in _NEAR_RE:
        ev = _extract_evidence(all_text, [rx])
        if ev:
            near_evidence.append(ev)

    for rx in _PIPELINE_RE:
        ev = _extract_evidence(all_text, [rx])
        if ev:
            pipeline_evidence.append(ev)

    # Also treat very fresh signals as a NOW booster
    if freshest is not None and freshest <= 7 and high_drivers:
        now_evidence.append(f"Signal received within last {freshest} day(s)")

    if now_evidence:
        window   = "NOW"
        evidence = now_evidence[:3]
    elif near_evidence:
        window   = "NEAR"
        evidence = near_evidence[:3]
    elif pipeline_evidence:
        window   = "PIPELINE"
        evidence = pipeline_evidence[:3]
    else:
        window   = "UNCLEAR"
        evidence = []

    action = _ACTION_MATRIX[window][confidence]

    return HotQualification(
        buying_window=window,
        intent_confidence=confidence,
        recommended_action=action,
        window_evidence=evidence,
        confidence_drivers=conf_drivers,
        freshest_signal_days=freshest,
    )
