#!/usr/bin/env python3
"""Quarantine HOT/WARM pipeline rows whose company.name is a news headline stub."""
from __future__ import annotations

import argparse
import csv
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_root))

from dotenv import load_dotenv

from app.env_loader import database_url_is_template_or_sqlite

_shell_database_url = (os.environ.get("DATABASE_URL") or "").strip()
load_dotenv(_root / "frontend" / "nextjs" / ".env.local")
load_dotenv(_root / ".env", override=True)
_dotenv_path = (os.getenv("DOTENV_PATH") or "").strip()
if _dotenv_path:
    load_dotenv(Path(_dotenv_path).expanduser(), override=True)
_loaded = (os.environ.get("DATABASE_URL") or "").strip()
if _shell_database_url and database_url_is_template_or_sqlite(_loaded):
    os.environ["DATABASE_URL"] = _shell_database_url

from sqlalchemy.orm import joinedload

from app.database import SessionLocal
from app.models.company import Company
from app.services.headline_hot_quarantine import headline_hot_leak_for_company
from app.services.pipeline_delete_policy import is_quarantined
from app.services.rectifier import quarantine


def main() -> int:
    parser = argparse.ArgumentParser(description="Quarantine headline junk in HOT/WARM pipeline")
    parser.add_argument("--apply", action="store_true", help="Set is_internal=False on matches")
    parser.add_argument("--tier", action="append", dest="tiers", default=["HOT", "WARM"])
    parser.add_argument("--limit", type=int, default=None, help="Max companies to scan")
    parser.add_argument("--report", default="", help="Optional CSV path")
    args = parser.parse_args()
    tier_filter = {t.strip().upper() for t in args.tiers if t.strip()}

    db = SessionLocal()
    rows: list[tuple[int, str, str, str, bool]] = []
    try:
        q = (
            db.query(Company)
            .options(joinedload(Company.signals), joinedload(Company.scores))
            .filter(Company.is_internal.is_(True))
            .order_by(Company.id.desc())
        )
        if args.limit:
            q = q.limit(args.limit)
        companies = q.all()
        print(f"Scanning {len(companies)} active companies for headline HOT/WARM leaks…")
        for company in companies:
            ok, reason, tier = headline_hot_leak_for_company(company)
            if not ok or tier not in tier_filter:
                continue
            rows.append(
                (
                    company.id,
                    (company.name or "").strip(),
                    tier,
                    reason,
                    is_quarantined(company),
                )
            )
    finally:
        db.close()

    tiers = Counter(t for _, _, t, _, _ in rows)
    report_path = args.report or str(
        _root / "reports" / f"headline_hot_quarantine_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
    )
    Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["company_id", "name", "tier", "reason", "action"])
        for cid, name, tier, reason, _ in rows:
            action = "quarantine" if args.apply else "would_quarantine"
            writer.writerow([cid, name, tier, reason, action])

    print(f"Headline leak candidates ({', '.join(sorted(tier_filter))}): {len(rows)}")
    for key, count in tiers.most_common():
        print(f"  {count:5d}  {key}")
    print(f"Report: {report_path}")
    for cid, name, tier, reason, _ in rows[:20]:
        print(f"  [{tier}] {cid}: {name!r} — {reason[:72]}")
    if len(rows) > 20:
        print(f"  ... and {len(rows) - 20} more")

    if not args.apply:
        print("Dry-run only. Re-run with --apply to quarantine.")
        return 0

    db = SessionLocal()
    applied = 0
    try:
        for cid, name, tier, reason, _ in rows:
            company = db.query(Company).filter(Company.id == cid).first()
            if not company or is_quarantined(company):
                continue
            quarantine(company, db, reason=reason)
            applied += 1
            if applied % 50 == 0:
                db.commit()
        db.commit()
        print(f"Quarantined: {applied}")
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
