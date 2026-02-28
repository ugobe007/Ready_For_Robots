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

    # ── Hospitality — Major Brands ──────────────────────────────────────────
    {
        "company": {
            "name": "Marriott International",
            "website": "https://www.marriott.com",
            "industry": "Hospitality",
            "sub_industry": "Hotel Chain",
            "employee_estimate": 177000,
            "location_city": "Bethesda",
            "location_state": "MD",
            "location_country": "US",
            "source": "seed",
        },
        "signals": [
            ("labor_shortage", "Marriott properties across US reporting severe housekeeping staff shortages, rooms taking 3+ hours to turn", 0.88),
            ("strategic_hire", "Marriott appoints Chief Operations Technology Officer to lead smart hotel and automation initiatives", 0.85),
            ("expansion",      "Marriott opening 300+ new properties globally in 2025-2026 spanning full and select service brands", 0.80),
            ("capex",          "Marriott commits $2.5B technology investment including guest-facing automation and back-of-house robotics", 0.82),
            ("news",           "Marriott International CEO cites labor costs as greatest operational challenge at investor day 2025", 0.78),
        ],
    },
    {
        "company": {
            "name": "Hilton Worldwide Holdings",
            "website": "https://www.hilton.com",
            "industry": "Hospitality",
            "sub_industry": "Hotel Chain",
            "employee_estimate": 150000,
            "location_city": "McLean",
            "location_state": "VA",
            "location_country": "US",
            "source": "seed",
        },
        "signals": [
            ("labor_shortage", "Hilton properties struggling to fill housekeeping and food service positions across 160+ countries", 0.85),
            ("capex",          "Hilton invests $1.8B in property upgrades, guest technology, and operational automation platforms 2025", 0.83),
            ("strategic_hire", "Hilton names new SVP of Operations Technology to drive automation across 7000+ properties", 0.87),
            ("expansion",      "Hilton fastest growing hotel pipeline on record: 3,800 properties under development globally", 0.79),
        ],
    },
    {
        "company": {
            "name": "IHG Hotels & Resorts",
            "website": "https://www.ihg.com",
            "industry": "Hospitality",
            "sub_industry": "Hotel Chain",
            "employee_estimate": 28000,
            "location_city": "Atlanta",
            "location_state": "GA",
            "location_country": "US",
            "source": "seed",
        },
        "signals": [
            ("labor_shortage", "IHG franchisees facing critical housekeeping shortage, 30% of hotel rooms understaffed", 0.84),
            ("capex",          "IHG investing $150M in hotel technology including robotics pilots at Holiday Inn and Crowne Plaza brands", 0.80),
            ("news",           "IHG CEO discusses robot deployment for room delivery and public area cleaning at owner conference 2025", 0.82),
            ("expansion",      "IHG signs 100+ new franchise agreements in US for 2025-2026 pipeline", 0.72),
        ],
    },
    {
        "company": {
            "name": "Wyndham Hotels & Resorts",
            "website": "https://www.wyndhamhotels.com",
            "industry": "Hospitality",
            "sub_industry": "Hotel Chain",
            "employee_estimate": 9000,
            "location_city": "Parsippany",
            "location_state": "NJ",
            "location_country": "US",
            "source": "seed",
        },
        "signals": [
            ("labor_shortage", "Wyndham franchise owners reporting housekeeping as top operational challenge across economy and midscale brands", 0.86),
            ("job_posting",    "Director of Hotel Operations Technology | back-of-house automation, housekeeping management systems", 0.78),
            ("expansion",      "Wyndham adds 500+ mid-scale hotels to pipeline, majority in labor-constrained suburban markets", 0.74),
            ("news",           "Wyndham piloting delivery robot program at select Days Inn and La Quinta locations in 2025", 0.83),
        ],
    },
    {
        "company": {
            "name": "Choice Hotels International",
            "website": "https://www.choicehotels.com",
            "industry": "Hospitality",
            "sub_industry": "Hotel Chain",
            "employee_estimate": 6000,
            "location_city": "North Bethesda",
            "location_state": "MD",
            "location_country": "US",
            "source": "seed",
        },
        "signals": [
            ("labor_shortage", "Choice Hotels franchisees report 40% vacancy in housekeeping roles, unable to meet RevPAR targets", 0.87),
            ("strategic_hire", "Choice Hotels recruits VP of Property Technology to roll out smart housekeeping and automation systems", 0.81),
            ("capex",          "Choice Hotels approves $200M capital plan for franchise tech upgrades including automation platforms", 0.76),
        ],
    },
    {
        "company": {
            "name": "Omni Hotels & Resorts",
            "website": "https://www.omnihotels.com",
            "industry": "Hospitality",
            "sub_industry": "Luxury Hotels",
            "employee_estimate": 25000,
            "location_city": "Dallas",
            "location_state": "TX",
            "location_country": "US",
            "source": "seed",
        },
        "signals": [
            ("job_posting",    "Housekeeping Supervisor | 40+ room attendants managed, high-volume luxury hotel with valet and concierge robotics interest", 0.80),
            ("capex",          "Omni Hotels approves $300M renovation program across flagship properties, includes operational technology", 0.77),
            ("news",           "Omni Hotels & Resorts piloting in-room delivery robots at Dallas and Atlanta properties", 0.85),
            ("strategic_hire", "Omni Hotels promotes Chief Innovation Officer to board-level role, budget includes service automation", 0.82),
        ],
    },
    {
        "company": {
            "name": "Aimbridge Hospitality",
            "website": "https://www.aimbridgehospitality.com",
            "industry": "Hospitality",
            "sub_industry": "Hotel Management",
            "employee_estimate": 60000,
            "location_city": "Dallas",
            "location_state": "TX",
            "location_country": "US",
            "source": "seed",
        },
        "signals": [
            ("labor_shortage", "Aimbridge managing 1,500+ hotels across 40 countries facing systemic housekeeping labor shortage", 0.90),
            ("strategic_hire", "Aimbridge Hospitality names Chief Operations Officer to drive standardisation across managed properties", 0.84),
            ("job_posting",    "Regional Director of Housekeeping | 80+ properties, scalable cleaning operations and technology adoption", 0.83),
            ("news",           "Aimbridge CEO: staffing costs up 28% YoY; evaluating automation in housekeeping and guest amenity delivery", 0.88),
        ],
    },
    {
        "company": {
            "name": "Loews Hotels & Co",
            "website": "https://www.loewshotels.com",
            "industry": "Hospitality",
            "sub_industry": "Luxury Hotels",
            "employee_estimate": 12000,
            "location_city": "New York",
            "location_state": "NY",
            "location_country": "US",
            "source": "seed",
        },
        "signals": [
            ("job_posting",    "VP of Guest Services & Technology | explore AI concierge and delivery robot pilots at flagship properties", 0.81),
            ("capex",          "Loews Hotels approves $150M property refresh including lobby automation and service technology", 0.75),
            ("expansion",      "Loews Hotels signing management contracts for 8 new properties in high-labor-cost metros", 0.70),
        ],
    },
    {
        "company": {
            "name": "Sage Hospitality Group",
            "website": "https://www.sagehospitality.com",
            "industry": "Hospitality",
            "sub_industry": "Hotel Management",
            "employee_estimate": 5500,
            "location_city": "Denver",
            "location_state": "CO",
            "location_country": "US",
            "source": "seed",
        },
        "signals": [
            ("news",           "Sage Hospitality deploys first delivery robots at Denver boutique hotels, positive guest feedback", 0.87),
            ("labor_shortage", "Sage portfolio properties reporting 35% housekeeping vacancy, outsourcing to staffing agencies at premium cost", 0.84),
            ("strategic_hire", "Sage hires Director of Innovation & Automation to scale robot deployments across managed portfolio", 0.89),
        ],
    },
    {
        "company": {
            "name": "Extended Stay America",
            "website": "https://www.extendedstayamerica.com",
            "industry": "Hospitality",
            "sub_industry": "Extended Stay Hotels",
            "employee_estimate": 9000,
            "location_city": "Charlotte",
            "location_state": "NC",
            "location_country": "US",
            "source": "seed",
        },
        "signals": [
            ("labor_shortage", "Extended Stay America: 700+ properties across US, chronic housekeeping shortage inflating per-room cleaning cost", 0.88),
            ("capex",          "Extended Stay America commits $300M in 2025 capex for property modernisation and operations technology", 0.81),
            ("job_posting",    "VP of Property Operations | housekeeping efficiency, cost reduction, operational automation programs", 0.79),
        ],
    },

    # ── Logistics — Major Operators ─────────────────────────────────────────
    {
        "company": {
            "name": "FedEx Ground",
            "website": "https://www.fedex.com/ground",
            "industry": "Logistics",
            "sub_industry": "Parcel Delivery",
            "employee_estimate": 200000,
            "location_city": "Memphis",
            "location_state": "TN",
            "location_country": "US",
            "source": "seed",
        },
        "signals": [
            ("capex",          "FedEx Ground announces $4B automation investment: sortation robots, autonomous forklifts, conveyor upgrades at 500 hubs", 0.92),
            ("job_posting",    "Director of Automation Engineering | sortation robotics, AMR deployment, WMS integration across 500+ facilities", 0.88),
            ("strategic_hire", "FedEx appoints Chief Automation Officer to lead Ground network transformation and robotics rollout", 0.91),
            ("labor_shortage", "FedEx Ground hubs severely understaffed; seasonal surge hiring falling 40% short of target headcount", 0.86),
            ("news",           "FedEx Ground deploying 1,000 autonomous mobile robots across top 20 sortation hubs by Q3 2025", 0.90),
        ],
    },
    {
        "company": {
            "name": "UPS Supply Chain Solutions",
            "website": "https://www.ups.com/supply-chain",
            "industry": "Logistics",
            "sub_industry": "3PL",
            "employee_estimate": 185000,
            "location_city": "Louisville",
            "location_state": "KY",
            "location_country": "US",
            "source": "seed",
        },
        "signals": [
            ("capex",          "UPS investing $1.4B in network automation including warehouse robotics and autonomous vehicle pilots", 0.89),
            ("strategic_hire", "UPS appoints SVP of Global Logistics Technology to oversee warehouse automation and robotics programs", 0.87),
            ("labor_shortage", "UPS seasonal workforce shortfall: 100,000+ positions unfilled during peak, driving automation urgency", 0.88),
            ("news",           "UPS deploying HAI Robotics and BionicHIVE robot systems at 50 US distribution facilities", 0.85),
        ],
    },
    {
        "company": {
            "name": "GXO Logistics",
            "website": "https://www.gxo.com",
            "industry": "Logistics",
            "sub_industry": "Contract Logistics",
            "employee_estimate": 110000,
            "location_city": "Greenwich",
            "location_state": "CT",
            "location_country": "US",
            "source": "seed",
        },
        "signals": [
            ("capex",          "GXO Logistics commits $500M to warehouse automation: AMRs, goods-to-person systems, robotic picking", 0.91),
            ("strategic_hire", "GXO appoints Chief Technology & Automation Officer at board level; explicit robotics mandate", 0.93),
            ("news",           "GXO CEO: automation is our core differentiator — deploying AMRs at 200+ client fulfillment sites in 2025", 0.90),
            ("job_posting",    "Senior Robotics Systems Engineer | AMR deployment, fleet management, WMS integration at tier-1 3PL", 0.78),
            ("funding_round",  "GXO raises $800M growth equity to accelerate automation technology rollout across North America", 0.86),
        ],
    },
    {
        "company": {
            "name": "C.H. Robinson Worldwide",
            "website": "https://www.chrobinson.com",
            "industry": "Logistics",
            "sub_industry": "Freight Brokerage",
            "employee_estimate": 16000,
            "location_city": "Eden Prairie",
            "location_state": "MN",
            "location_country": "US",
            "source": "seed",
        },
        "signals": [
            ("capex",          "C.H. Robinson investing $1B in technology and automation across logistics network over 3 years", 0.83),
            ("strategic_hire", "C.H. Robinson hires Chief Digital Officer to lead warehouse and cross-dock automation strategy", 0.82),
            ("news",           "C.H. Robinson opens automated cross-dock facility in Chicago with AMR sortation system", 0.79),
        ],
    },
    {
        "company": {
            "name": "J.B. Hunt Transport Services",
            "website": "https://www.jbhunt.com",
            "industry": "Logistics",
            "sub_industry": "Trucking & Intermodal",
            "employee_estimate": 34000,
            "location_city": "Lowell",
            "location_state": "AR",
            "location_country": "US",
            "source": "seed",
        },
        "signals": [
            ("capex",          "J.B. Hunt committing $300M to final-mile and warehouse automation including AMR and drone pilots", 0.82),
            ("strategic_hire", "J.B. Hunt names VP of Warehouse Technology to oversee robotics integration in cross-dock network", 0.83),
            ("expansion",      "J.B. Hunt opening 15 new intermodal facilities in 2025 with automation-first design spec", 0.77),
        ],
    },
    {
        "company": {
            "name": "Lineage Logistics",
            "website": "https://www.lineagelogistics.com",
            "industry": "Logistics",
            "sub_industry": "Cold Storage",
            "employee_estimate": 26000,
            "location_city": "Novi",
            "location_state": "MI",
            "location_country": "US",
            "source": "seed",
        },
        "signals": [
            ("capex",          "Lineage Logistics investing $2B in automated cold storage: robotic retrieval, autonomous forklifts, AS/RS", 0.93),
            ("labor_shortage", "Cold storage labor vacancy rate 45% nationally; Lineage deploying robotics to address chronic shortfall", 0.91),
            ("strategic_hire", "Lineage appoints Chief Robotics Officer to lead AS/RS and AMR deployment across 400+ cold-chain facilities", 0.92),
            ("funding_round",  "Lineage Logistics IPO raises $5.1B; proceeds fund aggressive automation and acquisition strategy", 0.88),
            ("news",           "Lineage deploying autonomous forklifts and goods-to-person systems at 80 US temperature-controlled DCs", 0.89),
        ],
    },
    {
        "company": {
            "name": "Americold Realty Trust",
            "website": "https://www.americold.com",
            "industry": "Logistics",
            "sub_industry": "Cold Storage REIT",
            "employee_estimate": 17000,
            "location_city": "Atlanta",
            "location_state": "GA",
            "location_country": "US",
            "source": "seed",
        },
        "signals": [
            ("capex",          "Americold committing $600M to automated temperature-controlled warehouse builds with AMR integration", 0.88),
            ("labor_shortage", "Americold freezer-level jobs 50% vacant; physical conditions driving turnover, robotics business case clear", 0.92),
            ("strategic_hire", "Americold hires SVP of Automation to lead AGV, robotic picking, and autonomous forklift deployments", 0.89),
            ("expansion",      "Americold breaking ground on 4 new automated cold storage facilities in TX, IL, CA, OH corridors", 0.84),
        ],
    },
    {
        "company": {
            "name": "Performance Food Group",
            "website": "https://www.pfgc.com",
            "industry": "Logistics",
            "sub_industry": "Food Distribution",
            "employee_estimate": 35000,
            "location_city": "Richmond",
            "location_state": "VA",
            "location_country": "US",
            "source": "seed",
        },
        "signals": [
            ("capex",          "Performance Food Group investing $400M in distribution center automation: robotic sortation and case picking", 0.86),
            ("labor_shortage", "PFG warehouse associates turnover at 65% annually; automation ROI justified at major distribution hubs", 0.87),
            ("expansion",      "Performance Food Group acquiring 3 competing food distributors; integrating 12 new DCs requiring standardized automation", 0.81),
            ("strategic_hire", "PFG hires VP of Distribution Technology to standardize operations and deploy automation across network", 0.84),
        ],
    },
    {
        "company": {
            "name": "Sysco Corporation",
            "website": "https://www.sysco.com",
            "industry": "Logistics",
            "sub_industry": "Food Distribution",
            "employee_estimate": 72000,
            "location_city": "Houston",
            "location_state": "TX",
            "location_country": "US",
            "source": "seed",
        },
        "signals": [
            ("capex",          "Sysco investing $1B over 3 years in supply chain automation including robotic picking at 100+ distribution centers", 0.91),
            ("labor_shortage", "Sysco distribution centers running at 70% headcount capacity; warehouse robot pilots showing 3x ROI", 0.90),
            ("strategic_hire", "Sysco appoints Chief Supply Chain Transformation Officer to lead automation initiative across 334 distribution facilities", 0.92),
            ("news",           "Sysco Q3 earnings: labor cost reduction through automation saves $87M annually at 15 pilot sites", 0.88),
        ],
    },
    {
        "company": {
            "name": "US Foods",
            "website": "https://www.usfoods.com",
            "industry": "Logistics",
            "sub_industry": "Food Distribution",
            "employee_estimate": 28000,
            "location_city": "Rosemont",
            "location_state": "IL",
            "location_country": "US",
            "source": "seed",
        },
        "signals": [
            ("capex",          "US Foods approves $350M capital deployment in warehouse automation and delivery route optimization", 0.85),
            ("labor_shortage", "US Foods warehouse turnover exceeds 80% annually; robotics pilot at Rosemont DC returns positive ROI", 0.87),
            ("strategic_hire", "US Foods promotes SVP of Operations to lead national distribution automation strategy", 0.82),
            ("expansion",      "US Foods opening 8 new distribution centers in 2025-2026 designed for AMR integration from day one", 0.79),
        ],
    },
    {
        "company": {
            "name": "NFI Industries",
            "website": "https://www.nfiindustries.com",
            "industry": "Logistics",
            "sub_industry": "3PL",
            "employee_estimate": 16000,
            "location_city": "Cherry Hill",
            "location_state": "NJ",
            "location_country": "US",
            "source": "seed",
        },
        "signals": [
            ("capex",          "NFI Industries investing $200M in automation across 60 fulfillment and distribution facilities", 0.82),
            ("labor_shortage", "NFI fulfillment centers in NJ and CA operating 35% below target headcount, driving robot pilot urgency", 0.86),
            ("news",           "NFI announces robotics-as-a-service contract with two Fortune 500 retailers for automated pick-and-pack", 0.80),
        ],
    },

    # ── Healthcare — Major Systems ──────────────────────────────────────────
    {
        "company": {
            "name": "CommonSpirit Health",
            "website": "https://www.commonspirit.org",
            "industry": "Healthcare",
            "sub_industry": "Health System",
            "employee_estimate": 150000,
            "location_city": "Chicago",
            "location_state": "IL",
            "location_country": "US",
            "source": "seed",
        },
        "signals": [
            ("labor_shortage", "CommonSpirit Health facing critical EVS and patient transport shortage across 140+ hospitals in 21 states", 0.90),
            ("capex",          "CommonSpirit approves $500M operations technology budget including autonomous logistics and disinfection robots", 0.88),
            ("strategic_hire", "CommonSpirit appoints System VP of Clinical Operations Technology to lead robot deployment in hospital facilities", 0.87),
            ("news",           "CommonSpirit Health deploying UV disinfection and linen delivery robots at 25 hospital campuses in 2025", 0.86),
        ],
    },
    {
        "company": {
            "name": "Ascension Health",
            "website": "https://www.ascension.org",
            "industry": "Healthcare",
            "sub_industry": "Health System",
            "employee_estimate": 134000,
            "location_city": "St. Louis",
            "location_state": "MO",
            "location_country": "US",
            "source": "seed",
        },
        "signals": [
            ("labor_shortage", "Ascension Health struggling to fill non-clinical support roles: EVS, dietary, materials management across 140 hospitals", 0.88),
            ("capex",          "Ascension commits $400M to hospital operations technology including autonomous internal logistics robots", 0.85),
            ("news",           "Ascension Health piloting autonomous medication and meal delivery robots at facilities in Indiana and Tennessee", 0.84),
            ("strategic_hire", "Ascension appoints Chief Digital & Technology Officer with explicit mandate for supply chain and facility automation", 0.86),
        ],
    },
    {
        "company": {
            "name": "Advocate Aurora Health",
            "website": "https://www.advocateaurorahealth.org",
            "industry": "Healthcare",
            "sub_industry": "Health System",
            "employee_estimate": 75000,
            "location_city": "Downers Grove",
            "location_state": "IL",
            "location_country": "US",
            "source": "seed",
        },
        "signals": [
            ("labor_shortage", "Advocate Aurora EVS department 42% understaffed; disinfection robot pilot at Midwest campuses showing strong ROI", 0.89),
            ("capex",          "Advocate Aurora $250M technology investment includes autonomous logistics and cleaning robots for hospital intralogistics", 0.84),
            ("news",           "Advocate Aurora expands hospital robot program after successful pilot reduces EVS costs by 18% per room", 0.90),
        ],
    },
    {
        "company": {
            "name": "Kaiser Permanente",
            "website": "https://www.kaiserpermanente.org",
            "industry": "Healthcare",
            "sub_industry": "Integrated Health System",
            "employee_estimate": 213000,
            "location_city": "Oakland",
            "location_state": "CA",
            "location_country": "US",
            "source": "seed",
        },
        "signals": [
            ("capex",          "Kaiser Permanente approves $3B multi-year capital investment in facilities and technology including hospital automation", 0.88),
            ("labor_shortage", "Kaiser Permanente non-clinical support vacancy 38%; unionized workforce constraints driving automation discussions", 0.85),
            ("strategic_hire", "Kaiser appoints SVP of Operations Innovation with mandate for automation of non-clinical hospital services", 0.83),
            ("expansion",      "Kaiser Permanente building 6 new hospitals in CA and WA, all designed with autonomous logistics infrastructure", 0.80),
        ],
    },
    {
        "company": {
            "name": "Tenet Healthcare",
            "website": "https://www.tenethealth.com",
            "industry": "Healthcare",
            "sub_industry": "For-profit Health System",
            "employee_estimate": 110000,
            "location_city": "Dallas",
            "location_state": "TX",
            "location_country": "US",
            "source": "seed",
        },
        "signals": [
            ("labor_shortage", "Tenet Healthcare facing persistent EVS and dietary staff vacancies across 60+ hospitals; contracted agency labor cost 2x internal", 0.87),
            ("capex",          "Tenet approves operations efficiency program: $180M budget includes linen logistics and EVS automation pilots", 0.82),
            ("news",           "Tenet Healthcare CEO mentions autonomous hospital logistics as near-term cost reduction lever in earnings call", 0.85),
            ("strategic_hire", "Tenet recruits VP of Hospital Operations Technology from supply chain automation background", 0.80),
        ],
    },
    {
        "company": {
            "name": "LifePoint Health",
            "website": "https://www.lifepointhealthcom",
            "industry": "Healthcare",
            "sub_industry": "For-profit Health System",
            "employee_estimate": 50000,
            "location_city": "Brentwood",
            "location_state": "TN",
            "location_country": "US",
            "source": "seed",
        },
        "signals": [
            ("labor_shortage", "LifePoint smaller community hospitals face labor shortage more acutely; EVS vacant 50% in rural markets", 0.89),
            ("ma_activity",    "LifePoint acquired by Apollo Global; PE ownership drives margin improvement focus and automation investment", 0.85),
            ("news",           "LifePoint Health piloting autonomous cleaning and transport robots at 12 community hospital sites", 0.84),
        ],
    },
    {
        "company": {
            "name": "Genesis Healthcare",
            "website": "https://www.genesishcc.com",
            "industry": "Healthcare",
            "sub_industry": "Post-Acute Care",
            "employee_estimate": 30000,
            "location_city": "Kennett Square",
            "location_state": "PA",
            "location_country": "US",
            "source": "seed",
        },
        "signals": [
            ("labor_shortage", "Genesis Healthcare skilled nursing facilities: CNA and dietary aide turnover at 90% annually; chronic staffing crisis", 0.91),
            ("news",           "Genesis Healthcare trialing companion and medication delivery robots at skilled nursing facilities in PA and NJ", 0.83),
            ("funding_round",  "Genesis Healthcare secures $120M refinancing to fund SNF modernization including robot-assisted care delivery", 0.79),
        ],
    },
    {
        "company": {
            "name": "Banner Health",
            "website": "https://www.bannerhealth.com",
            "industry": "Healthcare",
            "sub_industry": "Not-for-profit Health System",
            "employee_estimate": 52000,
            "location_city": "Phoenix",
            "location_state": "AZ",
            "location_country": "US",
            "source": "seed",
        },
        "signals": [
            ("capex",          "Banner Health approves $600M capital plan for hospital expansion and technology including autonomous intralogistics", 0.84),
            ("expansion",      "Banner Health opening 3 new hospital campuses in Phoenix metro, each with robot integration spec", 0.81),
            ("strategic_hire", "Banner Health recruits Chief Operations Transformation Officer from logistics automation sector", 0.88),
            ("labor_shortage", "Banner Health EVS and patient transport vacancy 40% in Arizona heat market; retention crisis driving automation urgency", 0.85),
        ],
    },
    {
        "company": {
            "name": "Providence Health & Services",
            "website": "https://www.providence.org",
            "industry": "Healthcare",
            "sub_industry": "Not-for-profit Health System",
            "employee_estimate": 120000,
            "location_city": "Renton",
            "location_state": "WA",
            "location_country": "US",
            "source": "seed",
        },
        "signals": [
            ("capex",          "Providence Health approves $700M innovation investment including autonomous hospital supply chain robots", 0.85),
            ("news",           "Providence Health deploys autonomous supply delivery robots at 5 Pacific Northwest hospitals with plans to expand", 0.87),
            ("strategic_hire", "Providence recruits SVP of Digital Clinical Operations with mandate to automate non-clinical hospital logistics", 0.83),
        ],
    },

    # ── Food Service — Major Chains & Operators ──────────────────────────────
    {
        "company": {
            "name": "McDonald's Corporation",
            "website": "https://corporate.mcdonalds.com",
            "industry": "Food Service",
            "sub_industry": "QSR",
            "employee_estimate": 200000,
            "location_city": "Chicago",
            "location_state": "IL",
            "location_country": "US",
            "source": "seed",
        },
        "signals": [
            ("capex",          "McDonald's commits $2B to restaurant modernization: automated kitchen equipment, robotic fry stations, server robots", 0.91),
            ("labor_shortage", "McDonald's system-wide labor vacancy at 22%; franchisees paying $18-22/hr with sign-on bonuses, still understaffed", 0.90),
            ("strategic_hire", "McDonald's appoints Global VP of Restaurant Technology & Automation to drive kitchen robot deployments", 0.88),
            ("news",           "McDonald's testing food delivery robots in dining room at 200+ US locations; planning national rollout 2026", 0.89),
            ("expansion",      "McDonald's opening 2,000+ new units globally in 2025, all designed with automation-ready kitchen layouts", 0.82),
        ],
    },
    {
        "company": {
            "name": "Starbucks Corporation",
            "website": "https://www.starbucks.com",
            "industry": "Food Service",
            "sub_industry": "Coffee & QSR",
            "employee_estimate": 350000,
            "location_city": "Seattle",
            "location_state": "WA",
            "location_country": "US",
            "source": "seed",
        },
        "signals": [
            ("labor_shortage", "Starbucks partner (employee) turnover at 65% annually; labor shortage creating long wait times and customer satisfaction issues", 0.87),
            ("capex",          "Starbucks Reinvention Plan: $2B investment in store automation, equipment, and technology to reduce partner workload", 0.90),
            ("strategic_hire", "Starbucks appoints Chief Reinvention Officer with explicit focus on automated beverage prep and order fulfillment", 0.86),
            ("news",           "Starbucks piloting automated cold brew and blended beverage station to reduce barista repetitive task burden", 0.85),
        ],
    },
    {
        "company": {
            "name": "Yum! Brands",
            "website": "https://www.yum.com",
            "industry": "Food Service",
            "sub_industry": "QSR",
            "employee_estimate": 36000,
            "location_city": "Louisville",
            "location_state": "KY",
            "location_country": "US",
            "source": "seed",
        },
        "signals": [
            ("capex",          "Yum! Brands investing $1B in restaurant technology: automated cooking, robot servers, delivery optimization across KFC, Taco Bell, Pizza Hut", 0.89),
            ("strategic_hire", "Yum! Brands names new Chief Digital & Technology Officer to drive kitchen automation and robot service pilots", 0.87),
            ("news",           "Yum! Brands deploys robot servers and automated prep equipment at 500 KFC and Taco Bell locations in US and Asia", 0.90),
            ("labor_shortage", "Yum! franchisees across QSR brands reporting 35% crew shortfall; automation mandatory to maintain operating hours", 0.88),
        ],
    },
    {
        "company": {
            "name": "Restaurant Brands International",
            "website": "https://www.rbi.com",
            "industry": "Food Service",
            "sub_industry": "QSR",
            "employee_estimate": 40000,
            "location_city": "Oakville",
            "location_state": "ON",
            "location_country": "CA",
            "source": "seed",
        },
        "signals": [
            ("capex",          "RBI invests $400M in digital and operational transformation for Burger King, Tim Hortons, Popeyes brands", 0.85),
            ("strategic_hire", "RBI appoints President of Operations & Technology to lead restaurant automation across 28,000 global units", 0.87),
            ("news",           "Restaurant Brands International pilots automated beverage station and robot prep at Burger King test markets", 0.83),
            ("labor_shortage", "RBI franchisees across US: 30%+ crew vacancy rate; labor cost as percent of sales at 10-year high", 0.86),
        ],
    },
    {
        "company": {
            "name": "Darden Restaurants",
            "website": "https://www.darden.com",
            "industry": "Food Service",
            "sub_industry": "Casual Dining",
            "employee_estimate": 180000,
            "location_city": "Orlando",
            "location_state": "FL",
            "location_country": "US",
            "source": "seed",
        },
        "signals": [
            ("labor_shortage", "Darden restaurants (Olive Garden, LongHorn Steakhouse): bussers, dishwashers, food runners in short supply", 0.86),
            ("capex",          "Darden approves $250M restaurant tech cycle: back-of-house automation, server robot pilots in casual dining", 0.82),
            ("news",           "Darden testing busser and food delivery robots at LongHorn Steakhouse units in Florida; positive guest data", 0.85),
            ("strategic_hire", "Darden hires VP of Restaurant Innovation & Technology with automation delivery mandate", 0.81),
        ],
    },
    {
        "company": {
            "name": "Compass Group USA",
            "website": "https://www.compass-usa.com",
            "industry": "Food Service",
            "sub_industry": "Contract Food Service",
            "employee_estimate": 250000,
            "location_city": "Charlotte",
            "location_state": "NC",
            "location_country": "US",
            "source": "seed",
        },
        "signals": [
            ("labor_shortage", "Compass Group: largest contract food service company in US with 250,000 hourly workers; turnover at 70% annually", 0.90),
            ("capex",          "Compass Group North America invests $300M in automation: autonomous food prep, server robots for hospitals and campuses", 0.87),
            ("strategic_hire", "Compass Group appoints Chief Automation Officer to industrialize robot deployment across healthcare and corporate dining segments", 0.91),
            ("news",           "Compass Group deploying delivery and cleaning robots at 120 hospital cafeterias and university foodservice sites", 0.89),
            ("expansion",      "Compass Group wins 50+ new healthcare and higher-ed foodservice contracts; robot-enabled service model cited as differentiator", 0.84),
        ],
    },
    {
        "company": {
            "name": "Aramark Corporation",
            "website": "https://www.aramark.com",
            "industry": "Food Service",
            "sub_industry": "Uniform & Food Services",
            "employee_estimate": 280000,
            "location_city": "Philadelphia",
            "location_state": "PA",
            "location_country": "US",
            "source": "seed",
        },
        "signals": [
            ("labor_shortage", "Aramark reporting 65% turnover in food service and facility management workforce; labor spend 15% over budget", 0.89),
            ("capex",          "Aramark approves $500M three-year capital plan; includes automated serving stations and cleaning robots at managed venues", 0.86),
            ("strategic_hire", "Aramark names new EVP of Operations Technology; mandate includes robot-assisted service at stadium, hospital, and campus accounts", 0.88),
            ("news",           "Aramark rolls out food delivery robots at 30 corporate campus dining accounts in San Jose and New York", 0.86),
        ],
    },
    {
        "company": {
            "name": "Delaware North Companies",
            "website": "https://www.delawarenorth.com",
            "industry": "Food Service",
            "sub_industry": "Sports & Entertainment Food Service",
            "employee_estimate": 55000,
            "location_city": "Buffalo",
            "location_state": "NY",
            "location_country": "US",
            "source": "seed",
        },
        "signals": [
            ("labor_shortage", "Delaware North stadium food service: event-day hiring impossible in post-COVID labor market; robots filling gaps", 0.88),
            ("news",           "Delaware North deploys food delivery robots and automated beverage stations at NBA and NFL stadium accounts", 0.87),
            ("capex",          "Delaware North invests $100M in venue technology and operational automation across sports and entertainment segment", 0.80),
            ("strategic_hire", "Delaware North hires VP of Technology Innovation with background in food service automation and robotics", 0.83),
        ],
    },
    {
        "company": {
            "name": "Shake Shack",
            "website": "https://www.shakeshack.com",
            "industry": "Food Service",
            "sub_industry": "Better Burger Fast Casual",
            "employee_estimate": 10000,
            "location_city": "New York",
            "location_state": "NY",
            "location_country": "US",
            "source": "seed",
        },
        "signals": [
            ("capex",          "Shake Shack investing $50M in kitchen automation and digital guest experience at high-volume urban locations", 0.79),
            ("news",           "Shake Shack pilots automated beverage prep and automated tray delivery at flagship NYC and Chicago units", 0.82),
            ("job_posting",    "Director of Restaurant Technology | kitchen automation, order fulfillment systems, robot integration pilot lead", 0.78),
        ],
    },
    {
        "company": {
            "name": "Wingstop Restaurants",
            "website": "https://www.wingstop.com",
            "industry": "Food Service",
            "sub_industry": "QSR",
            "employee_estimate": 3200,
            "location_city": "Addison",
            "location_state": "TX",
            "location_country": "US",
            "source": "seed",
        },
        "signals": [
            ("expansion",      "Wingstop fastest growing QSR in US: 2,000+ locations and adding 250+ units annually; labor-light digital model", 0.80),
            ("capex",          "Wingstop investing $75M in fryer automation and order routing technology across domestic store base", 0.78),
            ("labor_shortage", "Wingstop franchisees: kitchen crew vacancy 38% in top markets; automated frying and order assembly reduces headcount need", 0.83),
        ],
    },
    {
        "company": {
            "name": "Panera Bread",
            "website": "https://www.panerabread.com",
            "industry": "Food Service",
            "sub_industry": "Fast Casual",
            "employee_estimate": 100000,
            "location_city": "St. Louis",
            "location_state": "MO",
            "location_country": "US",
            "source": "seed",
        },
        "signals": [
            ("capex",          "Panera Bread approves $300M restaurant technology plan: automated bakery, soup dispensing, and order fulfillment systems", 0.84),
            ("labor_shortage", "Panera associates turnover at 75%; labor cost creeping to 36% of sales as minimum wage rises accelerate", 0.87),
            ("news",           "Panera rolling out automated espresso mach and soup dispensers to standardize quality and reduce labor dependency", 0.83),
            ("strategic_hire", "Panera appoints Chief Restaurant Officer with explicit mandate for back-of-house automation deployment", 0.85),
        ],
    },
    {
        "company": {
            "name": "Brinker International",
            "website": "https://www.brinker.com",
            "industry": "Food Service",
            "sub_industry": "Casual Dining",
            "employee_estimate": 60000,
            "location_city": "Dallas",
            "location_state": "TX",
            "location_country": "US",
            "source": "seed",
        },
        "signals": [
            ("labor_shortage", "Chili's and Maggiano's (Brinker): server, busser, and dishwasher shortage driving 20% reduction in dining room seating capacity", 0.86),
            ("news",           "Brinker International CEO publicly endorses server robot trials at Chili's to address front-of-house staffing shortfall", 0.89),
            ("capex",          "Brinker approves $120M restaurant tech investment cycle; automation equipment and robot server pilot included", 0.82),
            ("strategic_hire", "Brinker hires VP of Restaurant Innovation to evaluate and deploy front-of-house service robots across the system", 0.87),
        ],
    },
    {
        "company": {
            "name": "Texas Roadhouse",
            "website": "https://www.texasroadhouse.com",
            "industry": "Food Service",
            "sub_industry": "Casual Dining",
            "employee_estimate": 80000,
            "location_city": "Louisville",
            "location_state": "KY",
            "location_country": "US",
            "source": "seed",
        },
        "signals": [
            ("labor_shortage", "Texas Roadhouse adding $20M+ annually in recruiting and retention costs; busser and dishwasher roles toughest to fill", 0.85),
            ("expansion",      "Texas Roadhouse opening 30+ new restaurants annually with new-build kitchens specification including automation-ready layout", 0.79),
            ("job_posting",    "Director of Restaurant Operations Technology | evaluate automation solutions for back-of-house and guest delivery", 0.77),
        ],
    },

    # ── Senior Living / Post-Acute ──────────────────────────────────────────
    {
        "company": {
            "name": "Sunrise Senior Living",
            "website": "https://www.sunriseseniorliving.com",
            "industry": "Healthcare",
            "sub_industry": "Senior Living",
            "employee_estimate": 30000,
            "location_city": "McLean",
            "location_state": "VA",
            "location_country": "US",
            "source": "seed",
        },
        "signals": [
            ("labor_shortage", "Sunrise Senior Living: caregiver, dining aide, and housekeeping vacancy at 45% across 270+ communities", 0.91),
            ("news",           "Sunrise Senior Living piloting companion robots and meal delivery robots at 15 US communities in 2025", 0.87),
            ("capex",          "Sunrise invests $80M in resident experience technology including robot-assisted care and smart community systems", 0.79),
            ("strategic_hire", "Sunrise appoints Chief Care Innovation Officer to lead robotic care assistant and automation program", 0.83),
        ],
    },
    {
        "company": {
            "name": "Atria Senior Living",
            "website": "https://www.atriaseniorliving.com",
            "industry": "Healthcare",
            "sub_industry": "Senior Living",
            "employee_estimate": 11000,
            "location_city": "Louisville",
            "location_state": "KY",
            "location_country": "US",
            "source": "seed",
        },
        "signals": [
            ("labor_shortage", "Atria Senior Living communities: dining services and housekeeping 50% understaffed; relying heavily on agency labor", 0.90),
            ("news",           "Atria partners with robotics startup to deploy meal delivery and housekeeping assist robots at upscale communities", 0.85),
            ("expansion",      "Atria Senior Living acquiring 30 communities from Welltower; inherited labor challenges accelerate automation push", 0.80),
        ],
    },

    # ── Retail Logistics ────────────────────────────────────────────────────
    {
        "company": {
            "name": "Target Corporation",
            "website": "https://corporate.target.com",
            "industry": "Logistics",
            "sub_industry": "Retail Distribution",
            "employee_estimate": 390000,
            "location_city": "Minneapolis",
            "location_state": "MN",
            "location_country": "US",
            "source": "seed",
        },
        "signals": [
            ("capex",          "Target investing $3B in supply chain automation: robotic sortation, order-picking robots, autonomous distribution center tech", 0.89),
            ("expansion",      "Target opening 20 new sortation centers with automation-first design; 100 existing DCs slated for robotics retrofit", 0.87),
            ("strategic_hire", "Target appoints Chief Supply Chain Officer with explicit operational robotics mandate", 0.85),
            ("labor_shortage", "Target distribution fulfillment centers running 30% below headcount; sortation robot pilots show 4x throughput improvement", 0.86),
            ("news",           "Target deploying Symbotic warehouse robotics at 28 regional distribution centers; $500M contract announced", 0.90),
        ],
    },
    {
        "company": {
            "name": "Kroger Company",
            "website": "https://www.thekrogerco.com",
            "industry": "Logistics",
            "sub_industry": "Grocery Distribution",
            "employee_estimate": 430000,
            "location_city": "Cincinnati",
            "location_state": "OH",
            "location_country": "US",
            "source": "seed",
        },
        "signals": [
            ("capex",          "Kroger investing $1.5B in automated customer fulfillment centers: robotic picking, autonomous sortation, cold chain automation", 0.91),
            ("strategic_hire", "Kroger appoints VP of Supply Chain Robotics to oversee Ocado-powered automated fulfillment center rollout", 0.89),
            ("news",           "Kroger opening 4th Ocado-powered automated fulfillment center in Texas; 24 more planned nationally by 2027", 0.90),
            ("labor_shortage", "Kroger warehouse associates turnover at 80%; automated fulfillment centers need 80% fewer workers per unit of throughput", 0.87),
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
