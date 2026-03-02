"""
Scheduled scraper job functions
================================
Extracted here so they can be imported by both:
  - app/main.py (APScheduler lifespan)
  - app/api/admin.py (manual trigger endpoint)

All functions are synchronous — safe to call from FastAPI BackgroundTasks
or directly from an APScheduler job.
"""

import logging
from app.database import SessionLocal
from app.scrapers.scraper_watchdog import get_watchdog

logger = logging.getLogger(__name__)


def _db():
    return SessionLocal()


def job_news():
    from app.scrapers.news_scraper import NewsScraper
    from app.scrapers.scrape_targets import get_news_queries
    db = _db()
    queries = get_news_queries()
    try:
        with get_watchdog().track("news") as run:
            run.urls_attempted = len(queries)
            scraper = NewsScraper(db=db)
            scraper.run_intent_queries(queries=queries)
            run.urls_succeeded = getattr(scraper, "_leads_added", run.urls_attempted)
    except Exception as e:
        logger.error("[scheduler] news scraper error: %s", e)
    finally:
        db.close()


def job_rss():
    from app.scrapers.news_scraper import NewsScraper
    from app.scrapers.scrape_targets import get_urls
    db = _db()
    urls = get_urls("rss_feed")
    try:
        with get_watchdog().track("rss") as run:
            run.urls_attempted = len(urls)
            scraper = NewsScraper(db=db)
            scraper.run_rss_feeds(urls)
            run.urls_succeeded = getattr(scraper, "_leads_added", run.urls_attempted)
    except Exception as e:
        logger.error("[scheduler] rss scraper error: %s", e)
    finally:
        db.close()


def job_jobs():
    from app.scrapers.job_board_scraper import JobBoardScraper
    from app.scrapers.scrape_targets import get_urls
    db = _db()
    urls = get_urls("job_board")
    try:
        with get_watchdog().track("job_board") as run:
            run.urls_attempted = len(urls)
            scraper = JobBoardScraper(db=db)
            scraper.run(urls)
            run.urls_succeeded = getattr(scraper, "_leads_added", run.urls_attempted)
    except Exception as e:
        logger.error("[scheduler] job board scraper error: %s", e)
    finally:
        db.close()


def job_hotel():
    from app.scrapers.hotel_directory_scraper import HotelDirectoryScraper
    from app.scrapers.scrape_targets import get_urls
    db = _db()
    urls = get_urls("hotel_dir")
    try:
        with get_watchdog().track("hotel") as run:
            run.urls_attempted = len(urls)
            scraper = HotelDirectoryScraper(db=db)
            scraper.run(urls)
            run.urls_succeeded = getattr(scraper, "_leads_added", run.urls_attempted)
    except Exception as e:
        logger.error("[scheduler] hotel scraper error: %s", e)
    finally:
        db.close()


def job_serp():
    from app.scrapers.serp_scraper import SerpScraper, EXPANSION_QUERIES
    db = _db()
    try:
        with get_watchdog().track("serp") as run:
            run.urls_attempted = len(EXPANSION_QUERIES)
            scraper = SerpScraper(db=db)
            scraper.run(queries=EXPANSION_QUERIES)
            run.urls_succeeded = getattr(scraper, "_leads_added", run.urls_attempted)
    except Exception as e:
        logger.error("[scheduler] serp scraper error: %s", e)
    finally:
        db.close()


def job_logistics():
    from app.scrapers.logistics_directory_scraper import LogisticsDirectoryScraper, LOGISTICS_COMPANY_QUERIES
    db = _db()
    try:
        with get_watchdog().track("logistics") as run:
            run.urls_attempted = len(LOGISTICS_COMPANY_QUERIES)
            scraper = LogisticsDirectoryScraper(db=db)
            scraper.run(queries=LOGISTICS_COMPANY_QUERIES)
            run.urls_succeeded = getattr(scraper, "_leads_added", run.urls_attempted)
    except Exception as e:
        logger.error("[scheduler] logistics scraper error: %s", e)
    finally:
        db.close()


