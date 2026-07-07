"""
Controlled proof-of-deliverability: send Cal outreach to a curated set of buyers
by name, reusing the REAL send primitives (resolve -> trust gate -> deliverability
-> send_cal_intro_email -> follow-up enroll). Bypasses the cycle's top-100 window
so we can validate the hardened verified-only path on hand-picked clean companies.

Read-only unless --apply.
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--names", required=True, help="Comma-separated name substrings.")
    ap.add_argument("--apply", action="store_true", help="Actually send.")
    args = ap.parse_args()

    from app.database import SessionLocal
    from app.models.company import Company
    from app.models.crm import CrmAccount
    from app.services.cal_autonomy import _cal_buyer_eligible, resolve_cal_admin_context
    from app.services.cal_draft_guard import is_complete_cal_draft
    from app.services.cal_outreach_send import (
        enroll_cal_followup,
        parse_cal_draft,
        send_cal_intro_email,
    )
    from app.services.lead_enrichment import (
        outreach_recipient_trusted,
        resolve_outreach_email,
        verify_email_deliverable,
    )

    names = [n.strip().lower() for n in args.names.split(",") if n.strip()]
    db = SessionLocal()
    rows = []
    try:
        ctx = resolve_cal_admin_context(db)
        if not ctx:
            print("No cal admin context — cannot send.")
            return 1
        uid, team = ctx
        now = datetime.now(timezone.utc)

        candidates = (
            db.query(Company)
            .filter(Company.is_internal.is_(True))
            .all()
        )
        for company in candidates:
            nm = (company.name or "").lower()
            if not any(n in nm for n in names):
                continue
            acct = (
                db.query(CrmAccount)
                .filter(CrmAccount.company_id == company.id, CrmAccount.team_id == team.id)
                .first()
            )
            if not acct:
                rows.append((company.name, "no-acct", "-", "skip"))
                continue
            if acct.outreach_sent_at:
                rows.append((company.name, "already-sent", "-", "skip"))
                continue
            elig, r = _cal_buyer_eligible(company, acct)
            if not elig:
                rows.append((company.name, f"ineligible:{r}", "-", "skip"))
                continue
            to_email, source, _t = resolve_outreach_email(company, acct, use_apollo=True)
            if not to_email:
                rows.append((company.name, "no-email", "-", "skip"))
                continue
            trusted, treason = outreach_recipient_trusted(company, acct, to_email, source)
            if not trusted:
                rows.append((company.name, f"untrusted:{treason}", to_email, "skip"))
                continue
            okv, vreason = verify_email_deliverable(to_email)
            if not okv:
                rows.append((company.name, f"undeliverable:{vreason}", to_email, "skip"))
                continue
            if not acct.outreach_draft or not is_complete_cal_draft(acct.outreach_draft)[0]:
                rows.append((company.name, "no/incomplete-draft", to_email, "skip"))
                continue
            subject, body = parse_cal_draft(acct.outreach_draft, company.name or "your team")
            if not args.apply:
                rows.append((company.name, source, to_email, "WOULD-SEND"))
                continue
            try:
                send_cal_intro_email(
                    db,
                    acct=acct,
                    company=company,
                    team_id=team.id,
                    to_email=to_email,
                    subject=subject,
                    body_text=body,
                    sender_user_id=uid,
                    idempotency_key=f"cal-curated-{acct.id}-{now.date().isoformat()}",
                    send_identity="cal",
                )
                enroll_cal_followup(db, team_id=team.id, crm_account_id=acct.id)
                rows.append((company.name, source, to_email, "SENT"))
            except Exception as exc:  # noqa: BLE001
                rows.append((company.name, f"error:{type(exc).__name__}", to_email, str(exc)[:60]))

        if args.apply:
            db.commit()

        print("=" * 72)
        print(f"CAL CURATED SEND — {'APPLIED' if args.apply else 'DRY-RUN'}")
        print("=" * 72)
        for name, source, email, verdict in rows:
            print(f"  [{verdict:10}] {name[:26]:26} {source:20} {email}")
        print("=" * 72)
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
