#!/usr/bin/env python3
"""
Physically merge duplicate companies that share the same normalized website domain.

Usage:
  python scripts/merge_duplicate_companies_by_domain.py           # dry-run plan
  python scripts/merge_duplicate_companies_by_domain.py --execute # apply merges
  python scripts/merge_duplicate_companies_by_domain.py --execute --domain example.com

Requires DATABASE_URL (e.g. Supabase). Run Alembic migrations first so `website_domain` exists.
"""
from __future__ import annotations

import argparse
import os
import sys

# Repo root on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from pathlib import Path

from app.env_loader import database_url_is_template_or_sqlite

_shell_database_url = (os.environ.get("DATABASE_URL") or "").strip()
_root = Path(__file__).resolve().parents[1]
load_dotenv(_root / "frontend" / "nextjs" / ".env.local")
load_dotenv(_root / ".env", override=True)
_loaded_after_dotenv = (os.environ.get("DATABASE_URL") or "").strip()
if _shell_database_url and database_url_is_template_or_sqlite(_loaded_after_dotenv):
    os.environ["DATABASE_URL"] = _shell_database_url

from app.database import SessionLocal
from app.services.company_merge import merge_duplicate_companies_by_domain


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge duplicate companies by website_domain")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually merge (default is dry-run)",
    )
    parser.add_argument("--domain", type=str, default=None, help="Only this normalized domain")
    args = parser.parse_args()
    dry_run = not args.execute

    db = SessionLocal()
    try:
        result = merge_duplicate_companies_by_domain(
            db, dry_run=dry_run, domain_filter=args.domain
        )
    finally:
        db.close()

    import json

    print(json.dumps(result, indent=2, default=str))
    if dry_run:
        print("\nDry run — no rows deleted. Re-run with --execute to apply.", file=sys.stderr)


if __name__ == "__main__":
    main()
