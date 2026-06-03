"""
Analyst-style narrative for the humanoid intelligence report.

Turns scored catalog + deployment evidence into readable market commentary,
not just metric bullets.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.services.humanoid_deployment_report import TIER_LABELS
from app.services.humanoid_intelligence_report import DIM_LABELS, HEIF_DIMS, _top_strengths
from app.services.humanoid_scraper import HEIF_RESEARCH_BY_VENDOR, _normalize_vendor


def _pct(part: int, whole: int) -> float:
    return round(100 * part / whole, 1) if whole else 0.0


def _tier_label(tier: str) -> str:
    return TIER_LABELS.get(tier, tier.replace("_", " "))


def _uses_heir_vendor(vendor: str) -> bool:
    return _normalize_vendor(vendor) in HEIF_RESEARCH_BY_VENDOR


def _build_ranking_divergence(
    sorted_robots: List[dict],
    deployment_summary: dict,
    top_n: int,
) -> List[dict]:
    """Index rank vs deployment-weighted rank — where capability and field use disagree."""
    by_index = {r["model_slug"]: i + 1 for i, r in enumerate(sorted_robots[:top_n])}
    dep_sorted = sorted(
        deployment_summary.get("robots") or [],
        key=lambda s: (
            s.get("deployment_weighted_heif") or 0,
            s.get("heif_total") or 0,
        ),
        reverse=True,
    )[:top_n]
    by_dep = {s["model_slug"]: i + 1 for i, s in enumerate(dep_sorted)}

    divergence: List[dict] = []
    for slug, idx_rank in by_index.items():
        dep_rank = by_dep.get(slug)
        if dep_rank is None:
            continue
        delta = idx_rank - dep_rank
        if abs(delta) < 2:
            continue
        row = next((r for r in sorted_robots if r.get("model_slug") == slug), {})
        note = (
            "Field-use evidence ranks higher than raw index score"
            if delta > 0
            else "Index score outruns public deployment evidence"
        )
        divergence.append({
            "name": row.get("name"),
            "vendor": row.get("vendor"),
            "index_rank": idx_rank,
            "deployment_weighted_rank": dep_rank,
            "rank_delta": delta,
            "commentary": note,
        })
    divergence.sort(key=lambda x: abs(x["rank_delta"]), reverse=True)
    return divergence[:8]


def build_report_narrative(
    *,
    sorted_robots: List[dict],
    profiles: List[dict],
    deployment_summary: dict,
    comparisons: dict,
    adoption_metrics: dict,
    customer_landscape: List[dict],
    top_n: int,
    month_over_month: Optional[dict] = None,
) -> dict:
    total = len(sorted_robots)
    leader = profiles[0] if profiles else None
    leader_row = (
        next((r for r in sorted_robots if r.get("model_slug") == leader["model_slug"]), {})
        if leader
        else {}
    )
    runner_up = profiles[1] if len(profiles) > 1 else None

    poc_pct = adoption_metrics.get("fleet_poc_or_better_pct") or _pct(
        deployment_summary.get("poc_or_better_count", 0), total
    )
    commercial_pct = _pct(deployment_summary.get("deployment_signal_count", 0), total)
    capability_only = adoption_metrics.get("fleet_capability_only_count") or 0
    news_count = adoption_metrics.get("fleet_with_news_sources") or 0
    heir_count = sum(1 for r in sorted_robots if _uses_heir_vendor(r.get("vendor") or ""))

    tier_breakdown = comparisons.get("fleet_deployment_tier_breakdown") or {}
    research_only = tier_breakdown.get("none", 0) + tier_breakdown.get("demo", 0)
    leaders = comparisons.get("dimension_leaders") or []
    unique_leader_models = len({entry.get("model_slug") for entry in leaders})

    month_context = (
        "Humanoid vendors continue to ship faster hardware and louder demos, while enterprise buyers "
        "still ask the same question: who is actually running pilots, with which customers, and on what timeline."
    )

    market_overview = [
        month_context,
        (
            f"This edition scores {total} humanoids on the HEIF framework (mobility, manipulation, cognition, "
            f"safety, data pipeline, production) and cross-checks each against public deployment signals — "
            f"catalog status, estimated commercial deployments, and press coverage where available."
        ),
        (
            f"Across the full index, {poc_pct}% show PoC-or-better field evidence and {commercial_pct}% show "
            f"commercial or fleet-scale signals. That gap between \"capable on paper\" and \"proven in operation\" "
            f"is the central story: {capability_only} robots score primarily from specs with little or no "
            f"deployment corroboration."
        ),
    ]

    deployment_news_callout: Optional[str] = None
    if news_count == 0:
        deployment_news_callout = (
            "Deployment-news scanning has not yet been run for this dataset (or returned no persisted headlines). "
            "Customer and trial counts below reflect catalog evidence only — re-run the deployment-news job "
            "on the API to enrich press-linked customers before sharing externally."
        )
    elif news_count < total * 0.1:
        deployment_news_callout = (
            f"Only {news_count} robots have persisted news sources in the catalog; treat headline-linked "
            "customers as a lower bound, not a complete map of the market."
        )

    key_findings: List[dict] = []

    if leader:
        strengths = ", ".join(_top_strengths(leader_row)).lower()
        heir_note = (
            " HEIR 2026 research scores anchor this vendor's profile."
            if _uses_heir_vendor(leader.get("vendor") or "")
            else " Scores are inferred from published specs rather than HEIR primary research."
        )
        key_findings.append({
            "title": "Index leader",
            "body": (
                f"{leader['name']} ({leader['vendor']}) tops the composite index at "
                f"{leader['score_total']:.0f} (HEIF {leader['heif_total']:.1f}/4), led by {strengths}.{heir_note} "
                f"Deployment tier: {_tier_label(leader.get('deployment_tier', ''))}."
            ),
        })

    if runner_up and leader:
        score_gap = leader["score_total"] - runner_up["score_total"]
        if score_gap < 1:
            tier_a = _tier_label(runner_up.get("deployment_tier", ""))
            tier_b = _tier_label(leader.get("deployment_tier", ""))
            if tier_a == tier_b:
                dep_a = int(runner_up.get("commercial_deployments") or 0)
                dep_b = int(leader.get("commercial_deployments") or 0)
                tier_compare = (
                    f"both at {tier_a.lower()}, but {dep_b} vs {dep_a} catalog deployments"
                    if dep_a != dep_b
                    else f"both at {tier_a.lower()} with similar catalog deployment counts"
                )
            else:
                tier_compare = f"{tier_a} vs {tier_b}"
            key_findings.append({
                "title": "Tight race at the top",
                "body": (
                    f"{runner_up['name']} ties or nearly ties the leader on index score "
                    f"({runner_up['score_total']:.0f} vs {leader['score_total']:.0f}). "
                    f"Differentiate on field evidence ({tier_compare}) and dimension strengths, "
                    "not headline index alone."
                ),
            })

    if unique_leader_models >= 4:
        mobility = next((e for e in leaders if e.get("dimension_key") == "mobility"), {})
        manip = next((e for e in leaders if e.get("dimension_key") == "manipulation"), {})
        key_findings.append({
            "title": "No single \"best\" humanoid",
            "body": (
                f"{unique_leader_models} different robots lead at least one HEIF dimension. "
                f"Mobility is led by {mobility.get('name', '—')} ({mobility.get('vendor', '')}); "
                f"manipulation by {manip.get('name', '—')} ({manip.get('vendor', '')}). "
                "Buyers should short-list by task (locomotion vs dexterous work) rather than a single leaderboard rank."
            ),
        })

    high_gap = (comparisons.get("capability_vs_deployment_gaps") or {}).get("high_heif_low_use") or []
    if high_gap:
        names = ", ".join(g["name"] for g in high_gap[:4])
        extra = f" and {len(high_gap) - 4} others" if len(high_gap) > 4 else ""
        key_findings.append({
            "title": "Capability ahead of proof",
            "body": (
                f"{len(high_gap)} robots combine HEIF ≥2.5 with PoC-or-weaker deployment evidence — including "
                f"{names}{extra}. These are watch-list platforms for engineering progress, not proven operators yet."
            ),
        })

    vendors = comparisons.get("vendor_leaderboard") or []
    if vendors:
        v0 = vendors[0]
        key_findings.append({
            "title": "Vendor with broadest deployment footprint",
            "body": (
                f"{v0['vendor']} leads on combined signals: {v0.get('deployment_signal', 0)} robots with "
                f"commercial/fleet evidence, {v0.get('total_deployments', 0)} catalog-reported deployments across "
                f"{v0.get('robot_count', 0)} indexed models ({v0.get('poc_or_deployment_pct', 0)}% PoC-or-better)."
            ),
        })

    dep_weighted = comparisons.get("deployment_weighted_top10") or []
    if dep_weighted and dep_weighted[0].get("model_slug") != leader.get("model_slug"):
        dw = dep_weighted[0]
        key_findings.append({
            "title": "Deployment-weighted leader differs from index",
            "body": (
                f"When HEIF is weighted by logged deployments, {dw.get('name')} ({dw.get('vendor')}) "
                f"rises to the top — not {leader.get('name') if leader else 'the index leader'}. "
                "Use both rankings: index for engineering potential, deployment-weighted for operational proof."
            ),
        })

    if customer_landscape:
        top_c = customer_landscape[0]
        key_findings.append({
            "title": "Customer signal in press",
            "body": (
                f"{top_c['customer']} appears most often in extracted headlines "
                f"({len(top_c.get('robots', []))} robot matches). "
                "Verify each mention before citing in sales or investor materials."
            ),
        })
    elif news_count == 0:
        key_findings.append({
            "title": "Customer evidence not yet populated",
            "body": (
                "No named customers were extracted from news in this build. "
                "Catalog deployment counts and pilot/commercial tiers still differentiate vendors — "
                "run deployment-news persistence to add headline-level customer proof."
            ),
        })

    key_findings.append({
        "title": "HEIR research coverage",
        "body": (
            f"{heir_count} of {total} indexed vendors use authoritative HEIR 2026 benchmark overrides; "
            "the remainder are scored from public datasheets and status fields. "
            "Compare like-with-like when benchmarking against the HEIR PDF vendor table."
        ),
    })

    mom_section: List[str] = []
    if month_over_month:
        if not month_over_month.get("has_prior"):
            mom_section.append(month_over_month.get("baseline_note") or "")
            key_findings.insert(0, {
                "title": "Month over month",
                "body": month_over_month.get("baseline_note") or "Baseline month recorded.",
            })
        else:
            prev = month_over_month.get("previous_period")
            key_findings.insert(0, {
                "title": f"Vs last month ({prev})",
                "body": " ".join(month_over_month.get("narrative_bullets") or [])[:1200],
            })
            mom_section = list(month_over_month.get("narrative_bullets") or [])

    competitive_dynamics = [
        (
            "The market splits into locomotion-first platforms (strong gait, weaker manipulation evidence), "
            "manipulation-first systems (dexterity and payload drive value), and AI-first stacks where cognition "
            "scores run ahead of production readiness. The dimension-leader table in this report makes that split explicit."
        ),
    ]
    if research_only > total * 0.4:
        competitive_dynamics.append(
            f"Roughly {_pct(research_only, total)}% of the fleet still sits at demo-or-research tiers — "
            "the index is top-heavy with aspirational capability scores. Discount index rank when "
            "deployment tier is \"research\" or \"demo only.\""
        )

    deployment_reality: List[str] = []
    ratio = comparisons.get("poc_to_deployment_ratio")
    if ratio is not None:
        deployment_reality.append(
            f"Among robots with PoC-or-better evidence, about {ratio:.2f} also show commercial/fleet-class "
            "signals — the funnel from trial to scaled deployment remains narrow."
        )
    zero_dep = (comparisons.get("fleet_commercial_deployments_breakdown") or {}).get("0", 0)
    if zero_dep:
        deployment_reality.append(
            f"{zero_dep} robots report zero catalog commercial deployments; index score alone "
            "does not imply installed base."
        )
    for finding in (deployment_summary.get("key_findings") or [])[:3]:
        if finding not in deployment_reality:
            deployment_reality.append(finding)

    ranking_commentary: List[str] = []
    divergence = _build_ranking_divergence(sorted_robots, deployment_summary, top_n)
    if divergence:
        d0 = divergence[0]
        ranking_commentary.append(
            f"Largest index vs deployment-weighted gap: {d0['name']} "
            f"(index #{d0['index_rank']} vs deployment #{d0['deployment_weighted_rank']}) — {d0['commentary']}."
        )
    top_three = profiles[:3]
    if len(top_three) >= 3:
        tiers = [f"{p['name']} ({_tier_label(p['deployment_tier'])})" for p in top_three]
        ranking_commentary.append(
            f"Top-three index cluster: {'; '.join(tiers)}. "
            "Use deployment tier and catalog deployment counts to break ties when index scores cluster."
        )

    buyer_guidance = [
        "Short-list 3–5 robots by task fit (mobility vs manipulation vs cognition), then filter by deployment tier ≥ pilot.",
        "Request customer references when tier is PoC or demo-only, even if HEIF scores are high.",
        "Re-score after vendor spec updates — the live index at readyforrobots.com/robots updates as catalogs change.",
        "Submit your use case at readyforrobots.com/find-robots for vendor matching against this dataset.",
    ]

    executive_summary = [f["body"] for f in key_findings[:6]]

    return {
        "subtitle": "Monthly market intelligence on humanoid capability, deployments, and buyer readiness",
        "market_overview": market_overview,
        "month_over_month": mom_section,
        "key_findings": key_findings,
        "competitive_dynamics": competitive_dynamics,
        "deployment_reality": deployment_reality,
        "ranking_commentary": ranking_commentary,
        "ranking_divergence": divergence,
        "buyer_guidance": buyer_guidance,
        "executive_summary": executive_summary,
        "deployment_news_callout": deployment_news_callout,
        "at_a_glance": {
            "robots_indexed": total,
            "index_leader": leader.get("name") if leader else None,
            "index_leader_score": leader.get("score_total") if leader else None,
            "poc_or_better_pct": poc_pct,
            "commercial_signal_pct": commercial_pct,
            "dimension_leader_count": unique_leader_models,
        },
    }
