"""
Run ONE supervised live Cal cycle and report exactly what it drafted/sent,
then show the real recipients + delivery status so we can confirm no sends to
bad/guessed domains. Honors CAL_AUTONOMY_SEND_LIMIT (set low for first run).
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main() -> int:
    from app.database import SessionLocal
    from app.models.outreach import OutreachMessage
    from app.services.cal_autonomy import run_cal_autonomy_cycle

    started = datetime.now(timezone.utc)
    db = SessionLocal()
    try:
        r = run_cal_autonomy_cycle(db, dry_run=False)
        print("=" * 60)
        print("CAL LIVE CYCLE RESULT")
        print("=" * 60)
        print(f"  status               {r.get('status')}")
        for k in ("drafted", "refreshed", "sent",
                  "skipped_ineligible", "skipped_unverified",
                  "skipped_no_draft", "skipped_already_sent"):
            print(f"  {k:20} {r.get(k)}")

        errs = r.get("errors") or []
        if errs:
            print(f"\n  skip/error reasons ({min(len(errs),10)} of {len(errs)}):")
            for e in errs[:10]:
                print(f"    {str(e.get('name'))[:28]:28}  {e.get('error')}")

        window = started - timedelta(minutes=5)
        recent = (
            db.query(OutreachMessage)
            .filter(OutreachMessage.created_at >= window)
            .order_by(OutreachMessage.created_at.desc())
            .limit(30)
            .all()
        )
        print(f"\n  RECIPIENTS THIS CYCLE ({len(recent)}):")
        for m in recent:
            dom = (m.to_email or "").split("@")[-1]
            print(f"    {m.status:10} {dom:26} {m.to_email}")
        print("=" * 60)
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
