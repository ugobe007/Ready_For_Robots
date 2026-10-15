"""Import Bob's seed list into rfr_ tables (buyer_opportunity_spec Phase 1).

Dry run by default: everything runs in one transaction that is rolled back.
--apply commits. The database URL must be passed explicitly; DATABASE_URL is
never read, so the script cannot reach production by accident.

Usage:
    python3 scripts/rfr_import_seed.py --database-url postgresql://… [--csv data/seed/rfr_seed_accounts.csv] [--apply]
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

from app.services.buyer_opportunity.seed_import import import_seed  # noqa: E402

DEFAULT_CSV = ROOT / "data" / "seed" / "rfr_seed_accounts.csv"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--csv", default=str(DEFAULT_CSV))
    parser.add_argument("--apply", action="store_true", help="commit (default: roll back)")
    args = parser.parse_args(argv)

    engine = sa.create_engine(args.database_url)
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            result = import_seed(conn, args.csv)
        except Exception:
            trans.rollback()
            raise
        if args.apply:
            trans.commit()
        else:
            trans.rollback()
    print(json.dumps({"applied": args.apply, "writes": result.writes, **result.as_dict()}, indent=2))
    return 1 if result.rejected else 0


if __name__ == "__main__":
    raise SystemExit(main())
