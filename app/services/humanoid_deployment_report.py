"""
Humanoid deployment & PoC evidence report — HEIF capability vs field usage.

Classifies each robot by public deployment signals (status, commercial_deployments,
sources) and summarizes adoption gaps against HEIR HEIF scores.
"""
from __future__ import annotations

import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

try:
    from app.services.humanoid_deployment_news import news_evidence_level_from_sources
except ImportError:
    def news_evidence_level_from_sources(sources):  # type: ignore
        return "none"

DEPLOYMENT_TIERS = ("none", "demo", "poc", "pilot", "commercial", "fleet")

TIER_RANK = {t: i for i, t in enumerate(DEPLOYMENT_TIERS)}


def _tier_rank(tier: str) -> int:
    return TIER_RANK.get(tier, 0)


def _max_tier(a: str, b: str) -> str:
    return a if _tier_rank(a) >= _tier_rank(b) else b


def _news_tier(news_level: str, status: str) -> Optional[str]:
    """Map persisted news evidence to deployment tier."""
    if news_level == "deployment":
        if status == "available":
            return "commercial"
        return "pilot"
    if news_level == "trial":
        return "poc"
    if news_level == "general":
        return "demo"
    return None


TIER_LABELS = {
    "none": "Research / no public use evidence",
    "demo": "Demo / trade-show only",
    "poc": "PoC or limited trial",
    "pilot": "Active pilot program",
    "commercial": "Commercial deployment",
    "fleet": "Fleet-scale deployment",
    "news_unverified": "News mention without deployment keywords",
}


def _deployments(specs: dict) -> int:
    try:
        return max(0, int(specs.get("commercial_deployments") or 0))
    except (TypeError, ValueError):
        return 0


def _has_sources(row: dict) -> bool:
    sources = row.get("sources") or []
    return bool(sources)


def classify_deployment_tier(row: dict) -> str:
    """Map status, specs, sources, and news evidence to a deployment tier."""
    status = str(row.get("status") or "research").lower()
    specs = row.get("specs") or {}
    deployments = _deployments(specs)
    sources = row.get("sources") or []
    has_sources = bool(sources)
    news_level = news_evidence_level_from_sources(sources)

    tier = "none"
    if deployments >= 100 or (status == "available" and deployments >= 30):
        tier = "fleet"
    elif status == "available" or deployments >= 10:
        tier = "commercial"
    elif status == "pilot" and deployments >= 1:
        tier = "pilot"
    elif deployments >= 1:
        tier = "poc"
    elif status == "pilot":
        tier = "poc" if has_sources else "demo"
    elif has_sources:
        tier = "demo"

    news_tier = _news_tier(news_level, status)
    if news_tier:
        tier = _max_tier(tier, news_tier)

    return tier


def _evidence_class(tier: str) -> str:
    if tier in ("commercial", "fleet"):
        return "deployment_signal"
    if tier in ("poc", "pilot", "demo"):
        return "poc_signal"
    return "capability_only"


def _weighted_heif(row: dict) -> float:
    heif = float(row.get("heif_total") or 0)
    deployments = _deployments(row.get("specs") or {})
    return round(heif * math.log1p(deployments), 3)


def summarize_robot(row: dict) -> dict:
    specs = row.get("specs") or {}
    sources = row.get("sources") or []
    tier = classify_deployment_tier(row)
    news_level = news_evidence_level_from_sources(sources)
    news_article_count = sum(
        1 for s in sources
        if s.get("type") in ("deployment_news", "deployment_news_zh")
    )
    return {
        "model_slug": row.get("model_slug"),
        "name": row.get("name"),
        "vendor": row.get("vendor"),
        "status": row.get("status"),
        "deployment_tier": tier,
        "deployment_tier_label": TIER_LABELS.get(tier, tier),
        "evidence_class": _evidence_class(tier),
        "news_evidence_level": news_level,
        "news_article_count": news_article_count,
        "commercial_deployments": _deployments(specs),
        "has_sources": _has_sources(row),
        "source_count": len(sources),
        "heif_total": round(float(row.get("heif_total") or 0), 2),
        "heif_production": round(float(row.get("heif_production") or 0), 2),
        "score_total": round(float(row.get("score_total") or 0), 1),
        "deployment_weighted_heif": _weighted_heif(row),
    }


