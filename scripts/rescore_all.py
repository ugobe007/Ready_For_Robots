#!/usr/bin/env python3
"""
rescore_all.py
==============
Re-scores every company in the database using the current ontology
(CONCEPTS, RELATIONSHIPS, INFERENCE_RULES) from app/services/ontology.py.

Writes updated rows to the `scores` table.  Safe to run multiple times.

Usage:
    python3 scripts/rescore_all.py [--batch-size 200] [--dry-run]
"""
import sys
import os
import argparse
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ── Fast-mode patch: disable expensive fuzzy synonym sliding-window ──────────
# The fuzzy path (SequenceMatcher over every word window) is O(concepts×synonyms×words)
# and makes rescoring ~100× slower with no meaningful accuracy benefit because the
# important synonyms are already covered by the regex patterns above them.
# Direct substring matches still run; only the fuzzy window scan is disabled.
import app.services.semantic_parser as _sp_module
_sp_module.SemanticParser.SYNONYM_THRESHOLD = 2.0   # impossible threshold → no fuzzy hits
# ─────────────────────────────────────────────────────────────────────────────

from app.database import SessionLocal
from app.models.company import Company
from app.models.signal import Signal
from app.models.score import Score
from app.services.scoring_engine import compute_scores
from datetime import datetime, timezone

# ── New rules/concepts loaded since last score run ──────────────────────────
from app.services.ontology import CONCEPTS, RELATIONSHIPS, INFERENCE_RULES
print(f"Ontology loaded: {len(CONCEPTS)} concepts | "
      f"{len(RELATIONSHIPS)} relationships | "
      f"{len(INFERENCE_RULES)} inference rules")


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--batch-size", type=int, default=200,
                   help="Companies to process per DB transaction (default: 200)")
    p.add_argument("--dry-run", action="store_true",
                   help="Compute scores but do NOT write to database")
    p.add_argument("--min-score-delta", type=float, default=0.5,
                   help="Only update rows where overall_intent_score changed by >= N points")
    return p.parse_args()


def rescore(batch_size: int, dry_run: bool, min_delta: float):
    db = SessionLocal()
    try:
        total_companies = db.query(Company).count()
        print(f"\nTotal companies to score: {total_companies:,}")
        if dry_run:
            print("** DRY RUN — no DB writes **\n")

        updated = 0
        skipped_no_change = 0
        skipped_no_signals = 0
        errors = 0
        offset = 0
        t_start = time.time()

        while offset < total_companies:
            # Fetch companies batch
            companies = (
                db.query(Company)
                .order_by(Company.id)
                .offset(offset)
                .limit(batch_size)
                .all()
            )
            if not companies:
                break

            company_ids = [c.id for c in companies]

            # Bulk-fetch signals for this batch in ONE query
            all_signals = (
                db.query(Signal)
                .filter(Signal.company_id.in_(company_ids))
                .all()
            )
            signals_by_company: dict = {}
            for s in all_signals:
                signals_by_company.setdefault(s.company_id, []).append(s)

            # Bulk-fetch existing score rows in ONE query
            existing_scores = (
                db.query(Score)
                .filter(Score.company_id.in_(company_ids))
                .all()
            )
            scores_by_company = {s.company_id: s for s in existing_scores}

            new_score_rows = []

            for company in companies:
                try:
                    signals = signals_by_company.get(company.id, [])

                    if not signals:
                        skipped_no_signals += 1
                        continue

                    new_scores = compute_scores(company, signals)

                    score_row = scores_by_company.get(company.id)
                    old_overall = (score_row.overall_intent_score if score_row else None)
                    new_overall = new_scores["overall_intent_score"]

                    if old_overall is not None:
                        delta = abs(new_overall - old_overall)
                        if delta < min_delta:
                            skipped_no_change += 1
                            continue

                    if not dry_run:
                        if score_row:
                            score_row.automation_score     = new_scores["automation_score"]
                            score_row.labor_pain_score     = new_scores["labor_pain_score"]
                            score_row.expansion_score      = new_scores["expansion_score"]
                            score_row.robotics_fit_score   = new_scores["robotics_fit_score"]
                            score_row.overall_intent_score = new_scores["overall_intent_score"]
                            score_row.last_calculated_at   = datetime.now(timezone.utc)
                        else:
                            new_score_rows.append(Score(
                                company_id=company.id,
                                **new_scores,
                                last_calculated_at=datetime.now(timezone.utc),
                            ))

                    updated += 1

                except Exception as e:
                    errors += 1
                    print(f"  ERROR on company {company.id} ({company.name!r}): {e}")
                    continue

            if not dry_run:
                if new_score_rows:
                    db.add_all(new_score_rows)
                db.commit()

            offset += batch_size
            elapsed = time.time() - t_start
            pct = min(offset / total_companies * 100, 100)
            print(f"  [{pct:5.1f}%] processed {min(offset, total_companies):,}/{total_companies:,} "
                  f"| updated={updated:,} skipped_unchanged={skipped_no_change:,} "
                  f"no_signals={skipped_no_signals:,} errors={errors} "
                  f"| {elapsed:.1f}s elapsed")

        elapsed_total = time.time() - t_start
        print(f"\n{'='*60}")
        print(f"RESCORE COMPLETE  ({elapsed_total:.1f}s)")
        print(f"  Updated:              {updated:,}")
        print(f"  Skipped (no change):  {skipped_no_change:,}")
        print(f"  Skipped (no signals): {skipped_no_signals:,}")
        print(f"  Errors:               {errors}")
        if dry_run:
            print("  ** DRY RUN — nothing written to DB **")

    finally:
        db.close()


if __name__ == "__main__":
    args = parse_args()
    rescore(
        batch_size=args.batch_size,
        dry_run=args.dry_run,
        min_delta=args.min_score_delta,
    )
