#!/usr/bin/env python3
"""Demand-side buyer source — curated operating buyers → Cal HOT/WARM queue.

Why this exists: news discovery structurally finds robot *makers* (supply) and the
Apollo key is free-tier (org/people search both 403), so Cal's buyer queue goes dry.
This is the demand-side refill: a curated list of real *operators* (3PL, food
service, hospitality, healthcare, senior living, food manufacturing, facilities)
that buy service / material-handling / cleaning robots. Each is ingested through the
same scoring + CRM machinery the scraper uses, then Hunter verifies the contact at
send time (the only enrichment path that works on this account).

Signals here are sector-level and drive scoring/tiering only — Cal's email is built
from name + industry and never quotes signal text, so nothing false reaches a buyer.

Usage
-----
  python3 scripts/seed_demand_side_buyers.py                 # dry-run: new/existing + predicted tier
  python3 scripts/seed_demand_side_buyers.py --apply         # ingest + draft (writes)
  python3 scripts/seed_demand_side_buyers.py --apply --enrich # + Hunter contact resolution
  python3 scripts/seed_demand_side_buyers.py --limit 10 --apply
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

import app.models  # noqa: F401  (register all mappers)
from app.database import SessionLocal
from app.services.demand_side_ingest import (
    _find_existing,
    ingest_operator_batch,
    preview_operator_tier,
)

# Two sector-true signals per operator. {name}/{industry} are interpolated.
# These are defensible sector observations (labor + automation pressure), not
# fabricated company events, and are never quoted in Cal's outreach email.
SIGNALS = [
    (
        "labor_shortage",
        "{name}, a large {industry} operator, sits in a sector facing acute front-line "
        "labor shortages that are pushing operators to evaluate service and "
        "material-handling robots.",
        0.88,
    ),
    (
        "expansion",
        "As a high-volume {industry} operator, {name} runs the repetitive, hard-to-staff "
        "workflows where robots are being deployed to offset chronic staffing gaps.",
        0.82,
    ),
]

# Curated operating buyers. Industry strings intentionally contain a HIGH_FIT token
# (logistics / food service / hospitality / healthcare / senior living / manufacturing
# / distribution / warehouse) so priority_tier grants the high-fit boost. Biased toward
# mid-market / regional operators less likely to already exist from robotics news.
OPERATORS: list[dict] = [
    # ── Logistics / 3PL / cold storage / warehousing ──
    {"name": "Americold Logistics", "domain": "americold.com", "industry": "Logistics & Warehousing (Cold Storage)", "employee_estimate": 17000, "state": "GA"},
    {"name": "NFI Industries", "domain": "nfiindustries.com", "industry": "Logistics & Supply Chain (3PL)", "employee_estimate": 15000, "state": "NJ"},
    {"name": "Saddle Creek Logistics", "domain": "sclogistics.com", "industry": "Logistics & Warehousing (3PL)", "employee_estimate": 5000, "state": "FL"},
    {"name": "Kenco Logistics", "domain": "kencogroup.com", "industry": "Logistics & Warehousing (3PL)", "employee_estimate": 5500, "state": "TN"},
    {"name": "Ruan Transportation Management Systems", "domain": "ruan.com", "industry": "Logistics & Supply Chain", "employee_estimate": 5000, "state": "IA"},
    {"name": "Radial", "domain": "radial.com", "industry": "Logistics & Fulfillment (3PL)", "employee_estimate": 6000, "state": "PA"},
    {"name": "Port Logistics Group", "domain": "portlogisticsgroup.com", "industry": "Logistics & Warehousing (3PL)", "employee_estimate": 3000, "state": "CA"},
    {"name": "Performance Team", "domain": "performanceteam.net", "industry": "Logistics & Warehousing (3PL)", "employee_estimate": 4000, "state": "CA"},
    {"name": "Barrett Distribution Centers", "domain": "barrettdistribution.com", "industry": "Logistics & Warehousing (3PL)", "employee_estimate": 1500, "state": "MA"},
    {"name": "DSC Logistics", "domain": "dsclogistics.com", "industry": "Logistics & Supply Chain (3PL)", "employee_estimate": 3000, "state": "IL"},

    # ── Food service / catering / commissary ──
    {"name": "Aramark", "domain": "aramark.com", "industry": "Food Service & Facilities", "employee_estimate": 260000, "state": "PA"},
    {"name": "Sodexo North America", "domain": "sodexo.com", "industry": "Food Service & Facilities", "employee_estimate": 150000, "state": "MD"},
    {"name": "Compass Group USA", "domain": "compass-usa.com", "industry": "Food Service & Catering", "employee_estimate": 280000, "state": "NC"},
    {"name": "Delaware North", "domain": "delawarenorth.com", "industry": "Food Service & Hospitality", "employee_estimate": 55000, "state": "NY"},
    {"name": "HMSHost", "domain": "hmshost.com", "industry": "Food Service & Hospitality", "employee_estimate": 39000, "state": "MD"},
    {"name": "Elior North America", "domain": "elior-na.com", "industry": "Food Service & Catering", "employee_estimate": 18000, "state": "TN"},
    {"name": "Guckenheimer", "domain": "guckenheimer.com", "industry": "Food Service & Catering", "employee_estimate": 3500, "state": "CA"},

    # ── QSR / fast-casual chains (labor-heavy prep) ──
    {"name": "Panera Bread", "domain": "panerabread.com", "industry": "Food Service (Restaurants)", "employee_estimate": 100000, "state": "MO"},
    {"name": "Sweetgreen", "domain": "sweetgreen.com", "industry": "Food Service (Fast Casual)", "employee_estimate": 12000, "state": "CA"},
    {"name": "CAVA Group", "domain": "cava.com", "industry": "Food Service (Fast Casual)", "employee_estimate": 13000, "state": "DC"},
    {"name": "Wingstop", "domain": "wingstop.com", "industry": "Food Service (Restaurants)", "employee_estimate": 20000, "state": "TX"},
    {"name": "Jack in the Box", "domain": "jackinthebox.com", "industry": "Food Service (Restaurants)", "employee_estimate": 5000, "state": "CA"},
    {"name": "Zaxbys", "domain": "zaxbys.com", "industry": "Food Service (Restaurants)", "employee_estimate": 30000, "state": "GA"},

    # ── Hospitality / hotel management ──
    {"name": "Aimbridge Hospitality", "domain": "aimbridgehospitality.com", "industry": "Hospitality (Hotel Management)", "employee_estimate": 60000, "state": "TX"},
    {"name": "Highgate Hotels", "domain": "highgate.com", "industry": "Hospitality (Hotel Management)", "employee_estimate": 30000, "state": "NY"},
    {"name": "Sonesta International Hotels", "domain": "sonesta.com", "industry": "Hospitality (Hotels)", "employee_estimate": 20000, "state": "MA"},
    {"name": "Omni Hotels & Resorts", "domain": "omnihotels.com", "industry": "Hospitality (Hotels)", "employee_estimate": 24000, "state": "TX"},
    {"name": "Crescent Hotels & Resorts", "domain": "chrco.com", "industry": "Hospitality (Hotel Management)", "employee_estimate": 12000, "state": "VA"},
    {"name": "Davidson Hospitality Group", "domain": "davidsonhospitality.com", "industry": "Hospitality (Hotel Management)", "employee_estimate": 10000, "state": "GA"},

    # ── Healthcare systems / hospitals ──
    {"name": "Encompass Health", "domain": "encompasshealth.com", "industry": "Healthcare (Hospital Systems)", "employee_estimate": 44000, "state": "AL"},
    {"name": "Ardent Health", "domain": "ardenthealth.com", "industry": "Healthcare (Hospital Systems)", "employee_estimate": 24000, "state": "TN"},
    {"name": "Community Health Systems", "domain": "chs.net", "industry": "Healthcare (Hospital Systems)", "employee_estimate": 60000, "state": "TN"},
    {"name": "Tenet Healthcare", "domain": "tenethealth.com", "industry": "Healthcare (Hospital Systems)", "employee_estimate": 100000, "state": "TX"},
    {"name": "Ballad Health", "domain": "balladhealth.org", "industry": "Healthcare (Hospital Systems)", "employee_estimate": 15000, "state": "TN"},
    {"name": "ChristianaCare", "domain": "christianacare.org", "industry": "Healthcare (Hospital Systems)", "employee_estimate": 14000, "state": "DE"},

    # ── Senior living ──
    {"name": "Brookdale Senior Living", "domain": "brookdale.com", "industry": "Senior Living & Assisted Living", "employee_estimate": 26000, "state": "TN"},
    {"name": "Atria Senior Living", "domain": "atriaseniorliving.com", "industry": "Senior Living & Assisted Living", "employee_estimate": 15000, "state": "KY"},
    {"name": "Sunrise Senior Living", "domain": "sunriseseniorliving.com", "industry": "Senior Living & Assisted Living", "employee_estimate": 32000, "state": "VA"},
    {"name": "AlerisLife", "domain": "alerislife.com", "industry": "Senior Living & Assisted Living", "employee_estimate": 20000, "state": "MA"},

    # ── Food manufacturing / processing / CPG ──
    {"name": "Hearthside Food Solutions", "domain": "hearthsidefoods.com", "industry": "Food Manufacturing (Contract Manufacturing)", "employee_estimate": 12000, "state": "IL"},
    {"name": "TreeHouse Foods", "domain": "treehousefoods.com", "industry": "Food Manufacturing & CPG", "employee_estimate": 10000, "state": "IL"},
    {"name": "Perdue Farms", "domain": "perduefarms.com", "industry": "Food Processing & Manufacturing", "employee_estimate": 22000, "state": "MD"},
    {"name": "Post Holdings", "domain": "postholdings.com", "industry": "Food Manufacturing & CPG", "employee_estimate": 12000, "state": "MO"},
    {"name": "Del Monte Foods", "domain": "delmonte.com", "industry": "Food Processing & Manufacturing", "employee_estimate": 3000, "state": "CA"},
    {"name": "Rich Products", "domain": "richs.com", "industry": "Food Manufacturing & CPG", "employee_estimate": 12000, "state": "NY"},

    # ── Facilities services (cleaning / service robots) ──
    {"name": "ISS Facilities", "domain": "issworld.com", "industry": "Facilities Services & Manufacturing Support", "employee_estimate": 40000, "state": "TX"},
    {"name": "SBM Management", "domain": "sbmcorp.com", "industry": "Facilities Services & Manufacturing Support", "employee_estimate": 12000, "state": "CA"},
    {"name": "GDI Facilities", "domain": "gdi.com", "industry": "Facilities Services & Manufacturing Support", "employee_estimate": 30000, "state": "NY"},
    {"name": "Pritchard Industries", "domain": "pritchardindustries.com", "industry": "Facilities Services & Manufacturing Support", "employee_estimate": 8000, "state": "NY"},

    # ── Batch 2: mid-market operators (better Hunter coverage, less overlap) ──
    # Logistics / 3PL / cold storage
    {"name": "Lineage Logistics", "domain": "lineagelogistics.com", "industry": "Logistics & Warehousing (Cold Storage)", "employee_estimate": 26000, "state": "MI"},
    {"name": "United States Cold Storage", "domain": "uscold.com", "industry": "Logistics & Warehousing (Cold Storage)", "employee_estimate": 3500, "state": "NJ"},
    {"name": "Burris Logistics", "domain": "burrislogistics.com", "industry": "Logistics & Warehousing (Cold Storage)", "employee_estimate": 2500, "state": "DE"},
    {"name": "Capstone Logistics", "domain": "capstonelogistics.com", "industry": "Logistics & Warehousing (3PL)", "employee_estimate": 19000, "state": "GA"},
    {"name": "Verst Logistics", "domain": "verstlogistics.com", "industry": "Logistics & Warehousing (3PL)", "employee_estimate": 2000, "state": "KY"},
    {"name": "Hub Group", "domain": "hubgroup.com", "industry": "Logistics & Supply Chain", "employee_estimate": 6000, "state": "IL"},
    {"name": "Averitt Express", "domain": "averittexpress.com", "industry": "Logistics & Freight", "employee_estimate": 8000, "state": "TN"},
    {"name": "Echo Global Logistics", "domain": "echo.com", "industry": "Logistics & Supply Chain", "employee_estimate": 2500, "state": "IL"},
    {"name": "RJW Logistics Group", "domain": "rjwlogistics.com", "industry": "Logistics & Warehousing (3PL)", "employee_estimate": 1500, "state": "IL"},
    {"name": "Werner Enterprises", "domain": "werner.com", "industry": "Logistics & Supply Chain", "employee_estimate": 14000, "state": "NE"},

    # Food service / catering / commissary
    {"name": "Thompson Hospitality", "domain": "thompsonhospitality.com", "industry": "Food Service & Hospitality", "employee_estimate": 6000, "state": "VA"},
    {"name": "Whitsons Culinary Group", "domain": "whitsons.com", "industry": "Food Service & Catering", "employee_estimate": 5000, "state": "NY"},
    {"name": "AVI Foodsystems", "domain": "avifoodsystems.com", "industry": "Food Service & Catering", "employee_estimate": 10000, "state": "OH"},
    {"name": "Metz Culinary Management", "domain": "metzculinary.com", "industry": "Food Service & Catering", "employee_estimate": 4000, "state": "PA"},
    {"name": "Parkhurst Dining", "domain": "parkhurstdining.com", "industry": "Food Service & Catering", "employee_estimate": 3000, "state": "PA"},
    {"name": "CulinArt Group", "domain": "culinartgroup.com", "industry": "Food Service & Catering", "employee_estimate": 3000, "state": "NY"},
    {"name": "Bon Appetit Management", "domain": "bamco.com", "industry": "Food Service & Catering", "employee_estimate": 25000, "state": "CA"},

    # QSR / fast casual
    {"name": "Portillos", "domain": "portillos.com", "industry": "Food Service (Restaurants)", "employee_estimate": 9000, "state": "IL"},
    {"name": "Shake Shack", "domain": "shakeshack.com", "industry": "Food Service (Fast Casual)", "employee_estimate": 12000, "state": "NY"},
    {"name": "Jersey Mikes", "domain": "jerseymikes.com", "industry": "Food Service (Restaurants)", "employee_estimate": 5000, "state": "NJ"},
    {"name": "Culvers", "domain": "culvers.com", "industry": "Food Service (Restaurants)", "employee_estimate": 3000, "state": "WI"},
    {"name": "Bojangles", "domain": "bojangles.com", "industry": "Food Service (Restaurants)", "employee_estimate": 12000, "state": "NC"},
    {"name": "El Pollo Loco", "domain": "elpolloloco.com", "industry": "Food Service (Restaurants)", "employee_estimate": 4000, "state": "CA"},
    {"name": "Noodles & Company", "domain": "noodles.com", "industry": "Food Service (Fast Casual)", "employee_estimate": 9000, "state": "CO"},
    {"name": "Firehouse Subs", "domain": "firehousesubs.com", "industry": "Food Service (Restaurants)", "employee_estimate": 3000, "state": "FL"},

    # Hospitality / hotel management
    {"name": "Concord Hospitality Enterprises", "domain": "concordhotels.com", "industry": "Hospitality (Hotel Management)", "employee_estimate": 12000, "state": "NC"},
    {"name": "Pyramid Global Hospitality", "domain": "pyramidglobal.com", "industry": "Hospitality (Hotel Management)", "employee_estimate": 25000, "state": "MA"},
    {"name": "HEI Hotels & Resorts", "domain": "heihotels.com", "industry": "Hospitality (Hotel Management)", "employee_estimate": 12000, "state": "CT"},
    {"name": "White Lodging", "domain": "whitelodging.com", "industry": "Hospitality (Hotel Management)", "employee_estimate": 8000, "state": "IN"},
    {"name": "Springboard Hospitality", "domain": "springboardhospitality.com", "industry": "Hospitality (Hotel Management)", "employee_estimate": 3000, "state": "HI"},

    # Healthcare / senior living
    {"name": "Genesis Healthcare", "domain": "genesishcc.com", "industry": "Healthcare (Skilled Nursing)", "employee_estimate": 40000, "state": "PA"},
    {"name": "Ensign Group", "domain": "ensigngroup.net", "industry": "Healthcare (Skilled Nursing)", "employee_estimate": 30000, "state": "CA"},
    {"name": "Trilogy Health", "domain": "trilogyhs.com", "industry": "Senior Living & Assisted Living", "employee_estimate": 15000, "state": "KY"},
    {"name": "Life Care Centers of America", "domain": "lcca.com", "industry": "Healthcare (Skilled Nursing)", "employee_estimate": 40000, "state": "TN"},
    {"name": "Erickson Senior Living", "domain": "ericksonseniorliving.com", "industry": "Senior Living & Assisted Living", "employee_estimate": 15000, "state": "MD"},
    {"name": "Benchmark Senior Living", "domain": "benchmarkseniorliving.com", "industry": "Senior Living & Assisted Living", "employee_estimate": 6000, "state": "MA"},
    {"name": "Life Care Communities", "domain": "lcsnet.com", "industry": "Senior Living & Assisted Living", "employee_estimate": 40000, "state": "IA"},

    # Food manufacturing / processing / CPG
    {"name": "Schwans Company", "domain": "schwanscompany.com", "industry": "Food Manufacturing & CPG", "employee_estimate": 12000, "state": "MN"},
    {"name": "Flowers Foods", "domain": "flowersfoods.com", "industry": "Food Manufacturing & CPG", "employee_estimate": 9000, "state": "GA"},
    {"name": "Utz Brands", "domain": "utzsnacks.com", "industry": "Food Manufacturing & CPG", "employee_estimate": 3500, "state": "PA"},
    {"name": "Simmons Foods", "domain": "simmonsfoods.com", "industry": "Food Processing & Manufacturing", "employee_estimate": 8000, "state": "AR"},
    {"name": "Michael Foods Group", "domain": "michaelfoods.com", "industry": "Food Processing & Manufacturing", "employee_estimate": 8000, "state": "MN"},
    {"name": "Clemens Food Group", "domain": "clemensfoodgroup.com", "industry": "Food Processing & Manufacturing", "employee_estimate": 5000, "state": "PA"},
    {"name": "Johnsonville", "domain": "johnsonville.com", "industry": "Food Manufacturing & CPG", "employee_estimate": 3000, "state": "WI"},

    # Food & beverage distribution (grocery supply)
    {"name": "SpartanNash", "domain": "spartannash.com", "industry": "Food & Beverage Distribution", "employee_estimate": 20000, "state": "MI"},
    {"name": "KeHE Distributors", "domain": "kehe.com", "industry": "Food & Beverage Distribution", "employee_estimate": 6000, "state": "IL"},
    {"name": "Gordon Food Group", "domain": "gfs.com", "industry": "Food & Beverage Distribution", "employee_estimate": 25000, "state": "MI"},
    {"name": "Shamrock Foods", "domain": "shamrockfoods.com", "industry": "Food & Beverage Distribution", "employee_estimate": 5000, "state": "AZ"},
    {"name": "United Natural Foods", "domain": "unfi.com", "industry": "Food & Beverage Distribution", "employee_estimate": 29000, "state": "RI"},

    # Facilities services
    {"name": "Marsden Holding", "domain": "marsden.com", "industry": "Facilities Services & Manufacturing Support", "employee_estimate": 10000, "state": "MN"},
    {"name": "Diversified Maintenance Systems", "domain": "diversifiedm.com", "industry": "Facilities Services & Manufacturing Support", "employee_estimate": 10000, "state": "FL"},
    {"name": "Harvard Maintenance", "domain": "harvardmaintenance.com", "industry": "Facilities Services & Manufacturing Support", "employee_estimate": 9000, "state": "NY"},
]


def _with_signals(op: dict) -> dict:
    return {**op, "signals": SIGNALS}


def main() -> int:
    ap = argparse.ArgumentParser(description="Seed demand-side operating buyers into Cal's queue")
    ap.add_argument("--apply", action="store_true", help="persist companies + drafts (default: dry-run)")
    ap.add_argument("--enrich", action="store_true", help="after apply, resolve contacts via Hunter")
    ap.add_argument("--no-crm", action="store_true", help="score only; do not create Cal CRM accounts")
    ap.add_argument("--limit", type=int, default=0, help="only process the first N operators")
    args = ap.parse_args()

    operators = OPERATORS[: args.limit] if args.limit else OPERATORS
    db = SessionLocal()
    try:
        if not args.apply:
            print(f"DRY RUN — {len(operators)} curated operators (no writes)\n")
            new = existing = hot = warm = 0
            for op in operators:
                hit = _find_existing(db, op["name"], op.get("domain"))
                status = "existing" if hit else "NEW"
                pred = preview_operator_tier(
                    name=op["name"], industry=op["industry"], signals=SIGNALS,
                    employee_estimate=op.get("employee_estimate"),
                )
                tier = pred["tier"]
                if hit:
                    existing += 1
                else:
                    new += 1
                if tier == "HOT":
                    hot += 1
                elif tier == "WARM":
                    warm += 1
                print(f"  [{status:8}] {tier:5} {pred['overall_intent_score']:>5}  {op['name']}")
            print(
                f"\nSummary: {new} net-new, {existing} already in DB | predicted {hot} HOT, {warm} WARM"
                f"\nRun with --apply to ingest, --apply --enrich to also verify contacts via Hunter."
            )
            return 0

        print(f"APPLY — ingesting {len(operators)} operators (create_crm={not args.no_crm})\n")
        summary = ingest_operator_batch(
            db, [_with_signals(o) for o in operators], create_crm=not args.no_crm
        )
        for r in summary["rows"]:
            if "error" in r:
                print(f"  ERROR {r['name']}: {r['error']}")
                continue
            crm = "draft" if r["made_crm"] else "-"
            print(f"  [{r['status']:8}] {r['tier']:5} {r['overall_intent_score']:>5}  crm={crm:5}  {r['name']}")
        print(
            f"\nIngested: {summary['new_companies']} net-new, {summary['existing_companies']} existing"
            f" | {summary['hot']} HOT, {summary['warm']} WARM"
            f" | {summary['crm_accounts_ready']} Cal drafts ready"
        )

        if args.enrich:
            _enrich_contacts(db, summary)
        return 0
    finally:
        db.close()


def _enrich_contacts(db, summary: dict) -> None:
    """Resolve VERIFIED contacts via the Hunter-backed waterfall for new buyers.

    Only stamps ``contact_email`` when the send-time trust gate would accept the
    address (Hunter / Apollo / observed) — a domain-matched guess is left off so
    Cal never sends to an unverified inbox.
    """
    from app.models.company import Company
    from app.models.crm import CrmAccount
    from app.services.cal_autonomy import resolve_cal_admin_context
    from app.services.lead_enrichment import outreach_recipient_trusted, resolve_outreach_email

    from app.services.lead_enrichment import _VERIFIED_EMAIL_SOURCES

    ctx = resolve_cal_admin_context(db)
    if not ctx:
        print("\n[enrich] no Cal admin context — skipping contact enrichment")
        return
    _uid, team = ctx
    verified = guessed = 0
    print("\n[enrich] resolving contacts via Hunter waterfall …")
    for r in summary["rows"]:
        if r.get("error") or not r.get("made_crm"):
            continue
        company = db.query(Company).filter(Company.id == r["company_id"]).first()
        acct = (
            db.query(CrmAccount)
            .filter(CrmAccount.company_id == r["company_id"], CrmAccount.team_id == team.id)
            .first()
        )
        if not company or not acct:
            continue

        # _draft_and_store stamps a guessed role inbox onto contact_email, and any
        # stored contact_email short-circuits resolve_outreach_email BEFORE Hunter
        # (returns "crm_contact", untrusted). Clear unverified guesses first so the
        # waterfall actually reaches Hunter and can stamp a trusted hunter_domain hit.
        meta = dict(company.crm_metadata or {})
        stored_src = (meta.get("outreach_email_source") or "").strip().lower()
        if stored_src not in _VERIFIED_EMAIL_SOURCES:
            acct.contact_email = None
            meta.pop("outreach_email", None)
            meta.pop("outreach_email_source", None)
            company.crm_metadata = meta
            db.flush()

        try:
            email, source, _title = resolve_outreach_email(company, acct, use_apollo=False)
        except Exception as exc:  # Hunter hiccup shouldn't abort the loop
            print(f"  [enrich] {company.name}: error {str(exc)[:80]}")
            db.rollback()
            continue
        if not email:
            db.commit()
            print(f"  [enrich] {company.name}: no contact found")
            continue
        trusted, why = outreach_recipient_trusted(company, acct, email, source)
        if trusted:
            acct.contact_email = email
            db.commit()
            verified += 1
            print(f"  [enrich] {company.name}: {email}  (verified via {source})")
        else:
            # Don't keep a fresh guess on the account — leave it empty so a later
            # autonomy pass re-runs Hunter instead of send-blocking on a role inbox.
            acct.contact_email = None
            m2 = dict(company.crm_metadata or {})
            m2.pop("outreach_email", None)
            m2.pop("outreach_email_source", None)
            company.crm_metadata = m2
            db.commit()
            guessed += 1
            print(f"  [enrich] {company.name}: only a guess ({why}) — left empty for retry")
    print(f"\n[enrich] {verified} verified & sendable, {guessed} awaiting a verified contact.")


if __name__ == "__main__":
    raise SystemExit(main())
