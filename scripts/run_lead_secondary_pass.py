#!/usr/bin/env python3
"""Run the gap-driven secondary rescue batch (manual / CI smoke)."""
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
_dotenv_path = (os.getenv("DOTENV_PATH") or "").strip()
if _dotenv_path:
    load_dotenv(Path(_dotenv_path).expanduser(), override=True)
_loaded = (os.environ.get("DATABASE_URL") or "").strip()
if _shell_database_url and database_url_is_template_or_sqlite(_loaded):
    os.environ["DATABASE_URL"] = _shell_database_url

from app.database import SessionLocal
from app.services.lead_gap_audit import select_gap_repair_candidates
from app.services.lead_secondary_pass import run_secondary_pass_batch


def main() -> int:
    parser = argparse.ArgumentParser(description="Lead secondary pass — missing-field rescue batch")
    parser.add_argument("--limit", type=int, default=20, help="Max leads to repair")
    parser.add_argument("--min-score", type=float, default=15.0, help="Minimum intent score")
    parser.add_argument("--audit-only", action="store_true", help="List gaps without running passes")
    parser.add_argument("--no-llm", action="store_true", help="Skip LLM agent QA pass")
    parser.add_argument("--no-apollo", action="store_true", help="Skip Apollo contact lookup")
    parser.add_argument(
        "--no-signal-backfill",
        action="store_true",
        help="Skip Google News signal backfill (much faster for large batches)",
    )
    parser.add_argument(
        "--cooldown-hours",
        type=int,
        default=0,
        help="Hours before re-running a pass (default 0 for manual CLI runs)",
    )
    parser.add_argument("--quiet", action="store_true", help="Suppress progress lines")
    parser.add_argument("--no-rescore", action="store_true", help="Do not queue rescore after batch")
    parser.add_argument(
        "--all-leads",
        action="store_true",
        help="Include headline/junk Unknown rows (default: pipeline sales-lead filter only)",
    )
    parser.add_argument(
        "--require-gap",
        action="append",
        dest="require_gaps",
        metavar="GAP",
        help="Only repair leads with this gap (repeatable, e.g. --require-gap contact)",
    )
    args = parser.parse_args()

    sales_leads_only = not args.all_leads

    db = SessionLocal()
    try:
        if args.audit_only:
            if not args.quiet:
                print(f"── Audit — scanning for gap candidates (limit={args.limit})…", flush=True)
            reports = select_gap_repair_candidates(
                db,
                limit=args.limit,
                min_score=args.min_score,
                require_gaps=args.require_gaps or None,
                progress=not args.quiet,
                sales_leads_only=sales_leads_only,
            )
            print(json.dumps([r.to_dict() for r in reports], indent=2))
            return 0

        stats = run_secondary_pass_batch(
            db,
            limit=args.limit,
            min_score=args.min_score,
            use_llm=not args.no_llm,
            use_apollo=not args.no_apollo,
            signal_backfill=not args.no_signal_backfill,
            rescore=not args.no_rescore,
            cooldown_hours=args.cooldown_hours,
            progress=not args.quiet,
            sales_leads_only=sales_leads_only,
            require_gaps=args.require_gaps or None,
        )
        print(json.dumps(stats, indent=2, default=str))
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
