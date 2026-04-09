#!/usr/bin/env python3
"""
List company names still flagged as junk by lead_filter.is_junk (DB audit).

Use when checking the site: public UI uses exclude_junk=true by default; this shows
what would still be hidden or what remains to purge.

  python3 scripts/audit_junk_names.py
  python3 scripts/audit_junk_names.py --limit 200
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

_root = Path(__file__).resolve().parents[1]
load_dotenv(_root / ".env")
load_dotenv(_root / "frontend" / "nextjs" / ".env.local", override=True)

from app.database import SessionLocal
from app.models.company import Company
from app.services.lead_filter import is_junk


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=500, help="Max rows to print")
    args = ap.parse_args()

    db = SessionLocal()
    try:
        rows = db.query(Company.id, Company.name).order_by(Company.id.desc()).all()
        junk_rows = []
        for cid, name in rows:
            bad, reason = is_junk(name)
            if bad:
                junk_rows.append((cid, name, reason))

        print(f"Total companies: {len(rows)}")
        print(f"Junk by is_junk(): {len(junk_rows)}\n")
        for cid, name, reason in junk_rows[: args.limit]:
            print(f"  id={cid}  [{reason[:72]}]")
            print(f"         {name!r}")
        if len(junk_rows) > args.limit:
            print(f"\n… {len(junk_rows) - args.limit} more (raise --limit)")
        if not junk_rows:
            print("✅ No junk names left in DB — site filters will have nothing extra to hide.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