def job_score_recalc():
    from app.models.company import Company
    from app.models.score import Score
    from app.services.scoring_engine import compute_scores
    db = _db()
    try:
        with get_watchdog().track("score_recalc") as run:
            companies = db.query(Company).all()
            run.urls_attempted = len(companies)
            updated = 0
            for company in companies:
                try:
                    scores = compute_scores(company, company.signals or [])
                    s = db.query(Score).filter(Score.company_id == company.id).first()
                    if not s:
                        s = Score(company_id=company.id, **scores)
                        db.add(s)
                    else:
                        for k, v in scores.items():
                            setattr(s, k, v)
                    db.commit()  # commit per-company so one bad row can't roll back the batch
                    updated += 1
                except Exception as ex:
                    db.rollback()
                    run.errors.append(f"company {company.id}: {ex}")
                    logger.warning("[scheduler] score skip company %d: %s", company.id, ex)
            run.urls_succeeded = updated
            logger.info("[scheduler] score recalc done — %d companies", updated)
    except Exception as e:
        logger.error("[scheduler] score recalc error: %s", e)
    finally:
        db.close()


def job_intelligence():
    from app.scrapers.intelligence_scraper import run_intelligence_scraper
    try:
        result = run_intelligence_scraper()
        logger.info("[scheduler] intelligence scraper done: %s", result)
    except Exception as e:
        logger.error("[scheduler] intelligence scraper error: %s", e)


def job_refresh_cold_leads(min_score: float = 49.0, max_per_company: int = 8, limit: int = 0):
    """
    Re-fetch news signals for COLD companies, then re-score them.
    Promoted leads surface in the next /api/leads response automatically.
    """
    from app.models.company import Company
    from app.models.score import Score
    from app.models.signal import Signal
    from app.services.lead_filter import classify_lead, clean_signals
    from app.services.scoring_engine import compute_scores
    from app.scrapers.news_scraper import NewsScraper
    from sqlalchemy.orm import joinedload, selectinload

    db = _db()
    try:
        companies = (
            db.query(Company)
            .options(joinedload(Company.scores), selectinload(Company.signals))
            .all()
        )

        cold = []
        for c in companies:
            score_val = c.scores.overall_intent_score if c.scores else 0.0
            if score_val >= min_score:
                continue
            junk, _, pri = classify_lead(c, c.scores, c.signals)
            if not junk and pri.tier == "COLD":
                cold.append(c)

        if limit:
            cold = cold[:limit]

        logger.info("[scheduler] refresh_cold_leads — %d COLD companies to re-signal", len(cold))

        promoted = 0
        for company in cold:
            try:
                scraper = NewsScraper(db=db)
                scraper.run_company_queries([company.name], max_per_company=max_per_company)

                db.expire(company)
                db.refresh(company)
                all_sigs = db.query(Signal).filter(Signal.company_id == company.id).all()
                clean = clean_signals(all_sigs)

                scores = compute_scores(company, clean)
                s = db.query(Score).filter(Score.company_id == company.id).first()
                if not s:
                    s = Score(company_id=company.id, **scores)
                    db.add(s)
                else:
                    for k, v in scores.items():
                        setattr(s, k, v)
                db.commit()

                _, _, new_pri = classify_lead(company, s, clean)
                if new_pri.tier != "COLD":
                    promoted += 1
                    logger.info("  PROMOTED: %s → %s (%.1f)", company.name, new_pri.tier,
                                scores["overall_intent_score"])
            except Exception as ex:
                db.rollback()
                logger.warning("[scheduler] refresh skip %s: %s", company.name, ex)

        logger.info("[scheduler] refresh_cold_leads done — %d promoted out of %d", promoted, len(cold))

    except Exception as e:
        logger.error("[scheduler] refresh_cold_leads error: %s", e)
    finally:
        db.close()


