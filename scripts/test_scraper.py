"""
Scraper test + seed script.

Usage:
  python scripts/test_scraper.py             # seed mode (fast, no network)
  python scripts/test_scraper.py --live      # seed + live scrape (SimplyHired, Yellow Pages)
  python scripts/test_scraper.py --news      # seed + Google News RSS (real signals)
  python scripts/test_scraper.py --all       # everything
  python scripts/test_scraper.py --clear     # wipe DB first, then seed
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load .env so DATABASE_URL points to Supabase
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

from app.database import SessionLocal, Base, engine
import app.models  # ensure all tables are registered
Base.metadata.create_all(bind=engine)

from app.models.company import Company
from app.models.signal import Signal
from app.models.score import Score
from app.services.scoring_engine import compute_scores
from app.services.inference_engine import analyze_signals

# ──────────────────────────────────────────────────────────────────────────────
# SEED DATA  — real companies with realistic buying-intent signals
# ──────────────────────────────────────────────────────────────────────────────
SEED_COMPANIES = [
    # ── Logistics / Warehousing ──────────────────────────────────────────────
    {
        "company": {
            "name": "XPO Logistics",
            "website": "https://www.xpo.com",
            "industry": "Logistics",
            "sub_industry": "3PL",
            "employee_estimate": 35000,
            "location_city": "Greenwich",
            "location_state": "CT",
            "location_country": "US",
            "source": "seed",
        },
        "signals": [
            ("job_posting",    "Director of Warehouse Automation | WMS integration experience required, AMR deployment preferred", 0.85),
            ("news",           "XPO opens 1.2M sq ft fulfillment center in Dallas as part of expansion strategy", 0.75),
            ("job_posting",    "Robotics Engineer – Canton OH DC | AGV, conveyor systems, computer vision", 0.90),
            ("funding_round",  "XPO raises $1.4B growth equity round to fund warehouse automation and network expansion", 0.88),
            ("strategic_hire", "XPO appoints SVP of Automation Technology to lead robotics deployment across 50 DCs", 0.92),
        ],
    },
    {
        "company": {
            "name": "DHL Supply Chain",
            "website": "https://www.dhl.com",
            "industry": "Logistics",
            "sub_industry": "3PL",
            "employee_estimate": 20000,
            "location_city": "Westerville",
            "location_state": "OH",
            "location_country": "US",
            "source": "seed",
        },
        "signals": [
            ("job_posting",    "Automation Engineer | AMR fleet management, autonomous guided vehicles, WMS", 0.90),
            ("funding_round",  "DHL raises $500M Series C to fund warehouse automation and robotics rollout across US DCs", 0.80),
            ("job_posting",    "Labor shortage forcing DHL to modernize operations, seeking AI operations lead", 0.75),
            ("capex",          "DHL commits $2B capex to warehouse automation and robotics over next 3 years", 0.90),
            ("strategic_hire", "DHL hires Chief Automation Officer from Kion Group to oversee AMR deployment", 0.92),
        ],
    },
    {
        "company": {
            "name": "Prologis",
            "website": "https://www.prologis.com",
            "industry": "Logistics",
            "sub_industry": "Warehouse REIT",
            "employee_estimate": 1800,
            "location_city": "San Francisco",
            "location_state": "CA",
            "location_country": "US",
            "source": "seed",
        },
        "signals": [
            ("expansion",      "Prologis breaking ground on new 800,000 sq ft distribution center in Phoenix AZ", 0.80),
            ("ma_activity",    "Prologis acquires Duke Realty to expand US logistics real estate footprint by 150 DCs", 0.78),
            ("funding_round",  "Prologis raises $3.5B in debt financing to accelerate distribution center expansion", 0.82),
            ("capex",          "Prologis allocated $4B capital expenditure toward new warehouse construction and automation-ready facilities", 0.88),
        ],
    },
    {
        "company": {
            "name": "Amazon Fulfillment",
            "website": "https://www.amazon.com",
            "industry": "Logistics",
            "sub_industry": "E-commerce Fulfillment",
            "employee_estimate": 500000,
            "location_city": "Seattle",
            "location_state": "WA",
            "location_country": "US",
            "source": "seed",
        },
        "signals": [
            ("job_posting",    "Senior AMR Systems Engineer | Autonomous mobile robot deployment, WMS integration", 0.95),
            ("job_posting",    "Computer Vision Engineer – Pick-and-Place Robotics, goods-to-person systems", 0.90),
            ("news",           "Amazon expanding warehouse footprint by 20 new fulfillment centers, cant find enough warehouse workers", 0.88),
            ("strategic_hire", "Amazon appoints VP of Robotics and Automation to lead 10,000-robot AMR deployment", 0.93),
            ("capex",          "Amazon commits $10B capex to robotics and warehouse automation over next 5 years", 0.95),
        ],
    },
    {
        "company": {
            "name": "Ryder System",
            "website": "https://www.ryder.com",
            "industry": "Logistics",
            "sub_industry": "Fleet and Supply Chain",
            "employee_estimate": 40000,
            "location_city": "Miami",
            "location_state": "FL",
            "location_country": "US",
            "source": "seed",
        },
        "signals": [
            ("job_posting",    "Warehouse Automation Specialist | WMS, pick and place, reduce labor costs", 0.78),
            ("news",           "Ryder integrating AMR autonomous mobile robots across 12 DCs to combat staff shortage", 0.82),
            ("funding_round",  "Ryder raises $800M growth round to finance supply chain technology modernization", 0.80),
            ("strategic_hire", "Ryder hires Director of Intelligent Operations to lead robotics and automation rollout", 0.88),
        ],
    },

    # ── Hospitality ──────────────────────────────────────────────────────────
    {
        "company": {
            "name": "Marriott International",
            "website": "https://www.marriott.com",
            "industry": "Hospitality",
            "sub_industry": "Hotel Chain",
            "employee_estimate": 120000,
            "location_city": "Bethesda",
            "location_state": "MD",
            "location_country": "US",
            "source": "seed",
        },
        "signals": [
            ("job_posting",    "Front-of-House Service Robot Coordinator | robot butler, hospitality robot integration", 0.85),
            ("news",           "Marriott pilots delivery robots at 15 properties amid hotel staffing crisis", 0.88),
            ("expansion",      "Marriott opening 50 new hotel properties globally, hospitality expansion strategy", 0.72),
            ("funding_round",  "Marriott raises $2B in debt financing to fund property expansion and technology investment", 0.80),
            ("strategic_hire", "Marriott appoints Chief Digital and Technology Officer to lead hotel automation and AI", 0.88),
        ],
    },
    {
        "company": {
            "name": "Hilton Hotels and Resorts",
            "website": "https://www.hilton.com",
            "industry": "Hospitality",
            "sub_industry": "Hotel Chain",
            "employee_estimate": 85000,
            "location_city": "McLean",
            "location_state": "VA",
            "location_country": "US",
            "source": "seed",
        },
        "signals": [
            ("news",           "Hilton reports high turnover in housekeeping, exploring robot maid solutions", 0.82),
            ("job_posting",    "Director of Hotel Technology Innovation | AI operations, robotic service automation", 0.78),
            ("ma_activity",    "Hilton acquires Graduate Hotels brand, adding 35 properties to integrate with automation push", 0.76),
            ("capex",          "Hilton committing $1.5B technology investment across portfolio including service robot pilots", 0.84),
        ],
    },
    {
        "company": {
            "name": "MGM Resorts International",
            "website": "https://www.mgmresorts.com",
            "industry": "Hospitality",
            "sub_industry": "Casino Resort",
            "employee_estimate": 62000,
            "location_city": "Las Vegas",
            "location_state": "NV",
            "location_country": "US",
            "source": "seed",
        },
        "signals": [
            ("job_posting",    "Automation Technology Lead | service robot deployment, casino hospitality, reduce labor", 0.80),
            ("news",           "MGM Grand piloting room-service delivery robots at Bellagio, workforce shortage driving automation", 0.85),
            ("expansion",      "MGM breaking ground on new $2.5B resort in New York, largest expansion in decade", 0.78),
            ("strategic_hire", "MGM hires VP of Operations Technology to oversee service robot rollout across all properties", 0.90),
        ],
    },
    {
        "company": {
            "name": "Hyatt Hotels Corporation",
            "website": "https://www.hyatt.com",
            "industry": "Hospitality",
            "sub_industry": "Hotel Chain",
            "employee_estimate": 50000,
            "location_city": "Chicago",
            "location_state": "IL",
            "location_country": "US",
            "source": "seed",
        },
        "signals": [
            ("funding_round",  "Hyatt raised $300M Series B to expand property portfolio and modernize operations", 0.72),
            ("expansion",      "Hyatt opening 20 new hotel locations across US in Q2 including resort properties", 0.70),
            ("ma_activity",    "Hyatt merges with Apple Leisure Group adding 100 all-inclusive resort properties, integration needed", 0.75),
        ],
    },

    # ── Healthcare ───────────────────────────────────────────────────────────
    {
        "company": {
            "name": "HCA Healthcare",
            "website": "https://www.hcahealthcare.com",
            "industry": "Healthcare",
            "sub_industry": "Hospital Network",
            "employee_estimate": 250000,
            "location_city": "Nashville",
            "location_state": "TN",
            "location_country": "US",
            "source": "seed",
        },
        "signals": [
            ("job_posting",    "Autonomous Robot Deployment Engineer | hospital delivery robots, clinical automation", 0.80),
            ("news",           "HCA Healthcare facing critical nursing shortage, exploring autonomous delivery robots", 0.84),
            ("capex",          "HCA Healthcare allocated $600M capital expenditure for technology and automation modernization", 0.82),
            ("strategic_hire", "HCA appoints Head of Automation and Robotics to accelerate clinical logistics automation", 0.88),
        ],
    },
    {
        "company": {
            "name": "Brookdale Senior Living",
            "website": "https://www.brookdale.com",
            "industry": "Healthcare",
            "sub_industry": "Senior Living",
            "employee_estimate": 40000,
            "location_city": "Brentwood",
            "location_state": "TN",
            "location_country": "US",
            "source": "seed",
        },
        "signals": [
            ("news",    "Brookdale Senior Living struggling with caregiver shortage, high turnover in assisted living facilities", 0.86),
            ("news",    "Brookdale piloting delivery robots and companion robots at senior living communities", 0.82),
            ("expansion", "Brookdale acquiring 25 senior living communities from Holiday Retirement to scale operations", 0.75),
        ],
    },

    # ── Food Service ─────────────────────────────────────────────────────────
    {
        "company": {
            "name": "Sodexo USA",
            "website": "https://us.sodexo.com",
            "industry": "Food Service",
            "sub_industry": "Contract Food Service",
            "employee_estimate": 130000,
            "location_city": "Gaithersburg",
            "location_state": "MD",
            "location_country": "US",
            "source": "seed",
        },
        "signals": [
            ("job_posting",    "Robot Service Integration Manager | restaurant service robot, food service automation", 0.78),
            ("news",           "Sodexo testing delivery robots at hospital and campus cafeteria locations to combat staffing issues", 0.82),
            ("strategic_hire", "Sodexo hires SVP of Digital Operations to lead food service automation and robot deployment program", 0.87),
            ("funding_round",  "Sodexo raises $400M to fund digital transformation and automation across food service operations", 0.78),
        ],
    },
]


# ──────────────────────────────────────────────────────────────────────────────
# Live scrape URLs  (--live flag)
# ──────────────────────────────────────────────────────────────────────────────
LIVE_JOB_URLS = [
    # SimplyHired has more relaxed bot detection than Indeed/LinkedIn
    "https://www.simplyhired.com/search?q=warehouse+automation&l=united+states",
    "https://www.simplyhired.com/search?q=robotics+engineer+warehouse&l=united+states",
    "https://www.simplyhired.com/search?q=AMR+AGV+automation&l=united+states",
]

LIVE_HOTEL_URLS = [
    # Yellow Pages hotel listings — publicly accessible HTML
    "https://www.yellowpages.com/search?search_terms=hotels&geo_location_terms=Las+Vegas+NV",
    "https://www.yellowpages.com/search?search_terms=hotels&geo_location_terms=New+York+NY",
    "https://www.yellowpages.com/search?search_terms=hotels&geo_location_terms=Chicago+IL",
]


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────
def seed_database(db):
    """Insert seed companies and their signals, then score each one."""
    print("\n=== Seeding database with real companies ===")
    added_companies = 0
    added_signals = 0

    for entry in SEED_COMPANIES:
        c_data = entry["company"]
        existing = db.query(Company).filter(Company.name == c_data["name"]).first()
        if existing:
            company = existing
        else:
            company = Company(**c_data)
            db.add(company)
            db.commit()
            db.refresh(company)
            added_companies += 1

        for sig_type, sig_text, strength in entry["signals"]:
            # Avoid duplicate signals
            dup = db.query(Signal).filter(
                Signal.company_id == company.id,
                Signal.signal_text == sig_text
            ).first()
            if not dup:
                sig = Signal(
                    company_id=company.id,
                    signal_type=sig_type,
                    signal_text=sig_text,
                    signal_strength=strength,
                    source_url="seed",
                )
                db.add(sig)
                db.commit()
                added_signals += 1

    print(f"  Added {added_companies} new companies, {added_signals} new signals")


def score_all(db):
    """Run inference engine on every company that has signals."""
    print("\n=== Scoring all companies ===")
    companies = db.query(Company).all()
    scored = 0
    for company in companies:
        signals = db.query(Signal).filter(Signal.company_id == company.id).all()
        if not signals:
            continue
        texts = [s.signal_text for s in signals]
        result = analyze_signals(texts, company_name=company.name, industry=company.industry)
        score_data = result.to_score_dict()

        existing_score = db.query(Score).filter(Score.company_id == company.id).first()
        if existing_score:
            for k, v in score_data.items():
                setattr(existing_score, k, v)
        else:
            db.add(Score(company_id=company.id, **score_data))
        db.commit()
        scored += 1
    print(f"  Scored {scored} companies")


def print_results(db):
    companies = db.query(Company).all()
    signals_count = db.query(Signal).count()

    print(f"\n{'='*70}")
    print(f"  RESULTS: {len(companies)} companies | {signals_count} signals")
    print(f"{'='*70}")

    # Sort by overall intent score descending
    ranked = []
    for c in companies:
        score = db.query(Score).filter(Score.company_id == c.id).first()
        ranked.append((c, score))
    ranked.sort(key=lambda x: (x[1].overall_intent_score if x[1] else 0), reverse=True)

    print(f"\n{'Rank':<5} {'Company':<30} {'Industry':<15} {'Overall':>8} {'Auto':>7} {'Labor':>7} {'Expand':>8} {'Fit':>6}")
    print("-" * 90)
    for rank, (c, s) in enumerate(ranked, 1):
        if s:
            print(f"  {rank:<4} {c.name:<30} {c.industry:<15} "
                  f"{s.overall_intent_score:>7.1f}  "
                  f"{s.automation_score:>6.1f}  "
                  f"{s.labor_pain_score:>6.1f}  "
                  f"{s.expansion_score:>7.1f}  "
                  f"{s.robotics_fit_score:>5.1f}")
        else:
            print(f"  {rank:<4} {c.name:<30} {c.industry:<15} {'N/A':>8}")
    print()


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────
db = SessionLocal()

live_mode  = "--live"  in sys.argv
news_mode  = "--news"  in sys.argv or "--all" in sys.argv
clear_mode = "--clear" in sys.argv
all_mode   = "--all"   in sys.argv
if all_mode:
    live_mode = True

if clear_mode:
    print("Clearing existing data...")
    try:
        from sqlalchemy import text
        db.execute(text("TRUNCATE TABLE scores RESTART IDENTITY CASCADE"))
        db.execute(text("TRUNCATE TABLE signals RESTART IDENTITY CASCADE"))
        db.execute(text("TRUNCATE TABLE companies RESTART IDENTITY CASCADE"))
        db.commit()
    except Exception:
        # Fallback for SQLite
        db.query(Score).delete()
        db.query(Signal).delete()
        db.query(Company).delete()
        db.commit()

if live_mode:
    from app.scrapers.job_board_scraper import JobBoardScraper
    from app.scrapers.hotel_directory_scraper import HotelDirectoryScraper

    print("\n=== Live: Job Board Scraper (SimplyHired) ===")
    job_scraper = JobBoardScraper(db=db)
    job_scraper.run(LIVE_JOB_URLS)

    print("\n=== Live: Hotel Directory Scraper (Yellow Pages) ===")
    hotel_scraper = HotelDirectoryScraper(db=db)
    hotel_scraper.run(LIVE_HOTEL_URLS)

# Always seed real companies (skips existing by name)
seed_database(db)

if news_mode:
    from app.scrapers.news_scraper import NewsScraper
    import logging
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    # Company-specific news: expansion, funding, M&A, strategic hires
    tracked_companies = [c["company"]["name"] for c in SEED_COMPANIES]
    print(f"\n=== News Scraper: company-specific signals ({len(tracked_companies)} companies) ===")
    news_scraper = NewsScraper(db=db)
    news_scraper.run_company_queries(tracked_companies, max_per_company=3)

    # Open-market intent discovery
    print("\n=== News Scraper: open market intent queries ===")
    news_scraper.run_intent_queries(max_per_query=6)

# Score everything (including any new signals from news scraper)
score_all(db)

# Print ranked results
print_results(db)

db.close()
print("Done.")
