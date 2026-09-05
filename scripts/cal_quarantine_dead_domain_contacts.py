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
import concurrent.futures
import socket
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def _email_domain(email: str | None) -> str:
    return (email or "").split("@")[-1].strip().lower()


def _resolve_one(domain: str, timeout: float) -> str:
    """Classify a single domain 'ok' | 'nxdomain' | 'temporary' with a hard per-lookup
    timeout so one unresponsive resolver can't stall the whole run."""
    try:
        socket.getaddrinfo(domain, None, type=socket.SOCK_STREAM)
        return "ok"
    except socket.timeout:
        return "temporary"
    except socket.gaierror as exc:
        permanent = {getattr(socket, "EAI_NONAME", object()), getattr(socket, "EAI_NODATA", object())}
        return "nxdomain" if getattr(exc, "errno", None) in permanent else "temporary"
    except Exception:
        return "temporary"


def _resolve_domains(domains: list[str], workers: int, overall_timeout: float, per_timeout: float) -> dict[str, str]:
    """Resolve a batch of distinct domains CONCURRENTLY with live progress and a bounded
    overall timeout. Any domain not resolved in time is treated as 'temporary' (never
    quarantined) so the script always terminates promptly instead of hanging on slow DNS."""
    results: dict[str, str] = {}
    if not domains:
        return results
    # Bound each individual lookup too (getaddrinfo ignores socket.setdefaulttimeout on some
    # platforms, so we also cap via the executor below).
    socket.setdefaulttimeout(per_timeout)
    ex = concurrent.futures.ThreadPoolExecutor(max_workers=workers)
    fut_to_dom = {ex.submit(_resolve_one, d, per_timeout): d for d in domains}
    done = 0
    total = len(domains)
    try:
        for fut in concurrent.futures.as_completed(fut_to_dom, timeout=overall_timeout):
            dom = fut_to_dom[fut]
            try:
                results[dom] = fut.result()
            except Exception:
                results[dom] = "temporary"
            done += 1
            if done % 50 == 0 or done == total:
                print(f"    …resolved {done}/{total} domains", flush=True)
    except concurrent.futures.TimeoutError:
        print(f"    (overall DNS budget {overall_timeout:.0f}s hit at {done}/{total}; "
              f"treating the rest as transient)", flush=True)
    for dom in domains:
        results.setdefault(dom, "temporary")
    ex.shutdown(wait=False, cancel_futures=True)
    socket.setdefaulttimeout(None)
    return results


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="Null + quarantine dead-domain contacts.")
    ap.add_argument("--limit", type=int, default=0, help="Optional cap on accounts scanned (0 = all).")
    ap.add_argument("--workers", type=int, default=32, help="Concurrent DNS lookups (default 32).")
    ap.add_argument("--dns-timeout", type=float, default=4.0, help="Per-lookup DNS timeout seconds (default 4).")
    ap.add_argument("--budget", type=float, default=180.0, help="Overall DNS budget seconds (default 180).")
    args = ap.parse_args()

    from app.database import SessionLocal
    from app.models.company import Company
    from app.models.crm import CrmAccount
    from app.services.lead_enrichment import quarantine_outreach_email

    db = SessionLocal()
    try:
        print("Loading accounts with a stored contact_email…", flush=True)
        q = db.query(CrmAccount).filter(CrmAccount.contact_email.isnot(None))
        if args.limit:
            q = q.limit(args.limit)
        accts = q.all()

        # Distinct domains first, so DNS work is proportional to domains, not accounts.
        domains = sorted({_email_domain(a.contact_email) for a in accts if _email_domain(a.contact_email)})
        print(f"  {len(accts)} accounts across {len(domains)} distinct domains — resolving "
              f"({args.workers} workers, {args.dns_timeout:.0f}s/lookup, {args.budget:.0f}s budget)…",
              flush=True)
        dns_status = _resolve_domains(domains, args.workers, args.budget, args.dns_timeout)

        company_cache: dict = {}
        quarantined: list[tuple[str, str]] = []
        transient: list[tuple[str, str]] = []
        status_mix: Counter = Counter()

        for acct in accts:
            domain = _email_domain(acct.contact_email)
            if not domain:
                continue
            status = dns_status.get(domain, "temporary")
            status_mix[status] += 1

            if status == "ok":
                continue
            if status == "temporary":
                transient.append((acct.name or "?", acct.contact_email or ""))
                continue

            # nxdomain — permanently dead, quarantine.
            company = company_cache.get(acct.company_id)
            if company is None and acct.company_id:
                company = db.query(Company).filter(Company.id == acct.company_id).first()
                company_cache[acct.company_id] = company
            quarantined.append((acct.name or "?", acct.contact_email or ""))
            if args.apply:
                quarantine_outreach_email(company, acct, "email_domain_nxdomain")

        print("=" * 60)
        print("DEAD-DOMAIN CONTACT QUARANTINE")
        print("=" * 60)
        print(f"  accounts with a stored contact_email  {len(accts)}")
        print(f"  distinct domains checked              {len(domains)}")
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
