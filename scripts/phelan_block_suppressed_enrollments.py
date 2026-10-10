"""
Block active follow-up enrollments whose contact address is already suppressed.

Cal's follow-up loop (`process_due_enrollments`) keeps running while the
deliverability circuit breaker has PAUSED intros. Until now it was ungated, so it
re-sent to mailboxes that had already bounced — pinning the trailing 7-day bounce
rate above threshold so the breaker could never auto-recover.

The send path is now gated (a bounced address is skipped and the enrollment is
marked `blocked`), but that only fires lazily when each enrollment next comes due.
This one-off backfill eagerly walks every ACTIVE enrollment and blocks the ones
whose `contact_email` has already bounced/complained/suppressed, so the trailing
window clears on the next cycle instead of after each enrollment drains.

Read-only by default. Re-run with --apply to write.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="Mark suppressed active enrollments as blocked.")
    ap.add_argument("--limit", type=int, default=0, help="Optional cap on enrollments scanned (0 = all).")
    args = ap.parse_args()

    from app.database import SessionLocal
    from app.models.crm import CrmAccount
    from app.models.sequences import OutreachSequenceEnrollment
    from app.services.lead_enrichment import address_previously_bounced

    db = SessionLocal()
    try:
        q = (
            db.query(OutreachSequenceEnrollment)
            .filter(OutreachSequenceEnrollment.status == "active")
            .order_by(OutreachSequenceEnrollment.next_step_at.asc())
        )
        if args.limit:
            q = q.limit(args.limit)
        active = q.all()

        blocked: list[tuple[str, str]] = []
        missing = 0
        acct_cache: dict = {}
        for enr in active:
            acct = acct_cache.get(enr.crm_account_id)
            if acct is None:
                acct = db.query(CrmAccount).filter(CrmAccount.id == enr.crm_account_id).first()
                acct_cache[enr.crm_account_id] = acct
            email = (acct.contact_email or "").strip() if acct else ""
            if not email:
                missing += 1
                continue
            if address_previously_bounced(db, email):
                blocked.append((acct.name or "?", email))
                if args.apply:
                    enr.status = "blocked"
                    enr.paused_reason = "suppressed_bounced"

        print("=" * 60)
        print("SUPPRESSED-ENROLLMENT BACKFILL")
        print("=" * 60)
        print(f"  active enrollments scanned            {len(active)}")
        print(f"  active w/ missing contact_email       {missing}")
        print(f"  BLOCKED (address already suppressed)  {len(blocked)}")
        for name, email in blocked[:40]:
            print(f"      {name[:30]:30} {email}")
        if len(blocked) > 40:
            print(f"      … and {len(blocked) - 40} more")

        if args.apply and blocked:
            db.commit()
            print(f"\nAPPLIED: blocked {len(blocked)} active enrollments on suppressed addresses.")
        elif not args.apply:
            print("\nDry-run — no changes. Re-run with --apply to block them.")
        print("=" * 60)
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
