"""Dry-run backfill report: companies → rfr_buyers industries (buyer_opportunity_spec Phase 1).

Reads `companies` and `signals` in a read-only transaction and writes nothing
to the database. The database URL must be passed explicitly; DATABASE_URL is
never read. Output goes to files (default under reports/, which is not committed).

Usage:
    python3 scripts/rfr_backfill_report.py --database-url postgresql://… [--out reports/rfr_backfill_report]
        [--company-checks reports/rfr_industry_company_check.json]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import sqlalchemy as sa

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.buyer_opportunity.backfill_report import build_backfill_report, render_markdown  # noqa: E402
from app.services.buyer_opportunity.industry_company_check import decisions_by_company  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--out", default=str(ROOT / "reports" / "rfr_backfill_report"),
                        help="path prefix; writes <out>.json and <out>.md")
    parser.add_argument("--company-checks", help="JSON from rfr_industry_company_check.py")
    args = parser.parse_args(argv)
    checks = decisions_by_company(json.loads(Path(args.company_checks).read_text())) if args.company_checks else None

    engine = sa.create_engine(args.database_url)
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            report = build_backfill_report(conn, company_checks=checks)
        finally:
            trans.rollback()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.with_suffix(".json").write_text(json.dumps(report, indent=2) + "\n")
    out.with_suffix(".md").write_text(render_markdown(report))
    print(render_markdown(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
