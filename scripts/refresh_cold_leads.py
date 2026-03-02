"""
refresh_cold_leads.py
=====================
Re-signals and re-scores every company currently classified as COLD.

Pipeline per company
--------------------
  1. Classify current tier  (HOT / WARM / COLD)
  2. If COLD → run NewsScraper.run_company_queries([name])
     to pull fresh Google News signals
  3. Re-compute scores with compute_scores() on ALL signals
     (existing + newly fetched)
  4. Write updated Score row back to DB
  5. Re-classify and report tier change

Flags
-----
  --dry-run          Preview which companies are COLD without scraping.
  --industry HOTEL   Filter by partial industry name (case-insensitive).
  --min-score N      Only process companies with overall_intent_score < N
                     (default: 49 — everything below WARM threshold).
  --max-per-company  Max news articles fetched per company (default: 8).
  --limit N          Cap number of cold companies processed (default: all).

Run from repo root:
    python scripts/refresh_cold_leads.py --dry-run
    python scripts/refresh_cold_leads.py
    python scripts/refresh_cold_leads.py --industry hospitality --limit 20
"""

import argparse
import sys
import os
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("refresh_cold_leads")

# Suppress noisy sub-loggers unless debugging
logging.getLogger("app.scrapers.news_scraper").setLevel(logging.WARNING)
logging.getLogger("app.services.inference_engine").setLevel(logging.WARNING)
logging.getLogger("app.services.semantic_parser").setLevel(logging.WARNING)


