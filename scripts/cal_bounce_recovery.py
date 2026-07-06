"""
Unlock real buyer supply locked behind bounce-era sends.

During the guessed-domain era, Cal emailed real buyers (hotels, airlines, casinos)
at fabricated domains -> bounces. Those accounts now carry outreach_sent_at, so Cal
will not re-contact them at the corrected real domain. This script finds accounts
whose ONLY outcome was a bounce/complaint AT A DOMAIN THAT DIFFERS from the company's
real website domain (i.e. a fixable guessed-domain failure), and (with --apply) clears
outreach_sent_at so Cal re-contacts them properly through the recipient-trust gate.

Read-only by default.
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

_LANDED = {"delivered", "opened", "clicked", "replied", "resent"}
_FAILED = {"bounced", "complained", "suppressed", "failed"}


def _dom(email: str | None) -> str:
    return (email or "").split("@")[-1].lower().strip()


_VERIFIED = {"apollo", "hunter", "hunter_domain", "website_mailto", "signal_email"}


def _verified_retry(db, limit: int, apply: bool) -> int:
    """Controlled ramp: reset never-landed eligible accounts that resolve to a
    VERIFIED contact today, so Cal re-contacts them via the hardened gate. Only
    accounts with a verified email are reset (they will actually send, not re-skip)."""
    from app.models.company import Company
    from app.models.crm import CrmAccount
    from app.models.outreach import OutreachMessage
    from app.api.admin_extended import _cal_draft_for_company
    from app.services.cal_autonomy import _cal_buyer_eligible, format_cal_draft_storage
    from app.services.lead_enrichment import resolve_outreach_email

    msgs = db.query(OutreachMessage).all()
    by_acct: dict = {}
    for m in msgs:
        by_acct.setdefault(m.crm_account_id, []).append(m)

    # Candidate accounts: never landed, only failed outcomes.
    candidates: list[int] = []
    for acct_id, ms in by_acct.items():
        outcomes = {(m.status or "").lower() for m in ms}
        if outcomes & _LANDED or not (outcomes & _FAILED):
            continue
        candidates.append(acct_id)

    chosen = []
    scanned = 0
    scan_cap = max(limit * 4, 40)
    for acct_id in candidates:
        if len(chosen) >= limit or scanned >= scan_cap:
            break
        acct = db.query(CrmAccount).filter(CrmAccount.id == acct_id).first()
        if not acct or not acct.company_id:
            continue
        company = db.query(Company).filter(Company.id == acct.company_id).first()
        if not company or not _cal_buyer_eligible(company, acct)[0]:
            continue
        scanned += 1
        # Resolve FRESH (acct=None) so a stale bounce-era guessed contact_email does
        # not short-circuit the waterfall; resolve persists verified hits to company.
        email, source, _t = resolve_outreach_email(company, None, use_apollo=False)
        if source not in _VERIFIED or not email:
            continue
        chosen.append((company, acct, email, source))

    print("\n" + "=" * 60)
    print(f"VERIFIED-RETRY RAMP — scanned {scanned}, verified {len(chosen)} (limit {limit})")
    print("=" * 60)
    for company, _acct, email, source in chosen:
        print(f"  {company.name[:30]:30} {source:14} {email}")

    if apply and chosen:
        for company, acct, email, _source in chosen:
            acct.contact_email = email  # replace stale bounce-era guess with verified
            acct.outreach_sent_at = None
            if acct.outreach_stage == "suppressed_junk":
                acct.outreach_stage = None
            if not acct.outreach_draft:
                sub, body = _cal_draft_for_company(company, fresh=True)
                acct.outreach_draft = format_cal_draft_storage(sub, body)
        db.commit()
        print(f"\nAPPLIED: reset {len(chosen)} verified accounts for re-contact.")
    elif not apply:
        print("\nDry-run — no changes. Re-run with --apply --verified-retry to unlock.")
    print("=" * 60)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="Clear outreach_sent_at for recoverable accounts.")
    ap.add_argument("--verified-retry", action="store_true",
                    help="Controlled ramp: reset never-landed accounts that resolve to a verified contact.")
    ap.add_argument("--limit", type=int, default=20, help="Max accounts to reset in verified-retry mode.")
    args = ap.parse_args()

    from app.database import SessionLocal
    from app.models.company import Company
    from app.models.crm import CrmAccount
    from app.models.outreach import OutreachMessage
    from app.services.cal_autonomy import _cal_buyer_eligible
    from app.services.lead_enrichment import company_website_domain

    db = SessionLocal()
    try:
        if args.verified_retry:
            return _verified_retry(db, args.limit, args.apply)
        status_mix = Counter(s for (s,) in db.query(OutreachMessage.status).all())
        print("=" * 60)
        print("OUTREACH STATUS DISTRIBUTION")
        print("=" * 60)
        for s, n in status_mix.most_common():
            print(f"  {n:>5}  {s}")

        # Group messages by account
        msgs = db.query(OutreachMessage).all()
        by_acct: dict = {}
        for m in msgs:
            by_acct.setdefault(m.crm_account_id, []).append(m)

        recoverable = []
        landed_ok = bounced_real_domain = ineligible_now = 0
        for acct_id, ms in by_acct.items():
            outcomes = {(m.status or "").lower() for m in ms}
            if outcomes & _LANDED:
                landed_ok += 1
                continue
            if not (outcomes & _FAILED):
                continue  # still pending, leave alone
            acct = db.query(CrmAccount).filter(CrmAccount.id == acct_id).first()
            if not acct or not acct.company_id:
                continue
            company = db.query(Company).filter(Company.id == acct.company_id).first()
            if not company:
                continue
            ok, _r = _cal_buyer_eligible(company, acct)
            if not ok:
                ineligible_now += 1
                continue
            real = (company_website_domain(company, acct) or "").lower()
            bounced_domains = {_dom(m.to_email) for m in ms if (m.status or "").lower() in _FAILED}
            # fixable = bounced at a domain that is NOT the real one
            if real and all(d != real for d in bounced_domains if d):
                recoverable.append((company.name, real, sorted(bounced_domains)))
            else:
                bounced_real_domain += 1

        print("\n" + "=" * 60)
        print("RECOVERY ANALYSIS")
        print("=" * 60)
        print(f"  accounts that landed (delivered/opened/replied)  {landed_ok}")
        print(f"  bounced at REAL domain (address bad, skip)        {bounced_real_domain}")
        print(f"  ineligible now (skip)                             {ineligible_now}")
        print(f"  RECOVERABLE (bounced at guessed domain)           {len(recoverable)}")
        for name, real, bd in recoverable[:25]:
            print(f"      {name[:28]:28} real={real:24} bounced={bd[:2]}")

        if args.apply and recoverable:
            names = {r[0] for r in recoverable}
            n = 0
            for acct_id, ms in by_acct.items():
                acct = db.query(CrmAccount).filter(CrmAccount.id == acct_id).first()
                if not acct or not acct.company_id:
                    continue
                company = db.query(Company).filter(Company.id == acct.company_id).first()
                if company and company.name in names:
                    acct.outreach_sent_at = None
                    if acct.outreach_stage == "suppressed_junk":
                        acct.outreach_stage = None
                    n += 1
            db.commit()
            print(f"\nAPPLIED: reset outreach_sent_at for {n} recoverable accounts.")
        elif not args.apply:
            print("\nDry-run — no changes. Re-run with --apply to unlock re-contact.")
        print("=" * 60)
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
