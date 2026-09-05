"""
Humanoid intelligence report — why top robots score high, plus PoC/deployment/customer evidence.

Combines HEIF scores, published specs, HEIR research overrides, and persisted deployment-news sources.
"""
from __future__ import annotations

import logging
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
import re
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

from app.services.humanoid_deployment_report import (
    TIER_LABELS,
    build_deployment_summary,
    classify_deployment_tier,
    summarize_robot,
)
from app.services.humanoid_deployment_news import news_evidence_level_from_sources
from app.services.humanoid_scraper import HEIF_DIMS, HEIF_RESEARCH_BY_VENDOR, _normalize_vendor

DIM_LABELS = {
    "mobility": "Mobility",
    "manipulation": "Manipulation",
    "cognition": "Cognition",
    "safety": "Safety",
    "data_pipeline": "Data pipeline",
    "production": "Production",
}

SCORE_KEY = {
    "mobility": "score_mobility",
    "manipulation": "score_manipulation",
    "cognition": "score_autonomy",
    "safety": "score_safety",
    "data_pipeline": "score_endurance",
    "production": "score_market_readiness",
}

RECENT_WINDOW_DAYS = 60
RECENT_RELEASE_RE = re.compile(
    r"\b(launch(?:ed|es|ing)?|debut(?:ed|s)?|unveil(?:ed|s)?|introduc(?:ed|es)|announc(?:ed|es)|release(?:d|s)?)\b",
    re.I,
)

US_ALLIED_COUNTRIES = {
    "usa", "united states", "us",
    "canada", "uk", "united kingdom", "germany", "japan",
    "south korea", "norway", "switzerland", "spain", "israel",
    "australia", "poland", "france", "italy", "netherlands", "sweden",
}
US_COUNTRY_KEYS = {"usa", "united states", "us"}


