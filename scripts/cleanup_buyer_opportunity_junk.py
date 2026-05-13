#!/usr/bin/env python3
"""
Audit and optionally remove companies that fail the buyer-opportunity gate.

Default is dry-run:
  python3 scripts/cleanup_buyer_opportunity_junk.py

Write an audit report only:
  python3 scripts/cleanup_buyer_opportunity_junk.py --report reports/buyer_gate_audit.csv

Delete candidates after review:
  python3 scripts/cleanup_buyer_opportunity_junk.py --apply --delete --yes
  python3 scripts/cleanup_buyer_opportunity_junk.py --apply --delete --yes --delete-buckets fast_junk,publication_or_news

Safety:
- No writes unless --apply and --delete are both provided.
- Delete mode defaults to hard-junk buckets only. It will not delete buyer
  opportunity gate, logic-engine, or misattributed-headline rows unless those
  buckets are explicitly requested.
- Deletes child rows explicitly before the company row.
- Uses classify_lead(), so it applies the same logic used by public lead APIs.
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

from sqlalchemy import text
from sqlalchemy.orm import joinedload

from app.database import DATABASE_URL, SessionLocal, engine
from app.models.company import Company
from app.models.contact import Contact
from app.models.lead_rep_feedback import LeadRepFeedback
from app.models.score import Score
from app.models.signal import Signal
from app.services.lead_filter import classify_lead, is_junk
from app.services.semantic_roles import parse_semantic_roles
from app.services.text_classifier import EntityType, classify

DEFAULT_DELETE_BUCKETS = frozenset({
    "fast_junk",
    "ontology_descriptor",
    "publication_or_news",
    "vendor_or_seller",
    "target_false_positive",
})

ONTOLOGY_DELETE_TYPES = frozenset({
    EntityType.SECTOR_DESCRIPTOR,
    EntityType.FACILITY_DESCRIPTOR,
    EntityType.POPULATION_GROUP,
    EntityType.DESCRIPTOR_ONLY,
    EntityType.EQUIPMENT_CAT,
    EntityType.MARKET_FRAGMENT,
})

ONTOLOGY_REPAIR_TYPES = frozenset({
    EntityType.MALFORMED_ENTITY,
})


@dataclass
class Candidate:
    company_id: int
    name: str
    reason: str
    reason_bucket: str
    cleanup_action: str
    entity_type: str
    entity_confidence: float
    entity_evidence: str
    head_object: str
    object_kind: str
    object_candidate: str
    verb_anchor: str
    url_lookup_name: str
    resolved_url: str
    priority_tier: str
    priority_score: float
    industry: str
    signal_count: int
    signal_types: str


def _assert_database_ready() -> None:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            conn.execute(text("SELECT 1 FROM companies LIMIT 1"))
    except Exception as exc:
        print(
            "ERROR: Could not connect to a database with a companies table.\n"
            f"DATABASE_URL={DATABASE_URL!r}\n"
            f"{exc}",
            file=sys.stderr,
        )
        raise SystemExit(2)


def _bucket(reason: str) -> str:
    low = (reason or "").lower()
    # Buyer gate means "hide as an active opportunity", not "safe to delete".
    # Keep this before vendor/seller so real customers mentioned in vendor-ish
    # articles (e.g. Six Flags, Fresh Blends) do not land in delete buckets.
    if "buyer opportunity gate" in low:
        return "buyer_opportunity_gate"
    if "vendor" in low or "seller" in low or "oem" in low:
        return "vendor_or_seller"
    if "publication" in low or "publisher" in low or "news" in low:
        return "publication_or_news"
    if "logic engine" in low:
        return "logic_engine"
    if "junk" in low:
        return "fast_junk"
    if "target false positive" in low:
        return "target_false_positive"
    if "mis-attributed" in low:
        return "misattributed_headline"
    return "other"


def _cleanup_action(reason_bucket: str) -> str:
    if reason_bucket == "buyer_opportunity_gate":
        return "keep_not_current_opportunity"
    if reason_bucket == "malformed_entity":
        return "repair_or_merge_candidate"
    if reason_bucket in DEFAULT_DELETE_BUCKETS:
        return "delete_candidate"
    return "review"


def _semantic_bucket(name: str, current_bucket: str) -> tuple[str, object]:
    tc = classify(name or "")
    if tc.entity_type in ONTOLOGY_DELETE_TYPES and tc.confidence >= 0.65:
        return "ontology_descriptor", tc
    if tc.entity_type in ONTOLOGY_REPAIR_TYPES and tc.confidence >= 0.65:
        return "malformed_entity", tc
    if (
        tc.entity_type in {EntityType.ARTICLE_HEADLINE, EntityType.DESCRIPTION}
        and tc.confidence >= 0.75
    ):
        return "headline_or_description", tc
    return current_bucket, tc


def _signal_types(company: Company) -> str:
    return ",".join(
        sorted({(s.signal_type or "unknown") for s in (company.signals or [])})
    )


def _delete_company_rows(db, company_id: int) -> None:
    db.query(LeadRepFeedback).filter(LeadRepFeedback.company_id == company_id).delete(
        synchronize_session=False
    )
    db.query(Signal).filter(Signal.company_id == company_id).delete(synchronize_session=False)
    db.query(Score).filter(Score.company_id == company_id).delete(synchronize_session=False)
    db.query(Contact).filter(Contact.company_id == company_id).delete(synchronize_session=False)
    db.query(Company).filter(Company.id == company_id).delete(synchronize_session=False)


def _write_report(path: Path, candidates: list[Candidate]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "company_id",
                "name",
                "reason_bucket",
                "cleanup_action",
                "entity_type",
                "entity_confidence",
                "entity_evidence",
                "head_object",
                "object_kind",
                "object_candidate",
                "verb_anchor",
                "url_lookup_name",
                "resolved_url",
                "reason",
                "priority_tier",
                "priority_score",
                "industry",
                "signal_count",
                "signal_types",
            ],
        )
        writer.writeheader()
        for c in candidates:
            writer.writerow(c.__dict__)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit/delete companies hidden by classify_lead buyer-opportunity gate"
    )
    parser.add_argument("--apply", action="store_true", help="Allow database writes")
    parser.add_argument("--delete", action="store_true", help="Delete candidate company rows")
    parser.add_argument("--yes", action="store_true", help="Skip confirmation when deleting")
    parser.add_argument("--limit", type=int, default=None, help="Max candidates to delete")
    parser.add_argument(
        "--delete-buckets",
        default=",".join(sorted(DEFAULT_DELETE_BUCKETS)),
        help=(
            "Comma-separated reason buckets eligible for deletion. "
            "Default excludes buyer_opportunity_gate, logic_engine, and "
            "misattributed_headline because those can include real companies "
            "or partial real names that need review."
        ),
    )
    parser.add_argument(
        "--report",
        default="",
        help="CSV report path. Default: reports/buyer_opportunity_junk_<timestamp>.csv",
    )
    parser.add_argument(
        "--resolve-urls",
        action="store_true",
        help=(
            "Optionally resolve official homepages for extracted object candidates "
            "using app.services.company_url_openai when COMPANY_URL_OPENAI_RESOLVE=1."
        ),
    )
    args = parser.parse_args()

    if args.delete and not args.apply:
        parser.error("--delete requires --apply")

    _assert_database_ready()

    db = SessionLocal()
    db.expire_on_commit = False
    candidates: list[Candidate] = []
    try:
        rows = (
            db.query(Company)
            .options(joinedload(Company.signals), joinedload(Company.scores))
            .order_by(Company.id)
            .all()
        )
        print(f"Scanning {len(rows)} companies with full buyer-opportunity gate...")
        for idx, company in enumerate(rows, start=1):
            if idx % 500 == 0:
                print(f"  ...processed {idx}/{len(rows)}", flush=True)

            junk, reason, priority = classify_lead(company, company.scores, company.signals)
            if not junk:
                continue
            # Keep compatibility with existing audits: classify why the row fails.
            fast_junk, fast_reason = is_junk(company.name)
            final_reason = fast_reason if fast_junk else reason
            reason_bucket = _bucket(final_reason)
            reason_bucket, tc = _semantic_bucket(company.name or "", reason_bucket)
            roles = parse_semantic_roles(company.name or "")
            url_lookup_name = roles.object_candidate
            candidates.append(
                Candidate(
                    company_id=company.id,
                    name=company.name or "",
                    reason=final_reason,
                    reason_bucket=reason_bucket,
                    cleanup_action=_cleanup_action(reason_bucket),
                    entity_type=tc.entity_type.value,
                    entity_confidence=round(tc.confidence, 2),
                    entity_evidence="; ".join(tc.evidence[:3]),
                    head_object=roles.head_object,
                    object_kind=roles.object_kind,
                    object_candidate=roles.object_candidate,
                    verb_anchor=roles.verb_anchor,
                    url_lookup_name=url_lookup_name,
                    resolved_url="",
                    priority_tier=priority.tier,
                    priority_score=round(priority.score, 1),
                    industry=company.industry or "",
                    signal_count=len(company.signals or []),
                    signal_types=_signal_types(company),
                )
            )

        if args.resolve_urls:
            from app.services.company_url_openai import batch_resolve_company_homepage_urls

            names = [c.url_lookup_name for c in candidates if c.url_lookup_name]
            resolved = batch_resolve_company_homepage_urls(names)
            for c in candidates:
                if c.url_lookup_name:
                    c.resolved_url = resolved.get(c.url_lookup_name.lower()) or ""

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        report_path = Path(args.report or f"reports/buyer_opportunity_junk_{timestamp}.csv")
        _write_report(report_path, candidates)

        buckets = Counter(c.reason_bucket for c in candidates)
        actions = Counter(c.cleanup_action for c in candidates)
        print(f"\nCandidates hidden by cleanup gate: {len(candidates)}")
        print("Reason buckets:")
        for key, count in buckets.most_common():
            print(f"  {count:5d}  {key}")
        print("Cleanup actions:")
        for key, count in actions.most_common():
            print(f"  {count:5d}  {key}")
        print(f"\nReport: {report_path}")

        print("\nSample candidates:")
        for c in candidates[:40]:
            print(
                f"  id={c.company_id} signals={c.signal_count:<3} "
                f"[{c.reason_bucket}] {c.name!r} :: {c.reason[:90]}"
            )
        if len(candidates) > 40:
            print(f"  ... +{len(candidates) - 40} more")

        if not (args.apply and args.delete):
            print("\nDRY RUN - no rows deleted. Review the CSV before using --apply --delete --yes.")
            return

        allowed_buckets = {
            b.strip() for b in (args.delete_buckets or "").split(",") if b.strip()
        }
        to_delete = [c for c in candidates if c.reason_bucket in allowed_buckets]
        if args.limit:
            to_delete = to_delete[: args.limit]
        print(
            "\nDelete buckets: "
            + ", ".join(sorted(allowed_buckets))
            + f"\nEligible for deletion: {len(to_delete)} of {len(candidates)} candidates"
        )
        if not args.yes:
            confirm = input(f"\nDelete {len(to_delete)} companies and child rows? Type 'yes': ")
            if confirm.strip().lower() != "yes":
                print("Aborted - no changes made.")
                return

        for idx, candidate in enumerate(to_delete, start=1):
            _delete_company_rows(db, candidate.company_id)
            if idx % 100 == 0:
                db.commit()
                print(f"  ...deleted {idx}/{len(to_delete)}")
        db.commit()
        print(f"\nDeleted {len(to_delete)} companies. Report retained at {report_path}.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
