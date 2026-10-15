"""Check needs_company_check companies against their own websites (buyer_opportunity_spec Phase 1).

Lists companies whose industry maps to a needs_company_check = yes synonym row
(read-only transaction), then reads each company's website and picks industries
from that row's candidates, each with a quote validated against the page text.
Writes nothing to the database. The database URL must be passed explicitly;
DATABASE_URL is never read. Output goes to files (default under reports/, which
is not committed); feed the JSON to rfr_backfill_report.py --company-checks.

Usage:
    python3 scripts/rfr_industry_company_check.py --database-url postgresql://… [--limit 20] [--workers 4]
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import sqlalchemy as sa

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.buyer_opportunity import industry_company_check as icc  # noqa: E402
from app.services.robot_understanding_v1.taxonomy_extraction import load_taxonomy  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--out", default=str(ROOT / "reports" / "rfr_industry_company_check"),
                        help="path prefix; writes <out>.json and <out>.md")
    parser.add_argument("--limit", type=int, default=0, help="check at most N companies (0 = all)")
    parser.add_argument("--raw-value", action="append", default=[],
                        help="only companies with this source_value (repeatable)")
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args(argv)

    engine = sa.create_engine(args.database_url)
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            companies = icc.companies_to_check(conn)
        finally:
            trans.rollback()
    engine.dispose()

    wanted = {v.strip().lower() for v in args.raw_value}
    if wanted:
        companies = [c for c in companies if c.raw_value.lower() in wanted]
    if args.limit:
        companies = companies[: args.limit]

    from app.services.robot_understanding_v1.fetch import fetch_page

    taxonomy = load_taxonomy()
    decisions = icc.run_checks(
        companies, fetch=fetch_page, choose=icc.anthropic_chooser(), taxonomy=taxonomy, workers=args.workers,
    )
    payload = {
        "writes": 0,
        "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "taxonomy_version": taxonomy.get("version"),
        "model": icc.CHECK_MODEL,
        "decisions": [d.as_dict() for d in decisions],
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.with_suffix(".json").write_text(json.dumps(payload, indent=2) + "\n")
    md = icc.render_review_markdown(payload)
    out.with_suffix(".md").write_text(md)
    print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
