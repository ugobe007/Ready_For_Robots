"""
Estimate Hunter live hit-rate: for a small sample of eligible buyers WITHOUT a
verified stored contact, run the resolve_outreach_email waterfall and bucket the
resulting source + whether it would pass a verified-source-only gate.

Makes real Hunter API calls (one per sampled company). Keep --limit small.
Read-only: does not commit.
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

_VERIFIED = {"apollo", "hunter", "hunter_domain", "website_mailto", "signal_email"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=12)
    ap.add_argument("--apollo", action="store_true", help="Also try Apollo (costs credits).")
    args = ap.parse_args()

    from app.api.admin_extended import _hot_warm_companies
    from app.database import SessionLocal
    from app.services.cal_autonomy import _cal_buyer_eligible
    from app.services.lead_enrichment import resolve_outreach_email

    db = SessionLocal()
    try:
        pool = _hot_warm_companies(db, 300)
        sampled = 0
        src_mix: Counter = Counter()
        verified = 0
        rows = []
        for company, _s, _t in pool:
            if sampled >= args.limit:
                break
            ok, _r = _cal_buyer_eligible(company)
            if not ok:
                continue
            meta = company.crm_metadata or {}
            if (meta.get("outreach_email_source") or "").strip().lower() in _VERIFIED:
                continue  # already verified; we want the "needs enrich" set
            sampled += 1
            try:
                email, source, _title = resolve_outreach_email(
                    company, None, use_apollo=bool(args.apollo)
                )
            except Exception as exc:  # noqa: BLE001
                email, source = None, f"error:{type(exc).__name__}"
            src_mix[source] += 1
            is_v = source in _VERIFIED
            if is_v:
                verified += 1
            rows.append((company.name, source, email or "-", "OK" if is_v else "block"))

        print("=" * 64)
        print(f"HUNTER LIVE HIT-RATE SAMPLE — {sampled} eligible buyers (apollo={args.apollo})")
        print("=" * 64)
        for name, source, email, verdict in rows:
            print(f"  [{verdict:5}] {name[:26]:26} {source:16} {email}")
        print("-" * 64)
        print(f"  verified (would send): {verified}/{sampled}"
              f"  ({(100*verified//sampled) if sampled else 0}%)")
        print("  source mix:")
        for s, n in src_mix.most_common():
            print(f"    {n:>3}  {s}")
        print("=" * 64)
    finally:
        db.rollback()
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
