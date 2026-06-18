#!/usr/bin/env python3
"""
Pipeline junk filter — purge scraper noise from the full companies table.

Safe defaults: does NOT delete real buyers that merely fail the buyer-opportunity
gate or have one noisy RSS signal mixed with capex/deployment signals.

Default dry-run:
  python3 scripts/cleanup_pipeline_junk.py

Delete after reviewing CSV:
  python3 scripts/cleanup_pipeline_junk.py --apply --delete --yes
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

from app.env_loader import database_url_is_template_or_sqlite

_shell_database_url = (os.environ.get("DATABASE_URL") or "").strip()
_root = Path(__file__).resolve().parents[1]
load_dotenv(_root / "frontend" / "nextjs" / ".env.local")
load_dotenv(_root / ".env", override=True)
_cleanup_dotenv = (os.getenv("DOTENV_PATH") or "").strip()
if _cleanup_dotenv:
    load_dotenv(Path(_cleanup_dotenv).expanduser(), override=True)
_loaded_after_dotenv = (os.environ.get("DATABASE_URL") or "").strip()
if _shell_database_url and database_url_is_template_or_sqlite(_loaded_after_dotenv):
    os.environ["DATABASE_URL"] = _shell_database_url

from sqlalchemy.orm import joinedload

from app.database import SessionLocal
from app.models.company import Company
from app.models.contact import Contact
from app.models.lead_rep_feedback import LeadRepFeedback
from app.models.score import Score
from app.models.signal import Signal
from app.services.industry_inference import known_industry_for_company_name
from app.services.lead_filter import BUYER_DIRECT_SIGNAL_TYPES, classify_lead, is_junk
from app.services.rss_noise_lead import (
    entity_is_noise_headline,
    signals_predominantly_rss_html,
)
from app.services.scraper_blocklist import add_bulk_to_blocklist
from app.services.text_classifier import EntityType, classify as classify_entity

_DELETE_ENTITY_TYPES = frozenset({
    EntityType.ARTICLE_HEADLINE,
    EntityType.DESCRIPTION,
    EntityType.MARKET_FRAGMENT,
    EntityType.SECTOR_DESCRIPTOR,
    EntityType.FACILITY_DESCRIPTOR,
    EntityType.POPULATION_GROUP,
    EntityType.DESCRIPTOR_ONLY,
    EntityType.EQUIPMENT_CAT,
})


@dataclass
class JunkCandidate:
    company_id: int
    name: str
    industry: str
    bucket: str
    reason: str
    signal_count: int


def _has_buyer_direct_signals(signals) -> bool:
    types = {(getattr(s, "signal_type", None) or "") for s in signals or []}
    valuable = BUYER_DIRECT_SIGNAL_TYPES | frozenset({
        "expansion",
        "capex",
        "strategic_hire",
        "labor_shortage",
        "robot_installation",
        "pilot_success",
        "warehouse_throughput",
        "production_capacity",
        "automation_intent",
    })
    return bool(types & valuable)


def _signals_are_all_rss_html(signals) -> bool:
    texts = [str(getattr(s, "signal_text", None) or "") for s in signals or []]
    if not texts:
        return False
    from app.services.rss_noise_lead import _GOOGLE_RSS_HTML_RE

    return all(_GOOGLE_RSS_HTML_RE.search(t) for t in texts)


def _has_clean_signal_text(signals) -> bool:
    from app.services.rss_noise_lead import _GOOGLE_RSS_HTML_RE

    for s in signals or []:
        text = str(getattr(s, "signal_text", None) or "")
        if text and not _GOOGLE_RSS_HTML_RE.search(text):
            return True
    return False


def _pipeline_junk_bucket(company: Company) -> tuple[bool, str, str]:
    name = (company.name or "").strip()
    signals = company.signals or []
    has_buyer = _has_buyer_direct_signals(signals)

    if getattr(company, "is_internal", True) is False:
        return True, "quarantined (failed rectification)", "quarantined"

    junk, junk_reason = is_junk(name)
    if junk:
        if known_industry_for_company_name(name) and "robotics vendor" in junk_reason.lower():
            pass
        else:
            return True, junk_reason, "fast_junk"

    if _signals_are_all_rss_html(signals) and not known_industry_for_company_name(name):
        return True, "all signal text is Google RSS/HTML noise", "rss_html_noise"

    tc = classify_entity(name)
    if tc.entity_type in _DELETE_ENTITY_TYPES and tc.confidence >= 0.78 and not has_buyer:
        return True, f"entity={tc.entity_type.value}", "headline_entity"

    ent_ok, ent_reason = entity_is_noise_headline(name, min_confidence=0.82)
    if ent_ok and not has_buyer:
        return True, ent_reason, "headline_entity"

    junk_c, reason_c, _ = classify_lead(company, company.scores, signals)
    if not junk_c:
        return False, "", ""

    low = reason_c.lower()
    if "headline fragment" in low or "mis-attributed" in low:
        if _has_clean_signal_text(signals):
            return False, "", ""
        return True, reason_c, "headline_fragment"
    if "publication" in low or "publisher" in low:
        return True, reason_c, "publication_or_news"
    if "target false positive" in low:
        return True, reason_c, "target_false_positive"
    if ("vendor" in low or "oem" in low) and junk and not has_buyer:
        return True, reason_c, "vendor_or_seller"

    return False, "", ""


def _delete_company_rows(db, company_id: int) -> None:
    db.query(LeadRepFeedback).filter(LeadRepFeedback.company_id == company_id).delete(
        synchronize_session=False
    )
    db.query(Signal).filter(Signal.company_id == company_id).delete(synchronize_session=False)
    db.query(Score).filter(Score.company_id == company_id).delete(synchronize_session=False)
    db.query(Contact).filter(Contact.company_id == company_id).delete(synchronize_session=False)
    db.query(Company).filter(Company.id == company_id).delete(synchronize_session=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Purge junk from full sales pipeline")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--delete", action="store_true")
    parser.add_argument("--yes", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--report", default="")
    args = parser.parse_args()
    if args.delete and not args.apply:
        parser.error("--delete requires --apply")

    db = SessionLocal()
    candidates: list[JunkCandidate] = []
    try:
        rows = (
            db.query(Company)
            .options(joinedload(Company.signals), joinedload(Company.scores))
            .order_by(Company.id)
            .all()
        )
        print(f"Scanning {len(rows)} pipeline companies...")
        for company in rows:
            ok, reason, bucket = _pipeline_junk_bucket(company)
            if not ok:
                continue
            candidates.append(
                JunkCandidate(
                    company_id=company.id,
                    name=company.name or "",
                    industry=company.industry or "",
                    bucket=bucket,
                    reason=reason,
                    signal_count=len(company.signals or []),
                )
            )

        buckets = Counter(c.bucket for c in candidates)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        report_path = Path(args.report or f"reports/pipeline_junk_cleanup_{ts}.csv")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with report_path.open("w", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["company_id", "name", "industry", "bucket", "reason", "signal_count"],
            )
            writer.writeheader()
            for c in candidates:
                writer.writerow(c.__dict__)

        print(f"\nJunk delete candidates: {len(candidates)} of {len(rows)}")
        for key, count in buckets.most_common():
            print(f"  {count:5d}  {key}")
        print(f"Report: {report_path}")
        for c in candidates[:30]:
            print(f"  id={c.company_id} [{c.bucket}] {c.name!r}")
        if len(candidates) > 30:
            print(f"  ... +{len(candidates) - 30} more")

        if not (args.apply and args.delete):
            print("\nDRY RUN — no rows deleted. Use --apply --delete --yes after review.")
            return

        to_delete = candidates
        if args.limit:
            to_delete = to_delete[: args.limit]
        if not args.yes:
            confirm = input(f"\nDelete {len(to_delete)} companies? Type 'yes': ")
            if confirm.strip().lower() != "yes":
                print("Aborted.")
                return

        names: list[str] = []
        for idx, c in enumerate(to_delete, start=1):
            _delete_company_rows(db, c.company_id)
            if c.name:
                names.append(c.name)
            if idx % 100 == 0:
                db.commit()
                print(f"  ...deleted {idx}/{len(to_delete)}", flush=True)
        db.commit()
        if names:
            add_bulk_to_blocklist(names, reason="pipeline_junk_cleanup")
        print(f"\nDeleted {len(to_delete)} junk companies; blocklisted {len(names)} names.")
        print(f"Remaining companies: {len(rows) - len(to_delete)}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
