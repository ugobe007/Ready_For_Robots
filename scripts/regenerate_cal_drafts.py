"""
Flush stale Cal outreach drafts and re-render them in the current Cal voice.

Regenerates `CrmAccount.outreach_draft` for every account that still holds a
draft, using the same voice functions the admin "Regenerate drafts" button uses.
Buyer vs vendor voice is chosen from the account's own `account_type`.

Run on Fly (has prod DATABASE_URL + REDIS_URL):
    fly ssh console -a ready-2-robot -C "python scripts/regenerate_cal_drafts.py --pause-autopilot"

Flags:
    --pause-autopilot   Set the Redis runtime override OFF first (pauses the
                        worker's draft/send/follow-up loop until re-enabled).
    --include-sent      Also rewrite drafts on already-sent accounts (default: skip).
    --limit N           Cap the number rewritten (0 = all).
    --dry-run           Report counts without writing.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main() -> int:
    ap = argparse.ArgumentParser(description="Regenerate Cal outreach drafts in the current voice.")
    ap.add_argument("--pause-autopilot", action="store_true", help="Disable Cal autonomy runtime override first")
    ap.add_argument("--include-sent", action="store_true", help="Also rewrite already-sent drafts")
    ap.add_argument("--limit", type=int, default=0, help="Max drafts to rewrite (0 = all)")
    ap.add_argument("--dry-run", action="store_true", help="Report counts without writing")
    ap.add_argument(
        "--purge-junk",
        action="store_true",
        help="Clear unsent drafts on accounts whose name is junk (never send) instead of re-voicing",
    )
    args = ap.parse_args()

    if args.purge_junk:
        return _purge_junk_drafts(dry_run=args.dry_run, pause_autopilot=args.pause_autopilot)

    from app.database import SessionLocal
    from app.models.company import Company
    from app.models.crm import CrmAccount
    from app.services.cal_autonomy import (
        cal_buyer_outreach_body,
        cal_vendor_outreach_body,
        format_cal_draft_storage,
        set_cal_autonomy_runtime_override,
    )
    from app.api.crm import _draft_subject

    if args.pause_autopilot and not args.dry_run:
        ok = set_cal_autonomy_runtime_override(False)
        print(f"[pause] autopilot runtime override set to OFF: {'ok' if ok else 'FAILED (no redis?)'}")

    db = SessionLocal()
    regenerated = skipped_no_company = errors = 0
    try:
        q = db.query(CrmAccount).filter(CrmAccount.outreach_draft.isnot(None))
        if not args.include_sent:
            q = q.filter(CrmAccount.outreach_sent_at.is_(None))
        accounts = q.all()
        print(f"[scan] {len(accounts)} draft(s) to regenerate (include_sent={args.include_sent})")

        for acct in accounts:
            if args.limit and regenerated >= args.limit:
                break
            company = (
                db.query(Company).filter(Company.id == acct.company_id).first()
                if acct.company_id
                else None
            )
            if company is None:
                skipped_no_company += 1
                continue
            try:
                acct_type = (getattr(acct, "account_type", None) or "buyer").lower()
                if acct_type == "vendor":
                    body = cal_vendor_outreach_body(company, fresh=True)
                else:
                    body = cal_buyer_outreach_body(company, fresh=True)
                subject = _draft_subject(acct)
                new_draft = format_cal_draft_storage(subject, body)
                if not args.dry_run:
                    acct.outreach_draft = new_draft
                regenerated += 1
                if not args.dry_run and regenerated % 50 == 0:
                    db.commit()
                    print(f"[commit] {regenerated} regenerated so far…")
            except Exception as exc:  # noqa: BLE001 — keep going, report at end
                errors += 1
                print(f"[error] account={acct.id} company={getattr(company, 'name', '?')}: {exc}")

        if not args.dry_run:
            db.commit()
        print(
            f"[done] regenerated={regenerated} skipped_no_company={skipped_no_company} "
            f"errors={errors} dry_run={args.dry_run}"
        )
    finally:
        db.close()
    return 0


def _purge_junk_drafts(*, dry_run: bool, pause_autopilot: bool) -> int:
    """Clear unsent drafts whose account name is junk so Cal never emails them."""
    from app.database import SessionLocal
    from app.models.crm import CrmAccount
    from app.services.lead_filter import is_junk

    if pause_autopilot and not dry_run:
        from app.services.cal_autonomy import set_cal_autonomy_runtime_override

        ok = set_cal_autonomy_runtime_override(False)
        print(f"[pause] autopilot runtime override set to OFF: {'ok' if ok else 'FAILED (no redis?)'}")

    db = SessionLocal()
    purged = kept = 0
    try:
        accounts = (
            db.query(CrmAccount)
            .filter(CrmAccount.outreach_draft.isnot(None), CrmAccount.outreach_sent_at.is_(None))
            .all()
        )
        print(f"[scan] {len(accounts)} unsent draft(s) to screen for junk names")
        for acct in accounts:
            name = (acct.name or "").strip()
            mode = "oem_prospect" if (getattr(acct, "account_type", None) or "") == "vendor" else "buyer"
            junk, reason = is_junk(name, mode=mode)
            if not junk:
                kept += 1
                continue
            print(f"[purge] {acct.account_type or '?':<6} {name[:44]!r} — {reason}")
            if not dry_run:
                acct.outreach_draft = None
                acct.outreach_stage = "suppressed_junk"
            purged += 1
        if not dry_run:
            db.commit()
        print(f"[done] purged={purged} kept={kept} dry_run={dry_run}")
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
