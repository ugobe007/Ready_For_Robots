"""
Month-over-month comparison for the humanoid intelligence report.

Persists a compact monthly snapshot when the report is generated, then compares
the current period to the most recent prior month on disk.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.humanoid_report_snapshot import HumanoidReportSnapshot
from app.services.humanoid_deployment_report import summarize_robot


def _period_key(dt: Optional[datetime] = None) -> str:
    when = dt or datetime.now(timezone.utc)
    return when.strftime("%Y-%m")


def _prior_period_key(period_key: str) -> Optional[str]:
    try:
        year, month = period_key.split("-")
        y, m = int(year), int(month)
        m -= 1
        if m < 1:
            m = 12
            y -= 1
        return f"{y:04d}-{m:02d}"
    except (ValueError, AttributeError):
        return None


def build_compact_snapshot(
    sorted_robots: List[dict],
    deployment_summary: dict,
    profiles: List[dict],
    adoption_metrics: dict,
    *,
    when: Optional[datetime] = None,
) -> dict:
    """Serializable snapshot for one calendar month."""
    period = _period_key(when)
    leader = profiles[0] if profiles else None
    top_slugs = []
    rankings: List[dict] = []

    for i, row in enumerate(sorted_robots):
        dep = summarize_robot(row)
        entry = {
            "rank": i + 1,
            "model_slug": row.get("model_slug"),
            "name": row.get("name"),
            "vendor": row.get("vendor"),
            "score_total": round(float(row.get("score_total") or 0), 1),
            "heif_total": round(float(row.get("heif_total") or 0), 2),
            "deployment_tier": dep.get("deployment_tier"),
            "commercial_deployments": dep.get("commercial_deployments", 0),
        }
        rankings.append(entry)
        if i < 25:
            top_slugs.append(entry["model_slug"])

    vendors = deployment_summary.get("vendor_leaderboard") or []
    return {
        "period_key": period,
        "captured_at": (when or datetime.now(timezone.utc)).isoformat(),
        "summary": {
            "total_robots": len(sorted_robots),
            "leader_model_slug": leader.get("model_slug") if leader else None,
            "leader_name": leader.get("name") if leader else None,
            "leader_score": leader.get("score_total") if leader else None,
            "leader_heif": leader.get("heif_total") if leader else None,
            "poc_or_better_count": deployment_summary.get("poc_or_better_count", 0),
            "deployment_signal_count": deployment_summary.get("deployment_signal_count", 0),
            "capability_only_count": deployment_summary.get("capability_only_count", 0),
            "robots_with_news_sources": deployment_summary.get("robots_with_news_sources", 0),
            "fleet_poc_or_better_pct": adoption_metrics.get("fleet_poc_or_better_pct"),
            "fleet_avg_heif": round(
                sum(float(r.get("heif_total") or 0) for r in sorted_robots) / len(sorted_robots),
                2,
            ) if sorted_robots else 0,
            "top_vendor": vendors[0].get("vendor") if vendors else None,
        },
        "rankings": rankings,
        "top_25_slugs": top_slugs,
    }


def persist_snapshot(db: Session, snapshot: dict) -> HumanoidReportSnapshot:
    """Upsert snapshot for snapshot['period_key']."""
    period = snapshot["period_key"]
    row = db.query(HumanoidReportSnapshot).filter(HumanoidReportSnapshot.period_key == period).first()
    if row is None:
        row = HumanoidReportSnapshot(period_key=period)
        db.add(row)
    row.summary = snapshot["summary"]
    row.rankings = snapshot["rankings"]
    db.commit()
    db.refresh(row)
    return row


def load_snapshot_for_period(db: Session, period_key: str) -> Optional[dict]:
    row = db.query(HumanoidReportSnapshot).filter(HumanoidReportSnapshot.period_key == period_key).first()
    if not row:
        return None
    return {
        "period_key": row.period_key,
        "captured_at": row.captured_at.isoformat() if row.captured_at else None,
        "summary": row.summary or {},
        "rankings": row.rankings or [],
    }


def load_previous_snapshot(db: Session, current_period: str) -> Optional[dict]:
    """Most recent snapshot strictly before current_period."""
    prior_key = _prior_period_key(current_period)
    if prior_key:
        found = load_snapshot_for_period(db, prior_key)
        if found:
            return found
    rows = (
        db.query(HumanoidReportSnapshot)
        .filter(HumanoidReportSnapshot.period_key < current_period)
        .order_by(HumanoidReportSnapshot.period_key.desc())
        .limit(1)
        .all()
    )
    if not rows:
        return None
    row = rows[0]
    return {
        "period_key": row.period_key,
        "captured_at": row.captured_at.isoformat() if row.captured_at else None,
        "summary": row.summary or {},
        "rankings": row.rankings or [],
    }


def _ranking_by_slug(rankings: List[dict]) -> Dict[str, dict]:
    return {r["model_slug"]: r for r in rankings if r.get("model_slug")}


def _delta_int(cur: int, prev: int) -> dict:
    return {"current": cur, "previous": prev, "delta": cur - prev}


def _delta_float(cur: float, prev: float) -> dict:
    return {"current": round(cur, 2), "previous": round(prev, 2), "delta": round(cur - prev, 2)}


def compare_month_over_month(current: dict, previous: Optional[dict]) -> dict:
    cur_sum = current.get("summary") or {}
    cur_rankings = current.get("rankings") or []
    period = current.get("period_key")

    if not previous:
        return {
            "current_period": period,
            "previous_period": None,
            "has_prior": False,
            "baseline_note": (
                "This is the first stored monthly snapshot for month-over-month tracking. "
                "Future editions will compare against this baseline."
            ),
            "narrative_bullets": [],
        }

    prev_sum = previous.get("summary") or {}
    prev_rankings = previous.get("rankings") or []
    prev_period = previous.get("period_key")

    cur_by_slug = _ranking_by_slug(cur_rankings)
    prev_by_slug = _ranking_by_slug(prev_rankings)

    cur_top10 = {r["model_slug"] for r in cur_rankings[:10]}
    prev_top10 = {r["model_slug"] for r in prev_rankings[:10]}
    new_to_top10 = [cur_by_slug[s]["name"] for s in cur_top10 - prev_top10 if s in cur_by_slug]
    dropped_from_top10 = [prev_by_slug[s]["name"] for s in prev_top10 - cur_top10 if s in prev_by_slug]

    movers: List[dict] = []
    for slug, cur_row in cur_by_slug.items():
        prev_row = prev_by_slug.get(slug)
        if not prev_row:
            movers.append({
                "name": cur_row.get("name"),
                "model_slug": slug,
                "type": "new_entrant",
                "rank_current": cur_row.get("rank"),
                "rank_previous": None,
                "rank_delta": None,
                "score_delta": None,
            })
            continue
        rank_delta = (prev_row.get("rank") or 0) - (cur_row.get("rank") or 0)
        score_delta = round(
            float(cur_row.get("score_total") or 0) - float(prev_row.get("score_total") or 0),
            1,
        )
        if rank_delta != 0 or abs(score_delta) >= 2:
            movers.append({
                "name": cur_row.get("name"),
                "model_slug": slug,
                "type": "mover",
                "rank_current": cur_row.get("rank"),
                "rank_previous": prev_row.get("rank"),
                "rank_delta": rank_delta,
                "score_delta": score_delta,
            })
    movers.sort(key=lambda m: (m.get("rank_delta") or 0, m.get("score_delta") or 0), reverse=True)

    leader_changed = cur_sum.get("leader_model_slug") != prev_sum.get("leader_model_slug")
    fleet_metrics = {
        "total_robots": _delta_int(
            int(cur_sum.get("total_robots") or 0),
            int(prev_sum.get("total_robots") or 0),
        ),
        "poc_or_better_count": _delta_int(
            int(cur_sum.get("poc_or_better_count") or 0),
            int(prev_sum.get("poc_or_better_count") or 0),
        ),
        "deployment_signal_count": _delta_int(
            int(cur_sum.get("deployment_signal_count") or 0),
            int(prev_sum.get("deployment_signal_count") or 0),
        ),
        "fleet_avg_heif": _delta_float(
            float(cur_sum.get("fleet_avg_heif") or 0),
            float(prev_sum.get("fleet_avg_heif") or 0),
        ),
    }

    narrative_bullets: List[str] = []
    narrative_bullets.append(
        f"Versus {prev_period}: index grew from {prev_sum.get('total_robots')} to "
        f"{cur_sum.get('total_robots')} robots ({fleet_metrics['total_robots']['delta']:+d})."
    )
    if leader_changed:
        narrative_bullets.append(
            f"Index leader changed: {prev_sum.get('leader_name')} ({prev_sum.get('leader_score')}) → "
            f"{cur_sum.get('leader_name')} ({cur_sum.get('leader_score')})."
        )
    else:
        narrative_bullets.append(
            f"{cur_sum.get('leader_name')} retained the #1 index position "
            f"(score {cur_sum.get('leader_score')})."
        )
    poc_d = fleet_metrics["poc_or_better_count"]["delta"]
    if poc_d:
        narrative_bullets.append(
            f"PoC-or-better evidence: {fleet_metrics['poc_or_better_count']['previous']} → "
            f"{fleet_metrics['poc_or_better_count']['current']} ({poc_d:+d} robots)."
        )
    dep_d = fleet_metrics["deployment_signal_count"]["delta"]
    if dep_d:
        narrative_bullets.append(
            f"Commercial/fleet deployment signals: {fleet_metrics['deployment_signal_count']['previous']} → "
            f"{fleet_metrics['deployment_signal_count']['current']} ({dep_d:+d})."
        )
    heif_d = fleet_metrics["fleet_avg_heif"]["delta"]
    if abs(heif_d) >= 0.05:
        narrative_bullets.append(
            f"Fleet-average HEIF moved {heif_d:+.2f} to {fleet_metrics['fleet_avg_heif']['current']}."
        )
    if new_to_top10:
        narrative_bullets.append(
            f"New in top 10: {', '.join(new_to_top10[:5])}"
            + (f" and {len(new_to_top10) - 5} more" if len(new_to_top10) > 5 else "")
            + "."
        )
    if dropped_from_top10:
        narrative_bullets.append(
            f"Dropped from top 10: {', '.join(dropped_from_top10[:5])}"
            + (f" and {len(dropped_from_top10) - 5} more" if len(dropped_from_top10) > 5 else "")
            + "."
        )
    top_movers = [m for m in movers if m.get("type") == "mover"][:4]
    if top_movers:
        clips = []
        for m in top_movers:
            rd = m.get("rank_delta")
            if rd and rd > 0:
                clips.append(f"{m['name']} (+{rd} ranks)")
            elif rd and rd < 0:
                clips.append(f"{m['name']} ({rd} ranks)")
            elif m.get("score_delta"):
                clips.append(f"{m['name']} (score {m['score_delta']:+.0f})")
        if clips:
            narrative_bullets.append(f"Largest rank moves: {', '.join(clips)}.")

    return {
        "current_period": period,
        "previous_period": prev_period,
        "has_prior": True,
        "fleet_metrics": fleet_metrics,
        "leader": {
            "current": {
                "name": cur_sum.get("leader_name"),
                "model_slug": cur_sum.get("leader_model_slug"),
                "score": cur_sum.get("leader_score"),
            },
            "previous": {
                "name": prev_sum.get("leader_name"),
                "model_slug": prev_sum.get("leader_model_slug"),
                "score": prev_sum.get("leader_score"),
            },
            "changed": leader_changed,
        },
        "new_to_top10": new_to_top10,
        "dropped_from_top10": dropped_from_top10,
        "movers": movers[:15],
        "narrative_bullets": narrative_bullets,
    }


def attach_month_over_month(
    db: Session,
    sorted_robots: List[dict],
    deployment_summary: dict,
    profiles: List[dict],
    adoption_metrics: dict,
) -> dict:
    """Persist this month's snapshot and compare to the prior stored month."""
    snapshot = build_compact_snapshot(
        sorted_robots, deployment_summary, profiles, adoption_metrics
    )
    persist_snapshot(db, snapshot)
    previous = load_previous_snapshot(db, snapshot["period_key"])
    return compare_month_over_month(snapshot, previous)
