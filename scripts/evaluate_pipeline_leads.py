#!/usr/bin/env python3
"""
Evaluate pipeline leads by name + topic relevancy (not RSS source).

Strips HTML, dedupes signal phrases, extracts company names, and scores fit to the
assigned industry. RSS HTML is a quality flag only — never auto-junk by itself.

Default dry-run (CSV report):
  python3 scripts/evaluate_pipeline_leads.py

Apply safe fixes (rename + industry only when confidence is high):
  python3 scripts/evaluate_pipeline_leads.py --apply --yes

Filter examples:
  python3 scripts/evaluate_pipeline_leads.py --disposition review,junk
  python3 scripts/evaluate_pipeline_leads.py --rss-heavy --min-rss 0.6
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

from app.env_loader import database_url_is_template_or_sqlite

_shell_database_url = (os.environ.get("DATABASE_URL") or "").strip()
_root = Path(__file__).resolve().parents[1]
load_dotenv(_root / "frontend" / "nextjs" / ".env.local")
load_dotenv(_root / ".env", override=True)
_eval_dotenv = (os.getenv("DOTENV_PATH") or "").strip()
if _eval_dotenv:
    load_dotenv(Path(_eval_dotenv).expanduser(), override=True)
_loaded_after_dotenv = (os.environ.get("DATABASE_URL") or "").strip()
if _shell_database_url and database_url_is_template_or_sqlite(_loaded_after_dotenv):
    os.environ["DATABASE_URL"] = _shell_database_url

from sqlalchemy.orm import joinedload

from app.database import SessionLocal
from app.models.company import Company
from app.services.lead_relevance_evaluator import (
    _rename_is_safe,
    evaluate_lead_relevance,
)
from app.services.lead_relevance_evaluator import ExtractedName


def _build_db_lookup(db) -> dict:
    """Lowercase name → (canonical name, industry) for article extraction."""
    lookup: dict = {}
    for row in db.query(Company.name, Company.industry).all():
        name = (row.name or "").strip()
        if not name:
            continue
        key = name.lower()
        lookup[key] = (name, row.industry or "Unknown")
    return lookup


def _report_path(arg_path: str) -> Path:
    if arg_path:
        return Path(arg_path)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return _root / "reports" / f"lead_relevance_eval_{ts}.csv"


def _write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "company_id",
        "stored_name",
        "stored_industry",
        "suggested_name",
        "effective_industry",
        "industry_from_name",
        "industry_from_text",
        "topic_relevance_score",
        "industry_alignment_score",
        "buyer_intent_score",
        "rss_html_ratio",
        "deduped_phrase_count",
        "deduped_word_count",
        "top_extracted_name",
        "top_extracted_source",
        "top_extracted_confidence",
        "disposition",
        "disposition_reason",
        "evidence",
        "clean_text_preview",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow(row)


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate leads by name + topic fit")
    parser.add_argument("--apply", action="store_true", help="Apply rename / industry fixes")
    parser.add_argument("--yes", action="store_true", help="Required with --apply")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--report", default="", help="CSV output path")
    parser.add_argument(
        "--disposition",
        default="",
        help="Comma-separated filter: keep,enrich,rename,review,junk",
    )
    parser.add_argument(
        "--rss-heavy",
        action="store_true",
        help="Only rows where rss_html_ratio >= --min-rss",
    )
    parser.add_argument("--min-rss", type=float, default=0.6)
    parser.add_argument("--min-topic", type=float, default=None, help="Min topic_relevance_score")
    args = parser.parse_args()

    if args.apply and not args.yes:
        parser.error("--apply requires --yes")

    filter_dispositions = {
        x.strip().lower()
        for x in (args.disposition or "").split(",")
        if x.strip()
    }

    db = SessionLocal()
    csv_rows: list[dict] = []
    applied_renames = 0
    applied_industry = 0

    try:
        lookup = _build_db_lookup(db)
        q = (
            db.query(Company)
            .options(joinedload(Company.signals))
            .order_by(Company.id)
        )
        if args.limit:
            q = q.limit(args.limit)
        companies = q.all()
        print(f"Evaluating {len(companies)} companies...")

        for company in companies:
            report = evaluate_lead_relevance(company, company.signals or [], db_lookup=lookup)

            if filter_dispositions and report.disposition not in filter_dispositions:
                continue
            if args.rss_heavy and report.rss_html_ratio < args.min_rss:
                continue
            if args.min_topic is not None and report.topic_relevance_score < args.min_topic:
                continue

            top = report.extracted_names[0] if report.extracted_names else None
            csv_rows.append(
                {
                    "company_id": report.company_id,
                    "stored_name": report.stored_name,
                    "stored_industry": report.stored_industry,
                    "suggested_name": report.suggested_name or "",
                    "effective_industry": report.effective_industry,
                    "industry_from_name": report.industry_from_name or "",
                    "industry_from_text": report.industry_from_text,
                    "topic_relevance_score": report.topic_relevance_score,
                    "industry_alignment_score": report.industry_alignment_score,
                    "buyer_intent_score": report.buyer_intent_score,
                    "rss_html_ratio": report.rss_html_ratio,
                    "deduped_phrase_count": len(report.deduped_phrases),
                    "deduped_word_count": report.deduped_word_count,
                    "top_extracted_name": top.name if top else "",
                    "top_extracted_source": top.source if top else "",
                    "top_extracted_confidence": f"{top.confidence:.2f}" if top else "",
                    "disposition": report.disposition,
                    "disposition_reason": report.disposition_reason,
                    "evidence": "; ".join(report.evidence),
                    "clean_text_preview": (report.clean_text_blob or "")[:240],
                }
            )

            if not args.apply:
                continue

            if report.suggested_name and report.disposition in ("rename", "enrich", "keep"):
                top = report.extracted_names[0] if report.extracted_names else None
                if top and _rename_is_safe(company.name, top):
                    company.name = report.suggested_name
                    applied_renames += 1

            stored_low = (company.industry or "").strip().lower()
            if stored_low in ("", "unknown", "new", "other"):
                if report.effective_industry and report.effective_industry not in (
                    "Unknown",
                    "New",
                ):
                    if report.topic_relevance_score >= 0.35 or report.industry_from_name:
                        company.industry = report.effective_industry
                        applied_industry += 1

        report_path = _report_path(args.report)
        _write_csv(report_path, csv_rows)

        by_disp = Counter(r["disposition"] for r in csv_rows)
        print(f"Wrote {len(csv_rows)} rows → {report_path}")
        print("Disposition breakdown:", dict(by_disp))
        rss_kept = sum(
            1
            for r in csv_rows
            if float(r["rss_html_ratio"]) >= 0.6 and r["disposition"] in ("keep", "enrich", "rename")
        )
        if rss_kept:
            print(f"RSS-heavy but kept/enrich/rename: {rss_kept}")

        if args.apply:
            db.commit()
            print(f"Applied renames: {applied_renames}, industry updates: {applied_industry}")
        else:
            print("Dry run — pass --apply --yes to apply rename/industry fixes")

    finally:
        db.close()


if __name__ == "__main__":
    main()
