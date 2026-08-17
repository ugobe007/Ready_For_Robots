"""
Backfill missing trust-first variant tags on legacy outreach records.

Repairs historical attribution continuity for:
- Follow-up sends in outreach_messages.payload.variant_id
- Sequence enrollment payloads in outreach_sequence_enrollments.payload.variant_id

Read-only by default. Re-run with --apply to persist changes.
"""
from __future__ import annotations

import argparse
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def _parse_uuid(raw: str | None) -> uuid.UUID | None:
    if not raw:
        return None
    try:
        return uuid.UUID(str(raw))
    except (TypeError, ValueError):
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="Write repaired variant_id values.")
    ap.add_argument(
        "--limit-messages",
        type=int,
        default=0,
        help="Optional cap on follow-up messages scanned (0 = all).",
    )
    ap.add_argument(
        "--limit-enrollments",
        type=int,
        default=0,
        help="Optional cap on enrollments scanned (0 = all).",
    )
    args = ap.parse_args()

    from app.database import SessionLocal
    from app.models.company import Company
    from app.models.crm import CrmAccount
    from app.models.outreach import OutreachMessage
    from app.models.sequences import OutreachSequenceEnrollment
    from app.services.agent_messaging import BUYER_VARIANTS, resolve_buyer_variant

    db = SessionLocal()
    try:
        company_cache: dict[int, Company | None] = {}
        account_cache: dict[uuid.UUID, CrmAccount | None] = {}
        enrollment_cache: dict[uuid.UUID, OutreachSequenceEnrollment | None] = {}

        def get_account(account_id: uuid.UUID | None) -> CrmAccount | None:
            if not account_id:
                return None
            if account_id not in account_cache:
                account_cache[account_id] = (
                    db.query(CrmAccount).filter(CrmAccount.id == account_id).first()
                )
            return account_cache[account_id]

        def get_company(company_id: int | None, acct: CrmAccount | None) -> Company | None:
            cid = company_id or (acct.company_id if acct else None)
            if not cid:
                return None
            if cid not in company_cache:
                company_cache[cid] = db.query(Company).filter(Company.id == cid).first()
            return company_cache[cid]

        def resolve_variant_for_record(
            *, company_id: int | None, crm_account_id: uuid.UUID | None
        ) -> str | None:
            acct = get_account(crm_account_id)
            company = get_company(company_id, acct)
            if not company:
                return None
            resolved = resolve_buyer_variant(company, acct)
            if resolved in BUYER_VARIANTS:
                return resolved
            return None

        msg_q = (
            db.query(OutreachMessage)
            .filter(OutreachMessage.send_identity == "scout")
            .order_by(OutreachMessage.created_at.asc())
        )
        if args.limit_messages:
            msg_q = msg_q.limit(args.limit_messages)
        messages = msg_q.all()

        msg_scanned = 0
        msg_missing = 0
        msg_fixed = 0
        msg_unresolved = 0
        msg_samples: list[tuple[str, str, str]] = []

        for msg in messages:
            msg_scanned += 1
            payload = dict(msg.payload or {})
            current = (payload.get("variant_id") or "").strip()
            if current in BUYER_VARIANTS:
                continue
            msg_missing += 1

            variant_id = None
            seq_raw = payload.get("sequence_enrollment_id")
            seq_id = _parse_uuid(str(seq_raw)) if seq_raw else None
            if seq_id:
                if seq_id not in enrollment_cache:
                    enrollment_cache[seq_id] = (
                        db.query(OutreachSequenceEnrollment)
                        .filter(OutreachSequenceEnrollment.id == seq_id)
                        .first()
                    )
                enr = enrollment_cache[seq_id]
                if enr:
                    emeta = dict(enr.payload or {})
                    evar = (emeta.get("variant_id") or "").strip()
                    if evar in BUYER_VARIANTS:
                        variant_id = evar

            if not variant_id:
                variant_id = resolve_variant_for_record(
                    company_id=msg.company_id,
                    crm_account_id=msg.crm_account_id,
                )

            if not variant_id:
                msg_unresolved += 1
                continue

            payload["variant_id"] = variant_id
            msg.payload = payload
            msg_fixed += 1
            if len(msg_samples) < 20:
                msg_samples.append((str(msg.id), msg.to_email, variant_id))

        enr_q = db.query(OutreachSequenceEnrollment).order_by(OutreachSequenceEnrollment.created_at.asc())
        if args.limit_enrollments:
            enr_q = enr_q.limit(args.limit_enrollments)
        enrollments = enr_q.all()

        enr_scanned = 0
        enr_missing = 0
        enr_fixed = 0
        enr_unresolved = 0
        enr_samples: list[tuple[str, str]] = []

        for enr in enrollments:
            enr_scanned += 1
            meta = dict(enr.payload or {})
            current = (meta.get("variant_id") or "").strip()
            if current in BUYER_VARIANTS:
                continue
            enr_missing += 1

            variant_id = resolve_variant_for_record(
                company_id=None,
                crm_account_id=enr.crm_account_id,
            )
            if not variant_id:
                enr_unresolved += 1
                continue

            meta["variant_id"] = variant_id
            enr.payload = meta
            enr_fixed += 1
            if len(enr_samples) < 20:
                enr_samples.append((str(enr.id), variant_id))

        print("=" * 68)
        print("CAL VARIANT TAG BACKFILL")
        print("=" * 68)
        print(f"follow-up messages scanned              {msg_scanned}")
        print(f"follow-up messages missing variant_id   {msg_missing}")
        print(f"follow-up messages backfilled           {msg_fixed}")
        print(f"follow-up messages unresolved           {msg_unresolved}")
        if msg_samples:
            print("sample message fixes:")
            for mid, to_email, vid in msg_samples:
                print(f"  {mid}  {to_email:35}  {vid}")

        print("-" * 68)
        print(f"enrollments scanned                     {enr_scanned}")
        print(f"enrollments missing variant_id          {enr_missing}")
        print(f"enrollments backfilled                  {enr_fixed}")
        print(f"enrollments unresolved                  {enr_unresolved}")
        if enr_samples:
            print("sample enrollment fixes:")
            for eid, vid in enr_samples:
                print(f"  {eid}  {vid}")

        if args.apply and (msg_fixed or enr_fixed):
            db.commit()
            print("-" * 68)
            print(f"APPLIED: message fixes={msg_fixed}, enrollment fixes={enr_fixed}")
        elif args.apply:
            print("-" * 68)
            print("APPLY requested, but no repairable rows found.")
        else:
            db.rollback()
            print("-" * 68)
            print("Dry-run only. Re-run with --apply to persist.")
        print("=" * 68)
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
