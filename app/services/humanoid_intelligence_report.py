"""
Humanoid intelligence report — why top robots score high, plus PoC/deployment/customer evidence.

Combines HEIF scores, published specs, HEIR research overrides, and persisted deployment-news sources.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

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
        f"Rank #{rank} with index {dep.get('score_total', 0):.0f} "
        f"(HEIF {dep.get('heif_total', 0):.1f}/4). "
        f"Strongest dimensions: {', '.join(strengths)}.",
    ]
    if tier:
        parts.append(f"Deployment evidence: {tier}.")
    if dep_count:
        parts.append(f"Catalog reports {dep_count} commercial deployment(s).")
    if news.get("trial_article_count") or news.get("deployment_article_count"):
        parts.append(
            f"News scan: {news.get('trial_article_count', 0)} trial/PoC headline(s), "
            f"{news.get('deployment_article_count', 0)} deployment headline(s)."
        )
    if customers:
        parts.append(f"Named customers in headlines: {', '.join(customers[:5])}.")
    elif news.get("article_count"):
        parts.append("Press coverage without extracted customer names yet.")
    return " ".join(parts)


def _build_robot_profile(row: dict, rank: int) -> dict:
    dep = summarize_robot(row)
    news = _parse_news_sources(row.get("sources") or [])
    tier = dep["deployment_tier"]

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
        "status": row.get("status"),
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


def build_humanoid_intelligence_report_payload(robots: List[dict], *, top_n: int = 12) -> dict:
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

    return {
        "report": {
            "title": f"Humanoid Intelligence Report — {datetime.now(timezone.utc).strftime('%B %Y')}",
            "framework": "HEIF (HEIR 2026) + deployment-news evidence + catalog deployment estimates",
            "methodology": (
                "Index scores combine HEIR research benchmarks and inferred specs. "
                "PoC/pilot/commercial tiers use status, commercial_deployments, and English/Chinese RSS headlines. "
                "Customer names are extracted from headline keyword matching — verify before citing."
            ),
            "deployment_tier_labels": TIER_LABELS,
            "total_robots": len(sorted_robots),
            "executive_summary": _executive_summary(
                sorted_robots, profiles, deployment_summary, customer_landscape
            ),
            "adoption_metrics": {
                "robots_in_top_slice": len(profiles),
                "catalog_commercial_deployments_sum": catalog_deployments,
                "news_trial_headlines_top_slice": trial_headlines,
                "news_deployment_headlines_top_slice": deployment_headlines,
                "robots_with_named_customers_top_slice": sum(
                    1 for p in profiles
                    if (p.get("customer_integrations") or {}).get("named_customers")
                ),
                "deployment_tier_breakdown_top_slice": dict(tier_counts),
            },
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
            "customer_landscape": customer_landscape[:20],
            "top_ranked": profiles,
            "all_robots_deployment": deployment_summary.get("robots", [])[:30],
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
