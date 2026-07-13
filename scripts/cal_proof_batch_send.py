#!/usr/bin/env python3
"""One-time controlled proof-batch send of Cal's new-voice buyer outreach.

Sends a curated set of verified, new-voice, send-ready buyers through the SAME
guarded path Cal's autopilot uses (resolve email -> trust gate -> deliverability
-> assembly review -> send + follow-up enrollment). Scheduled autopilot stays
paused; this is a deliberate, human-approved batch so the rewritten voice can
prove out before any volume.

Usage
-----
  python3 scripts/cal_proof_batch_send.py                # dry-run, show the curated 25
  python3 scripts/cal_proof_batch_send.py --limit 25 --apply
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

import app.models  # noqa: F401
from app.database import SessionLocal

# Software/OEM-ish or off-ICP names to hold out of the proof batch.
_DENYLIST = {"red hat"}

# Higher = send earlier. Robots land hardest in physical-throughput operations.
_FIT_PRIORITY = [
    "logistics", "warehousing", "cold storage", "supply chain", "freight",
    "distribution", "food processing", "food manufacturing", "manufacturing",
    "food service", "catering", "restaurants", "fast casual",
    "facilities", "senior living", "assisted living", "hospitality", "hotel",
    "healthcare", "skilled nursing",
]


def _fit_rank(industry: str) -> int:
    low = (industry or "").lower()
    for i, token in enumerate(_FIT_PRIORITY):
        if token in low:
            return i
    return len(_FIT_PRIORITY) + 1


def _clean_name(name: str) -> bool:
    n = (name or "").strip()
    if not n or n.lower() in _DENYLIST:
        return False
    # Headline-contaminated names are wordy or contain sentence verbs.
    if len(n.split()) > 5:
        return False
    for verb in (" sees ", " says ", " launches ", " raises ", " expands ", " announces ", " unveils "):
        if verb in f" {n.lower()} ":
            return False
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description="Send Cal new-voice proof batch")
    ap.add_argument("--limit", type=int, default=25)
    ap.add_argument("--apply", action="store_true", help="actually send (default: dry-run)")
    args = ap.parse_args()

    from app.models.company import Company
    from app.models.crm import CrmAccount
    from app.services.cal_assembly_agent import assemble_buyer_outreach, cal_assembly_required
    from app.services.cal_autonomy import resolve_cal_admin_context
    from app.services.cal_draft_guard import is_complete_cal_draft
    from app.services.cal_outreach_send import enroll_cal_followup, parse_cal_draft, send_cal_intro_email
    from app.services.lead_enrichment import (
        _VERIFIED_EMAIL_SOURCES,
        outreach_recipient_trusted,
        resolve_outreach_email,
        verify_email_deliverable,
    )
    from app.services.outreach_email_inference import infer_cc_outreach_emails
    from app.services.resend_email import ResendEmailError
    from app.services.company_domain import normalize_website_domain

    db = SessionLocal()
    try:
        ctx = resolve_cal_admin_context(db)
        if not ctx:
            print("No Cal admin context.")
            return 1
        uid, team = ctx

        unsent = (
            db.query(CrmAccount)
            .filter(CrmAccount.team_id == team.id, CrmAccount.account_type == "buyer",
                    CrmAccount.outreach_sent_at.is_(None))
            .all()
        )
        candidates = []
        for a in unsent:
            c = db.query(Company).filter(Company.id == a.company_id).first()
            if not c or not _clean_name(a.name):
                continue
            src = ((c.crm_metadata or {}).get("outreach_email_source") or "").strip().lower()
            if not ((a.contact_email or "").strip() and src in _VERIFIED_EMAIL_SOURCES):
                continue
            if not (a.outreach_draft and is_complete_cal_draft(a.outreach_draft)[0]):
                continue
            candidates.append((a, c))

        candidates.sort(key=lambda ac: (_fit_rank(ac[1].industry or ""), ac[0].name.lower()))
        batch = candidates[: args.limit]

        mode = "APPLY (SENDING)" if args.apply else "DRY RUN"
        print(f"{mode} — proof batch of {len(batch)} (from {len(candidates)} send-ready)\n")

        sent = failed = skipped = 0
        now = datetime.now(timezone.utc)
        for a, c in batch:
            to_email, source, _t = resolve_outreach_email(c, a, use_apollo=True)
            if not to_email:
                skipped += 1; print(f"  SKIP {a.name}: no email"); continue
            trusted, why = outreach_recipient_trusted(c, a, to_email, source)
            if not trusted:
                skipped += 1; print(f"  SKIP {a.name}: unverified ({why})"); continue
            ok, _r = verify_email_deliverable(to_email)
            if not ok:
                skipped += 1; print(f"  SKIP {a.name}: undeliverable"); continue
            subject, body_text = parse_cal_draft(a.outreach_draft, c.name or "your team")
            if cal_assembly_required():
                asm = assemble_buyer_outreach(company_name=c.name or "", subject=subject, body=body_text)
                if not asm.approved:
                    skipped += 1; print(f"  SKIP {a.name}: assembly {asm.issues[:2]}"); continue

            if not args.apply:
                print(f"  [{_fit_rank(c.industry or ''):>2}] {a.name[:32]:32} -> {to_email}  | {subject}")
                sent += 1
                continue

            dom = normalize_website_domain(c.website or a.website)
            cc = infer_cc_outreach_emails(dom, c.industry, primary=to_email)
            from app.services.agent_messaging import resolve_buyer_variant

            variant_id = resolve_buyer_variant(c, a)
            try:
                send_cal_intro_email(
                    db, acct=a, company=c, team_id=team.id, to_email=to_email,
                    subject=subject, body_text=body_text,
                    cc=[cc[0]] if cc else None, sender_user_id=uid,
                    idempotency_key=f"cal-proof-{a.id}-{now.date().isoformat()}",
                    send_identity="cal", variant_id=variant_id,
                )
                enroll_cal_followup(db, team_id=team.id, crm_account_id=a.id, variant_id=variant_id)
                # send_cal_intro_email only flushes; commit here so the OutreachMessage,
                # outreach_sent_at, and follow-up enrollment survive the session close.
                # Without this the email leaves via Resend but the tracking row is rolled
                # back — no bounce attribution and a duplicate-send risk next cycle.
                db.commit()
                sent += 1
                print(f"  SENT {a.name[:32]:32} -> {to_email}")
            except ResendEmailError as exc:
                db.rollback()
                failed += 1
                print(f"  FAIL {a.name}: {str(exc)[:80]}")

        verb = "sent" if args.apply else "would send"
        print(f"\n{verb}={sent}, skipped={skipped}, failed={failed}")
        if not args.apply:
            print("Re-run with --apply to send this batch.")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
