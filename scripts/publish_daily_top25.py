#!/usr/bin/env python
"""
Publish Daily Top-25 Robot Opportunities
=========================================
Generates and stores today's top-25 sales brief with contact discovery.

Usage
-----
  python scripts/publish_daily_top25.py              # run and publish
  python scripts/publish_daily_top25.py --dry-run    # run but don't write to DB
  python scripts/publish_daily_top25.py --print      # pretty-print each opportunity

Scheduled automatically at 07:30 UTC daily via APScheduler (main.py).
Can also be triggered via: POST /api/admin/scrape/trigger {"scraper":"publish_daily_top25"}
"""

import sys
import os
import argparse

# Force UTF-8 output on Windows terminals to avoid charmap encode errors
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# ── path bootstrap ────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Publish daily top-25 robot opportunities")
    parser.add_argument("--dry-run", action="store_true", help="Discover contacts but don't write daily report to DB")
    parser.add_argument("--print",   action="store_true", help="Pretty-print each opportunity to stdout")
    parser.add_argument("--no-contacts", action="store_true", help="Skip contact discovery (faster, for testing)")
    args = parser.parse_args()

    from datetime import date as dt_date, datetime, timezone
    from sqlalchemy.orm import joinedload, selectinload

    from app.database import SessionLocal, engine, Base
    import app.models  # ensure all models are registered
    Base.metadata.create_all(bind=engine)

    from app.models.company import Company
    from app.models.contact import Contact
    from app.models.daily_report import DailyReport
    from app.services.lead_filter import classify_lead, qualify_hot_lead
    from app.services.signal_ranker import compute_weighted_score
    from app.api.strategy import (
        ROBOT_MAP, _DEFAULT_ROBOT, CONTACT_MAP, _DEFAULT_CONTACT,
        SIGNAL_TIMING, _DEFAULT_TIMING, _pitch, _deal_tier, _talking_points,
    )

    db = SessionLocal()
    today = dt_date.today()

    try:
        logger.info("=" * 64)
        logger.info("DAILY TOP-25 ROBOT OPPORTUNITIES  —  %s", today)
        logger.info("=" * 64)

        # ── Load & rank ──────────────────────────────────────────────────
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

        logger.info("Total eligible companies: %d  -> selecting top %d", len(ranked), len(top25_pairs))

        # ── Contact discovery ────────────────────────────────────────────
        if not args.no_contacts:
            from app.scrapers.contact_scraper import ContactScraper
            scraper = ContactScraper(db, delay=1.2)
            for pri, company in top25_pairs:
                try:
                    results = scraper.run_company(company)
                    logger.info("  [contacts] %-45s -> %d contacts", company.name[:45], len(results))
                except Exception as e:
                    logger.warning("  [contacts] SKIP %s: %s", company.name, e)
        else:
            logger.info("Skipping contact discovery (--no-contacts)")

        # ── Build output ─────────────────────────────────────────────────
        opportunities = []
        contacts_found_total = 0

        for rank, (pri, c) in enumerate(top25_pairs, start=1):
            db.expire(c)
            db.refresh(c)
            s = c.scores
            sigs = sorted(c.signals or [], key=lambda x: x.signal_strength, reverse=True)

            industry      = (c.industry or "").strip()
            rmap          = ROBOT_MAP.get(industry, _DEFAULT_ROBOT)
            primary_robot = rmap["primary"]
            top_sig_type  = sigs[0].signal_type if sigs else "news"

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

            hot_qual = None
            if pri.tier == "HOT":
                hq = qualify_hot_lead(c.signals or [])
                hot_qual = {
                    "buying_window":       hq.buying_window,
                    "intent_confidence":   hq.intent_confidence,
                    "recommended_action":  hq.recommended_action,
                    "window_evidence":     hq.window_evidence,
                    "confidence_drivers":  hq.confidence_drivers,
                }

            opp = {
                "rank":           rank,
                "id":             c.id,
                "company_name":   c.name,
                "website":        c.website,
                "industry":       industry,
                "location":       f"{c.location_city or ''}, {c.location_state or ''}".strip(", "),
                "priority_tier":  pri.tier,
                "priority_score": round(pri.score, 1),
                "score": {
                    "overall":    round((s.overall_intent_score if s else 0), 1),
                    "automation": round((s.automation_score     if s else 0), 1),
                    "labor_pain": round((s.labor_pain_score     if s else 0), 1),
                },
                "signal_count":    len(sigs),
                "signals":         fmt_signals,
                "contacts":        contacts_out,
                "hot_qualification": hot_qual,
                "strategy": {
                    "primary_robot":   primary_robot,
                    "robots":          rmap["robots"],
                    "use_case":        rmap["use_case"],
                    "contact_role":    contact,
                    "outreach_timing": timing,
                    "pitch_angle":     pitch,
                    "talking_points":  talking,
                    "deal_tier":       deal["tier"],
                    "deal_est_units":  deal["est_units"],
                },
            }
            opportunities.append(opp)

            if args.print:
                _pretty_print(rank, opp)

        # ── Print summary ────────────────────────────────────────────────
        logger.info("")
        logger.info("SUMMARY  —  %d opportunities  |  %d contacts found", len(opportunities), contacts_found_total)
        logger.info("")
        for o in opportunities:
            contact_str = ""
            cts = o.get("contacts", [])
            verified_ct = next((c for c in cts if (c.get("confidence") or 0) >= 90 and c.get("linkedin")), None)
            possible_ct = next((c for c in cts if 70 <= (c.get("confidence") or 0) < 90), None)
            best_ct = verified_ct or possible_ct
            if best_ct:
                tag = " [LinkedIn]" if best_ct.get("linkedin") else " [possible]"
                contact_str = f"  ->  {best_ct['name']} ({best_ct['title']}){tag}"
            logger.info(
                "  %2d. %-45s  [%s / %.0f]%s",
                o["rank"], o["company_name"][:45], o["priority_tier"], o["priority_score"], contact_str,
            )

        # ── Publish to DB ────────────────────────────────────────────────
        if args.dry_run:
            logger.info("")
            logger.info("DRY RUN — database not updated")
        else:
            report_data = {
                "report_date":       today.isoformat(),
                "generated_at":      datetime.now(timezone.utc).isoformat(),
                "opportunity_count": len(opportunities),
                "contacts_found":    contacts_found_total,
                "opportunities":     opportunities,
            }
            existing = db.query(DailyReport).filter(DailyReport.report_date == today).first()
            if existing:
                existing.set_data(report_data)
                existing.contacts_found = contacts_found_total
                existing.generated_at   = datetime.now(timezone.utc)
                action = "updated"
            else:
                rec = DailyReport(
                    report_date=today,
                    contacts_found=contacts_found_total,
                )
                rec.set_data(report_data)
                db.add(rec)
                action = "created"
            db.commit()
            logger.info("")
            logger.info("Report %s in daily_reports for %s", action, today)
            logger.info("Available at:  GET /api/strategy/today")

    except Exception as e:
        logger.error("Fatal error: %s", e, exc_info=True)
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


