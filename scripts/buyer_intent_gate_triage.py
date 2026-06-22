#!/usr/bin/env python3
"""
Buyer-intent gate triage — stamp telemetry and optionally quarantine no-intent rows.

Dry-run (default):
  python3 scripts/buyer_intent_gate_triage.py --limit 500

Stamp crm_metadata only:
  python3 scripts/buyer_intent_gate_triage.py --stamp --limit 500

Quarantine no-intent / seller-story rows (not known brands):
  python3 scripts/buyer_intent_gate_triage.py --apply --limit 500
"""
from __future__ import annotations

import argparse
import csv
import sys
from datetime import datetime, timezone
from pathlib import Path

_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_root))

from scripts.harness_env import load_harness_env

load_harness_env(_root)

from app.database import SessionLocal
from app.models.company import Company
from app.models.signal import Signal
from app.services.buyer_intent_gate import (
    assess_buyer_intent_gate,
    stamp_buyer_intent_gate,
)
from app.services.lead_filter import classify_lead, pick_primary_score
from app.services.pipeline_delete_policy import is_quarantined
from app.services.rectifier import quarantine


def _scan(limit: int | None) -> list[dict]:
    db = SessionLocal()
    rows: list[dict] = []
    try:
        q = (
            db.query(Company)
            .filter(Company.is_internal.is_(True))
            .order_by(Company.id.desc())
        )
        if limit:
            q = q.limit(limit)
        companies = q.all()
        for company in companies:
            signals = (
                db.query(Signal)
                .filter(Signal.company_id == company.id)
                .order_by(Signal.created_at.desc())
                .limit(20)
                .all()
            )
            if not signals:
                continue
            assessment = assess_buyer_intent_gate(
                company_name=company.name,
                signals=signals,
            )
            junk, junk_reason, _pri = classify_lead(
                company,
                pick_primary_score(company.scores),
                signals,
            )
            rows.append(
                {
                    "company_id": company.id,
                    "name": company.name or "",
                    "industry": company.industry or "",
                    "disposition": assessment.disposition,
                    "route": assessment.route,
                    "gate_reason": assessment.reason,
                    "classify_junk": junk,
                    "classify_reason": junk_reason,
                    "company": company,
                    "assessment": assessment,
                }
            )
    finally:
        db.close()
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Buyer-intent gate triage")
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument("--stamp", action="store_true", help="Write crm_metadata.buyer_intent_gate")
    parser.add_argument("--apply", action="store_true", help="Quarantine route=quarantine rows")
    parser.add_argument("--report", default="", help="CSV report path")
    args = parser.parse_args()

    if args.apply and args.stamp:
        print("Use --apply OR --stamp, not both in one pass.", file=sys.stderr)
        return 1

    scanned = _scan(args.limit)
    quarantine_candidates = [
        r for r in scanned if r["route"] == "quarantine" and r["classify_junk"]
    ]
    no_intent = [r for r in scanned if r["disposition"] == "no_intent"]
    seller = [r for r in scanned if r["disposition"] == "seller_story"]

    report_path = args.report or str(
        _root
        / "reports"
        / f"buyer_intent_gate_triage_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
    )
    Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            [
                "company_id",
                "name",
                "industry",
                "disposition",
                "route",
                "gate_reason",
                "classify_junk",
                "classify_reason",
                "action",
            ]
        )
        for row in scanned:
            if args.apply and row in quarantine_candidates:
                action = "quarantine"
            elif args.stamp:
                action = "stamp"
            else:
                action = "dry_run"
            writer.writerow(
                [
                    row["company_id"],
                    row["name"],
                    row["industry"],
                    row["disposition"],
                    row["route"],
                    row["gate_reason"],
                    row["classify_junk"],
                    row["classify_reason"],
                    action,
                ]
            )

    print(f"Scanned (with signals): {len(scanned)}")
    print(f"  no_intent: {len(no_intent)}")
    print(f"  seller_story: {len(seller)}")
    print(f"  quarantine route + classify junk: {len(quarantine_candidates)}")
    print(f"Report: {report_path}")

    if not args.stamp and not args.apply:
        for row in quarantine_candidates[:15]:
            print(f"  {row['company_id']}: {row['name']!r} — {row['disposition']}")
        if len(quarantine_candidates) > 15:
            print(f"  ... and {len(quarantine_candidates) - 15} more")
        print("Dry-run only. Re-run with --stamp or --apply.")
        return 0

    db = SessionLocal()
    stamped = 0
    applied = 0
    try:
        for row in scanned:
            company = db.query(Company).filter(Company.id == row["company_id"]).first()
            if not company:
                continue
            if args.stamp:
                stamp_buyer_intent_gate(company, row["assessment"])
                stamped += 1
            elif args.apply and row in quarantine_candidates and not is_quarantined(company):
                quarantine(
                    company,
                    db,
                    reason=f"buyer_intent_gate:{row['disposition']}",
                )
                stamp_buyer_intent_gate(company, row["assessment"])
                applied += 1
        if args.stamp:
            db.commit()
            print(f"Stamped: {stamped}")
        elif args.apply:
            print(f"Quarantined: {applied}")
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
