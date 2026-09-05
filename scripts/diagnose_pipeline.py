#!/usr/bin/env python3
"""
End-to-end pipeline diagnostic: DB → Fly API → Vercel proxy → frontend-shaped payloads.

Run from repo root:
  python3 scripts/diagnose_pipeline.py
  python3 scripts/diagnose_pipeline.py --production-only
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import requests
from dotenv import load_dotenv
from sqlalchemy import func, text

_root = Path(__file__).resolve().parents[1]
load_dotenv(_root / "frontend" / "nextjs" / ".env.local")
load_dotenv(_root / ".env", override=True)

FLY_BASE = "https://ready-2-robot.fly.dev"
VERCEL_BASE = "https://readyforrobots.com"


def _section(title: str) -> None:
    print(f"\n{'=' * 60}\n{title}\n{'=' * 60}")


def _ok(msg: str) -> None:
    print(f"  OK  {msg}")


def _fail(msg: str) -> None:
    print(f"  FAIL  {msg}")


def _warn(msg: str) -> None:
    print(f"  WARN  {msg}")


def check_database() -> dict:
    _section("1. DATABASE (local DATABASE_URL from .env)")
    out: dict = {"ok": False}
    try:
        from app.database import DATABASE_URL, SessionLocal
        from app.models.company import Company
        from app.models.signal import Signal
        from app.models.score import Score

        u = urlparse(DATABASE_URL.replace("postgresql+psycopg2://", "postgresql://", 1))
        print(f"  host={u.hostname} port={u.port} user={u.username}")

        db = SessionLocal()
        try:
            t0 = time.time()
            companies = db.query(func.count(Company.id)).scalar() or 0
            signals = db.query(func.count(Signal.id)).scalar() or 0
            scored = db.query(func.count(Score.id)).scalar() or 0
            elapsed = time.time() - t0

            out.update({
                "ok": companies > 0,
                "companies": companies,
                "signals": signals,
                "scored": scored,
                "elapsed_s": round(elapsed, 2),
            })
            if companies > 0:
                _ok(f"connected — {companies} companies, {signals} signals, {scored} scored ({elapsed:.2f}s)")
            else:
                _fail("connected but companies table is empty")
        finally:
            db.close()
    except Exception as exc:
        out["error"] = str(exc)
        _fail(str(exc))
    return out


def _fetch_json(url: str, timeout: float = 20.0, headers: dict | None = None) -> dict:
    t0 = time.time()
    try:
        r = requests.get(url, timeout=timeout, headers=headers or {})
        elapsed = time.time() - t0
        body = None
        try:
            body = r.json()
        except Exception:
            body = r.text[:200]
        return {
            "url": url,
            "status": r.status_code,
            "elapsed_s": round(elapsed, 2),
            "ok": r.status_code == 200,
            "body": body,
            "error": None,
        }
    except Exception as exc:
        return {
            "url": url,
            "status": 0,
            "elapsed_s": round(time.time() - t0, 2),
            "ok": False,
            "body": None,
            "error": str(exc),
        }


def check_http_layer(base: str, label: str) -> dict:
    _section(f"2. API — {label} ({base})")
    results: dict = {"base": base, "checks": {}}

    health = _fetch_json(f"{base}/health", timeout=15)
    results["checks"]["health"] = health
    if health["ok"]:
        _ok(f"/health → {health['status']} in {health['elapsed_s']}s")
    else:
        _fail(f"/health → {health.get('error') or health['status']}")

    db_health = _fetch_json(f"{base}/health/db", timeout=15)
    results["checks"]["health_db"] = db_health
    if db_health["ok"]:
        db_body = db_health["body"] if isinstance(db_health["body"], dict) else {}
        _ok(f"/health/db → {db_body} in {db_health['elapsed_s']}s")
    else:
        _fail(f"/health/db → {db_health.get('error') or db_health['status']}")

    summary = _fetch_json(f"{base}/api/leads/summary?exclude_junk=true", timeout=25)
    results["checks"]["summary"] = summary
    if summary["ok"] and isinstance(summary["body"], dict):
        b = summary["body"]
        companies = b.get("companies_in_database")
        hot = b.get("hot")
        _ok(
            f"/api/leads/summary → companies={companies} hot={hot} "
            f"in {summary['elapsed_s']}s"
        )
        if not companies and not b.get("total"):
            _warn("summary returned zero totals — Pipeline cards will show 0")
    else:
        _fail(f"/api/leads/summary → {summary.get('error') or summary['status']}")

    leads = _fetch_json(f"{base}/api/leads?limit=18&exclude_junk=true&sort=score", timeout=25)
    results["checks"]["leads"] = leads
    if leads["ok"] and isinstance(leads["body"], list):
        n = len(leads["body"])
        first = leads["body"][0].get("company_name") if leads["body"] else None
        _ok(f"/api/leads → {n} rows, first={first!r} in {leads['elapsed_s']}s")
        if n == 0:
            _warn("leads list empty — Pipeline working slice will be 0")
    else:
        _fail(f"/api/leads → {leads.get('error') or leads['status']}")

    homepage = _fetch_json(f"{base}/api/leads/homepage", timeout=30)
    results["checks"]["homepage"] = homepage
    if homepage["ok"] and isinstance(homepage["body"], dict):
        s = homepage["body"].get("summary") or {}
        hot_leads = homepage["body"].get("hotLeads") or []
        _ok(
            f"/api/leads/homepage → summary.total={s.get('total')} "
            f"hotLeads={len(hot_leads)} in {homepage['elapsed_s']}s"
        )
    else:
        _fail(f"/api/leads/homepage → {homepage.get('error') or homepage['status']}")

    return results


def check_api_code_paths() -> dict:
    _section("3. API CODE PATHS (local, no HTTP)")
    out: dict = {"ok": False}
    try:
        from app.database import SessionLocal
        from app.api.leads import (
            _compute_pipeline_summary,
            _compute_pipeline_summary_fast,
            _lead_rows_query_limited,
        )

        db = SessionLocal()
        try:
            t0 = time.time()
            fast = _compute_pipeline_summary_fast(db)
            t_fast = time.time() - t0

            t0 = time.time()
            full = _compute_pipeline_summary(db, True)
            t_full = time.time() - t0

            t0 = time.time()
            rows = _lead_rows_query_limited(db, 18).all()
            t_rows = time.time() - t0

            out = {
                "ok": fast.get("companies_in_database", 0) > 0,
                "fast": fast,
                "fast_s": round(t_fast, 2),
                "full_s": round(t_full, 2),
                "rows_s": round(t_rows, 2),
                "row_count": len(rows),
            }
            _ok(
                f"fast summary: {fast.get('companies_in_database')} companies "
                f"({t_fast:.2f}s)"
            )
            _ok(f"full summary: {full.get('companies_in_database')} companies ({t_full:.2f}s)")
            _ok(f"lead_rows_query_limited(18): {len(rows)} rows ({t_rows:.2f}s)")
            if t_full > 10:
                _warn(f"full summary slow ({t_full:.1f}s) — cold cache may timeout on Fly")
        finally:
            db.close()
    except Exception as exc:
        out["error"] = str(exc)
        _fail(str(exc))
    return out


def print_diagnosis(db: dict, fly: dict, vercel: dict, code: dict) -> None:
    _section("DIAGNOSIS")
    issues: list[str] = []

    if not db.get("ok"):
        issues.append("Database unreachable or empty — fix DATABASE_URL / Supabase first.")
    if db.get("ok") and fly.get("checks", {}).get("summary", {}).get("ok") is False:
        issues.append("Fly API not returning summary — machine down, timeout, or deploy issue.")
    if db.get("ok") and vercel.get("checks", {}).get("summary", {}).get("ok") is False:
        issues.append(
            "Vercel proxy not returning summary — check vercel.json rewrites and redeploy."
        )
    if fly.get("checks", {}).get("leads", {}).get("ok") and isinstance(
        fly["checks"]["leads"].get("body"), list
    ) and len(fly["checks"]["leads"]["body"]) == 0:
        issues.append("Fly /api/leads returns [] — backend filter or cold-path timeout.")

    fly_summary = (fly.get("checks") or {}).get("summary") or {}
    vercel_summary = (vercel.get("checks") or {}).get("summary") or {}
    if fly_summary.get("ok") and not vercel_summary.get("ok"):
        issues.append(
            "Fly works but readyforrobots.com proxy fails — frontend will show 0 until Vercel fix deploys."
        )
    if fly_summary.get("ok") and vercel_summary.get("ok"):
        fb = fly_summary.get("body") or {}
        vb = vercel_summary.get("body") or {}
        if fb.get("companies_in_database") and not vb.get("companies_in_database"):
            issues.append("Vercel summary missing companies_in_database — stale cache or partial response.")

    if code.get("full_s", 0) > 15:
        issues.append(
            f"Full summary build takes {code['full_s']}s locally — today's regressions used this on cold requests."
        )

    if not issues:
        _ok("All layers healthy. If UI still shows 0, hard-refresh browser or clear localStorage (rfr_admin_snapshot_v1).")
    else:
        print("\n  Likely break points (in order):")
        for i, item in enumerate(issues, 1):
            print(f"    {i}. {item}")

    print("\n  Recent fixes (investigate if regression after these):")
    print("    • Slow full-table summary query + cross-origin Fly calls from Vercel")
    print("    • Homepage cache overwriting pipeline summary cache")
    print("    • Admin snapshot 503 on empty sections")
    print("    • Fly machine stopped / load-balancer errors during deploy")


def main() -> None:
    parser = argparse.ArgumentParser(description="Pipeline layer diagnostic")
    parser.add_argument(
        "--production-only",
        action="store_true",
        help="Skip local DB and code-path checks",
    )
    args = parser.parse_args()

    print("Pipeline diagnostic — DB → Fly → Vercel → code paths")
    db: dict = {"ok": True}
    code: dict = {"ok": True}
    if not args.production_only:
        db = check_database()
        code = check_api_code_paths()

    fly = check_http_layer(FLY_BASE, "Fly.io")
    vercel = check_http_layer(VERCEL_BASE, "Vercel (readyforrobots.com)")

    print_diagnosis(db, fly, vercel, code)

    failed = (
        not db.get("ok", True)
        or not fly.get("checks", {}).get("summary", {}).get("ok")
        or not vercel.get("checks", {}).get("summary", {}).get("ok")
    )
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
