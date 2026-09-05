#!/usr/bin/env python3
"""Hunter re-enrichment sweep over Cal's existing unsent buyer pool.

Many buyers sit unsent because a guessed role inbox (info@/operations@) was
stamped onto contact_email at draft time — and any stored contact_email
short-circuits the resolve waterfall BEFORE Hunter runs (returns "crm_contact",
untrusted), so the account can never send. This sweep clears the unverified
guess and lets the Hunter-backed waterfall resolve a real, verified named
contact, stamping it only when the send-time trust gate would accept it.

Pairs with the _draft_and_store fix (which stops writing guesses going forward);
this backfills the pool that was already blocked.

Usage
-----
  python3 scripts/cal_hunter_reenrich.py                 # dry-run over unsent buyers
  python3 scripts/cal_hunter_reenrich.py --apply         # stamp verified contacts
  python3 scripts/cal_hunter_reenrich.py --apply --limit 30
  python3 scripts/cal_hunter_reenrich.py --apply --include-sent   # also sweep already-sent (for later bounce retry)
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

import app.models  # noqa: F401
from app.database import SessionLocal


def main() -> int:
    ap = argparse.ArgumentParser(description="Hunter re-enrichment sweep for Cal's buyer pool")
    ap.add_argument("--apply", action="store_true", help="stamp verified contacts (default: dry-run)")
    ap.add_argument("--limit", type=int, default=0, help="only process the first N accounts")
    ap.add_argument("--include-sent", action="store_true", help="also sweep already-sent accounts")
    args = ap.parse_args()

    from app.models.company import Company
    from app.models.crm import CrmAccount
    from app.services.cal_autonomy import resolve_cal_admin_context
    from app.services.hunter_client import hunter_contact_enabled
    from app.services.lead_enrichment import (
        _VERIFIED_EMAIL_SOURCES,
        outreach_recipient_trusted,
        resolve_outreach_email,
    )

    if not hunter_contact_enabled():
        print("Hunter is not enabled (set HUNTER_API_KEY / CONTACT_USE_HUNTER). Aborting.")
        return 1

    db = SessionLocal()
    try:
        ctx = resolve_cal_admin_context(db)
        if not ctx:
            print("No Cal admin context (admin-cal-outreach team).")
            return 1
        _uid, team = ctx
        q = db.query(CrmAccount).filter(
            CrmAccount.team_id == team.id, CrmAccount.account_type == "buyer"
        )
        if not args.include_sent:
            q = q.filter(CrmAccount.outreach_sent_at.is_(None))
        accts = q.order_by(CrmAccount.id).all()
        if args.limit:
            accts = accts[: args.limit]

        mode = "APPLY" if args.apply else "DRY RUN"
        print(f"{mode} — Hunter sweep over {len(accts)} buyer accounts "
              f"({'incl. sent' if args.include_sent else 'unsent only'})\n")

        verified = already = guess = nocontact = 0
        for acct in accts:
            company = db.query(Company).filter(Company.id == acct.company_id).first()
            if not company:
                continue

            meta = dict(company.crm_metadata or {})
            stored_src = (meta.get("outreach_email_source") or "").strip().lower()
            # Already have a verified contact — nothing to do.
            if (acct.contact_email or "").strip() and stored_src in _VERIFIED_EMAIL_SOURCES:
                already += 1
                continue

            if not args.apply:
                # Non-destructive probe: resolve without persisting the cleared guess.
                # Temporarily blank the in-memory guess so the waterfall reaches Hunter.
                acct.contact_email = None
                company.crm_metadata = {k: v for k, v in meta.items()
                                        if k not in ("outreach_email", "outreach_email_source")}

            else:
                acct.contact_email = None
                meta.pop("outreach_email", None)
                meta.pop("outreach_email_source", None)
                company.crm_metadata = meta
                db.flush()

            try:
                email, source, _title = resolve_outreach_email(company, acct, use_apollo=False)
            except Exception as exc:
                print(f"  ERROR {company.name}: {str(exc)[:80]}")
                db.rollback()
                continue

            if not email:
                nocontact += 1
                if args.apply:
                    db.commit()
                else:
                    db.rollback()
                continue

            trusted, why = outreach_recipient_trusted(company, acct, email, source)
            if trusted:
                verified += 1
                print(f"  {company.name}: {email}  (verified via {source})")
                if args.apply:
                    acct.contact_email = email
                    db.commit()
                else:
                    db.rollback()
            else:
                guess += 1
                if args.apply:
                    acct.contact_email = None
                    m2 = dict(company.crm_metadata or {})
                    m2.pop("outreach_email", None)
                    m2.pop("outreach_email_source", None)
                    company.crm_metadata = m2
                    db.commit()
                else:
                    db.rollback()

        print(
            f"\n{'Stamped' if args.apply else 'Would stamp'} {verified} verified contacts. "
            f"already-verified={already}, only-a-guess={guess}, no-contact={nocontact}."
        )
        if not args.apply and verified:
            print("Re-run with --apply to persist verified contacts.")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