def _pretty_print(rank: int, opp: dict) -> None:
    """Print a formatted strategy card for one opportunity."""
    st = opp["strategy"]
    hq = opp.get("hot_qualification") or {}
    contacts = opp.get("contacts", [])

    sep = "=" * 70
    print(f"\n{sep}")
    print(f"  #{rank:02d}  {opp['company_name']}  [{opp['priority_tier']} / {opp['priority_score']}]")
    print(f"        {opp['industry']}  |  {opp['location']}  |  {opp['signal_count']} signals")
    print(sep)
    print(f"  ROBOT      : {st['primary_robot']}  ({', '.join(st['robots'])})")
    print(f"  USE CASE   : {st['use_case']}")
    print(f"  DEAL TIER  : {st['deal_tier']}  ({st['deal_est_units']} units est.)")
    print(f"  TIMING     : {st['outreach_timing']}")
    print(f"  PITCH      : {st['pitch_angle']}")
    if st.get("talking_points"):
        print("  TALKING PTS:")
        for pt in st["talking_points"]:
            print(f"    - {pt}")
    if hq:
        print(f"  WINDOW     : {hq.get('buying_window', '?')}  |  CONFIDENCE: {hq.get('intent_confidence', '?')}")
        if hq.get("recommended_action"):
            print(f"  ACTION     : {hq['recommended_action']}")
        evidence_items = hq.get("window_evidence") or []
        if evidence_items:
            print("  EVIDENCE   :")
            for ev in evidence_items:
                # Truncate long evidence lines for readable terminal output
                ev_clean = str(ev)[:120]
                print(f"    > {ev_clean}")
    verified_cts = [ct for ct in contacts if (ct.get("confidence") or 0) >= 90 and ct.get("linkedin")]
    possible_cts = [ct for ct in contacts if 70 <= (ct.get("confidence") or 0) < 90]
    if verified_cts:
        print("  CONFIRMED  :")
        for ct in verified_cts:
            print(f"    + {ct['name']} -- {ct['title']}")
            print(f"      LinkedIn: {ct['linkedin']}")
            if ct.get("email"):
                print(f"      Email:    {ct['email']}")
    if possible_cts:
        print("  POSSIBLE   :")
        for ct in possible_cts[:4]:
            print(f"    ? {ct['name']} -- {ct['title']} (conf:{ct['confidence']})")
    if not verified_cts and not possible_cts:
        print(f"  CONTACT    : {st['contact_role']}  (no named contact found yet)")


if __name__ == "__main__":
    main()
