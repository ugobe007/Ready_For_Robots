"""
Deduplicate company rows by exact name (case-insensitive).

For each group of duplicates, keep the row with the most signals (or highest
score, or earliest created_at as tiebreaker), then re-point all signals/scores
from the loser rows to the winner and delete the losers.

Usage:
    python3 scripts/dedup_companies.py           # dry run
    python3 scripts/dedup_companies.py --apply   # write changes
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import func, text
from app.database import SessionLocal
from app.models.company import Company
from app.models.signal import Signal
from app.models.score import Score


def main(apply: bool) -> None:
    db = SessionLocal()
    try:
        # Find all names that appear more than once (case-insensitive)
        dup_names = (
            db.query(func.lower(Company.name).label("lname"), func.count(Company.id).label("cnt"))
            .group_by(func.lower(Company.name))
            .having(func.count(Company.id) > 1)
            .all()
        )

        print(f"Found {len(dup_names)} duplicate name groups.")
        total_deleted = 0
        total_signals_repointed = 0

        for row in dup_names:
            lname = row.lname
            # Get all rows for this name, ordered by signal count desc, then score desc
            companies = (
                db.query(Company)
                .filter(func.lower(Company.name) == lname)
                .all()
            )

            # Rank: most signals → highest score → earliest id
            def rank(c: Company) -> tuple:
                sig_count = db.query(func.count(Signal.id)).filter(Signal.company_id == c.id).scalar() or 0
                score_row = db.query(func.max(Score.overall_intent_score)).filter(Score.company_id == c.id).scalar()
                score = score_row or 0.0
                return (-sig_count, -score, c.id)

            companies.sort(key=rank)
            winner = companies[0]
            losers = companies[1:]

            winner_sigs = db.query(func.count(Signal.id)).filter(Signal.company_id == winner.id).scalar() or 0
            print(f"\n  KEEP  id={winner.id:6d} signals={winner_sigs:4d}  {winner.name!r}")

            for loser in losers:
                loser_sigs = db.query(func.count(Signal.id)).filter(Signal.company_id == loser.id).scalar() or 0
                print(f"  DROP  id={loser.id:6d} signals={loser_sigs:4d}  {loser.name!r}")

                total_deleted += 1
                if apply:
                    # Re-point signals — skip duplicates of signal_text already on winner
                    winner_texts = {
                        t for (t,) in db.query(Signal.signal_text)
                        .filter(Signal.company_id == winner.id).all()
                    }
                    loser_signals = db.query(Signal).filter(Signal.company_id == loser.id).all()
                    for sig in loser_signals:
                        if sig.signal_text not in winner_texts:
                            sig.company_id = winner.id
                            winner_texts.add(sig.signal_text)
                            total_signals_repointed += 1
                        else:
                            db.delete(sig)

                    # Delete loser scores then company
                    db.query(Score).filter(Score.company_id == loser.id).delete()
                    db.delete(loser)

        if apply:
            db.commit()
            print(f"\n✓ Deleted {total_deleted} duplicate companies.")
            print(f"✓ Re-pointed {total_signals_repointed} signals to canonical rows.")
        else:
            print(f"\nDry run — {total_deleted} companies would be deleted.")
            print("Run with --apply to commit changes.")

    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    main(apply=args.apply)
