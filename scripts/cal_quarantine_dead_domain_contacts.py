"""
Quarantine existing accounts whose stored contact_email sits on a dead domain.

The URL-first policy (resolve_outreach_email) now refuses to look up or guess an
address until the company URL resolves, and quarantines it to null when it does not.
That protects NEW resolutions — but accounts enriched during the guessed-domain era
still carry a stored contact_email at a domain that never resolves. This one-off walks
those accounts and quarantines them (nulls contact_email + stamps the company
outreach_email_status=quarantined) so the historical guesses stop feeding the send
paths, instead of waiting for each account to be lazily re-resolved.

DNS is classified permanent (nxdomain) vs transient: ONLY permanently-dead domains are
quarantined; a transient resolver failure is left untouched so we never null a good
address over a blip. Already-empty and already-quarantined accounts are skipped.

Read-only by default. Re-run with --apply to write.
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def _email_domain(email: str | None) -> str:
    return (email or "").split("@")[-1].strip().lower()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="Null + quarantine dead-domain contacts.")
    ap.add_argument("--limit", type=int, default=0, help="Optional cap on accounts scanned (0 = all).")
    args = ap.parse_args()

    from app.database import SessionLocal
    from app.models.company import Company
    from app.models.crm import CrmAccount
    from app.services.lead_enrichment import _domain_dns_status, quarantine_outreach_email

    db = SessionLocal()
    try:
        q = db.query(CrmAccount).filter(CrmAccount.contact_email.isnot(None))
        if args.limit:
            q = q.limit(args.limit)
        accts = q.all()

        dns_cache: dict[str, str] = {}
        company_cache: dict = {}
        quarantined: list[tuple[str, str]] = []
        transient: list[tuple[str, str]] = []
        status_mix: Counter = Counter()

        for acct in accts:
            email = (acct.contact_email or "").strip()
            domain = _email_domain(email)
            if not domain:
                continue
            status = dns_cache.get(domain)
            if status is None:
                status = _domain_dns_status(domain)
                dns_cache[domain] = status
            status_mix[status] += 1

            if status == "ok":
                continue
            if status == "temporary":
                transient.append((acct.name or "?", email))
                continue

            # nxdomain — permanently dead, quarantine.
            company = company_cache.get(acct.company_id)
            if company is None and acct.company_id:
                company = db.query(Company).filter(Company.id == acct.company_id).first()
                company_cache[acct.company_id] = company
            quarantined.append((acct.name or "?", email))
            if args.apply:
                quarantine_outreach_email(company, acct, "email_domain_nxdomain")

        print("=" * 60)
        print("DEAD-DOMAIN CONTACT QUARANTINE")
        print("=" * 60)
        print(f"  accounts with a stored contact_email  {len(accts)}")
        print(f"  distinct domains checked              {len(dns_cache)}")
        print(f"  domains resolving OK                  {status_mix.get('ok', 0)}")
        print(f"  transient DNS (left untouched)        {len(transient)}")
        print(f"  QUARANTINED (dead domain)             {len(quarantined)}")
        for name, email in quarantined[:40]:
            print(f"      {name[:30]:30} {email}")
        if len(quarantined) > 40:
            print(f"      … and {len(quarantined) - 40} more")
        if transient:
            print(f"\n  Note: {len(transient)} address(es) hit a transient DNS failure and were skipped —")
            print("  re-run later to confirm before deciding they are dead.")

        if args.apply and quarantined:
            db.commit()
            print(f"\nAPPLIED: quarantined {len(quarantined)} dead-domain contacts to null.")
        elif not args.apply:
            print("\nDry-run — no changes. Re-run with --apply to quarantine them.")
        print("=" * 60)
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
