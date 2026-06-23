#!/usr/bin/env python3
"""Rebuild public pipeline/homepage caches (local CLI or prod DB via DATABASE_URL)."""
from __future__ import annotations

import argparse
import json
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
_loaded = (os.environ.get("DATABASE_URL") or "").strip()
if _shell_database_url and database_url_is_template_or_sqlite(_loaded):
    os.environ["DATABASE_URL"] = _shell_database_url


def main() -> int:
    parser = argparse.ArgumentParser(description="Rebuild pipeline/public surface caches")
    parser.add_argument(
        "--remote",
        action="store_true",
        help="POST to Fly admin API (needs ADMIN_KEY in .env)",
    )
    parser.add_argument(
        "--api-base",
        default=os.getenv("API_BASE", "https://ready-2-robot.fly.dev"),
        help="API base when using --remote",
    )
    args = parser.parse_args()

    if args.remote:
        admin_key = (os.getenv("ADMIN_KEY") or "").strip()
        if not admin_key:
            print("ADMIN_KEY missing from .env — cannot call admin API", file=sys.stderr)
            return 1
        import subprocess

        base = args.api_base.rstrip("/")
        url = f"{base}/api/admin/leads/refresh-pipeline-cache"
        try:
            proc = subprocess.run(
                [
                    "curl",
                    "-sS",
                    "-X",
                    "POST",
                    url,
                    "-H",
                    f"X-Admin-Key: {admin_key}",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            print(proc.stdout)
            return 0
        except subprocess.CalledProcessError as exc:
            print(f"Remote refresh failed: {exc.stderr or exc.stdout}", file=sys.stderr)
            return 1

    from app.database import SessionLocal
    from app.services.public_surface_cache import refresh_pipeline_surface_caches

    db = SessionLocal()
    try:
        print("Rebuilding pipeline surfaces (may take several minutes)…", flush=True)
        stats = refresh_pipeline_surface_caches(db)
        db.commit()
        print(json.dumps(stats, indent=2, default=str))
        return 0
    except Exception as exc:
        db.rollback()
        print(f"Refresh failed: {exc}", file=sys.stderr)
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
