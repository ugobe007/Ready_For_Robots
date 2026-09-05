#!/usr/bin/env python3
"""
Purge junk company records from the database.

Usage:
  python3 scripts/purge_junk_leads.py            # dry run — preview only
  python3 scripts/purge_junk_leads.py --delete   # actually delete junk (prompts for yes)
  python3 scripts/purge_junk_leads.py --delete --yes  # non-interactive (CI / automation)
  python3 scripts/purge_junk_leads.py --delete --limit 500  # delete in batches

Run from the repo root with the venv active:
  cd /path/to/your/Ready_For_Robots
  source venv/bin/activate
  python3 scripts/purge_junk_leads.py

Requires a valid ``DATABASE_URL`` in repo-root ``.env`` (see ``.env.example``).
"""
import sys
import os
import argparse
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path

from dotenv import load_dotenv

from app.env_loader import database_url_is_template_or_sqlite

_shell_database_url = (os.environ.get("DATABASE_URL") or "").strip()
_root = Path(__file__).resolve().parents[1]
load_dotenv(_root / "frontend" / "nextjs" / ".env.local")
load_dotenv(_root / ".env", override=True)
_loaded_after_dotenv = (os.environ.get("DATABASE_URL") or "").strip()
if _shell_database_url and database_url_is_template_or_sqlite(_loaded_after_dotenv):
    os.environ["DATABASE_URL"] = _shell_database_url

from app.database import SessionLocal
from app.models.company import Company
from app.services.lead_name_gate import check_lead_name


def main():
    parser = argparse.ArgumentParser(description="Purge junk company names from the DB")
    parser.add_argument("--delete", action="store_true",
                        help="Actually delete. Default is dry-run (preview only).")
    parser.add_argument("--limit", type=int, default=None,
                        help="Max records to delete in one run (safety cap).")
    parser.add_argument("--yes", action="store_true",
                        help="With --delete, skip confirmation prompt (use with care).")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        print("Scanning companies…")
        companies = db.query(Company).all()
        total = len(companies)
        print(f"Total companies in DB: {total}")

        junk = []
        reason_counts: Counter = Counter()
        for c in companies:
            ok, reason = check_lead_name(c.name or "")
            bad = not ok
            if bad:
                short_reason = reason.split(":")[0]
                reason_counts[short_reason] += 1
                junk.append((c, reason))

        print(f"\nJunk found: {len(junk)} ({100*len(junk)/max(1,total):.1f}% of total)\n")

        # Reason breakdown
        print("── Junk reason breakdown ──────────────────────────────")
        for reason, count in reason_counts.most_common():
            print(f"  {count:4d}  {reason}")

        # Sample of names
        print(f"\n── Sample junk names (first 60) ───────────────────────")
        for c, reason in sorted(junk, key=lambda x: x[0].name or "")[:60]:
            print(f"  [{reason[:50]}]  {repr(c.name)}")

        if len(junk) > 60:
            print(f"  … and {len(junk)-60} more")

        if not args.delete:
            print("\n── Dry run — no changes made. ─────────────────────────")
            print("Run with --delete to remove these records.")
            return

        # Apply limit
        to_delete = junk
        if args.limit:
            to_delete = junk[:args.limit]
            print(f"\n⚠  limit set — deleting {len(to_delete)} of {len(junk)} junk records")

        if not args.yes:
            confirm = input(f"\nDelete {len(to_delete)} junk companies + their signals? [yes/no]: ")
            if confirm.strip().lower() != "yes":
                print("Aborted — no changes made.")
                return

        deleted = 0
        for c, _ in to_delete:
            db.delete(c)
            deleted += 1
            if deleted % 100 == 0:
                db.flush()
                print(f"  …deleted {deleted}")

        db.commit()
        print(f"\n✅  Deleted {deleted} junk records. DB now has {total - deleted} companies.")

    finally:
        db.close()


if __name__ == "__main__":
    main()
