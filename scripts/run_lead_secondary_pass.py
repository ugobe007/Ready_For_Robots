#!/usr/bin/env python3
"""Run the gap-driven secondary rescue batch (manual / CI smoke)."""
from __future__ import annotations

import argparse
import json
import sys

from app.database import SessionLocal
from app.services.lead_gap_audit import select_gap_repair_candidates
from app.services.lead_secondary_pass import run_secondary_pass_batch


def main() -> int:
    parser = argparse.ArgumentParser(description="Lead secondary pass — missing-field rescue batch")
    parser.add_argument("--limit", type=int, default=20, help="Max leads to repair")
    parser.add_argument("--min-score", type=float, default=15.0, help="Minimum intent score")
    parser.add_argument("--audit-only", action="store_true", help="List gaps without running passes")
    parser.add_argument("--no-llm", action="store_true", help="Skip LLM agent QA pass")
    parser.add_argument("--no-rescore", action="store_true", help="Do not queue rescore after batch")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        if args.audit_only:
            reports = select_gap_repair_candidates(
                db, limit=args.limit, min_score=args.min_score
            )
            print(json.dumps([r.to_dict() for r in reports], indent=2))
            return 0

        stats = run_secondary_pass_batch(
            db,
            limit=args.limit,
            min_score=args.min_score,
            use_llm=not args.no_llm,
            rescore=not args.no_rescore,
        )
        print(json.dumps(stats, indent=2, default=str))
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
