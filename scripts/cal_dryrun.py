"""Preview one Cal autonomy cycle without sending (dry-run). Read-only."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main() -> int:
    from app.database import SessionLocal
    from app.services.cal_autonomy import run_cal_autonomy_cycle

    import json

    db = SessionLocal()
    try:
        r = run_cal_autonomy_cycle(db, dry_run=True)
        print("=" * 54)
        print("CAL DRY-RUN CYCLE PREVIEW")
        print("=" * 54)
        print("  RAW:", json.dumps({k: v for k, v in r.items() if k != "errors"}, default=str)[:500])
        for k in (
            "drafted", "refreshed", "sent",
            "skipped_ineligible", "skipped_no_draft",
            "skipped_already_sent", "skipped_unverified",
        ):
            print(f"  {k:22} {r.get(k)}")
        errs = r.get("errors") or []
        if errs:
            print(f"\n  sample skips/errors ({len(errs)} shown):")
            for e in errs[:10]:
                print(f"    {str(e.get('name'))[:30]:30}  {e.get('error')}")
        print("=" * 54)
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
