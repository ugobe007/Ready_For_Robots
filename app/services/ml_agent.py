"""
ML Agent — Lead Intelligence Engine
====================================
Analyzes collected signal + scoring data to:
  1. Rank lead sources by quality of leads they produce
  2. Identify high-confidence signal combinations (patterns)
  3. Generate per-company approach strategies (who, how, when)
  4. Recommend next scrape targets based on gaps
  5. Provide timing windows based on signal recency

No external ML libraries required — uses statistical scoring + rule-based
inference that improves as data accumulates (Bayesian-style weight updates).
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from collections import defaultdict
from datetime import datetime, timezone, timedelta
import math
import re

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.company import Company
from app.models.signal import Signal
from app.models.score import Score


# ── Types ──────────────────────────────────────────────────────────────────────

@dataclass
class SourceRanking:
    domain: str
    lead_count: int
    avg_score: float
    top_industries: List[str]
    top_signal_types: List[str]
    quality_tier: str          # GOLD / SILVER / BRONZE / UNPROVEN

@dataclass
class SignalPattern:
    signals: List[str]         # combination of signal_types
    occurrence_count: int
    avg_score: float
    industries: List[str]
    insight: str               # human-readable pattern description

@dataclass
class ApproachStrategy:
    company_id: int
    company_name: str
    urgency: str               # NOW / SOON / MONITOR
    contact_role: str          # who to reach out to
    pitch_angle: str           # what pain point to lead with
    talking_points: List[str]
    best_channel: str          # email / linkedin / phone / event
    timing_note: str
    confidence: float          # 0.0 – 1.0

@dataclass
class NextTarget:
    url: str
    scraper_type: str
    reason: str
    expected_industry: str
    priority_score: float

@dataclass
class AgentInsights:
    generated_at: str
    data_points: int           # total signals analyzed
    source_rankings: List[SourceRanking]
    signal_patterns: List[SignalPattern]
    top_strategies: List[ApproachStrategy]  # top 5 "act now" companies
    recommended_targets: List[NextTarget]
    learning_notes: List[str]  # what the agent has learned
    coverage_gaps: List[str]   # missing industries / signal types


# ── Constants ──────────────────────────────────────────────────────────────────

# Signal → pain point mapping
_SIGNAL_PAIN = {
    "labor_pain":       "struggling to hire and retain frontline workers",
    "labor_shortage":   "facing acute labor shortages and rising turnover costs",
    "automation_intent":"actively evaluating automation and robotics solutions",
    "strategic_hire":   "building an ops/automation leadership team",
    "funding_round":    "flush with capital and ready to invest in infrastructure",
    "capex":            "allocating major capital expenditures to operations",
    "expansion":        "opening new locations and scaling operations",
    "ma_activity":      "in post-merger integration mode — ripe for standardization",
    "service_consistency": "dealing with inconsistent service quality across locations",
    "equipment_integration": "upgrading and integrating operational equipment",
    "job_posting":      "actively hiring for roles robots can augment or replace",
    "news":             "in the news — high-visibility moment for outreach",
}

# Industry → contact role mapping
_INDUSTRY_CONTACT = {
    "Hospitality":   "VP of Operations / General Manager / Director of F&B",
    "Logistics":     "VP of Supply Chain / COO / Director of Warehouse Operations",
    "Healthcare":    "COO / Director of Support Services / VP of Patient Experience",
    "Food Service":  "Director of Operations / VP of Culinary / COO",
    "Retail":        "VP of Store Operations / Director of Loss Prevention / COO",
    "Manufacturing": "VP of Operations / Plant Manager / Director of Automation",
}

# Industry → best pitch angle
_INDUSTRY_PITCH = {
    "Hospitality":   "eliminate labor gaps in food delivery, cleaning, and front-desk tasks — Richtech robots maintain service consistency across every shift",
    "Logistics":     "automate repetitive warehouse pick-pack-sort operations — reduce labor costs 30–60% while running 24/7 with zero fatigue",
    "Healthcare":    "autonomous delivery robots for medications, linens, and supplies — free nursing staff for patient care",
    "Food Service":  "autonomous cooking and serving robots that ensure consistent food quality and handle peak-hour volume without extra staff",
    "Retail":        "inventory scanning, shelf-stocking assistance, and customer-facing service robots",
    "Manufacturing": "collaborative robots for assembly, quality inspection, and material handling",
}

# Signal type → urgency weight
_SIGNAL_URGENCY = {
    "automation_intent": 1.0,
    "funding_round":     0.95,
    "capex":             0.90,
    "strategic_hire":    0.85,
    "labor_pain":        0.80,
    "labor_shortage":    0.75,
    "ma_activity":       0.70,
    "expansion":         0.65,
    "service_consistency": 0.60,
    "equipment_integration": 0.55,
    "job_posting":       0.50,
    "news":              0.40,
}

# Source domain → known scraper type
_DOMAIN_SCRAPER = {
    "simplyhired.com":    "job_board",
    "indeed.com":         "job_board",
    "linkedin.com":       "job_board",
    "ziprecruiter.com":   "job_board",
    "yellowpages.com":    "hotel_dir",
    "tripadvisor.com":    "hotel_dir",
    "ahla.com":           "hotel_dir",
    "freightwaves.com":   "news",
    "logisticsmgmt.com":  "news",
    "hospitalitynet.org": "news",
    "restaurantbusiness": "news",
}


# ── Helpers ────────────────────────────────────────────────────────────────────

def _domain(url: str) -> str:
    """Extract root domain from a URL string."""
    if not url or url in ("seed", "manual"):
        return url or "unknown"
    url = re.sub(r'^https?://', '', url)
    parts = url.split('/')[0].split('.')
    if len(parts) >= 2:
        return '.'.join(parts[-2:])
    return url.split('/')[0]


def _recency_weight(created_at: Optional[datetime]) -> float:
    """Signals < 30 days old score full weight; decay over 180 days."""
    if not created_at:
        return 0.5
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    age_days = (datetime.now(timezone.utc) - created_at).days
    if age_days <= 30:
        return 1.0
    if age_days >= 180:
        return 0.2
    return 1.0 - 0.8 * (age_days - 30) / 150


def _quality_tier(avg_score: float, count: int) -> str:
    if count < 2:
        return "UNPROVEN"
    if avg_score >= 80:
        return "GOLD"
    if avg_score >= 60:
        return "SILVER"
    return "BRONZE"


# ── Core Agent ─────────────────────────────────────────────────────────────────

class MLAgent:
    """
    Stateless analysis agent.  Call MLAgent.run(db) to get AgentInsights.
    Re-run any time new data arrives — the agent is fully data-driven.
    """

    @staticmethod
    def run(db: Session) -> AgentInsights:
        companies = (
            db.query(Company)
            .outerjoin(Score, Score.company_id == Company.id)
            .all()
        )
        signals_all = db.query(Signal).all()

        agent = MLAgent()
        source_rankings = agent._analyze_sources(companies, signals_all)
        patterns        = agent._analyze_patterns(companies, signals_all)
        strategies      = agent._generate_strategies(companies, signals_all)
        targets         = agent._recommend_targets(companies, source_rankings)
        notes           = agent._learning_notes(companies, signals_all, source_rankings)
        gaps            = agent._coverage_gaps(companies, signals_all)

        return AgentInsights(
            generated_at=datetime.now(timezone.utc).isoformat(),
            data_points=len(signals_all),
            source_rankings=source_rankings,
            signal_patterns=patterns,
            top_strategies=strategies,
            recommended_targets=targets,
            learning_notes=notes,
            coverage_gaps=gaps,
        )

    # ── Source analysis ────────────────────────────────────────────────────────

    def _analyze_sources(
        self, companies: list, signals: list
    ) -> List[SourceRanking]:
        """Group signals by source domain, correlate with company scores."""

        # Build company score lookup
        score_lookup: Dict[int, float] = {}
        industry_lookup: Dict[int, str] = {}
        for c in companies:
            s = c.scores
            score_lookup[c.id]    = (s.overall_intent_score * 100) if s else 0.0
            industry_lookup[c.id] = c.industry or "Unknown"

        # Aggregate by domain
        by_domain: Dict[str, Dict] = defaultdict(lambda: {
            "scores": [], "industries": defaultdict(int),
            "signal_types": defaultdict(int), "companies": set()
        })

        for sig in signals:
            dom = _domain(sig.source_url)
            d   = by_domain[dom]
            d["scores"].append(score_lookup.get(sig.company_id, 0))
            d["industries"][industry_lookup.get(sig.company_id, "Unknown")] += 1
            d["signal_types"][sig.signal_type] += 1
            d["companies"].add(sig.company_id)

        rankings: List[SourceRanking] = []
        for domain, data in by_domain.items():
            if not data["scores"]:
                continue
            avg_score = sum(data["scores"]) / len(data["scores"])
            top_ind   = sorted(data["industries"], key=data["industries"].get, reverse=True)[:3]
            top_sig   = sorted(data["signal_types"], key=data["signal_types"].get, reverse=True)[:3]
            rankings.append(SourceRanking(
                domain=domain,
                lead_count=len(data["companies"]),
                avg_score=round(avg_score, 1),
                top_industries=top_ind,
                top_signal_types=top_sig,
                quality_tier=_quality_tier(avg_score, len(data["companies"])),
            ))

        rankings.sort(key=lambda r: (r.avg_score * math.log1p(r.lead_count)), reverse=True)
        return rankings[:10]

    # ── Pattern analysis ───────────────────────────────────────────────────────

    def _analyze_patterns(
        self, companies: list, signals: list
    ) -> List[SignalPattern]:
        """Identify signal combinations that correlate with high scores."""

        # Build signal set per company
        company_sigs: Dict[int, set] = defaultdict(set)
        for sig in signals:
            company_sigs[sig.company_id].add(sig.signal_type)

        # Get score per company
        score_map: Dict[int, float] = {}
        ind_map:   Dict[int, str]   = {}
        for c in companies:
            s = c.scores
            score_map[c.id] = (s.overall_intent_score * 100) if s else 0.0
            ind_map[c.id]   = c.industry or "Unknown"

        # Count common pairs/triples
        pair_data: Dict[tuple, Dict] = defaultdict(lambda: {"scores": [], "industries": defaultdict(int)})

        for cid, sig_set in company_sigs.items():
            sig_list = sorted(sig_set)
            # single signals
            for s in sig_list:
                pair_data[(s,)]["scores"].append(score_map.get(cid, 0))
                pair_data[(s,)]["industries"][ind_map.get(cid, "Unknown")] += 1
            # pairs
            for i in range(len(sig_list)):
                for j in range(i+1, len(sig_list)):
                    key = (sig_list[i], sig_list[j])
                    pair_data[key]["scores"].append(score_map.get(cid, 0))
                    pair_data[key]["industries"][ind_map.get(cid, "Unknown")] += 1

        patterns: List[SignalPattern] = []
        for combo, data in pair_data.items():
            if len(data["scores"]) < 1:
                continue
            avg = sum(data["scores"]) / len(data["scores"])
            if avg < 60:
                continue
            top_ind = sorted(data["industries"], key=data["industries"].get, reverse=True)[:2]
            insight = _build_pattern_insight(combo, avg, top_ind)
            patterns.append(SignalPattern(
                signals=list(combo),
                occurrence_count=len(data["scores"]),
                avg_score=round(avg, 1),
                industries=top_ind,
                insight=insight,
            ))

        patterns.sort(key=lambda p: p.avg_score * math.log1p(p.occurrence_count), reverse=True)
        return patterns[:8]

    # ── Approach strategies ────────────────────────────────────────────────────

    def _generate_strategies(
        self, companies: list, signals: list
    ) -> List[ApproachStrategy]:
        """Generate a tailored approach strategy for each high-priority company."""

        # Build signal map
        sig_map: Dict[int, List[Signal]] = defaultdict(list)
        for sig in signals:
            sig_map[sig.company_id].append(sig)

        strategies: List[ApproachStrategy] = []
        for c in companies:
            s = c.scores
            if not s:
                continue
            overall = s.overall_intent_score * 100
            if overall < 50:
                continue

            sigs = sig_map.get(c.id, [])
            strategy = _build_strategy(c, s, sigs)
            strategies.append(strategy)

        strategies.sort(key=lambda s: (
            {"NOW": 3, "SOON": 2, "MONITOR": 1}.get(s.urgency, 0),
            s.confidence
        ), reverse=True)
        return strategies[:10]

    # ── Target recommendations ────────────────────────────────────────────────

    def _recommend_targets(
        self, companies: list, rankings: List[SourceRanking]
    ) -> List[NextTarget]:
        """Suggest new scrape sources based on coverage gaps and source performance."""

        industries_covered = set(c.industry for c in companies if c.industry)
        count_by_ind = defaultdict(int)
        for c in companies:
            count_by_ind[c.industry or "Unknown"] += 1

        targets: List[NextTarget] = []

        # Suggest based on underrepresented industries
        industry_sources = {
            "Hospitality": [
                ("https://www.ahla.com/member-directory", "hotel_dir", "AHLA member directory — 25,000+ hotel operators"),
                ("https://www.restaurantbusiness.com/food-service-news", "news", "Restaurant Business top chain coverage"),
            ],
            "Logistics": [
                ("https://www.dcvelocity.com/", "news", "DC Velocity — warehouse automation news"),
                ("https://www.freightwaves.com/news", "news", "FreightWaves — live logistics signals"),
            ],
            "Healthcare": [
                ("https://www.healthcareit.net/category/news", "news", "Healthcare IT news — ops automation signals"),
                ("https://www.beckershospitalreview.com/", "news", "Becker's — hospital C-suite strategy signals"),
            ],
            "Food Service": [
                ("https://www.qsrmagazine.com/outside-insights/operations", "news", "QSR Magazine — fast food operator signals"),
                ("https://www.nrn.com/operations", "news", "Nation's Restaurant News — chain operations"),
            ],
            "Manufacturing": [
                ("https://www.automationworld.com/", "news", "Automation World — factory automation signals"),
                ("https://www.industryweek.com/operations/", "news", "IndustryWeek — ops investment signals"),
            ],
        }

        for industry, sources in industry_sources.items():
            gap_score = 10.0 / max(count_by_ind.get(industry, 0) + 1, 1)
            for url, scraper, reason in sources:
                targets.append(NextTarget(
                    url=url,
                    scraper_type=scraper,
                    reason=reason,
                    expected_industry=industry,
                    priority_score=round(gap_score, 2),
                ))

        targets.sort(key=lambda t: t.priority_score, reverse=True)
        return targets[:8]

    # ── Learning notes ────────────────────────────────────────────────────────

    def _learning_notes(
        self, companies: list, signals: list, rankings: List[SourceRanking]
    ) -> List[str]:
        notes = []
        n_cos = len(companies)
        n_sig = len(signals)

        if n_sig == 0:
            return ["No signal data yet — run a scraper to start learning."]

        avg_sigs = n_sig / max(n_cos, 1)
        notes.append(
            f"Analyzed {n_sig} signals across {n_cos} companies "
            f"({avg_sigs:.1f} signals/company average)."
        )

        if rankings:
            top = rankings[0]
            notes.append(
                f"Highest-quality source: {top.domain} "
                f"(avg score {top.avg_score}, {top.lead_count} leads, {top.quality_tier})."
            )

        # Score distribution
        scores = [c.scores.overall_intent_score * 100 for c in companies if c.scores]
        if scores:
            hot  = sum(1 for s in scores if s >= 75)
            warm = sum(1 for s in scores if 40 <= s < 75)
            cold = sum(1 for s in scores if s < 40)
            notes.append(
                f"Pipeline quality: {hot} HOT ({hot*100//len(scores)}%), "
                f"{warm} WARM ({warm*100//len(scores)}%), "
                f"{cold} COLD cold leads."
            )

        # Signal type distribution insight
        type_counts: Dict[str, int] = defaultdict(int)
        for sig in signals:
            type_counts[sig.signal_type] += 1
        top_type = max(type_counts, key=type_counts.get) if type_counts else None
        if top_type:
            notes.append(
                f"Dominant signal type: {top_type} ({type_counts[top_type]} occurrences) — "
                f"{_SIGNAL_PAIN.get(top_type, 'key buying trigger')}."
            )

        return notes

    # ── Coverage gaps ─────────────────────────────────────────────────────────

    def _coverage_gaps(self, companies: list, signals: list) -> List[str]:
        gaps = []
        industries = [c.industry for c in companies if c.industry]
        ind_counts  = {i: industries.count(i) for i in set(industries)}

        all_target_industries = {"Hospitality", "Logistics", "Healthcare", "Food Service", "Manufacturing"}
        for ind in all_target_industries:
            if ind not in ind_counts:
                gaps.append(f"No {ind} leads yet — add scrape sources for this industry.")
            elif ind_counts[ind] < 3:
                gaps.append(f"Only {ind_counts[ind]} {ind} lead(s) — expand scraping for better signal coverage.")

        sig_types = {s.signal_type for s in signals}
        high_value = {"automation_intent", "capex", "funding_round"}
        missing = high_value - sig_types
        for st in missing:
            gaps.append(f"No '{st}' signals detected yet — these are the strongest buying triggers.")

        return gaps


# ── Strategy builder (standalone helper) ────────────────────────────────────────

def _build_strategy(company: Company, score: Score, sigs: List[Signal]) -> ApproachStrategy:
    industry = company.industry or "Unknown"
    overall  = score.overall_intent_score * 100

    # Urgency: weighted by signal types + recency
    urgency_score = 0.0
    for sig in sigs:
        base   = _SIGNAL_URGENCY.get(sig.signal_type, 0.3)
        rec    = _recency_weight(sig.created_at if hasattr(sig, 'created_at') else None)
        weight = sig.signal_strength * base * rec
        urgency_score = max(urgency_score, weight)

    if urgency_score >= 0.75 or overall >= 80:
        urgency = "NOW"
    elif urgency_score >= 0.45 or overall >= 55:
        urgency = "SOON"
    else:
        urgency = "MONITOR"

    # Contact role
    contact_role = _INDUSTRY_CONTACT.get(industry, "COO / VP of Operations")

    # Best pitch angle based on dominant signals
    sig_types = [s.signal_type for s in sigs]
    dominant  = max(set(sig_types), key=sig_types.count) if sig_types else ""

    if dominant in ("labor_pain", "labor_shortage", "job_posting"):
        pitch = "labor cost reduction and consistent headcount"
    elif dominant in ("automation_intent", "strategic_hire"):
        pitch = "robotics ROI and fast deployment timeline"
    elif dominant in ("funding_round", "capex"):
        pitch = "capital allocation and automation ROI"
    elif dominant in ("expansion", "ma_activity"):
        pitch = "scaling operations consistently across new locations"
    elif dominant == "service_consistency":
        pitch = "24/7 consistent service delivery without staffing variability"
    else:
        pitch = _INDUSTRY_PITCH.get(industry, "operational efficiency and automation ROI")

    # Talking points
    talking_points = _build_talking_points(company, score, sigs, industry)

    # Best channel
    if industry in ("Logistics", "Manufacturing"):
        channel = "LinkedIn → direct email to ops/supply chain leadership"
    elif industry == "Hospitality":
        channel = "Industry event (HITEC, AHLA) → follow-up email"
    else:
        channel = "LinkedIn outreach → personalized email with ROI case study"

    # Timing
    recent_sigs = [s for s in sigs if _recency_weight(
        s.created_at if hasattr(s, 'created_at') else None
    ) > 0.7]
    if recent_sigs:
        timing = "Act within 2 weeks — recent signals indicate active evaluation window."
    elif urgency == "MONITOR":
        timing = "Re-check in 30 days — monitor for new funding or hiring signals."
    else:
        timing = "Outreach within 30 days — signals are warm but may cool."

    confidence = min(
        0.5 + (overall / 200) + (len(sigs) * 0.02) + (urgency_score * 0.3),
        0.99
    )

    return ApproachStrategy(
        company_id=company.id,
        company_name=company.name,
        urgency=urgency,
        contact_role=contact_role,
        pitch_angle=pitch,
        talking_points=talking_points,
        best_channel=channel,
        timing_note=timing,
        confidence=round(confidence, 2),
    )


def _build_talking_points(company: Company, score: Score, sigs: List, industry: str) -> List[str]:
    points = []
    sig_types = {s.signal_type for s in sigs}

    if "labor_pain" in sig_types or "labor_shortage" in sig_types:
        points.append("Labor costs represent 30–40% of your operating budget — our robots reduce that by up to 50%.")

    if "automation_intent" in sig_types or "strategic_hire" in sig_types:
        points.append("You're already evaluating automation — Richtech has deployed at scale in your exact use case.")

    if "funding_round" in sig_types or "capex" in sig_types:
        points.append("With your recent capital allocation, now is the ideal window to lock in pricing and deployment.")

    if "expansion" in sig_types or "ma_activity" in sig_types:
        points.append("As you scale to new locations, robots ensure consistent quality without proportional headcount growth.")

    if "service_consistency" in sig_types:
        points.append("Richtech robots deliver the same service standard on the 1st shift as the 4th — zero variability.")

    if industry == "Hospitality":
        points.append("Hotels and restaurants using our ADAM robot report 40% reduction in delivery labor and 95%+ guest satisfaction.")
    elif industry == "Logistics":
        points.append("Our AMRs integrate with existing WMS systems in days, not months — zero disruption to your current ops.")
    elif industry == "Healthcare":
        points.append("Our delivery robots are FDA-cleared for hospital environments and handle 200+ deliveries/day per unit.")

    # Fallback
    if not points:
        points.append(f"Richtech Robotics has case studies in {industry} with measurable ROI within 12–18 months.")
        points.append("Our robots integrate with existing software and require minimal infrastructure changes.")

    return points[:4]


def _build_pattern_insight(combo: tuple, avg: float, industries: List[str]) -> str:
    if len(combo) == 1:
        pain = _SIGNAL_PAIN.get(combo[0], combo[0])
        return f"Single signal '{combo[0]}' ({pain}) → avg score {avg:.0f}. Strong standalone indicator."
    s1, s2 = combo[0], combo[1]
    p1 = _SIGNAL_PAIN.get(s1, s1)
    p2 = _SIGNAL_PAIN.get(s2, s2)
    ind_str = " + ".join(industries) if industries else "multiple industries"
    return (
        f"'{s1}' + '{s2}' combo in {ind_str} → avg score {avg:.0f}. "
        f"Company is {p1} AND {p2} — ideal dual-pressure buying condition."
    )


# ── Serialization ─────────────────────────────────────────────────────────────

def insights_to_dict(ins: AgentInsights) -> dict:
    return {
        "generated_at": ins.generated_at,
        "data_points":  ins.data_points,
        "source_rankings": [
            {
                "domain":          r.domain,
                "lead_count":      r.lead_count,
                "avg_score":       r.avg_score,
                "top_industries":  r.top_industries,
                "top_signal_types": r.top_signal_types,
                "quality_tier":    r.quality_tier,
            } for r in ins.source_rankings
        ],
        "signal_patterns": [
            {
                "signals":          p.signals,
                "occurrence_count": p.occurrence_count,
                "avg_score":        p.avg_score,
                "industries":       p.industries,
                "insight":          p.insight,
            } for p in ins.signal_patterns
        ],
        "top_strategies": [
            {
                "company_id":    s.company_id,
                "company_name":  s.company_name,
                "urgency":       s.urgency,
                "contact_role":  s.contact_role,
                "pitch_angle":   s.pitch_angle,
                "talking_points": s.talking_points,
                "best_channel":  s.best_channel,
                "timing_note":   s.timing_note,
                "confidence":    s.confidence,
            } for s in ins.top_strategies
        ],
        "recommended_targets": [
            {
                "url":               t.url,
                "scraper_type":      t.scraper_type,
                "reason":            t.reason,
                "expected_industry": t.expected_industry,
                "priority_score":    t.priority_score,
            } for t in ins.recommended_targets
        ],
        "learning_notes": ins.learning_notes,
        "coverage_gaps":  ins.coverage_gaps,
    }
