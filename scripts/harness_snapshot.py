#!/usr/bin/env python3
"""
Collect harness metrics for the RFR agent loop.

Writes reports/harness_snapshot.json (and reports/harness_snapshot_latest.json).

Usage:
  python3 scripts/harness_snapshot.py
  python3 scripts/harness_snapshot.py --api-base https://ready-2-robot.fly.dev
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_root))

from app.env_loader import database_url_is_template_or_sqlite
from scripts.harness_env import database_telemetry, load_harness_env

load_harness_env(_root)


def _fetch_json(url: str, timeout: int = 25) -> tuple[dict | list | None, str | None]:
    try:
        import httpx

        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            resp = client.get(url, headers={"Accept": "application/json"})
            resp.raise_for_status()
            raw = resp.text
        if raw.strip().startswith("<"):
            return None, "non-json (html) response"
        return json.loads(raw), None
    except Exception as exc:
        return None, str(exc)


def _git_info() -> dict:
    def run(args: list[str]) -> str:
        try:
            return subprocess.check_output(
                ["git", *args],
                cwd=_root,
                stderr=subprocess.DEVNULL,
                text=True,
            ).strip()
        except Exception:
            return ""

    dirty = bool(run(["status", "--porcelain"]))
    return {
        "branch": run(["rev-parse", "--abbrev-ref", "HEAD"]),
        "commit": run(["rev-parse", "--short", "HEAD"]),
        "dirty": dirty,
        "dirty_count": len([ln for ln in run(["status", "--porcelain"]).splitlines() if ln.strip()]),
    }


def _load_previous_snapshot() -> dict | None:
    latest = _root / "reports" / "harness_snapshot_latest.json"
    if not latest.is_file():
        return None
    try:
        return json.loads(latest.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _db_session():
    db_url = (os.environ.get("DATABASE_URL") or "").strip()
    if not db_url or database_url_is_template_or_sqlite(db_url):
        return None
    try:
        from app.database import SessionLocal

        return SessionLocal()
    except Exception:
        return None


def _db_counts(db) -> dict | None:
    if db is None:
        return None
    try:
        from sqlalchemy import text

        quarantined = db.execute(
            text("SELECT COUNT(*) FROM companies WHERE is_internal = false")
        ).scalar()
        active = db.execute(
            text("SELECT COUNT(*) FROM companies WHERE is_internal IS NOT FALSE")
        ).scalar()
        with_signals = db.execute(
            text(
                """
                SELECT COUNT(DISTINCT c.id)
                FROM companies c
                JOIN signals s ON s.company_id = c.id
                WHERE c.is_internal IS NOT FALSE
                """
            )
        ).scalar()
        unknown_industry = db.execute(
            text(
                """
                SELECT COUNT(DISTINCT c.id)
                FROM companies c
                JOIN signals s ON s.company_id = c.id
                WHERE c.is_internal IS NOT FALSE
                  AND (
                    c.industry IS NULL
                    OR TRIM(c.industry) = ''
                    OR LOWER(TRIM(c.industry)) IN ('unknown', 'other', 'new', 'unclassified')
                  )
                """
            )
        ).scalar()
        return {
            "quarantined_companies": int(quarantined or 0),
            "active_companies": int(active or 0),
            "companies_with_signals": int(with_signals or 0),
            "unknown_industry_with_signals": int(unknown_industry or 0),
        }
    except Exception as exc:
        return {"error": str(exc)}


def _merge_database_block(db, telemetry: dict[str, Any]) -> dict[str, Any]:
    counts = _db_counts(db)
    block: dict[str, Any] = {"telemetry": telemetry}
    if counts:
        block.update(counts)
    elif telemetry.get("status") != "connected":
        block["counts_available"] = False
    return block


def _junk_reason_sample(db, sample_size: int = 400) -> dict[str, Any]:
    if db is None:
        return {"available": False}
    try:
        from app.models.company import Company
        from app.services.lead_filter import is_junk

        rows = (
            db.query(Company.name)
            .order_by(Company.id.desc())
            .limit(max(50, sample_size))
            .all()
        )
        reasons: Counter[str] = Counter()
        junk_count = 0
        for (name,) in rows:
            bad, reason = is_junk(name)
            if not bad:
                continue
            junk_count += 1
            key = (reason or "unknown").split(":")[0].strip()[:80] or "unknown"
            reasons[key] += 1
        return {
            "available": True,
            "sample_size": len(rows),
            "junk_in_sample": junk_count,
            "junk_rate": round(junk_count / len(rows), 3) if rows else 0.0,
            "top_reasons": [{"reason": r, "count": c} for r, c in reasons.most_common(12)],
        }
    except Exception as exc:
        return {"available": False, "error": str(exc)}


def _industry_top(db, top_n: int = 15) -> list[dict[str, Any]]:
    if db is None:
        return []
    try:
        from sqlalchemy import text

        rows = db.execute(
            text(
                """
                SELECT COALESCE(NULLIF(TRIM(c.industry), ''), '(blank)') AS industry,
                       COUNT(DISTINCT c.id) AS n
                FROM companies c
                JOIN signals s ON s.company_id = c.id
                WHERE c.is_internal IS NOT FALSE
                GROUP BY 1
                ORDER BY n DESC
                LIMIT :lim
                """
            ),
            {"lim": top_n},
        ).fetchall()
        return [{"industry": str(ind), "count": int(n)} for ind, n in rows]
    except Exception:
        return []


def _gap_frequency(db, limit: int = 80) -> dict[str, Any]:
    if db is None:
        return {"available": False}
    try:
        from app.services.lead_gap_audit import select_gap_repair_candidates

        reports = select_gap_repair_candidates(
            db,
            limit=limit,
            min_score=0.0,
            sales_leads_only=True,
            progress=False,
        )
        gaps: Counter[str] = Counter()
        for report in reports:
            for gap in report.gaps:
                gaps[gap] += 1
        return {
            "available": True,
            "candidates_with_gaps": len(reports),
            "gap_frequency": [{"gap": g, "count": c} for g, c in gaps.most_common(12)],
        }
    except Exception as exc:
        return {"available": False, "error": str(exc)}


def _pipeline_surface_intel(pipeline_leads: list) -> dict[str, Any]:
    industries: Counter[str] = Counter()
    tiers: Counter[str] = Counter()
    robot_types: Counter[str] = Counter()
    for lead in pipeline_leads:
        if not isinstance(lead, dict):
            continue
        ind = (lead.get("industry") or lead.get("sector") or "(blank)").strip() or "(blank)"
        industries[ind] += 1
        tier = (lead.get("tier") or lead.get("priority") or "unknown").strip()
        tiers[tier] += 1
        for rt in lead.get("robot_types_needed") or []:
            if isinstance(rt, str) and rt.strip():
                robot_types[rt.strip()] += 1
    return {
        "lead_count": len(pipeline_leads),
        "industries": [{"industry": i, "count": c} for i, c in industries.most_common(8)],
        "tiers": [{"tier": t, "count": c} for t, c in tiers.most_common(5)],
        "robot_types": [{"type": t, "count": c} for t, c in robot_types.most_common(10)],
    }


def _compute_deltas(current: dict, previous: dict | None) -> dict[str, Any]:
    if not previous:
        return {"available": False}
    prev_intel = previous.get("intelligence") or {}
    cur_intel = current.get("intelligence") or {}

    def _ind_map(rows: list) -> dict[str, int]:
        out: dict[str, int] = {}
        for row in rows or []:
            if isinstance(row, dict):
                out[str(row.get("industry"))] = int(row.get("count") or 0)
        return out

    prev_ind = _ind_map(prev_intel.get("industry_top"))
    cur_ind = _ind_map(cur_intel.get("industry_top"))
    all_keys = set(prev_ind) | set(cur_ind)
    industry_delta = [
        {
            "industry": k,
            "previous": prev_ind.get(k, 0),
            "current": cur_ind.get(k, 0),
            "delta": cur_ind.get(k, 0) - prev_ind.get(k, 0),
        }
        for k in sorted(all_keys, key=lambda x: abs(cur_ind.get(x, 0) - prev_ind.get(x, 0)), reverse=True)
    ][:10]

    prev_gaps = {
        str(r.get("gap")): int(r.get("count") or 0)
        for r in (prev_intel.get("gap_frequency") or {}).get("gap_frequency") or []
        if isinstance(r, dict)
    }
    cur_gaps = {
        str(r.get("gap")): int(r.get("count") or 0)
        for r in (cur_intel.get("gap_frequency") or {}).get("gap_frequency") or []
        if isinstance(r, dict)
    }
    gap_keys = set(prev_gaps) | set(cur_gaps)
    gap_delta = [
        {
            "gap": g,
            "previous": prev_gaps.get(g, 0),
            "current": cur_gaps.get(g, 0),
            "delta": cur_gaps.get(g, 0) - prev_gaps.get(g, 0),
        }
        for g in sorted(gap_keys, key=lambda x: abs(cur_gaps.get(x, 0) - prev_gaps.get(x, 0)), reverse=True)
    ][:10]

    return {
        "available": True,
        "previous_generated_at": previous.get("generated_at"),
        "industry_delta": industry_delta,
        "gap_delta": gap_delta,
        "pipeline_leads_delta": (
            (cur_intel.get("pipeline_surface") or {}).get("lead_count", 0)
            - (prev_intel.get("pipeline_surface") or {}).get("lead_count", 0)
        ),
    }


def _buyer_intent_gate_sample(db, sample_size: int = 150) -> dict[str, Any]:
    if db is None:
        return {"available": False}
    try:
        from collections import Counter

        from app.models.company import Company
        from app.models.signal import Signal
        from app.services.buyer_intent_gate import assess_buyer_intent_gate

        companies = (
            db.query(Company)
            .filter(Company.is_internal.is_(True))
            .order_by(Company.id.desc())
            .limit(max(50, sample_size))
            .all()
        )
        dispositions: Counter[str] = Counter()
        routes: Counter[str] = Counter()
        assessed = 0
        for company in companies:
            signals = (
                db.query(Signal)
                .filter(Signal.company_id == company.id)
                .limit(10)
                .all()
            )
            if not signals:
                continue
            assessed += 1
            result = assess_buyer_intent_gate(
                company_name=company.name,
                signals=signals,
            )
            dispositions[result.disposition] += 1
            routes[result.route] += 1
        return {
            "available": True,
            "sample_companies": len(companies),
            "assessed_with_signals": assessed,
            "dispositions": [{"disposition": d, "count": c} for d, c in dispositions.most_common()],
            "routes": [{"route": r, "count": c} for r, c in routes.most_common()],
            "no_intent_rate": round(
                dispositions.get("no_intent", 0) / assessed, 3
            )
            if assessed
            else 0.0,
        }
    except Exception as exc:
        return {"available": False, "error": str(exc)}


def _build_intelligence(db, pipeline_leads: list, previous: dict | None) -> dict[str, Any]:
    industry_top = _industry_top(db)
    intel = {
        "junk_reasons": _junk_reason_sample(db),
        "gap_frequency": _gap_frequency(db),
        "buyer_intent_gate": _buyer_intent_gate_sample(db),
        "industry_top": industry_top,
        "pipeline_surface": _pipeline_surface_intel(pipeline_leads),
    }
    intel["deltas"] = _compute_deltas({"intelligence": intel}, previous)
    return intel


def build_snapshot(api_base: str, *, previous: dict | None = None) -> dict:
    base = api_base.rstrip("/")
    now = datetime.now(timezone.utc)
    if previous is None:
        previous = _load_previous_snapshot()

    pipeline, pipeline_err = _fetch_json(f"{base}/api/leads/pipeline")
    homepage, homepage_err = _fetch_json(f"{base}/api/leads/homepage")
    summary, summary_err = _fetch_json(f"{base}/api/leads/summary?exclude_junk=true")

    pipeline_leads = []
    if isinstance(pipeline, dict):
        pipeline_leads = pipeline.get("leads") or []

    hot_leads = []
    if isinstance(homepage, dict):
        hot_leads = homepage.get("hotLeads") or []

    alerts: list[str] = []
    built_at = pipeline.get("built_at") if isinstance(pipeline, dict) else None
    if pipeline_err:
        alerts.append(f"pipeline fetch failed: {pipeline_err}")
    elif not pipeline_leads:
        alerts.append("pipeline feed empty")
    if built_at:
        try:
            built_dt = datetime.fromisoformat(str(built_at).replace("Z", "+00:00"))
            age_h = (now - built_dt).total_seconds() / 3600
            if age_h > 6:
                alerts.append(f"pipeline cache stale ({age_h:.1f}h)")
        except ValueError:
            pass
    if homepage_err:
        alerts.append(f"homepage fetch failed: {homepage_err}")
    elif not hot_leads:
        alerts.append("homepage hotLeads empty")

    db = _db_session()
    telemetry = database_telemetry(_root)
    if telemetry.get("status") != "connected" and db is None:
        telemetry = {**telemetry, "intelligence_blocked": True}
    try:
        intelligence = _build_intelligence(db, pipeline_leads, previous)
        database = _merge_database_block(db, telemetry)
    finally:
        if db is not None:
            db.close()

    intel_alerts: list[str] = []
    if telemetry.get("status") != "connected":
        reason = telemetry.get("reason") or "unknown"
        intel_alerts.append(f"DB telemetry unavailable ({reason})")
    elif not (intelligence.get("junk_reasons") or {}).get("available"):
        intel_alerts.append("intelligence slice incomplete despite DB connection")
    junk = intelligence.get("junk_reasons") or {}
    if junk.get("available") and junk.get("junk_rate", 0) > 0.35:
        intel_alerts.append(f"high junk rate in sample ({junk.get('junk_rate'):.0%})")
    gaps = intelligence.get("gap_frequency") or {}
    if gaps.get("available"):
        top_gap = (gaps.get("gap_frequency") or [{}])[0]
        if top_gap.get("gap") == "industry" and top_gap.get("count", 0) >= 10:
            intel_alerts.append("industry gap dominant in pipeline surface candidates")
    if database and database.get("unknown_industry_with_signals", 0) > 50:
        intel_alerts.append(
            f"unknown industry rows with signals: {database['unknown_industry_with_signals']}"
        )
    alerts.extend(intel_alerts)

    return {
        "generated_at": now.isoformat(),
        "api_base": base,
        "git": _git_info(),
        "api": {
            "pipeline": {
                "ok": pipeline_err is None,
                "error": pipeline_err,
                "built_at": built_at,
                "cache_pending": pipeline.get("cache_pending") if isinstance(pipeline, dict) else None,
                "leads_count": len(pipeline_leads),
                "visible_count": (
                    (pipeline.get("entitlements") or {}).get("visible_count")
                    if isinstance(pipeline, dict)
                    else None
                ),
            },
            "homepage": {
                "ok": homepage_err is None,
                "error": homepage_err,
                "hot_leads_count": len(hot_leads),
            },
            "summary": {
                "ok": summary_err is None,
                "error": summary_err,
                "data": summary if isinstance(summary, dict) else None,
            },
        },
        "database": database,
        "intelligence": intelligence,
        "alerts": alerts,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Write harness metrics snapshot JSON")
    parser.add_argument(
        "--api-base",
        default=os.getenv("API_BASE", "https://ready-2-robot.fly.dev"),
    )
    parser.add_argument("--stdout", action="store_true", help="Print JSON to stdout only")
    args = parser.parse_args()

    snapshot = build_snapshot(args.api_base)
    payload = json.dumps(snapshot, indent=2, default=str)

    if args.stdout:
        print(payload)
        return 0

    reports = _root / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = reports / f"harness_snapshot_{stamp}.json"
    latest = reports / "harness_snapshot_latest.json"
    path.write_text(payload + "\n", encoding="utf-8")
    latest.write_text(payload + "\n", encoding="utf-8")

    print(f"Wrote {path}")
    print(f"Wrote {latest}")
    telemetry = (snapshot.get("database") or {}).get("telemetry") or {}
    print(f"DB telemetry: {telemetry.get('status')} ({telemetry.get('source') or telemetry.get('reason', 'n/a')})")
    intel = snapshot.get("intelligence") or {}
    junk_ok = (intel.get("junk_reasons") or {}).get("available")
    gap_ok = (intel.get("gap_frequency") or {}).get("available")
    print(f"Intelligence: junk={junk_ok} gaps={gap_ok} industries={len(intel.get('industry_top') or [])}")
    if snapshot["alerts"]:
        print("Alerts:", "; ".join(snapshot["alerts"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
