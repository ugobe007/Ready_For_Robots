"""
Re-ground buyer `automation_requirements` in crm_metadata.

Historically, when the signal-text regex found no concrete requirement, an inferred
robot-fit *menu* (e.g. "humanoid robots", "mobile manipulators", "baggage handling robots")
was stored as `automation_requirements`. Those guesses then leaked into vendor matching and
produced off-domain matches (an airline trialing humanoids matching an AMR vendor).

This pass recomputes `automation_requirements` strictly from the signal text and moves any
non-grounded leftovers into `inferred_robot_fit` (display only, never matched on).

Run on Fly (has prod DATABASE_URL):
    fly ssh console -a ready-2-robot -C "sh -c 'cd /code && python scripts/reground_automation_requirements.py'"

Flags:
    --dry-run     Report changes without writing.
    --limit N     Cap rows processed (0 = all).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main() -> int:
    ap = argparse.ArgumentParser(description="Re-ground automation_requirements from signal text.")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    from sqlalchemy.orm import joinedload
    from sqlalchemy.orm.attributes import flag_modified

    from app.database import SessionLocal
    from app.models.company import Company
    from app.services.crm_extractor import _extract_automation_requirements

    regrounded = cleared = unchanged = 0
    printed = 0

    # Lightweight pass: collect only the IDs to process (companies with stored
    # automation_requirements). Keeps memory flat on small machines.
    id_db = SessionLocal()
    try:
        candidate_ids = [row[0] for row in id_db.query(Company.id).filter(Company.crm_metadata.isnot(None)).all()]
    finally:
        id_db.close()
    print(f"[scan] {len(candidate_ids)} companies with crm_metadata")

    chunk = 150
    for start in range(0, len(candidate_ids), chunk):
        if args.limit and (regrounded + cleared) >= args.limit:
            break
        batch_ids = candidate_ids[start : start + chunk]
        db = SessionLocal()
        try:
            companies = (
                db.query(Company)
                .options(joinedload(Company.signals))
                .filter(Company.id.in_(batch_ids))
                .all()
            )
            for company in companies:
                if args.limit and (regrounded + cleared) >= args.limit:
                    break
                meta = company.crm_metadata
                if not isinstance(meta, dict):
                    continue
                old = meta.get("automation_requirements")
                if not isinstance(old, list) or not old:
                    continue

                signal_texts = [
                    (s.signal_text or "", s.source_url or "")
                    for s in (company.signals or [])
                    if s.signal_text
                ]
                grounded = _extract_automation_requirements(signal_texts)
                moved = [x for x in old if x not in grounded]

                if grounded == old and not moved:
                    unchanged += 1
                    continue

                existing_inferred = meta.get("inferred_robot_fit") or []
                if not isinstance(existing_inferred, list):
                    existing_inferred = []
                new_inferred = list(dict.fromkeys(list(existing_inferred) + moved))

                if not args.dry_run:
                    meta["automation_requirements"] = grounded
                    meta["inferred_robot_fit"] = new_inferred
                    flag_modified(company, "crm_metadata")

                if grounded:
                    regrounded += 1
                else:
                    cleared += 1
                if printed < 25:
                    printed += 1
                    print(f"[reground] {company.name[:34]!r}: {old} -> grounded={grounded} inferred+={moved}")

            if not args.dry_run:
                db.commit()
                print(f"[commit] processed through {start + len(batch_ids)} / {len(candidate_ids)}")
        finally:
            db.close()

    print(
        f"[done] regrounded={regrounded} cleared_to_inferred={cleared} "
        f"unchanged={unchanged} dry_run={args.dry_run}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
