#!/usr/bin/env python3
"""
Report companies where keyword inference differs from stored industry, excluding Unknown.

Uses the same name + signal text blob as ``cleanup_leads.phase_reinfer_industry``:
``infer_industry_from_text(name + signal texts)`` vs ``companies.industry``.

Does not modify the database.

Usage::

  export DOTENV_PATH=/path/to/main/.env   # optional; see cleanup_leads.py
  python3 scripts/examine_industry_mismatch.py
  python3 scripts/examine_industry_mismatch.py --sample 100
  python3 scripts/examine_industry_mismatch.py --respect-cleanup-skip --jsonl -o data/industry_mismatches.jsonl

  # Limit scan for a quick smoke test
  python3 scripts/examine_industry_mismatch.py --max-companies 500
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

from app.env_loader import database_url_is_template_or_sqlite

_shell_database_url = (os.environ.get("DATABASE_URL") or "").strip()
_root = Path(__file__).resolve().parents[1]
load_dotenv(_root / "frontend" / "nextjs" / ".env.local")
load_dotenv(_root / ".env", override=True)
_dotenv_path = (os.getenv("DOTENV_PATH") or "").strip()
if _dotenv_path:
    load_dotenv(Path(_dotenv_path).expanduser(), override=True)
_loaded_after_dotenv = (os.environ.get("DATABASE_URL") or "").strip()
if _shell_database_url and database_url_is_template_or_sqlite(_loaded_after_dotenv):
    os.environ["DATABASE_URL"] = _shell_database_url

from sqlalchemy.orm import joinedload

from app.database import SessionLocal
from app.models.company import Company
from app.services.industry_inference import (
    infer_industry_from_text,
    should_skip_industry_reinfer_for_company_name,
)


def _blob_for_company(c: Company) -> str:
    parts = [c.name or ""]
    for s in c.signals or []:
        if s.signal_text:
            parts.append(s.signal_text)
    return " ".join(parts)


def main() -> None:
    ap = argparse.ArgumentParser(
        description="List rows where inferred industry != stored and inference is not Unknown."
    )
    ap.add_argument(
        "--sample",
        "-n",
        type=int,
        default=50,
        metavar="N",
        help="Max mismatch rows to print or write (default 50). Use 0 for no limit.",
    )
    ap.add_argument(
        "--max-companies",
        type=int,
        default=None,
        metavar="M",
        help="Only scan the first M companies by id (optional smoke test).",
    )
    ap.add_argument(
        "--since-id",
        type=int,
        default=None,
        help="Only companies with id >= this value.",
    )
    ap.add_argument(
        "--respect-cleanup-skip",
        action="store_true",
        help="Exclude rows where cleanup_leads would skip reinfer (should_skip_industry_reinfer_for_company_name).",
    )
    ap.add_argument(
        "--jsonl",
        action="store_true",
        help="Write JSONL instead of a text table (respects --sample as max lines written).",
    )
    ap.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output file for --jsonl (default: stdout).",
    )
    args = ap.parse_args()

    db = SessionLocal()
    try:
        q = db.query(Company).options(joinedload(Company.signals)).order_by(Company.id)
        if args.since_id is not None:
            q = q.filter(Company.id >= args.since_id)
        if args.max_companies is not None:
            q = q.limit(args.max_companies)
        companies = q.all()
    finally:
        db.close()

    mismatches: list[dict] = []
    for c in companies:
        stored = (c.industry or "").strip()
        skip_name = should_skip_industry_reinfer_for_company_name(c.name)
        if args.respect_cleanup_skip and skip_name:
            continue
        inf = infer_industry_from_text(_blob_for_company(c))
        if inf == "Unknown":
            continue
        if inf == stored:
            continue
        mismatches.append(
            {
                "id": c.id,
                "name": c.name or "",
                "stored_industry": stored or None,
                "inferred_industry": inf,
                "cleanup_would_skip_name": skip_name,
            }
        )

    total = len(mismatches)
    if args.sample < 0:
        print("--sample must be >= 0", file=sys.stderr)
        sys.exit(2)
    out_limit: int | None = None if args.sample == 0 else args.sample

    print(
        f"examine_industry_mismatch: scanned={len(companies)}  mismatches={total}  "
        f"(infer != stored, infer != Unknown"
        + ("; respect-cleanup-skip" if args.respect_cleanup_skip else "")
        + ")",
        file=sys.stderr,
    )

    if args.jsonl:
        dest = open(args.output, "w", encoding="utf-8") if args.output else sys.stdout
        try:
            for i, row in enumerate(mismatches):
                if out_limit is not None and i >= out_limit:
                    break
                dest.write(json.dumps(row, ensure_ascii=False) + "\n")
            if args.output:
                print(f"wrote {min(total, out_limit or total)} line(s) → {args.output}", file=sys.stderr)
        finally:
            if args.output:
                dest.close()
        return

    for i, row in enumerate(mismatches):
        if out_limit is not None and i >= out_limit:
            break
        skip = " skip" if row["cleanup_would_skip_name"] else ""
        print(
            f"id={row['id']}{skip}\n  stored: {row['stored_industry']!r}\n  infer:  {row['inferred_industry']!r}\n  name: {row['name'][:120]!r}"
        )
    if out_limit is not None and total > out_limit:
        print(f"\n… and {total - out_limit} more mismatches (--sample 0 for all, or --jsonl -o)", file=sys.stderr)


if __name__ == "__main__":
    main()