def main():
    parser = argparse.ArgumentParser(description="Re-signal and re-score COLD leads.")
    parser.add_argument("--dry-run",         action="store_true",
                        help="List cold leads without fetching new signals.")
    parser.add_argument("--industry",        type=str, default=None,
                        help="Partial industry filter, e.g. 'hospitality'.")
    parser.add_argument("--min-score",       type=float, default=49.0,
                        help="Process companies with overall_intent_score below this (default 49).")
    parser.add_argument("--max-per-company", type=int, default=8,
                        help="Max articles fetched per company from Google News (default 8).")
    parser.add_argument("--limit",           type=int, default=0,
                        help="Cap total companies processed (0 = all).")
    args = parser.parse_args()

    from app.database import SessionLocal
    from app.models.company import Company
    from app.models.score import Score
    from app.models.signal import Signal
    from app.services.lead_filter import classify_lead, clean_signals
    from app.services.scoring_engine import compute_scores

    db = SessionLocal()
    try:
        # ── 1. Load all companies with scores and signals ──────────────────────
        from sqlalchemy.orm import joinedload, selectinload
        query = (
            db.query(Company)
            .options(joinedload(Company.scores), selectinload(Company.signals))
        )
        if args.industry:
            query = query.filter(Company.industry.ilike(f"%{args.industry}%"))

        companies = query.all()
        logger.info("Loaded %d companies%s.", len(companies),
                    f" (industry filter: {args.industry})" if args.industry else "")

        # ── 2. Identify COLD leads ─────────────────────────────────────────────
        cold = []
        for c in companies:
            score_val = c.scores.overall_intent_score if c.scores else 0.0
            if score_val >= args.min_score:
                continue
            junk, junk_reason, pri = classify_lead(c, c.scores, c.signals)
            if junk:
                continue
            if pri.tier == "COLD":
                cold.append((c, score_val, pri))

        # Sort coldest first
        cold.sort(key=lambda x: x[1])

        if args.limit:
            cold = cold[:args.limit]

        logger.info("COLD leads identified: %d", len(cold))
        print(f"\n{'='*70}")
        print(f"  COLD leads to refresh: {len(cold)}")
        print(f"{'='*70}")
        for c, sv, pri in cold:
            sigs = clean_signals(c.signals or [])
            print(f"  [{c.id:>4}] {c.name:<45}  score={sv:5.1f}  signals={len(sigs):<3}  industry={c.industry or 'Unknown'}")

        if args.dry_run:
            print(f"\n[DRY RUN] Re-run without --dry-run to fetch new signals and re-score.")
            return

        if not cold:
            print("\nNo cold leads to process. Nothing to do.")
            return

        print(f"\nFetching news signals for {len(cold)} cold leads...\n")

        # ── 3. For each cold lead: fetch signals then re-score ─────────────────
        from app.scrapers.news_scraper import NewsScraper

        results = []
        for idx, (company, old_score, old_pri) in enumerate(cold, start=1):
            name = company.name
            logger.info("[%d/%d] Scraping news for: %s", idx, len(cold), name)
            print(f"  [{idx:>3}/{len(cold)}] {name}")

            # --- fetch new signals ---
            signals_before = db.query(Signal).filter(Signal.company_id == company.id).count()
            try:
                scraper = NewsScraper(db=db)
                scraper.run_company_queries(
                    [name],
                    max_per_company=args.max_per_company,
                )
            except Exception as e:
                logger.warning("  News fetch failed for %s: %s", name, e)

            signals_after = db.query(Signal).filter(Signal.company_id == company.id).count()
            new_signals = signals_after - signals_before

            # --- reload signals from DB (includes newly fetched ones) ---
            db.expire(company)
            db.refresh(company)
            all_sigs = db.query(Signal).filter(Signal.company_id == company.id).all()
            clean_sigs = clean_signals(all_sigs)

            # --- re-score ---
            try:
                scores = compute_scores(company, clean_sigs)
                s = db.query(Score).filter(Score.company_id == company.id).first()
                if not s:
                    s = Score(company_id=company.id, **scores)
                    db.add(s)
                else:
                    for k, v in scores.items():
                        setattr(s, k, v)
                db.commit()
                db.refresh(s)
            except Exception as e:
                db.rollback()
                logger.warning("  Scoring failed for %s: %s", name, e)
                results.append({
                    "company": name, "industry": company.industry,
                    "old_score": old_score, "new_score": old_score,
                    "old_tier": old_pri.tier, "new_tier": "COLD",
                    "new_signals": new_signals, "error": str(e),
                })
                continue

            new_score_val = s.overall_intent_score

            # --- re-classify ---
            _, _, new_pri = classify_lead(company, s, clean_sigs)

            tier_change = (
                f"  {old_pri.tier} → {new_pri.tier}"
                if new_pri.tier != old_pri.tier else f"  {new_pri.tier} (unchanged)"
            )

            flag = ""
            if new_pri.tier == "HOT":
                flag = " *** HOT ***"
            elif new_pri.tier == "WARM":
                flag = " ↑ WARM"

            print(f"         score {old_score:.1f} → {new_score_val:.1f} | "
                  f"+{new_signals} signals |{tier_change}{flag}")

            results.append({
                "company":     name,
                "industry":    company.industry,
                "old_score":   old_score,
                "new_score":   new_score_val,
                "old_tier":    old_pri.tier,
                "new_tier":    new_pri.tier,
                "new_signals": new_signals,
                "error":       None,
            })

        # ── 4. Summary ────────────────────────────────────────────────────────
        promoted_warm = [r for r in results if r["new_tier"] == "WARM"]
        promoted_hot  = [r for r in results if r["new_tier"] == "HOT"]
        still_cold    = [r for r in results if r["new_tier"] == "COLD"]
        errors        = [r for r in results if r["error"]]

        total_new_sigs = sum(r["new_signals"] for r in results)

        print(f"\n{'='*70}")
        print(f"  REFRESH COMPLETE")
        print(f"{'='*70}")
        print(f"  Companies processed : {len(results)}")
        print(f"  New signals fetched : {total_new_sigs}")
        print(f"  Promoted to HOT     : {len(promoted_hot)}")
        print(f"  Promoted to WARM    : {len(promoted_warm)}")
        print(f"  Still COLD          : {len(still_cold)}")
        print(f"  Errors              : {len(errors)}")

        if promoted_hot:
            print(f"\n  *** HOT promotions ***")
            for r in sorted(promoted_hot, key=lambda x: -x["new_score"]):
                print(f"    {r['company']:<45}  score={r['new_score']:.1f}  industry={r['industry']}")

        if promoted_warm:
            print(f"\n  ↑ WARM promotions")
            for r in sorted(promoted_warm, key=lambda x: -x["new_score"]):
                print(f"    {r['company']:<45}  score={r['new_score']:.1f}  industry={r['industry']}")

        if errors:
            print(f"\n  ⚠ Errors")
            for r in errors[:10]:
                print(f"    {r['company']}: {r['error']}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
