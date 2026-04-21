#!/usr/bin/env python3
"""Audit the data pipeline: Supabase `companies` / `signals` + optional Fly `/api/leads`.

Env (optional):
  AUDIT_PIPELINE_API_URL          — default https://ready-2-robot.fly.dev
  AUDIT_PIPELINE_API_TIMEOUT_SEC  — HTTP read timeout in seconds (default 25)
  AUDIT_PIPELINE_SKIP_API         — if 1/true, skip Step 2 (API probe)

Loads DATABASE_URL like ``check_db_connection.py`` (``.env.local``, ``.env``, ``DOTENV_PATH``).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_root))

from dotenv import load_dotenv

from app.env_loader import database_url_is_template_or_sqlite

_shell_database_url = (os.environ.get("DATABASE_URL") or "").strip()
load_dotenv(_root / "frontend" / "nextjs" / ".env.local")
load_dotenv(_root / ".env", override=True)
_dotenv_path = (os.getenv("DOTENV_PATH") or "").strip()
if _dotenv_path:
    load_dotenv(Path(_dotenv_path).expanduser(), override=True)
_loaded_after_dotenv = (os.environ.get("DATABASE_URL") or "").strip()
if _shell_database_url and database_url_is_template_or_sqlite(_loaded_after_dotenv):
    os.environ["DATABASE_URL"] = _shell_database_url

import psycopg2


def _env_float(name: str, default: float) -> float:
    raw = (os.getenv(name) or "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _truthy(name: str) -> bool:
    return (os.getenv(name) or "").strip().lower() in ("1", "true", "yes", "on")


def audit_database() -> bool:
    """Check Supabase: ``companies`` and ``signals`` (current schema — not a ``leads`` table)."""
    print("🔍 STEP 1: DATABASE AUDIT")
    print("=" * 60)

    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not set!")
        return False

    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM companies")
        total = cur.fetchone()[0]
        print(f"\n📊 COMPANIES TABLE: {total} total rows")

        cur.execute("SELECT COUNT(*) FROM companies WHERE is_internal = false")
        external = cur.fetchone()[0]
        print(f"✨ External companies (is_internal = false): {external}")

        # Tier HOT/WARM is computed in Python (classify_lead). Proxy: any score row ≥ 70.
        cur.execute(
            """
            SELECT COUNT(DISTINCT c.id) FROM companies c
            WHERE c.is_internal = false
              AND EXISTS (
                SELECT 1 FROM scores s
                WHERE s.company_id = c.id AND s.overall_intent_score >= 70
              )
            """
        )
        high_intent = cur.fetchone()[0]
        print(
            f"🎯 High-intent proxy (external + score ≥ 70, any row): {high_intent}  "
            "(not identical to API HOT/WARM tiers)"
        )

        cur.execute("SELECT COUNT(*) FROM signals")
        signals = cur.fetchone()[0]
        print(f"\n⚡ SIGNALS TABLE: {signals} total signals")

        cur.execute(
            """
            SELECT c.name, c.industry,
                   COALESCE(
                     (SELECT MAX(s.overall_intent_score) FROM scores s WHERE s.company_id = c.id),
                     0
                   )::float AS best_score
            FROM companies c
            WHERE c.is_internal = false
            ORDER BY c.id DESC
            LIMIT 3
            """
        )
        samples = cur.fetchall()
        print("\n📋 SAMPLE EXTERNAL COMPANIES (latest ids):")
        for name, industry, best_score in samples:
            ind = industry or "—"
            print(f"  - {name!r}: industry={ind!r}, best overall_intent_score={best_score:.1f}")

        cur.close()
        conn.close()

        print("\n✅ Database has company rows!")
        if total > 0 and external == 0:
            print(
                "ℹ️  All sampled rows have is_internal=true in DB; the public API may still "
                "surface companies (see _lead_rows_query / classify_lead — not gated on is_internal)."
            )

        # API lists from the full candidate pool; “pipeline has data” means companies exist.
        return total > 0

    except Exception as e:
        print(f"❌ Database error: {e}")
        return False


def test_api_endpoint() -> bool:
    """GET ``/api/leads`` on Fly (or override). Timeout configurable."""
    if _truthy("AUDIT_PIPELINE_SKIP_API"):
        print("\n\n🔍 STEP 2: API ENDPOINT TEST (skipped — AUDIT_PIPELINE_SKIP_API set)")
        print("=" * 60)
        return True

    import requests

    print("\n\n🔍 STEP 2: API ENDPOINT TEST")
    print("=" * 60)

    base = (os.getenv("AUDIT_PIPELINE_API_URL") or "https://ready-2-robot.fly.dev").rstrip("/")
    timeout = _env_float("AUDIT_PIPELINE_API_TIMEOUT_SEC", 25.0)
    url = f"{base}/api/leads?limit=5"
    print(f"\nGET {url}")
    print(f"Timeout: {timeout}s (set AUDIT_PIPELINE_API_TIMEOUT_SEC to change)")

    try:
        resp = requests.get(url, timeout=timeout)
        print(f"Status: {resp.status_code}")

        if resp.status_code != 200:
            print(f"❌ API returned {resp.status_code}")
            if resp.text[:500]:
                print(resp.text[:500])
            return False

        data = resp.json()
        if not isinstance(data, list):
            print(f"❌ Expected JSON list, got {type(data).__name__}")
            return False

        print(f"Rows returned: {len(data)}")
        if len(data) > 0:
            first = data[0].get("company_name") or data[0].get("name")
            print(f"First row company_name: {first!r}")
            print("✅ API returning data!")
            return True

        print("❌ API returns empty array (may be normal if pool is empty for this rotation).")
        return False

    except Exception as e:
        print(f"❌ API error: {e}")
        return False


def check_backend_code() -> None:
    """Lightweight peek at ``get_leads`` wiring (informational)."""
    print("\n\n🔍 STEP 3: BACKEND CODE REVIEW")
    print("=" * 60)

    leads_path = _root / "app" / "api" / "leads.py"
    if not leads_path.is_file():
        print(f"\n⚠️  Missing {leads_path}")
        return

    content = leads_path.read_text(encoding="utf-8")
    print("\nChecking app/api/leads.py...")

    if "is_internal" in content:
        print("ℹ️  References is_internal (Company rows)")

    if ".filter(" in content:
        print("ℹ️  Uses SQLAlchemy .filter() on lead query")

    marker = '@router.get("/leads")'
    if marker in content:
        lines = content.split("\n")
        function_code: list[str] = []
        in_function = False
        for line in lines:
            if marker in line:
                in_function = True
            if in_function:
                function_code.append(line)
                if line.strip().startswith("@router") and len(function_code) > 5:
                    break
                if line.strip().startswith("def ") and len(function_code) > 5:
                    break

        print("\n📄 Current /api/leads handler (first lines):")
        print("-" * 60)
        print("\n".join(function_code[:30]))
        print("-" * 60)


if __name__ == "__main__":
    print("🚀 DATA PIPELINE AUDIT")
    print("=" * 60)

    db_ok = audit_database()
    api_ok = test_api_endpoint()
    check_backend_code()

    print("\n\n📊 AUDIT SUMMARY")
    print("=" * 60)
    print(f'Database has companies: {"✅" if db_ok else "❌"}')
    skipped = _truthy("AUDIT_PIPELINE_SKIP_API")
    if skipped:
        print("API probe: skipped")
    else:
        print(f'API returns rows: {"✅" if api_ok else "❌"}')

    if db_ok and not api_ok and not skipped:
        print("\n🔧 DIAGNOSIS: Data in DB but /api/leads empty or unreachable")
        print("   → Check Fly app health, cold start, or AUDIT_PIPELINE_API_TIMEOUT_SEC")
        print("   → Or lead filters / rotation returning an empty slice for this request")
    elif not db_ok:
        print("\n🔧 DIAGNOSIS: companies table empty or DB connection failed")
        print("   → Verify DATABASE_URL and migrations")
    else:
        print("\n✅ Pipeline checks passed for configured steps!")