def job_publish_daily_top25():
    """
    Publish the daily top-25 robot opportunity brief.

    Steps
    -----
    1. Score all companies and pick the top 25 HOT leads.
    2. Run contact discovery on each company (ContactScraper).
    3. Attach found contacts to each opportunity.
    4. Snapshot the result into the `daily_reports` table.
    5. Log a summary.

    Runs at 07:00 UTC every weekday (configured in main.py).
    Can also be triggered manually via POST /api/admin/scrape/trigger
    with {"scraper": "publish_daily_top25"}.
    """
    from datetime import date as dt_date, datetime, timezone
    from sqlalchemy.orm import joinedload, selectinload

    from app.models.company import Company
    from app.models.contact import Contact
    from app.models.daily_report import DailyReport
    from app.scrapers.contact_scraper import ContactScraper
    from app.services.lead_filter import classify_lead
    from app.services.signal_ranker import compute_weighted_score
    from app.api.strategy import (
        ROBOT_MAP, _DEFAULT_ROBOT, CONTACT_MAP, _DEFAULT_CONTACT,
        SIGNAL_TIMING, _DEFAULT_TIMING, _pitch, _deal_tier, _talking_points,
    )

    db = _db()
    try:
        today = dt_date.today()
        logger.info("[daily_top25] generating report for %s", today)

        # ── 1. Load & rank companies ─────────────────────────────────────
        companies = (
            db.query(Company)
            .options(joinedload(Company.scores), selectinload(Company.signals))
            .limit(2000)
            .all()
        )

        ranked = []
        for c in companies:
            junk, _, pri = classify_lead(c, c.scores, c.signals)
            if junk:
                continue
            ranked.append((pri, c))

        tier_order = {"HOT": 0, "WARM": 1, "COLD": 2}
        ranked.sort(key=lambda x: (tier_order.get(x[0].tier, 3), -x[0].score))
        top25_pairs = ranked[:25]

        # ── 2. Run contact discovery ─────────────────────────────────────
        logger.info("[daily_top25] running contact discovery for %d companies", len(top25_pairs))
        scraper = ContactScraper(db, delay=1.0)
        for _, company in top25_pairs:
            try:
                scraper.run_company(company)
            except Exception as e:
                logger.warning("[daily_top25] contact discovery failed for %s: %s", company.name, e)

        # ── 3. Build opportunity objects ────────────────────────────────
        opportunities = []
        contacts_found_total = 0

        for pri, c in top25_pairs:
            db.expire(c)
            db.refresh(c)
            s = c.scores
            sigs = sorted(c.signals or [], key=lambda x: x.signal_strength, reverse=True)

            industry = (c.industry or "").strip()
            rmap = ROBOT_MAP.get(industry, _DEFAULT_ROBOT)
            primary_robot = rmap["primary"]
            top_sig_type = sigs[0].signal_type if sigs else "news"

            fmt_signals = [
                {
                    "signal_type":    sig.signal_type,
                    "strength":       sig.signal_strength,
                    "weighted_score": compute_weighted_score(sig),
                    "raw_text":       sig.signal_text,
                    "source_url":     sig.source_url,
                }
                for sig in sigs
            ]

            deal    = _deal_tier(c.employee_estimate)
            contact = CONTACT_MAP.get(industry, _DEFAULT_CONTACT)
            timing  = SIGNAL_TIMING.get(top_sig_type, _DEFAULT_TIMING)
            pitch   = _pitch(industry, top_sig_type, primary_robot)
            talking = _talking_points(industry, pri.reasons, fmt_signals, primary_robot)

            # Load contacts saved in step 2
            db_contacts = (
                db.query(Contact)
                .filter(Contact.company_id == c.id)
                .order_by(Contact.confidence_score.desc())
                .all()
            )
            contacts_found_total += len(db_contacts)
            contacts_out = [
                {
                    "name":       f"{ct.first_name} {ct.last_name}".strip(),
                    "title":      ct.title or contact,
                    "linkedin":   ct.linkedin_url,
                    "email":      ct.email,
                    "confidence": ct.confidence_score,
                }
                for ct in db_contacts
            ]

            # HOT qualification (if available)
            hot_qual = None
            if pri.tier == "HOT":
                from app.services.lead_filter import qualify_hot_lead
                hq = qualify_hot_lead(c.signals or [])
                hot_qual = {
                    "buying_window":       hq.buying_window,
                    "intent_confidence":   hq.intent_confidence,
                    "recommended_action":  hq.recommended_action,
                    "window_evidence":     hq.window_evidence,
                    "confidence_drivers":  hq.confidence_drivers,
                    "freshest_signal_days": hq.freshest_signal_days,
                }

            opportunities.append({
                "id":               c.id,
                "company_name":     c.name,
                "website":          c.website,
                "industry":         industry,
                "location_city":    c.location_city,
                "location_state":   c.location_state,
                "employee_estimate": c.employee_estimate,
                "priority_tier":    pri.tier,
                "priority_score":   round(pri.score, 1),
                "priority_reasons": pri.reasons,
                "score": {
                    "overall_score":    round((s.overall_intent_score if s else 0), 1),
                    "automation_score": round((s.automation_score     if s else 0), 1),
                    "labor_pain_score": round((s.labor_pain_score     if s else 0), 1),
                    "expansion_score":  round((s.expansion_score      if s else 0), 1),
                    "market_fit_score": round((s.robotics_fit_score   if s else 0), 1),
                },
                "signal_count":    len(sigs),
                "signals":         fmt_signals,
                "contacts":        contacts_out,
                "hot_qualification": hot_qual,
                "strategy": {
                    "robots":          rmap["robots"],
                    "primary_robot":   primary_robot,
                    "use_case":        rmap["use_case"],
                    "contact_role":    contact,
                    "outreach_timing": timing,
                    "pitch_angle":     pitch,
                    "talking_points":  talking,
                    "deal_tier":       deal["tier"],
                    "deal_est_units":  deal["est_units"],
                },
            })

        # ── 4. Snapshot to DB ────────────────────────────────────────────
        report_data = {
            "report_date":        today.isoformat(),
            "generated_at":       datetime.now(timezone.utc).isoformat(),
            "opportunity_count":  len(opportunities),
            "contacts_found":     contacts_found_total,
            "opportunities":      opportunities,
        }

        existing = db.query(DailyReport).filter(DailyReport.report_date == today).first()
        if existing:
            existing.set_data(report_data)
            existing.contacts_found = contacts_found_total
            existing.generated_at   = datetime.now(timezone.utc)
        else:
            rec = DailyReport(
                report_date=today,
                contacts_found=contacts_found_total,
            )
            rec.set_data(report_data)
            db.add(rec)

        db.commit()

        logger.info(
            "[daily_top25] published %d opportunities, %d contacts — %s",
            len(opportunities), contacts_found_total, today,
        )

    except Exception as e:
        logger.error("[daily_top25] error: %s", e, exc_info=True)
        db.rollback()
    finally:
        db.close()


def job_enrich_contacts():
    """Run contact discovery for the current top-25 list (no publishing)."""
    from app.scrapers.contact_scraper import ContactScraper
    db = _db()
    try:
        scraper = ContactScraper(db)
        total = scraper.run_top25()
        logger.info("[scheduler] enrich_contacts — %d contacts saved", total)
    except Exception as e:
        logger.error("[scheduler] enrich_contacts error: %s", e)
    finally:
        db.close()


def job_all():
    """Run all scrapers sequentially."""
    job_news()
    job_rss()
    job_jobs()
    job_hotel()
    job_serp()
    job_logistics()
    job_score_recalc()
    job_intelligence()
