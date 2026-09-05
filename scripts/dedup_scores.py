"""
Collapse duplicate Score rows per company: keep the highest-scoring row, delete the rest.

Usage:
    python3 scripts/dedup_scores.py           # dry run
    python3 scripts/dedup_scores.py --apply
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import func
from app.database import SessionLocal
from app.models.company import Company
from app.models.score import Score


def main(apply: bool) -> None:
    db = SessionLocal()
    try:
        dupes = (
            db.query(Score.company_id, func.count(Score.id).label("cnt"))
            .group_by(Score.company_id)
            .having(func.count(Score.id) > 1)
            .all()
        )
        print(f"Companies with multiple score rows: {len(dupes)}")
        deleted = 0
        for row in dupes:
            cid = row.company_id
            scores = db.query(Score).filter(Score.company_id == cid).order_by(Score.overall_intent_score.desc()).all()
            winner = scores[0]
            losers = scores[1:]
            name = db.query(Company.name).filter(Company.id == cid).scalar()
            print(f"  KEEP  id={winner.id} score={winner.overall_intent_score:.1f}  {name!r}")
            for loser in losers:
                print(f"  DROP  id={loser.id} score={loser.overall_intent_score:.1f}")
                deleted += 1
                if apply:
                    db.delete(loser)

        if apply:
            db.commit()
            print(f"\n✓ Deleted {deleted} duplicate score rows.")
        else:
            print(f"\nDry run — {deleted} score rows would be deleted.")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    main(apply=args.apply)
