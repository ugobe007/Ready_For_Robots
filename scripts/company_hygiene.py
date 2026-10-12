#!/usr/bin/env python3
"""Report duplicate companies and junk company names. Never deletes anything.

    python3 scripts/company_hygiene.py                 # counts + samples + two CSVs in reports/
    python3 scripts/company_hygiene.py --apply         # also tag rows in companies.crm_metadata

Outputs
  reports/duplicate_companies.csv  one row per company row, grouped (Target / Target Corp / …)
  reports/junk_company_names.csv   headline fragments, place names, encoded strings

--apply writes crm_metadata.identity = {group_id, primary_company_id, is_primary}
and crm_metadata.junk_name = "<reason>" so UIs and exports can hide them. Buyer
ranking already pools duplicates and ignores junk names without this flag.
"""
from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--out", default="reports")
    args = ap.parse_args()

    from sqlalchemy import func

    from app.database import SessionLocal
    from app.models.company import Company
    from app.models.signal import Signal
    from app.services.company_identity import canonical_company_key, group_companies, junk_name_reason

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    db = SessionLocal()
    try:
        sig_counts = dict(db.query(Signal.company_id, func.count(Signal.id)).group_by(Signal.company_id).all())
        rows = db.query(Company.id, Company.name, Company.website_domain, Company.website).all()
        groups = group_companies((r.id, r.name or "", r.website_domain) for r in rows)
        by_root: dict[int, list] = defaultdict(list)
        for r in rows:
            by_root[groups.get(r.id, r.id)].append(r)
        dupes = {root: rs for root, rs in by_root.items() if len(rs) > 1}

        def primary(rs):
            return sorted(rs, key=lambda r: (-sig_counts.get(r.id, 0), 0 if r.website else 1, len(r.name or ""), r.id))[0]

        with open(out / "duplicate_companies.csv", "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["group_id", "company_id", "name", "is_primary", "signals", "website_domain", "match_key"])
            for root, rs in sorted(dupes.items(), key=lambda kv: -sum(sig_counts.get(r.id, 0) for r in kv[1])):
                p = primary(rs)
                for r in sorted(rs, key=lambda r: r.id != p.id):
                    w.writerow([root, r.id, r.name, "yes" if r.id == p.id else "", sig_counts.get(r.id, 0),
                                r.website_domain or "", canonical_company_key(r.name)])

        junk = [(r, junk_name_reason(r.name)) for r in rows]
        junk = [(r, why) for r, why in junk if why]
        with open(out / "junk_company_names.csv", "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["company_id", "name", "reason", "signals"])
            for r, why in sorted(junk, key=lambda x: -sig_counts.get(x[0].id, 0)):
                w.writerow([r.id, r.name, why, sig_counts.get(r.id, 0)])

        if args.apply:
            junk_ids = {r.id: why for r, why in junk}
            primary_of = {root: primary(rs).id for root, rs in dupes.items()}
            touched = set(junk_ids) | {r.id for rs in dupes.values() for r in rs}
            for i, c in enumerate(db.query(Company).filter(Company.id.in_(touched)).yield_per(1000), 1):
                meta = dict(c.crm_metadata or {})
                if c.id in junk_ids:
                    meta["junk_name"] = junk_ids[c.id]
                root = groups.get(c.id, c.id)
                if root in dupes:
                    meta["identity"] = {"group_id": root, "primary_company_id": primary_of[root],
                                        "is_primary": c.id == primary_of[root]}
                c.crm_metadata = meta
                if i % 1000 == 0:
                    db.commit()
            db.commit()

        dup_rows = sum(len(rs) for rs in dupes.values())
        print(f"companies:                 {len(rows):>8,}")
        print(f"duplicate groups:          {len(dupes):>8,}  ({dup_rows:,} rows → {len(dupes):,} companies)")
        print(f"junk names:                {len(junk):>8,}")
        print("\nlargest duplicate groups:")
        for root, rs in sorted(dupes.items(), key=lambda kv: -sum(sig_counts.get(r.id, 0) for r in kv[1]))[:15]:
            names = " | ".join(sorted({r.name for r in rs}))[:110]
            print(f"  {sum(sig_counts.get(r.id, 0) for r in rs):>6,} signals  {names}")
        print("\njunk names with the most signals:")
        for r, why in sorted(junk, key=lambda x: -sig_counts.get(x[0].id, 0))[:15]:
            print(f"  {sig_counts.get(r.id, 0):>6,}  {(r.name or '')[:60]:60} {why}")
        print(f"\nCSVs: {out / 'duplicate_companies.csv'}, {out / 'junk_company_names.csv'}")
        print("tagged in crm_metadata." if args.apply else "DRY RUN — nothing written. --apply tags rows (never deletes).")
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
