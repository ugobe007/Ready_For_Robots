#!/usr/bin/env python3
"""
Recompute ML scores for every company and upsert the `scores` table.

When to run
-----------
- After you change the **inference / scoring_engine** logic, OR you want fresh
  `overall_intent_score` (and related columns) from current signals.

When you do **not** need this
-----------------------------
- **Hot / Warm / Emerging tiers** (`lead_filter.priority_tier`) are computed on
  each API request from DB score + live signals. Changing thresholds in
  `lead_filter.py` applies on the next HTTP request — no script.
- **Per-signal `weighted_score`** (`signal_ranker`) is computed per request — no script.

Usage (macOS Terminal)
----------------------
  cd /Users/leguplabs/Desktop/Ready_For_Robots
  source venv/bin/activate
  python3 scripts/recalculate_all_scores.py

Requires `.env` with `DATABASE_URL` (or defaults to SQLite `ready_for_robots.db` in cwd).
"""
from __future__ import annotations

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

if __name__ == "__main__":
    try:
        from dotenv import load_dotenv

        load_dotenv(os.path.join(PROJECT_ROOT, ".env"))
    except ImportError:
        pass

    from sqlalchemy.orm import joinedload

    from app.database import SessionLocal
    from app.models.company import Company
    from app.models.score import Score
    from app.services.scoring_engine import compute_scores

    db = SessionLocal()
    updated = 0
    errors = 0
    try:
        companies = db.query(Company).options(joinedload(Company.signals)).all()
        total = len(companies)
        for i, company in enumerate(companies, start=1):
            try:
                scores = compute_scores(company, company.signals or [])
                s = db.query(Score).filter(Score.company_id == company.id).first()
                if not s:
                    s = Score(company_id=company.id, **scores)
                    db.add(s)
                else:
                    for k, v in scores.items():
                        setattr(s, k, v)
                updated += 1
                if i % 200 == 0 or i == total:
                    print(f"  processed {i}/{total} companies…", flush=True)
            except Exception as e:
                errors += 1
                print(f"  skip company_id={company.id}: {e}", file=sys.stderr)
        db.commit()
        print(f"Done. Updated scores for {updated} companies ({errors} skipped).")
    finally:
        db.close()
