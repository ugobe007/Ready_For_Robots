#!/usr/bin/env python3
"""
Export per-company quality decisions as JSONL for offline ML / rule mining.

Each line is one JSON object with outputs from the current stack:
  junk filter (is_junk), logic engine (is_valid_lead), text_classifier (classify).

Typical workflow (see docs/lead_quality_pipeline.md):
  1. Run scrapers / ingest.
  2. Export logs → label corrections in a spreadsheet or notebook.
  3. Propose new substrings/patterns in lead_filter.py or ontology tweaks.
  4. Re-run tests + bounded scraper smoke.

  python3 scripts/export_quality_decision_log.py --output data/quality_log.jsonl
  python3 scripts/export_quality_decision_log.py --limit 2000 --since-id 5700

Progress / line counts go to stderr; JSONL goes only to -o or stdout.

Viewing JSONL (one JSON object per line — ``python -m json.tool`` expects a single value):

  python3 -c "import json, pathlib; p=pathlib.Path('data/quality_log.jsonl'); [print(json.dumps(json.loads(l), indent=2), chr(10)+'---'+chr(10)) for l in p.read_text().splitlines()[:5]]"

  With jq:  head -5 data/quality_log.jsonl | jq .

  In Cursor: open the ``.jsonl`` file in the editor (no ``open`` in Terminal required).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

_root = Path(__file__).resolve().parents[1]
load_dotenv(_root / "frontend" / "nextjs" / ".env.local")
load_dotenv(_root / ".env", override=True)

from app.database import SessionLocal
from app.models.company import Company
from app.services.quality_decision_log import (
    assert_decision_record_schema,
    build_decision_record,
    export_timestamp_iso,
)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", "-o", type=Path, help="JSONL file path (stdout if omitted)")
    ap.add_argument("--limit", type=int, default=None, help="Max rows (default: all)")
    ap.add_argument("--since-id", type=int, default=None, help="Only companies.id >= this")
    ap.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print each id to stderr as written (for large exports)",
    )
    args = ap.parse_args()

    out = open(args.output, "w", encoding="utf-8") if args.output else sys.stdout
    db = SessionLocal()
    n = 0
    try:
        q = db.query(Company).order_by(Company.id.desc())
        if args.since_id is not None:
            q = q.filter(Company.id >= args.since_id)
        if args.limit is not None:
            q = q.limit(args.limit)
        rows = q.all()
        export_ts = export_timestamp_iso()
        for c in rows:
            rec = build_decision_record(
                company_id=c.id,
                name=c.name or "",
                source=c.source,
                created_at=c.created_at,
                export_ts=export_ts,
            )
            assert_decision_record_schema(rec)
            out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            n += 1
            if args.verbose:
                print(f"wrote id={c.id}", file=sys.stderr)
    finally:
        db.close()
        if args.output:
            out.close()

    dest = str(args.output) if args.output else "(stdout)"
    print(f"quality_decision_log: wrote {n} JSONL line(s) → {dest}", file=sys.stderr)


if __name__ == "__main__":
    main()