def build_deployment_summary(robots: List[dict]) -> dict:
    """Aggregate deployment/PoC metrics for a scored humanoid list."""
    if not robots:
        return {}

    summaries = [summarize_robot(r) for r in robots]
    tier_counts = Counter(s["deployment_tier"] for s in summaries)
    status_counts = Counter(str(r.get("status") or "unknown") for r in robots)
    evidence_counts = Counter(s["evidence_class"] for s in summaries)

    deployment_buckets = Counter()
    for s in summaries:
        d = s["commercial_deployments"]
        if d <= 0:
            deployment_buckets["0"] += 1
        elif d < 10:
            deployment_buckets["1-9"] += 1
        elif d < 100:
            deployment_buckets["10-99"] += 1
        else:
            deployment_buckets["100+"] += 1

    with_sources = sum(1 for s in summaries if s["has_sources"])
    with_news = sum(1 for s in summaries if s["news_evidence_level"] != "none")
    news_trial_plus = sum(
        1 for s in summaries if s["news_evidence_level"] in ("trial", "deployment")
    )
    news_deployment = sum(1 for s in summaries if s["news_evidence_level"] == "deployment")
    with_deployments = sum(1 for s in summaries if s["commercial_deployments"] > 0)
    poc_or_better = sum(
        1 for s in summaries if s["deployment_tier"] in ("poc", "pilot", "commercial", "fleet")
    )
    deployment_signal = sum(
        1 for s in summaries if s["evidence_class"] == "deployment_signal"
    )

    high_heif = [s for s in summaries if (s["heif_total"] or 0) >= 2.5]
    high_heif_low_use = [
        s for s in high_heif
        if s["deployment_tier"] in ("none", "demo", "poc")
    ]
    high_prod_heif = [s for s in summaries if (s["heif_production"] or 0) >= 3.0]
    high_prod_no_deploy = [
        s for s in high_prod_heif if s["commercial_deployments"] == 0
    ]

    scale_safety_gap = []
    for s in summaries:
        if s["commercial_deployments"] < 10:
            continue
        row = next(r for r in robots if r.get("model_slug") == s["model_slug"])
        safety = float(row.get("heif_safety") or 0)
        if safety < 2.5:
            scale_safety_gap.append({**s, "heif_safety": round(safety, 2)})
    scale_safety_gap.sort(key=lambda x: x["commercial_deployments"], reverse=True)
    scale_safety_gap = scale_safety_gap[:10]

    vendor_stats: Dict[str, dict] = defaultdict(lambda: {
        "robot_count": 0,
        "poc_or_deployment": 0,
        "deployment_signal": 0,
        "total_deployments": 0,
    })
    for s in summaries:
        v = s["vendor"] or "Unknown"
        vendor_stats[v]["robot_count"] += 1
        vendor_stats[v]["total_deployments"] += s["commercial_deployments"]
        if s["deployment_tier"] in ("poc", "pilot", "commercial", "fleet"):
            vendor_stats[v]["poc_or_deployment"] += 1
        if s["evidence_class"] == "deployment_signal":
            vendor_stats[v]["deployment_signal"] += 1

    vendor_leaderboard = sorted(
        [
            {
                "vendor": vendor,
                **stats,
                "poc_or_deployment_pct": round(
                    100 * stats["poc_or_deployment"] / stats["robot_count"], 1
                ),
            }
            for vendor, stats in vendor_stats.items()
        ],
        key=lambda x: (x["deployment_signal"], x["total_deployments"], x["poc_or_deployment"]),
        reverse=True,
    )[:15]

    total = len(robots)
    findings: List[str] = []
    findings.append(
        f"{poc_or_better} of {total} robots ({round(100 * poc_or_better / total, 1)}%) "
        f"show PoC-or-better public use evidence"
    )
    findings.append(
        f"{deployment_signal} of {total} ({round(100 * deployment_signal / total, 1)}%) "
        f"have commercial or fleet-scale deployment signals"
    )
    findings.append(
        f"{with_deployments} robots report commercial_deployments > 0 "
        f"({deployment_buckets['0']} at zero)"
    )
    if high_heif_low_use:
        findings.append(
            f"{len(high_heif_low_use)} high-HEIF robots (≥2.5) lack pilot+ deployment evidence"
        )
    findings.append(
        f"{with_sources} robots have linked source URLs; "
        f"{total - with_sources} are capability-score only"
    )
    if with_news:
        findings.append(
            f"{news_trial_plus} robots ({round(100 * news_trial_plus / total, 1)}%) "
            f"have deployment/trial news in sources ({news_deployment} deployment headlines)"
        )

    return {
        "total_robots": total,
        "status_breakdown": dict(status_counts),
        "deployment_tier_breakdown": {t: tier_counts.get(t, 0) for t in DEPLOYMENT_TIERS},
        "deployment_tier_labels": TIER_LABELS,
        "evidence_class_breakdown": dict(evidence_counts),
        "commercial_deployments_breakdown": dict(deployment_buckets),
        "poc_or_better_count": poc_or_better,
        "deployment_signal_count": deployment_signal,
        "with_sources_count": with_sources,
        "news_trial_plus_count": news_trial_plus,
        "news_deployment_count": news_deployment,
        "robots_with_news_sources": with_news,
        "capability_only_count": evidence_counts.get("capability_only", 0),
        "poc_to_deployment_ratio": round(
            deployment_signal / poc_or_better, 2
        ) if poc_or_better else None,
        "gap_analysis": {
            "high_heif_low_use": sorted(
                high_heif_low_use,
                key=lambda x: x["heif_total"],
                reverse=True,
            )[:10],
            "high_production_heif_no_deployments": sorted(
                high_prod_no_deploy,
                key=lambda x: x["heif_production"],
                reverse=True,
            )[:10],
            "scale_with_lower_safety_heif": scale_safety_gap[:10],
        },
        "vendor_leaderboard": vendor_leaderboard,
        "key_findings": findings,
        "robots": sorted(
            summaries,
            key=lambda x: (
                DEPLOYMENT_TIERS.index(x["deployment_tier"]),
                x["deployment_weighted_heif"],
                x["heif_total"],
            ),
            reverse=True,
        ),
    }


def build_humanoid_deployment_report_payload(robots: List[dict]) -> dict:
    """Full deployment report envelope."""
    summary = build_deployment_summary(robots)
    if not summary:
        return {"report": None, "generated_at": datetime.now(timezone.utc).isoformat()}

    return {
        "report": {
            "title": f"Humanoid Deployment & PoC Report — {datetime.now(timezone.utc).strftime('%B %Y')}",
            "framework": "HEIF (HEIR 2026) capability scores vs public deployment evidence",
            "methodology": (
                "Tiers inferred from status, commercial_deployments estimate, and news sources "
                "(English + Chinese RSS with translated headlines). Verify before citing."
            ),
            **summary,
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