def _parse_iso_utc(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _country_key(country: Optional[str]) -> str:
    return (country or "Unknown").strip().lower()


def _policy_profile(country: Optional[str]) -> dict:
    ckey = _country_key(country)
    label = (country or "Unknown").strip() or "Unknown"

    if ckey == "china":
        return {
            "country": label,
            "policy_tag": "high_restriction_risk",
            "us_market_access_risk": "high",
            "us_demand_shift_score": 12,
            "policy_score": 24,
            "rationale": "Higher US market-access risk under foreign-supplier restrictions; near-term US demand shifts toward domestic/allied suppliers.",
        }
    if ckey in {"usa", "united states", "us"}:
        return {
            "country": label,
            "policy_tag": "us_favored",
            "us_market_access_risk": "low",
            "us_demand_shift_score": 92,
            "policy_score": 92,
            "rationale": "US suppliers are structurally favored when import restrictions tighten, increasing domestic pilot and procurement preference.",
        }
    if ckey in US_ALLIED_COUNTRIES:
        return {
            "country": label,
            "policy_tag": "allied_advantage",
            "us_market_access_risk": "low_to_medium",
            "us_demand_shift_score": 72,
            "policy_score": 74,
            "rationale": "Allied suppliers may benefit from demand reallocation with materially lower policy friction than restricted-origin vendors.",
        }
    return {
        "country": label,
        "policy_tag": "uncertain",
        "us_market_access_risk": "medium",
        "us_demand_shift_score": 48,
        "policy_score": 50,
        "rationale": "Policy impact is mixed and supplier-specific; demand may shift but requires account-level procurement validation.",
    }


def _recent_activity_60d(row: dict, news: dict, *, now: datetime) -> dict:
    window_start = now - timedelta(days=RECENT_WINDOW_DAYS)
    articles = list(news.get("articles") or [])
    launch_hits: List[dict] = []
    trial_hits: List[dict] = []
    deployment_hits: List[dict] = []
    newest: Optional[datetime] = None

    for art in articles:
        scraped_at = _parse_iso_utc(art.get("scraped_at"))
        if not scraped_at or scraped_at < window_start:
            continue
        newest = scraped_at if newest is None else max(newest, scraped_at)
        title_blob = f"{art.get('title') or ''} {art.get('title_zh') or ''}"
        level = art.get("evidence_level") or "general"
        if RECENT_RELEASE_RE.search(title_blob):
            launch_hits.append(art)
        if level == "deployment":
            deployment_hits.append(art)
        elif level == "trial":
            trial_hits.append(art)

    status = str(row.get("status") or "research").lower()
    status_boost = 14 if status == "available" else 10 if status == "pilot" else 4
    launch_count = len(launch_hits)
    deployment_count = len(deployment_hits)
    trial_count = len(trial_hits)
    recency_score = min(
        100,
        launch_count * 32 + deployment_count * 24 + trial_count * 14 + status_boost,
    )

    signal_kind = "none"
    if deployment_count > 0:
        signal_kind = "deployment"
    elif trial_count > 0:
        signal_kind = "trial"
    elif launch_count > 0:
        signal_kind = "launch"

    headline_samples = [
        {
            "title": (a.get("title_en") or a.get("title")),
            "url": a.get("url"),
            "detected_at": a.get("scraped_at"),
            "evidence_level": a.get("evidence_level"),
        }
        for a in (launch_hits + deployment_hits + trial_hits)[:4]
        if a.get("title") or a.get("title_en")
    ]

    created_at = _parse_iso_utc(row.get("created_at"))
    is_new_catalog_entry = bool(created_at and created_at >= window_start)

    return {
        "window_days": RECENT_WINDOW_DAYS,
        "signal_kind": signal_kind,
        "launch_headlines": launch_count,
        "deployment_headlines": deployment_count,
        "trial_headlines": trial_count,
        "is_new_catalog_entry": is_new_catalog_entry,
        "freshest_signal_at": newest.isoformat() if newest else None,
        "recency_score": recency_score,
        "headline_samples": headline_samples,
    }


def _deployments(specs: dict) -> int:
    try:
        return max(0, int(specs.get("commercial_deployments") or 0))
    except (TypeError, ValueError):
        return 0


def _parse_news_sources(sources: List[dict]) -> dict:
    articles: List[dict] = []
    customers: List[str] = []
    trial_articles = 0
    deployment_articles = 0

    for src in sources or []:
        if src.get("type") not in ("deployment_news", "deployment_news_zh"):
            continue
        level = src.get("evidence_level") or "general"
        if level == "trial":
            trial_articles += 1
        elif level == "deployment":
            deployment_articles += 1

        for sig in src.get("signals") or []:
            if isinstance(sig, str) and sig.startswith("customer:"):
                cust = sig.split(":", 1)[1].strip()
                if cust and cust not in customers:
                    customers.append(cust)

        articles.append({
            "title": src.get("title_en") or src.get("title"),
            "title_zh": src.get("title") if src.get("locale") == "zh" else None,
            "url": src.get("url"),
            "evidence_level": level,
            "locale": src.get("locale", "en"),
            "scraped_at": src.get("scraped_at"),
        })

    articles.sort(
        key=lambda a: {"deployment": 3, "trial": 2, "general": 1}.get(a.get("evidence_level", ""), 0),
        reverse=True,
    )
    return {
        "articles": articles[:8],
        "article_count": len(articles),
        "trial_article_count": trial_articles,
        "deployment_article_count": deployment_articles,
        "named_customers": customers,
        "news_evidence_level": news_evidence_level_from_sources(sources),
    }


def _uses_heir_research(vendor: str, dim: str, inferred_heif: float) -> bool:
    research = HEIF_RESEARCH_BY_VENDOR.get(_normalize_vendor(vendor))
    if not research or dim not in research:
        return False
    return abs(float(research[dim]) - inferred_heif) > 0.15


def _dim_drivers(row: dict, dim: str) -> List[str]:
    specs = row.get("specs") or {}
    status = str(row.get("status") or "research").lower()
    vendor = row.get("vendor") or ""
    drivers: List[str] = []

    from app.services.humanoid_scraper import infer_heif_scores

    inferred = infer_heif_scores(specs, status=status)
    if _uses_heir_research(vendor, dim, inferred.get(dim, 0)):
        drivers.append("HEIR 2026 vendor research score (authoritative benchmark)")

    if dim == "mobility":
        speed = specs.get("top_speed_mps")
        if speed is not None:
            drivers.append(f"Top speed {speed} m/s")
        if specs.get("can_climb_stairs"):
            drivers.append("Stair climbing supported")
        if specs.get("can_navigate_rough_terrain"):
            drivers.append("Rough-terrain navigation")
        if specs.get("can_run"):
            drivers.append("Running capability claimed")

    elif dim == "manipulation":
        payload = specs.get("payload_kg")
        if payload is not None:
            drivers.append(f"Payload {payload} kg")
        fingers = specs.get("finger_count")
        if fingers:
            drivers.append(f"{fingers} finger DOF")
        if specs.get("has_dexterous_hands"):
            drivers.append("Dexterous hands")

    elif dim == "cognition":
        level = specs.get("autonomy_level")
        if level:
            drivers.append(f"Autonomy level: {level}")
        dep = _deployments(specs)
        if dep:
            drivers.append(f"{dep} commercial deployment(s) in catalog")
        if specs.get("has_sdk"):
            drivers.append("Developer SDK available")

    elif dim == "safety":
        if specs.get("has_estop"):
            drivers.append("E-stop present")
        if specs.get("force_limited_joints"):
            drivers.append("Force-limited joints")
        if specs.get("safety_certified"):
            drivers.append("Safety certification cited")
        force = specs.get("collision_force_n")
        if force is not None:
            drivers.append(f"Collision force {force} N (ISO TS 15066 context)")

    elif dim == "data_pipeline":
        if specs.get("has_sdk"):
            drivers.append("SDK for data collection / fleet learning")
        if specs.get("has_api"):
            drivers.append("API integration")
        dep = _deployments(specs)
        if dep >= 10:
            drivers.append(f"Fleet scale signal ({dep} deployments)")

    elif dim == "production":
        drivers.append(f"Market status: {status}")
        dep = _deployments(specs)
        if dep:
            drivers.append(f"Commercial deployments estimate: {dep}")
        if specs.get("price_usd"):
            drivers.append(f"Published price ${int(float(specs['price_usd'])):,}")
        if specs.get("has_support_sla"):
            drivers.append("Support SLA offered")

    if not drivers:
        drivers.append("Inferred from published specs and catalog status")
    return drivers[:5]


def _score_rationale(row: dict) -> dict:
    rationale = {}
    for dim in HEIF_DIMS:
        heif_key = f"heif_{dim}"
        score_key = SCORE_KEY[dim]
        rationale[dim] = {
            "label": DIM_LABELS[dim],
            "heif": round(float(row.get(heif_key) or 0), 2),
            "index_score": round(float(row.get(score_key) or 0), 1),
            "drivers": _dim_drivers(row, dim),
        }
    return rationale


def _top_strengths(row: dict, limit: int = 3) -> List[str]:
    ranked = sorted(
        HEIF_DIMS,
        key=lambda d: float(row.get(f"heif_{d}") or 0),
        reverse=True,
    )
    return [DIM_LABELS[d] for d in ranked[:limit]]


def _why_top_rank(row: dict, rank: int, news: dict, dep_summary: dict) -> str:
    specs = row.get("specs") or {}
    strengths = _top_strengths(row)
    dep = dep_summary
    tier = dep.get("deployment_tier_label", "")
    dep_count = dep.get("commercial_deployments", 0)
    customers = news.get("named_customers") or []

    parts = [
        f"Ranks #{rank} on the live index ({dep.get('score_total', 0):.0f}/100, HEIF {dep.get('heif_total', 0):.1f}/4). "
        f"Engineering strengths: {', '.join(strengths)}.",
    ]
    if tier:
        parts.append(f"Field evidence: {tier}.")
    if dep_count:
        parts.append(f"{dep_count} commercial deployment(s) in catalog.")
    if news.get("trial_article_count") or news.get("deployment_article_count"):
        parts.append(
            f"Press: {news.get('trial_article_count', 0)} trial/PoC and "
            f"{news.get('deployment_article_count', 0)} deployment headline(s)."
        )
    if customers:
        parts.append(f"Customers cited: {', '.join(customers[:5])}.")
    elif news.get("article_count"):
        parts.append("Headlines present but no customer names extracted yet.")
    return " ".join(parts)


def _build_robot_profile(row: dict, rank: int) -> dict:
    dep = summarize_robot(row)
    news = _parse_news_sources(row.get("sources") or [])
    tier = dep["deployment_tier"]
    now = datetime.now(timezone.utc)
    recent = _recent_activity_60d(row, news, now=now)
    policy = _policy_profile(row.get("country"))

    poc_count = 0
    if tier in ("poc", "demo"):
        poc_count = 1
    if news["trial_article_count"]:
        poc_count = max(poc_count, news["trial_article_count"])

    pilot_count = 1 if tier == "pilot" else 0
    integration_count = dep["commercial_deployments"]
    if tier in ("commercial", "fleet"):
        integration_count = max(integration_count, 1)

    return {
        "rank": rank,
        "model_slug": row.get("model_slug"),
        "name": row.get("name"),
        "vendor": row.get("vendor"),
        "image_url": row.get("image_url"),
        "status": row.get("status"),
        "country": row.get("country"),
        "score_total": dep["score_total"],
        "heif_total": dep["heif_total"],
        "deployment_tier": tier,
        "deployment_tier_label": dep["deployment_tier_label"],
        "evidence_class": dep["evidence_class"],
        "commercial_deployments": dep["commercial_deployments"],
        "trials_and_pocs": {
            "catalog_poc_or_demo": tier in ("poc", "demo"),
            "catalog_pilot": tier == "pilot",
            "news_trial_headlines": news["trial_article_count"],
            "news_deployment_headlines": news["deployment_article_count"],
            "estimated_poc_signals": poc_count,
            "estimated_pilot_signals": pilot_count,
        },
        "customer_integrations": {
            "catalog_deployment_count": dep["commercial_deployments"],
            "named_customers": news["named_customers"],
            "integration_signal_count": integration_count,
        },
        "news_evidence": news,
        "recent_activity_60d": recent,
        "policy_positioning": policy,
        "score_rationale": _score_rationale(row),
        "why_top_rank": _why_top_rank(row, rank, news, dep),
        "top_headlines": [
            {
                "title": a.get("title"),
                "url": a.get("url"),
                "evidence_level": a.get("evidence_level"),
            }
            for a in (news.get("articles") or [])[:4]
            if a.get("title")
        ],
    }


def _build_customer_landscape(profiles: List[dict]) -> List[dict]:
    by_customer: Dict[str, dict] = defaultdict(lambda: {
        "customer": "",
        "robots": [],
        "vendors": set(),
        "headline_count": 0,
        "deployment_headlines": 0,
        "trial_headlines": 0,
    })

    for p in profiles:
        for cust in p.get("customer_integrations", {}).get("named_customers") or []:
            entry = by_customer[cust]
            entry["customer"] = cust
            entry["robots"].append(p["name"])
            entry["vendors"].add(p["vendor"])
            news = p.get("news_evidence") or {}
            entry["headline_count"] += news.get("article_count", 0)
            entry["deployment_headlines"] += news.get("deployment_article_count", 0)
            entry["trial_headlines"] += news.get("trial_article_count", 0)

    landscape = []
    for cust, data in by_customer.items():
        landscape.append({
            "customer": cust,
            "robots": sorted(set(data["robots"])),
            "vendors": sorted(data["vendors"]),
            "headline_count": data["headline_count"],
            "deployment_headlines": data["deployment_headlines"],
            "trial_headlines": data["trial_headlines"],
        })
    landscape.sort(
        key=lambda x: (x["deployment_headlines"], x["trial_headlines"], len(x["robots"])),
        reverse=True,
    )
    return landscape


def _executive_summary(
    robots: List[dict],
    profiles: List[dict],
    deployment_summary: dict,
    customer_landscape: List[dict],
) -> List[str]:
    total = len(robots)
    if not profiles:
        return ["No scored humanoids in database."]

    leader = profiles[0]
    leader_row = next(r for r in robots if r["model_slug"] == leader["model_slug"])
    bullets = [
        f"{leader['name']} ({leader['vendor']}) leads the index at "
        f"{leader['score_total']:.0f} with HEIF {leader['heif_total']:.1f}/4 — "
        f"top strengths: {', '.join(_top_strengths(leader_row))}.",
        f"{deployment_summary.get('poc_or_better_count', 0)} of {total} robots show PoC-or-better "
        f"deployment evidence; {deployment_summary.get('deployment_signal_count', 0)} show commercial/fleet signals.",
    ]

    with_news = sum(1 for p in profiles if (p.get("news_evidence") or {}).get("article_count"))
    with_customers = sum(
        1 for p in profiles
        if (p.get("customer_integrations") or {}).get("named_customers")
    )
    bullets.append(
        f"{with_news} robots have linked deployment-news headlines; "
        f"{with_customers} name at least one customer in press coverage."
    )
    if customer_landscape:
        top_cust = customer_landscape[0]
        bullets.append(
            f"Most-cited customer in headlines: {top_cust['customer']} "
            f"({len(top_cust['robots'])} robot matches)."
        )

    high_heif_gap = deployment_summary.get("gap_analysis", {}).get("high_heif_low_use") or []
    if high_heif_gap:
        bullets.append(
            f"{len(high_heif_gap)} high-HEIF robots still lack strong pilot+ field evidence — "
            "capability ahead of proven deployments."
        )
    return bullets


def _build_comparisons(
    sorted_robots: List[dict],
    profiles: List[dict],
    deployment_summary: dict,
) -> dict:
    """Cross-robot comparisons: dimension leaders, index vs deployment, HEIF matrix."""
    summaries = deployment_summary.get("robots") or []
    slug_to_row = {r["model_slug"]: r for r in sorted_robots}

    dimension_leaders = []
    for dim in HEIF_DIMS:
        best = max(sorted_robots, key=lambda r: float(r.get(f"heif_{dim}") or 0))
        dimension_leaders.append({
            "dimension": DIM_LABELS[dim],
            "dimension_key": dim,
            "name": best.get("name"),
            "vendor": best.get("vendor"),
            "model_slug": best.get("model_slug"),
            "heif": round(float(best.get(f"heif_{dim}") or 0), 2),
            "index_score": round(float(best.get(SCORE_KEY[dim]) or 0), 1),
        })

    index_vs_deployment: List[dict] = []
    for p in profiles:
        gap = (p.get("heif_total") or 0) >= 2.5 and p.get("deployment_tier") in ("none", "demo", "poc")
        index_vs_deployment.append({
            "rank": p["rank"],
            "name": p["name"],
            "vendor": p["vendor"],
            "score_total": p["score_total"],
            "heif_total": p["heif_total"],
            "deployment_tier": p["deployment_tier"],
            "deployment_tier_label": p["deployment_tier_label"],
            "commercial_deployments": p.get("commercial_deployments", 0),
            "news_trial_headlines": (p.get("trials_and_pocs") or {}).get("news_trial_headlines", 0),
            "news_deployment_headlines": (p.get("trials_and_pocs") or {}).get("news_deployment_headlines", 0),
            "named_customers": (p.get("customer_integrations") or {}).get("named_customers") or [],
            "capability_ahead_of_deployment": gap,
        })

    peer_heif_matrix = {
        "dimension_labels": [DIM_LABELS[d] for d in HEIF_DIMS],
        "robots": [],
    }
    for p in profiles:
        row = slug_to_row.get(p["model_slug"]) or {}
        peer_heif_matrix["robots"].append({
            "rank": p["rank"],
            "name": p["name"],
            "vendor": p["vendor"],
            "heif_total": p["heif_total"],
            "score_total": p["score_total"],
            "dimensions": {
                dim: round(float(row.get(f"heif_{dim}") or 0), 2) for dim in HEIF_DIMS
            },
        })

    gap = deployment_summary.get("gap_analysis") or {}
    return {
        "dimension_leaders": dimension_leaders,
        "index_vs_deployment": index_vs_deployment,
        "peer_heif_matrix": peer_heif_matrix,
        "fleet_deployment_tier_breakdown": deployment_summary.get("deployment_tier_breakdown") or {},
        "fleet_commercial_deployments_breakdown": deployment_summary.get("commercial_deployments_breakdown") or {},
        "fleet_status_breakdown": deployment_summary.get("status_breakdown") or {},
        "poc_to_deployment_ratio": deployment_summary.get("poc_to_deployment_ratio"),
        "capability_vs_deployment_gaps": {
            "high_heif_low_use": gap.get("high_heif_low_use") or [],
            "high_production_heif_no_deployments": gap.get("high_production_heif_no_deployments") or [],
        },
        "vendor_leaderboard": deployment_summary.get("vendor_leaderboard") or [],
        "deployment_weighted_top10": sorted(
            summaries,
            key=lambda s: s.get("deployment_weighted_heif") or 0,
            reverse=True,
        )[:10],
    }


def build_humanoid_intelligence_report_payload(
    robots: List[dict],
    *,
    top_n: int = 12,
    db=None,
) -> dict:
    """Full intelligence report: scores explained + trials/PoCs/customers."""
    if not robots:
        return {"report": None, "generated_at": datetime.now(timezone.utc).isoformat()}

    sorted_robots = sorted(robots, key=lambda r: float(r.get("score_total") or 0), reverse=True)
    deployment_summary = build_deployment_summary(sorted_robots)

    profiles = [
        _build_robot_profile(row, rank=i + 1)
        for i, row in enumerate(sorted_robots[:top_n])
    ]
    customer_landscape = _build_customer_landscape(profiles)

    trial_headlines = sum((p.get("news_evidence") or {}).get("trial_article_count", 0) for p in profiles)
    deployment_headlines = sum(
        (p.get("news_evidence") or {}).get("deployment_article_count", 0) for p in profiles
    )
    catalog_deployments = sum(
        (p.get("commercial_deployments") or 0) for p in profiles
    )

    tier_counts = Counter(p["deployment_tier"] for p in profiles)
    comparisons = _build_comparisons(sorted_robots, profiles, deployment_summary)
    total = len(sorted_robots)

    recent_launches = sorted(
        [
            {
                "rank": p["rank"],
                "name": p["name"],
                "vendor": p["vendor"],
                "country": p.get("country"),
                "recency_score": (p.get("recent_activity_60d") or {}).get("recency_score", 0),
                "signal_kind": (p.get("recent_activity_60d") or {}).get("signal_kind", "none"),
                "freshest_signal_at": (p.get("recent_activity_60d") or {}).get("freshest_signal_at"),
                "launch_headlines": (p.get("recent_activity_60d") or {}).get("launch_headlines", 0),
                "deployment_headlines": (p.get("recent_activity_60d") or {}).get("deployment_headlines", 0),
                "trial_headlines": (p.get("recent_activity_60d") or {}).get("trial_headlines", 0),
                "score_total": p.get("score_total"),
                "heif_total": p.get("heif_total"),
            }
            for p in profiles
            if (p.get("recent_activity_60d") or {}).get("recency_score", 0) > 0
        ],
        key=lambda x: (x.get("recency_score") or 0, x.get("deployment_headlines") or 0, x.get("launch_headlines") or 0),
        reverse=True,
    )

    policy_rows = [p.get("policy_positioning") or {} for p in profiles]
    policy_counts = Counter((pr.get("policy_tag") or "unknown") for pr in policy_rows)
    beneficiaries = sorted(
        [
            {
                "rank": p["rank"],
                "name": p["name"],
                "vendor": p["vendor"],
                "country": p.get("country"),
                "policy_score": (p.get("policy_positioning") or {}).get("policy_score", 0),
                "demand_shift_score": (p.get("policy_positioning") or {}).get("us_demand_shift_score", 0),
                "policy_tag": (p.get("policy_positioning") or {}).get("policy_tag"),
            }
            for p in profiles
        ],
        key=lambda x: (x.get("policy_score") or 0, x.get("demand_shift_score") or 0),
        reverse=True,
    )

    constrained = sorted(
        [
            {
                "rank": p["rank"],
                "name": p["name"],
                "vendor": p["vendor"],
                "country": p.get("country"),
                "policy_score": (p.get("policy_positioning") or {}).get("policy_score", 0),
                "policy_tag": (p.get("policy_positioning") or {}).get("policy_tag"),
            }
            for p in profiles
            if (p.get("policy_positioning") or {}).get("policy_tag") == "high_restriction_risk"
        ],
        key=lambda x: (x.get("policy_score") or 0, -(x.get("rank") or 999)),
    )

    non_us_suppliers = sorted(
        [
            {
                "rank": p["rank"],
                "name": p["name"],
                "vendor": p["vendor"],
                "country": p.get("country"),
                "policy_tag": (p.get("policy_positioning") or {}).get("policy_tag"),
                "policy_score": (p.get("policy_positioning") or {}).get("policy_score", 0),
            }
            for p in profiles
            if _country_key(p.get("country")) not in US_COUNTRY_KEYS
        ],
        key=lambda x: (x.get("policy_score") or 0, -(x.get("rank") or 999)),
    )

    china_restriction_suppliers = [
        row for row in constrained if _country_key(row.get("country")) == "china"
    ]

    avg_policy_score = round(
        sum(float((pr.get("policy_score") or 0)) for pr in policy_rows) / max(1, len(policy_rows)),
        1,
    )

    policy_intelligence = {
        "policy_window": "US 2026 China-origin supplier restriction cycle (procurement and market-access risk)",
        "notes": [
            "New US restrictions targeting China-origin suppliers can re-route near-term humanoid procurement toward domestic and allied vendors.",
            "Treat this as go-to-market risk intelligence, not legal advice; validate at deal level with procurement, legal, and compliance teams.",
        ],
        "policy_tag_breakdown_top_slice": dict(policy_counts),
        "average_policy_score_top_slice": avg_policy_score,
        "demand_shift_beneficiaries": beneficiaries[:10],
        "higher_access_risk_suppliers": constrained[:10],
        "non_us_suppliers": non_us_suppliers[:20],
        "china_restriction_update": {
            "headline": "China-origin supplier restrictions raise US access risk for affected humanoid vendors.",
            "affected_supplier_count_top_slice": len(china_restriction_suppliers),
            "affected_suppliers_top_slice": china_restriction_suppliers[:10],
            "recommended_actions": [
                "Prioritize domestic/allied alternatives for near-term US pilots in regulated or security-sensitive accounts.",
                "Prepare account-level fallback plans (vendor swap + timeline impact) before procurement review.",
                "Track policy changes monthly and refresh supplier risk tags before deal-stage progression.",
            ],
            "last_updated": datetime.now(timezone.utc).date().isoformat(),
        },
    }

    adoption_metrics = {
        "robots_in_top_slice": len(profiles),
        "catalog_commercial_deployments_sum": catalog_deployments,
        "news_trial_headlines_top_slice": trial_headlines,
        "news_deployment_headlines_top_slice": deployment_headlines,
        "robots_with_named_customers_top_slice": sum(
            1 for p in profiles
            if (p.get("customer_integrations") or {}).get("named_customers")
        ),
        "deployment_tier_breakdown_top_slice": dict(tier_counts),
        "fleet_total_robots": total,
        "fleet_poc_or_better_count": deployment_summary.get("poc_or_better_count", 0),
        "fleet_poc_or_better_pct": round(
            100 * deployment_summary.get("poc_or_better_count", 0) / total, 1
        ) if total else 0,
        "fleet_deployment_signal_count": deployment_summary.get("deployment_signal_count", 0),
        "fleet_with_news_sources": deployment_summary.get("robots_with_news_sources", 0),
        "fleet_capability_only_count": deployment_summary.get("capability_only_count", 0),
    }

    from app.services.humanoid_intelligence_narrative import build_report_narrative
    from app.services.humanoid_report_mom import attach_month_over_month

    month_over_month = None
    if db is not None:
        try:
            month_over_month = attach_month_over_month(
                db, sorted_robots, deployment_summary, profiles, adoption_metrics
            )
        except Exception as exc:
            logger.warning("month-over-month snapshot failed: %s", exc)
            month_over_month = None

    narrative = build_report_narrative(
        sorted_robots=sorted_robots,
        profiles=profiles,
        deployment_summary=deployment_summary,
        comparisons=comparisons,
        adoption_metrics=adoption_metrics,
        customer_landscape=customer_landscape,
        top_n=top_n,
        month_over_month=month_over_month,
    )
    comparisons["ranking_divergence"] = narrative.get("ranking_divergence") or []

    return {
        "report": {
            "title": f"Humanoid Intelligence Report — {datetime.now(timezone.utc).strftime('%B %Y')}",
            "subtitle": narrative.get("subtitle"),
            "framework": "HEIF (HEIR 2026) + deployment-news evidence + catalog deployment estimates",
            "methodology": (
                "Index scores combine HEIR research benchmarks and inferred specs. "
                "PoC/pilot/commercial tiers use status, commercial_deployments, and English/Chinese RSS headlines. "
                "Customer names are extracted from headline keyword matching — verify before citing."
            ),
            "deployment_tier_labels": TIER_LABELS,
            "total_robots": total,
            "executive_summary": narrative.get("executive_summary") or _executive_summary(
                sorted_robots, profiles, deployment_summary, customer_landscape
            ),
            "narrative": narrative,
            "month_over_month": month_over_month,
            "adoption_metrics": adoption_metrics,
            "comparisons": comparisons,
            "deployment_summary": {
                k: deployment_summary[k]
                for k in (
                    "deployment_tier_breakdown",
                    "evidence_class_breakdown",
                    "poc_or_better_count",
                    "deployment_signal_count",
                    "vendor_leaderboard",
                    "gap_analysis",
                    "key_findings",
                )
                if k in deployment_summary
            },
            "recent_market_entries_60d": recent_launches[:15],
            "policy_intelligence": policy_intelligence,
            "customer_landscape": customer_landscape[:20],
            "top_ranked": profiles,
            "all_robots_deployment": deployment_summary.get("robots", [])[:30],
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
