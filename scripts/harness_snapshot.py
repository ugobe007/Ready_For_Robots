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
from datetime import datetime, timezone
from pathlib import Path

_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_root))

from dotenv import load_dotenv

from app.env_loader import database_url_is_template_or_sqlite

_shell_database_url = (os.environ.get("DATABASE_URL") or "").strip()
load_dotenv(_root / "frontend" / "nextjs" / ".env.local")
load_dotenv(_root / ".env", override=True)
_loaded = (os.environ.get("DATABASE_URL") or "").strip()
if _shell_database_url and database_url_is_template_or_sqlite(_loaded):
    os.environ["DATABASE_URL"] = _shell_database_url


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


def _db_counts() -> dict | None:
    db_url = (os.environ.get("DATABASE_URL") or "").strip()
    if not db_url or database_url_is_template_or_sqlite(db_url):
        return None
    try:
        from sqlalchemy import text

        from app.database import SessionLocal

        db = SessionLocal()
        try:
            quarantined = db.execute(
                text("SELECT COUNT(*) FROM companies WHERE is_internal = false")
            ).scalar()
            public = db.execute(
                text("SELECT COUNT(*) FROM companies WHERE is_internal IS NOT FALSE")
            ).scalar()
            return {"quarantined_companies": int(quarantined or 0), "public_companies": int(public or 0)}
        finally:
            db.close()
    except Exception as exc:
        return {"error": str(exc)}


def build_snapshot(api_base: str) -> dict:
    base = api_base.rstrip("/")
    now = datetime.now(timezone.utc)

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
        "database": _db_counts(),
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
    if snapshot["alerts"]:
        print("Alerts:", "; ".join(snapshot["alerts"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
