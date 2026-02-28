"""
seed_leads_v2.py — Bulk lead expansion across 6 industries, NA + UK/EU

Usage:
  python scripts/seed_leads_v2.py           # dry-run count
  python scripts/seed_leads_v2.py --commit  # write to DB
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

from app.database import SessionLocal, Base, engine
import app.models
Base.metadata.create_all(bind=engine)

from app.models.company import Company
from app.models.signal import Signal
from app.models.score import Score
from app.services.inference_engine import analyze_signals

# ─────────────────────────────────────────────────────────────────────────────
# LEAD DATA  — 150+ companies, 6 industries, North America + UK/EU
# ─────────────────────────────────────────────────────────────────────────────
NEW_LEADS = [

    # =========================================================================
    # AIRPORTS & TRANSPORTATION HUBS
    # =========================================================================
    {
        "company": {
            "name": "Swissport International",
            "website": "https://www.swissport.com",
            "industry": "Airports & Transportation",
            "sub_industry": "Ground Handling",
            "employee_estimate": 64000,
            "location_city": "Zurich",
            "location_state": "",
            "location_country": "CH",
            "source": "seed_v2",
        },
        "signals": [
            ("labor_shortage", "Swissport ground handling crews 38% vacant at major European airports; baggage and cargo operations critically understaffed", 0.91),
            ("capex",          "Swissport investing EUR 400M in operational automation: autonomous baggage carts, ground support equipment, cargo handling robots", 0.88),
            ("strategic_hire", "Swissport appoints Global Chief Operations Technology Officer to lead robotics and automation across 300 airport stations", 0.89),
            ("news",           "Swissport deploys autonomous baggage handling robots at Frankfurt, Amsterdam, and Zurich hubs; expanding to 20 more airports", 0.87),
            ("expansion",      "Swissport awarded new ground handling contracts at 15 airports; all new contracts include automation-first service model", 0.82),
        ],
    },
    {
        "company": {
            "name": "Menzies Aviation",
            "website": "https://www.menziesaviation.com",
            "industry": "Airports & Transportation",
            "sub_industry": "Ground Handling",
            "employee_estimate": 38000,
            "location_city": "Edinburgh",
            "location_state": "",
            "location_country": "GB",
            "source": "seed_v2",
        },
        "signals": [
            ("labor_shortage", "Menzies Aviation ground crews 45% below required staffing at US and UK airports; flight delays attributed to worker shortage", 0.92),
            ("capex",          "Menzies Aviation commits $150M to automated baggage and cargo equipment to reduce reliance on manual labour", 0.86),
            ("news",           "Menzies Aviation CEO: ground handling labour market is broken; autonomous vehicles are not optional any more", 0.88),
            ("strategic_hire", "Menzies hires VP of Innovation & Automation to identify and deploy autonomous ground support equipment globally", 0.84),
        ],
    },
    {
        "company": {
            "name": "Gate Gourmet (Gategroup)",
            "website": "https://www.gategroup.com",
            "industry": "Airports & Transportation",
            "sub_industry": "Airline Catering",
            "employee_estimate": 43000,
            "location_city": "Zurich",
            "location_state": "",
            "location_country": "CH",
            "source": "seed_v2",
        },
        "signals": [
            ("labor_shortage", "Gate Gourmet airline catering kitchens 40% understaffed post-COVID; meal assembly lines operating at reduced capacity", 0.90),
            ("capex",          "Gategroup investing $200M in catering kitchen automation: robotic tray assembly, autonomous trolley transport, meal delivery systems", 0.87),
            ("news",           "Gate Gourmet deploys collaborative robots in flight kitchen operations at Heathrow, JFK, and LAX catering centres", 0.86),
            ("strategic_hire", "Gategroup appoints SVP of Operational Technology to lead kitchen automation and autonomous trolley deployment", 0.85),
        ],
    },
    {
        "company": {
            "name": "LSG Sky Chefs",
            "website": "https://www.lsggroup.com",
            "industry": "Airports & Transportation",
            "sub_industry": "Airline Catering",
            "employee_estimate": 28000,
            "location_city": "Neu-Isenburg",
            "location_state": "",
            "location_country": "DE",
            "source": "seed_v2",
        },
        "signals": [
            ("labor_shortage", "LSG Sky Chefs flight kitchen staffing at 60% capacity in North America and Europe; meal production below contract levels", 0.89),
            ("capex",          "LSG Group approves EUR 120M automation investment in flight catering kitchen robotics and autonomous logistics", 0.84),
            ("news",           "LSG Sky Chefs testing robot-assisted meal tray assembly at Chicago O'Hare and Dallas Fort Worth catering facilities", 0.85),
        ],
    },
    {
        "company": {
            "name": "ABM Industries",
            "website": "https://www.abm.com",
            "industry": "Airports & Transportation",
            "sub_industry": "Facilities & Airport Services",
            "employee_estimate": 100000,
            "location_city": "New York",
            "location_state": "NY",
            "location_country": "US",
            "source": "seed_v2",
        },
        "signals": [
            ("labor_shortage", "ABM Industries airport cleaning and facility contracts running 35% below headcount; janitorial turnover exceeds 90% annually", 0.91),
            ("capex",          "ABM Industries investing $150M in autonomous cleaning robots for airport terminals, convention centers, and commercial buildings", 0.87),
            ("news",           "ABM deploys autonomous scrubbers and disinfection robots at LAX, O'Hare, and Dallas Fort Worth terminals", 0.90),
            ("strategic_hire", "ABM appoints Chief Innovation Officer to scale autonomous cleaning and facility robot fleet to 5,000 units", 0.88),
            ("expansion",      "ABM wins new janitorial contracts at 8 major US airports and 3 international airport terminals; robot-enabled bids cited as differentiator", 0.83),
        ],
    },
    {
        "company": {
            "name": "Sodexo Airport Services",
            "website": "https://www.sodexo.com/airports",
            "industry": "Airports & Transportation",
            "sub_industry": "Airport Food Service & Facilities",
            "employee_estimate": 22000,
            "location_city": "Gaithersburg",
            "location_state": "MD",
            "location_country": "US",
            "source": "seed_v2",
        },
        "signals": [
            ("labor_shortage", "Sodexo airport concession operations 40% understaffed at major US hubs; traveler count back to 2019 levels but workers are not", 0.88),
            ("news",           "Sodexo launches robot food delivery and autonomous concession service trial at Minneapolis-Saint Paul and Houston airports", 0.86),
            ("capex",          "Sodexo allocates $80M to airport operations automation including self-service kiosks and autonomous delivery systems", 0.82),
        ],
    },
    {
        "company": {
            "name": "HMSHost",
            "website": "https://www.hmshost.com",
            "industry": "Airports & Transportation",
            "sub_industry": "Airport Restaurant Operator",
            "employee_estimate": 40000,
            "location_city": "Bethesda",
            "location_state": "MD",
            "location_country": "US",
            "source": "seed_v2",
        },
        "signals": [
            ("labor_shortage", "HMSHost airport restaurants operating with 30-40% crew shortage; traveller complaint scores rising as service degrades", 0.89),
            ("capex",          "HMSHost invests $120M in airport restaurant automation: self-order kiosks, automated beverage stations, kitchen robotics", 0.84),
            ("news",           "HMSHost partners with robot food service company to run fully automated quick-service restaurant pod at Atlanta Hartsfield", 0.87),
            ("strategic_hire", "HMSHost appoints Director of Restaurant Innovation to lead automation and robot restaurant concepts in airport terminals", 0.83),
        ],
    },
    {
        "company": {
            "name": "Prospect Airport Services",
            "website": "https://www.prospectairportservices.com",
            "industry": "Airports & Transportation",
            "sub_industry": "Passenger Assistance & Cleaning",
            "employee_estimate": 8000,
            "location_city": "Chicago",
            "location_state": "IL",
            "location_country": "US",
            "source": "seed_v2",
        },
        "signals": [
            ("labor_shortage", "Prospect Airport Services passenger assist and skycap roles 50% vacant at ORD and midway; robot-assist programs being evaluated", 0.88),
            ("news",           "Prospect deploying autonomous floor scrubbers and guide robots for mobility-impaired passengers at Chicago airports", 0.83),
        ],
    },
    {
        "company": {
            "name": "SATS Ltd",
            "website": "https://www.sats.com.sg",
            "industry": "Airports & Transportation",
            "sub_industry": "Ground Handling & Catering",
            "employee_estimate": 45000,
            "location_city": "Singapore",
            "location_state": "",
            "location_country": "SG",
            "source": "seed_v2",
        },
        "signals": [
            ("capex",          "SATS investing SGD 500M in kitchen and ground handling automation; robotic meal assembly lines and autonomous cargo vehicles", 0.90),
            ("strategic_hire", "SATS appoints Group Chief Digital & Technology Officer to lead automated kitchen and ground handling transformation", 0.88),
            ("expansion",      "SATS acquires Worldwide Flight Services in Europe; integrating 30,000 employees and deploying automation across combined network", 0.87),
            ("news",           "SATS announces full robotic meal tray assembly line at Changi Airport catering centre; expanding to 6 more hubs", 0.89),
        ],
    },
    {
        "company": {
            "name": "dnata",
            "website": "https://www.dnata.com",
            "industry": "Airports & Transportation",
            "sub_industry": "Ground Handling",
            "employee_estimate": 58000,
            "location_city": "Dubai",
            "location_state": "",
            "location_country": "AE",
            "source": "seed_v2",
        },
        "signals": [
            ("capex",          "dnata investing AED 1B in ground handling automation: autonomous baggage vehicles, robotic cargo loading, kitchen robots", 0.91),
            ("strategic_hire", "dnata appoints Chief Technology & Innovation Officer to oversee autonomous ground handling deployment at 35 countries", 0.88),
            ("news",           "dnata deploys autonomous baggage tractors at Dubai International, with US airport rollout planned for JFK and JFK", 0.87),
            ("expansion",      "dnata expanding ground handling operations to 12 new North American and European airports, all with automation-first spec", 0.84),
        ],
    },

    # =========================================================================
    # UK / EU HOSPITALITY
    # =========================================================================
    {
        "company": {
            "name": "Whitbread (Premier Inn)",
            "website": "https://www.whitbread.co.uk",
            "industry": "Hospitality",
            "sub_industry": "Hotel Chain",
            "employee_estimate": 35000,
            "location_city": "London",
            "location_state": "",
            "location_country": "GB",
            "source": "seed_v2",
        },
        "signals": [
            ("labor_shortage", "Premier Inn housekeeping vacancy 42% across 800+ UK hotels; wages rising 15% annually, still insufficient to fill roles", 0.90),
            ("capex",          "Whitbread commits GBP 250M to property operations technology including autonomous housekeeping and room service robots", 0.86),
            ("strategic_hire", "Whitbread appoints Head of Operations Technology to deploy robot-assisted housekeeping and public area cleaning", 0.84),
            ("expansion",      "Whitbread fastest-growing hotel company in UK; adding 8,000 rooms annually including Germany expansion", 0.80),
            ("news",           "Premier Inn tests room service delivery robots at London and Manchester flagship hotels with positive guest feedback", 0.85),
        ],
    },
    {
        "company": {
            "name": "Accor Hotels",
            "website": "https://www.accor.com",
            "industry": "Hospitality",
            "sub_industry": "Hotel Chain",
            "employee_estimate": 230000,
            "location_city": "Paris",
            "location_state": "",
            "location_country": "FR",
            "source": "seed_v2",
        },
        "signals": [
            ("labor_shortage", "Accor group hotels across France, UK, Germany, Benelux: housekeeping and F&B roles 35% vacant post-COVID", 0.88),
            ("capex",          "Accor investing EUR 300M in hotel technology transformation including service robots for housekeeping and delivery across brands", 0.85),
            ("strategic_hire", "Accor appoints Chief Digital Officer with innovation mandate including robotic guest services and AI-powered hotel operations", 0.83),
            ("news",           "Accor deploying room delivery robots at ibis, Novotel, and Mercure brands in France and UK pilot cities", 0.84),
            ("expansion",      "Accor expanding pipeline by 300 hotels in Europe and Middle East; automation-ready specifications in all new builds", 0.79),
        ],
    },
    {
        "company": {
            "name": "Radisson Hotel Group",
            "website": "https://www.radissonhotels.com",
            "industry": "Hospitality",
            "sub_industry": "Hotel Chain",
            "employee_estimate": 95000,
            "location_city": "Brussels",
            "location_state": "",
            "location_country": "BE",
            "source": "seed_v2",
        },
        "signals": [
            ("labor_shortage", "Radisson Blu and Park Inn properties across Nordics, UK, Germany: housekeeping vacancy at record levels", 0.86),
            ("capex",          "Radisson Hotel Group investing EUR 150M in operations technology including autonomous housekeeping and delivery robots", 0.83),
            ("news",           "Radisson Blu deploys delivery robots and autonomous public area cleaners at flagship European hotels in 2025", 0.84),
            ("strategic_hire", "Radisson appoints Group VP of Innovation & Technology to drive smart hotel and service robot deployments", 0.82),
        ],
    },
    {
        "company": {
            "name": "NH Hotels (Minor Hotels Europe)",
            "website": "https://www.nh-hotels.com",
            "industry": "Hospitality",
            "sub_industry": "Hotel Chain",
            "employee_estimate": 20000,
            "location_city": "Madrid",
            "location_state": "",
            "location_country": "ES",
            "source": "seed_v2",
        },
        "signals": [
            ("labor_shortage", "NH Hotels properties in Spain, Italy, and Netherlands: 40% housekeeping vacancy; minimum wage rises accelerating automation ROI", 0.87),
            ("news",           "NH Hotels deploys delivery robots and autonomous cleaning systems at Amsterdam, Barcelona, and Rome flagship hotels", 0.83),
            ("strategic_hire", "NH Hotels appoints Head of Smart Hotel Operations to scale robot deployments across 350-property European portfolio", 0.80),
        ],
    },
    {
        "company": {
            "name": "Soho House Group",
            "website": "https://www.sohohouse.com",
            "industry": "Hospitality",
            "sub_industry": "Members Club & Hotel",
            "employee_estimate": 10000,
            "location_city": "London",
            "location_state": "",
            "location_country": "GB",
            "source": "seed_v2",
        },
        "signals": [
            ("labor_shortage", "Soho House London, NY, LA, Chicago: F&B and housekeeping 35% vacant; high labour cost squeezing membership economics", 0.84),
            ("expansion",      "Soho House opening 12 new clubs globally in next 18 months; operational efficiency is critical path to profitability", 0.81),
            ("funding_round",  "Soho House secures $200M growth equity to fund global expansion and operations modernisation program", 0.79),
        ],
    },
    {
        "company": {
            "name": "Jurys Inn (Amaris Hospitality)",
            "website": "https://www.jurysinns.com",
            "industry": "Hospitality",
            "sub_industry": "Budget Hotel Chain",
            "employee_estimate": 5000,
            "location_city": "Dublin",
            "location_state": "",
            "location_country": "IE",
            "source": "seed_v2",
        },
        "signals": [
            ("labor_shortage", "Jurys Inn and Leonardo Hotels: housekeeping vacancies at 45% across UK and Ireland portfolio", 0.87),
            ("news",           "Amaris Hospitality trialling room service delivery robots at six Jurys Inn properties in London and Dublin", 0.84),
            ("capex",          "Amaris committing GBP 50M to property operations technology and autonomous service deployment across portfolio", 0.80),
        ],
    },
    {
        "company": {
            "name": "Intercontinental Hotels Group – EMEAA",
            "website": "https://www.ihg.com/emeaa",
            "industry": "Hospitality",
            "sub_industry": "Hotel Chain",
            "employee_estimate": 25000,
            "location_city": "Windsor",
            "location_state": "",
            "location_country": "GB",
            "source": "seed_v2",
        },
        "signals": [
            ("labor_shortage", "IHG EMEAA: Holiday Inn and Crowne Plaza franchisees in UK, Germany, France facing acute housekeeping staffing crisis", 0.87),
            ("capex",          "IHG EMEAA investing GBP 100M in hotel technology upgrade programme including autonomous delivery robots at select-service brands", 0.82),
            ("news",           "IHG pilots delivery robot and front-desk automation at UK and German Holiday Inn Express properties", 0.83),
        ],
    },
    {
        "company": {
            "name": "Meininger Hotels",
            "website": "https://www.meininger-hotels.com",
            "industry": "Hospitality",
            "sub_industry": "Hybrid Budget Hotel",
            "employee_estimate": 1800,
            "location_city": "Berlin",
            "location_state": "",
            "location_country": "DE",
            "source": "seed_v2",
        },
        "signals": [
            ("labor_shortage", "Meininger Hotels: lean hybrid hotel model depends on small staff; housekeeping vacancies forcing operational innovation", 0.86),
            ("news",           "Meininger Hotels tests autonomous cleaning robots at Berlin and Vienna properties; staffing supplement use case confirmed", 0.82),
            ("expansion",      "Meininger Hotels expanding to 8 new European cities; low-cost operations model requires automated housekeeping at scale", 0.79),
        ],
    },
    {
        "company": {
            "name": "Britannia Hotels",
            "website": "https://www.britanniahotels.com",
            "industry": "Hospitality",
            "sub_industry": "Hotel Chain",
            "employee_estimate": 6000,
            "location_city": "Manchester",
            "location_state": "",
            "location_country": "GB",
            "source": "seed_v2",
        },
        "signals": [
            ("labor_shortage", "Britannia Hotels: UK hotel group with 50+ properties; housekeeping and F&B vacancy at 50%, highest in portfolio history", 0.90),
            ("job_posting",    "Director of Operations Technology | housekeeping automation, cleaning robots, operational cost reduction", 0.79),
            ("news",           "Britannia Hotels evaluating autonomous housekeeping robot program after 3-property pilot shows 25% labour cost reduction", 0.85),
        ],
    },
    {
        "company": {
            "name": "Travelodge UK",
            "website": "https://www.travelodge.co.uk",
            "industry": "Hospitality",
            "sub_industry": "Budget Hotel Chain",
            "employee_estimate": 12000,
            "location_city": "Thame",
            "location_state": "",
            "location_country": "GB",
            "source": "seed_v2",
        },
        "signals": [
            ("labor_shortage", "Travelodge UK: budget hotel model hit hardest by minimum wage increases; housekeeping per-room cost up 40% since 2022", 0.89),
            ("capex",          "Travelodge UK approves GBP 75M investment in operational efficiency including autonomous cleaning robots and self-check-in tech", 0.84),
            ("job_posting",    "Head of Property Operations Technology | autonomous cleaning, room servicing robots, cost reduction programme", 0.78),
        ],
    },

    # =========================================================================
    # UK / EU LOGISTICS
    # =========================================================================
    {
        "company": {
            "name": "DPD Group (GeoPost)",
            "website": "https://www.dpd.com",
            "industry": "Logistics",
            "sub_industry": "Parcel Delivery",
            "employee_estimate": 120000,
            "location_city": "Issy-les-Moulineaux",
            "location_state": "",
            "location_country": "FR",
            "source": "seed_v2",
        },
        "signals": [
            ("capex",          "DPD Group investing EUR 600M in depot automation: robotic sortation, autonomous parcel handling, conveyor AI across EU network", 0.90),
            ("labor_shortage", "DPD parcel depots 40% below headcount across UK, Germany, France; sortation robots delivering 5x throughput improvement", 0.88),
            ("strategic_hire", "DPD Group appoints Group Chief Digital Officer to lead warehouse and depot automation across 230 facilities", 0.86),
            ("news",           "DPD UK deploying autonomous parcel sortation robots at Birmingham, Manchester, and London super-depots", 0.87),
        ],
    },
    {
        "company": {
            "name": "Evri (formerly Hermes UK)",
            "website": "https://www.evri.com",
            "industry": "Logistics",
            "sub_industry": "Parcel Delivery",
            "employee_estimate": 9000,
            "location_city": "Morley",
            "location_state": "",
            "location_country": "GB",
            "source": "seed_v2",
        },
        "signals": [
            ("capex",          "Evri committing GBP 200M to parcel hub automation: robotic sorting arms, autonomous guided vehicles, AI routing", 0.87),
            ("labor_shortage", "Evri depot operations chronically understaffed; courier gig worker model introducing reliability issues driving automation urgency", 0.85),
            ("news",           "Evri opens fully automated parcel hub in Leeds with 200 sortation robots; halving manual handling costs", 0.88),
            ("expansion",      "Evri adding 12 new automated parcel hubs in UK by end of 2026 to meet e-commerce growth", 0.82),
        ],
    },
    {
        "company": {
            "name": "Kuehne + Nagel International",
            "website": "https://www.kuehne-nagel.com",
            "industry": "Logistics",
            "sub_industry": "Freight Forwarding & Logistics",
            "employee_estimate": 79000,
            "location_city": "Schindellegi",
            "location_state": "",
            "location_country": "CH",
            "source": "seed_v2",
        },
        "signals": [
            ("capex",          "Kuehne + Nagel commits CHF 500M to warehouse automation: AMRs, robotic picking, autonomous forklifts at 200+ global DCs", 0.89),
            ("strategic_hire", "K+N appoints Chief Technology Officer with explicit mandate for warehouse robotics and automation transformation programme", 0.87),
            ("news",           "Kuehne + Nagel deploying Locus Robotics and Geek+ AMRs at 30 European and North American fulfilment centres", 0.86),
            ("labor_shortage", "K+N warehouse workers in Germany, Netherlands, Benelux 35% below target headcount; robots deployed as structural fix", 0.84),
        ],
    },
    {
        "company": {
            "name": "DB Schenker",
            "website": "https://www.dbschenker.com",
            "industry": "Logistics",
            "sub_industry": "Freight & Logistics",
            "employee_estimate": 76000,
            "location_city": "Frankfurt",
            "location_state": "",
            "location_country": "DE",
            "source": "seed_v2",
        },
        "signals": [
            ("capex",          "DB Schenker investing EUR 400M in warehouse and freight terminal automation including AMR fleet expansion across Germany", 0.88),
            ("strategic_hire", "DB Schenker names new Global Head of Innovation & Automation; mandate includes 1,000 robot deployment target", 0.86),
            ("news",           "DB Schenker deploys autonomous mobile robots at Munich, Hamburg, and Leipzig freight facilities; expanding to 30 EU locations", 0.85),
            ("labor_shortage", "DB Schenker German warehouse staffing 30% below target; Works Council negotiating robot co-deployment agreement", 0.83),
        ],
    },
    {
        "company": {
            "name": "Wincanton",
            "website": "https://www.wincanton.co.uk",
            "industry": "Logistics",
            "sub_industry": "Contract Logistics",
            "employee_estimate": 19000,
            "location_city": "Chippenham",
            "location_state": "",
            "location_country": "GB",
            "source": "seed_v2",
        },
        "signals": [
            ("labor_shortage", "Wincanton UK 3PL: warehouse and transport roles 38% vacant across 180 sites; post-Brexit labour market structurally broken", 0.91),
            ("capex",          "Wincanton committing GBP 100M to automated warehouse operations: AMRs, goods-to-person systems, robotic pick and pack", 0.86),
            ("news",           "Wincanton wins major retail client by demonstrating robot-staffed fulfilment centre concept in Bristol", 0.84),
            ("ma_activity",    "Wincanton acquired by CEVA Logistics; combined entity accelerating automation investment across UK network", 0.82),
        ],
    },
    {
        "company": {
            "name": "GEODIS",
            "website": "https://www.geodis.com",
            "industry": "Logistics",
            "sub_industry": "Supply Chain & Logistics",
            "employee_estimate": 49000,
            "location_city": "Paris",
            "location_state": "",
            "location_country": "FR",
            "source": "seed_v2",
        },
        "signals": [
            ("capex",          "GEODIS investing EUR 250M in automated warehouse solutions: AMR, robotic picking, automated crossdocking across EU and US", 0.87),
            ("strategic_hire", "GEODIS appoints Chief Supply Chain Transformation Officer to lead robotics and AI programme across global network", 0.85),
            ("news",           "GEODIS deploys autonomous mobile robots at 25 fulfilment sites in France, Germany, and US; 40% throughput improvement reported", 0.86),
            ("expansion",      "GEODIS opening 8 new automated distribution centres in Europe and North America to serve e-commerce growth", 0.81),
        ],
    },
    {
        "company": {
            "name": "Ceva Logistics",
            "website": "https://www.cevalogistics.com",
            "industry": "Logistics",
            "sub_industry": "Contract Logistics",
            "employee_estimate": 85000,
            "location_city": "Marseille",
            "location_state": "",
            "location_country": "FR",
            "source": "seed_v2",
        },
        "signals": [
            ("capex",          "CEVA Logistics commits USD 350M to automation: robotic palletising, AMR fleets, autonomous dock equipment across global network", 0.86),
            ("labor_shortage", "CEVA Logistics European operations 33% below headcount; minimum wage rises in France and Germany driving automation urgency", 0.84),
            ("strategic_hire", "CEVA Logistics names SVP of Operations Technology to drive robot deployment across 1,000-site global contract logistics network", 0.85),
        ],
    },
    {
        "company": {
            "name": "Royal Mail (International Distribution)",
            "website": "https://www.royalmail.com",
            "industry": "Logistics",
            "sub_industry": "Postal & Parcel",
            "employee_estimate": 140000,
            "location_city": "London",
            "location_state": "",
            "location_country": "GB",
            "source": "seed_v2",
        },
        "signals": [
            ("capex",          "Royal Mail investing GBP 700M in parcel network automation: robotic sortation, autonomous handling equipment, AMR pilots", 0.88),
            ("labor_shortage", "Royal Mail warehouse and sortation roles 28% vacant; union agreements now include robot co-deployment clauses", 0.83),
            ("strategic_hire", "Royal Mail appoints Chief Transformation Officer to oversee automation of 37 parcel hubs", 0.82),
            ("news",           "Royal Mail partners with OWI/Brightpick to automate parcel sortation at four major UK distribution centres", 0.85),
        ],
    },

    # =========================================================================
    # CANADIAN COMPANIES
    # =========================================================================
    {
        "company": {
            "name": "Fairmont Hotels & Resorts",
            "website": "https://www.fairmont.com",
            "industry": "Hospitality",
            "sub_industry": "Luxury Hotel Chain",
            "employee_estimate": 40000,
            "location_city": "Toronto",
            "location_state": "ON",
            "location_country": "CA",
            "source": "seed_v2",
        },
        "signals": [
            ("labor_shortage", "Fairmont hotels across Canada and US: banquet, housekeeping, and F&B staff shortage driving service quality issues", 0.85),
            ("capex",          "Fairmont (Accor) investing CAD 200M in luxury property operations including autonomous F&B delivery and housekeeping assist robots", 0.82),
            ("strategic_hire", "Fairmont appoints VP of Hotel Innovation to assess and deploy service robots across luxury portfolio", 0.81),
            ("expansion",      "Fairmont opening 6 new resort properties in Canada and US; automation integration in specifications", 0.78),
        ],
    },
    {
        "company": {
            "name": "Empire Company (Sobeys / Voilà)",
            "website": "https://www.empireco.ca",
            "industry": "Logistics",
            "sub_industry": "Grocery Distribution",
            "employee_estimate": 130000,
            "location_city": "Stellarton",
            "location_state": "NS",
            "location_country": "CA",
            "source": "seed_v2",
        },
        "signals": [
            ("capex",          "Empire Co investing CAD 350M in Ocado-powered automated customer fulfilment centres for Sobeys and FreshCo banners", 0.90),
            ("strategic_hire", "Empire appoints Chief Supply Chain Technology Officer to oversee robotic fulfilment and warehouse automation rollout", 0.88),
            ("news",           "Sobeys Voilà robotic fulfilment CFC in Montreal reporting 99.3% order accuracy and 40% lower fulfilment cost vs manual", 0.91),
            ("expansion",      "Empire Company opening 3 additional robotic Voilà CFCs across Canada by 2027", 0.86),
        ],
    },
    {
        "company": {
            "name": "TJX Canada (Winners / HomeSense / Marshalls)",
            "website": "https://www.tjx.com/canada",
            "industry": "Logistics",
            "sub_industry": "Retail Distribution",
            "employee_estimate": 28000,
            "location_city": "Mississauga",
            "location_state": "ON",
            "location_country": "CA",
            "source": "seed_v2",
        },
        "signals": [
            ("labor_shortage", "TJX Canada distribution centres running 35% below headcount; high-velocity off-price retail model requires reliable throughput", 0.86),
            ("capex",          "TJX Canada investing CAD 150M in DC automation: goods-to-person systems, robotic sortation, conveyor AI at Mississauga hub", 0.83),
            ("expansion",      "TJX Canada opening 40+ new stores annually; distribution capacity requires automated throughput scale", 0.79),
        ],
    },
    {
        "company": {
            "name": "Chartwell Retirement Residences",
            "website": "https://www.chartwell.com",
            "industry": "Healthcare",
            "sub_industry": "Senior Living",
            "employee_estimate": 15000,
            "location_city": "Mississauga",
            "location_state": "ON",
            "location_country": "CA",
            "source": "seed_v2",
        },
        "signals": [
            ("labor_shortage", "Chartwell senior residences across Ontario, Quebec, BC: PSW and dining aide vacancy at 48%; agency labour cost 2.5x budget", 0.91),
            ("capex",          "Chartwell investing CAD 80M in resident technology including companion robots, meal delivery robots, and care assist systems", 0.84),
            ("news",           "Chartwell Retirement Residences piloting meal delivery and companion robots at 10 Ontario communities", 0.83),
            ("strategic_hire", "Chartwell appoints VP of Resident Services Innovation to lead robot-assisted care and dining program", 0.81),
        ],
    },
    {
        "company": {
            "name": "Groupe Germain Hotels",
            "website": "https://www.groupegermain.com",
            "industry": "Hospitality",
            "sub_industry": "Boutique Hotel Chain",
            "employee_estimate": 2500,
            "location_city": "Montreal",
            "location_state": "QC",
            "location_country": "CA",
            "source": "seed_v2",
        },
        "signals": [
            ("labor_shortage", "Groupe Germain hotels (ALT, Le Germain, Escad): Quebec hospitality labour market critically short; CAD minimum wage 15% above 2022", 0.87),
            ("news",           "Groupe Germain piloting autonomous lobby and floor cleaning robot at Le Germain Montreal; expanding to 5 more properties", 0.82),
        ],
    },

    # =========================================================================
    # US RETAIL & GROCERY (NEW)
    # =========================================================================
    {
        "company": {
            "name": "Albertsons Companies",
            "website": "https://www.albertsonscompanies.com",
            "industry": "Logistics",
            "sub_industry": "Grocery Distribution",
            "employee_estimate": 290000,
            "location_city": "Boise",
            "location_state": "ID",
            "location_country": "US",
            "source": "seed_v2",
        },
        "signals": [
            ("capex",          "Albertsons investing $800M in supply chain automation: robotic micro-fulfilment centres, automated DCs, robotic picking for delivery", 0.88),
            ("labor_shortage", "Albertsons distribution centres 35% understaffed; automated micro-fulfilment pilots showing 10x pick rate vs manual", 0.86),
            ("strategic_hire", "Albertsons appoints Chief Supply Chain Technology Officer to lead warehouse and fulfilment automation strategy", 0.85),
            ("news",           "Albertsons launches Takeoff-powered micro-fulfilment robots at Vons, Jewel-Osco, Safeway distribution points across US", 0.87),
        ],
    },
    {
        "company": {
            "name": "H-E-B Grocery Company",
            "website": "https://www.heb.com",
            "industry": "Logistics",
            "sub_industry": "Grocery Retail & Distribution",
            "employee_estimate": 145000,
            "location_city": "San Antonio",
            "location_state": "TX",
            "location_country": "US",
            "source": "seed_v2",
        },
        "signals": [
            ("capex",          "H-E-B investing $500M in supply chain and distribution automation: robotic DCs, AMR-powered picking, last-mile automation", 0.89),
            ("expansion",      "H-E-B opening 15 new supermarket locations and 2 new distribution centres in Texas in 2025-2026", 0.83),
            ("strategic_hire", "H-E-B appoints VP of Supply Chain Innovation to lead automated fulfillment and distribution technology programme", 0.84),
            ("labor_shortage", "H-E-B warehouse and distribution roles 25% vacant in San Antonio and Houston markets; automation pilot ROI positive", 0.82),
        ],
    },
    {
        "company": {
            "name": "Dollar General Corporation",
            "website": "https://www.dollargeneral.com",
            "industry": "Logistics",
            "sub_industry": "Discount Retail Distribution",
            "employee_estimate": 180000,
            "location_city": "Goodlettsville",
            "location_state": "TN",
            "location_country": "US",
            "source": "seed_v2",
        },
        "signals": [
            ("capex",          "Dollar General investing $650M in distribution centre automation: robotic conveyors, AMR-assisted sortation, autonomous dock systems", 0.87),
            ("labor_shortage", "Dollar General DCs chronically understaffed; high-velocity low-SKU distribution model is ideal AMR use case", 0.86),
            ("expansion",      "Dollar General opening 800+ new stores annually; supply chain automation required to support unprecedented growth rate", 0.85),
            ("strategic_hire", "Dollar General names SVP of Supply Chain Operations to modernise distribution technology and robot deployment", 0.83),
            ("news",           "Dollar General breaks ground on fourth robotics-enabled distribution centre in 2025; robot count to exceed 3,000", 0.88),
        ],
    },
    {
        "company": {
            "name": "Publix Super Markets",
            "website": "https://www.publix.com",
            "industry": "Logistics",
            "sub_industry": "Grocery Retail",
            "employee_estimate": 240000,
            "location_city": "Lakeland",
            "location_state": "FL",
            "location_country": "US",
            "source": "seed_v2",
        },
        "signals": [
            ("capex",          "Publix investing $400M in distribution and fulfilment automation: automated DC technology, robotic case picking, conveyor upgrades", 0.85),
            ("labor_shortage", "Publix Florida DCs running 30% below headcount; retail associate turnover at store level driving efficiency focus", 0.82),
            ("news",           "Publix announces automated customer fulfilment centre in Orlando with robotic picking for online grocery delivery", 0.84),
            ("expansion",      "Publix expanding into Virginia and Kentucky with 60 new stores; distribution automation needed to support footprint growth", 0.80),
        ],
    },
    {
        "company": {
            "name": "Aldi USA",
            "website": "https://www.aldi.us",
            "industry": "Logistics",
            "sub_industry": "Grocery Distribution",
            "employee_estimate": 45000,
            "location_city": "Batavia",
            "location_state": "IL",
            "location_country": "US",
            "source": "seed_v2",
        },
        "signals": [
            ("expansion",      "Aldi US fastest growing grocery chain: adding 100+ stores annually; requires scalable automated distribution infrastructure", 0.87),
            ("capex",          "Aldi investing $9B in US over 5 years; automated DCs core to low-cost grocery expansion model", 0.91),
            ("labor_shortage", "Aldi DC operations 30% under headcount; limited SKU grocery model ideal for robotic case-pick and palletising", 0.83),
            ("strategic_hire", "Aldi US appoints VP of Distribution & Automation to lead warehouse robotics specification for new builds", 0.84),
        ],
    },
    {
        "company": {
            "name": "Walgreens Boots Alliance",
            "website": "https://www.walgreensbootsalliance.com",
            "industry": "Logistics",
            "sub_industry": "Pharmacy Distribution",
            "employee_estimate": 315000,
            "location_city": "Deerfield",
            "location_state": "IL",
            "location_country": "US",
            "source": "seed_v2",
        },
        "signals": [
            ("capex",          "Walgreens investing $1B in micro-fulfilment DC automation: robotic pharmacy picking, prescription fulfilment, delivery automation", 0.89),
            ("labor_shortage", "Walgreens pharmacy technician vacancy 40%; robotic dispensing and fulfilment shown to reduce per-script labour by 60%", 0.88),
            ("strategic_hire", "Walgreens appoints Chief Supply Chain Officer with mandate to automate 12 regional DC operations", 0.85),
            ("news",           "Walgreens deploying robotic pharmacy fulfilment tech at 4 automated distribution centres; 1 million Rx per day capacity", 0.90),
        ],
    },
    {
        "company": {
            "name": "CVS Health Supply Chain",
            "website": "https://www.cvshealth.com",
            "industry": "Logistics",
            "sub_industry": "Pharmacy & Healthcare Distribution",
            "employee_estimate": 300000,
            "location_city": "Woonsocket",
            "location_state": "RI",
            "location_country": "US",
            "source": "seed_v2",
        },
        "signals": [
            ("capex",          "CVS Health investing $750M in pharmacy automation: robotic dispensing, autonomous DC systems, last-mile delivery robots", 0.88),
            ("labor_shortage", "CVS pharmacy tech vacancies at 38% nationally; robotic dispensing pilot at Woonsocket DC shows 3x throughput improvement", 0.87),
            ("strategic_hire", "CVS appoints EVP of Pharmacy Operations & Innovation to lead robotic pharmacy and DC automation programme", 0.84),
            ("news",           "CVS Health opens fifth automated pharmacy fulfilment centre with 750+ robotic systems; expanding nationally", 0.89),
        ],
    },
    {
        "company": {
            "name": "BJ's Wholesale Club",
            "website": "https://www.bjs.com",
            "industry": "Logistics",
            "sub_industry": "Wholesale Club Retail",
            "employee_estimate": 35000,
            "location_city": "Marlborough",
            "location_state": "MA",
            "location_country": "US",
            "source": "seed_v2",
        },
        "signals": [
            ("capex",          "BJ's Wholesale Club investing $300M in supply chain transformation including robotic DC automation and last-mile fulfilment", 0.83),
            ("labor_shortage", "BJ's DC operations running 28% below headcount; automation investment framed as strategic response to labour market", 0.81),
            ("expansion",      "BJ's Wholesale opening 15 new clubs per year; supply chain automation required to support club count growth", 0.79),
            ("strategic_hire", "BJ's appoints Chief Supply Chain Officer from logistics automation background", 0.82),
        ],
    },
    {
        "company": {
            "name": "Five Below",
            "website": "https://www.fivebelow.com",
            "industry": "Logistics",
            "sub_industry": "Specialty Retail Distribution",
            "employee_estimate": 22000,
            "location_city": "Philadelphia",
            "location_state": "PA",
            "location_country": "US",
            "source": "seed_v2",
        },
        "signals": [
            ("expansion",      "Five Below adding 200+ stores annually; one of fastest growing specialty retailers; requires automated DC throughput", 0.85),
            ("capex",          "Five Below investing $250M in fulfilment and distribution automation to support double-digit store count growth", 0.83),
            ("labor_shortage", "Five Below DCs 35% understaffed; extreme SKU velocity at low margin requires high-efficiency robotic handling", 0.80),
            ("strategic_hire", "Five Below names SVP of Supply Chain to lead distribution automation programme across two new automated DCs", 0.81),
        ],
    },
    {
        "company": {
            "name": "Chewy Inc",
            "website": "https://www.chewy.com",
            "industry": "Logistics",
            "sub_industry": "E-Commerce Fulfilment",
            "employee_estimate": 20000,
            "location_city": "Dania Beach",
            "location_state": "FL",
            "location_country": "US",
            "source": "seed_v2",
        },
        "signals": [
            ("capex",          "Chewy investing $800M in next-generation automated fulfilment centres: goods-to-person robots, robotic packing, autonomous handling", 0.89),
            ("labor_shortage", "Chewy FC headcount 33% below target; high-velocity e-commerce model requires automated picking at scale", 0.86),
            ("strategic_hire", "Chewy appoints Chief Supply Chain Officer from warehouse robotics background to build automated FC network", 0.88),
            ("news",           "Chewy opening 4th automated fulfilment centre in 2025; fully roboticised from day one; 98.5% pick accuracy reported", 0.87),
            ("expansion",      "Chewy expanding from 9 to 14 fulfilment centres over 2 years to capture growing pet product subscription growth", 0.83),
        ],
    },
    {
        "company": {
            "name": "Wayfair",
            "website": "https://www.wayfair.com",
            "industry": "Logistics",
            "sub_industry": "E-Commerce Fulfilment",
            "employee_estimate": 19000,
            "location_city": "Boston",
            "location_state": "MA",
            "location_country": "US",
            "source": "seed_v2",
        },
        "signals": [
            ("capex",          "Wayfair investing $600M in CastleGate fulfilment network automation: robotic goods-to-person, autonomous forklifts, pick robots", 0.87),
            ("labor_shortage", "Wayfair FC associates turnover at 95% annually; large-item e-commerce handling ideal for AMR and robotic palletise solutions", 0.83),
            ("strategic_hire", "Wayfair names Chief Physical Operations Officer to lead automated FC build-out across North America", 0.85),
            ("news",           "Wayfair partners with 6 River Systems for robot-assisted picking at all new CastleGate fulfilment sites in 2025", 0.84),
        ],
    },

    # =========================================================================
    # ADDITIONAL US HOSPITALITY
    # =========================================================================
    {
        "company": {
            "name": "Choice Hotels International",
            "website": "https://www.choicehotels.com",
            "industry": "Hospitality",
            "sub_industry": "Hotel Franchise",
            "employee_estimate": 1800,
            "location_city": "North Bethesda",
            "location_state": "MD",
            "location_country": "US",
            "source": "seed_v2",
        },
        "signals": [
            ("labor_shortage", "Choice Hotels franchisees (Comfort Inn, Quality Inn, Clarion) reporting housekeeping vacancy at 55% — worst in company history", 0.91),
            ("capex",          "Choice Hotels launching franchise support programme with subsidised robot housekeeping trial at 200 locations", 0.84),
            ("news",           "Choice Hotels piloting cleaning robot programme at Comfort Inn and Sleep Inn franchised properties; cost-share model with owners", 0.86),
            ("strategic_hire", "Choice Hotels appoints VP of Franchisee Operations Technology to deploy automation tools to owner-operator community", 0.81),
        ],
    },
    {
        "company": {
            "name": "Best Western Hotels & Resorts",
            "website": "https://www.bestwestern.com",
            "industry": "Hospitality",
            "sub_industry": "Hotel Franchise",
            "employee_estimate": 2400,
            "location_city": "Phoenix",
            "location_state": "AZ",
            "location_country": "US",
            "source": "seed_v2",
        },
        "signals": [
            ("labor_shortage", "Best Western independent franchise owners: 58% of properties operating below minimum housekeeping staffing levels", 0.90),
            ("news",           "Best Western launches Hotel Robotics Initiative; approved vendor list for delivery and cleaning robots for franchisees", 0.85),
            ("capex",          "Best Western investing $50M in providing franchisee technology support including robot procurement programme", 0.78),
        ],
    },
    {
        "company": {
            "name": "Aimbridge Hospitality",
            "website": "https://www.aimbridgehospitality.com",
            "industry": "Hospitality",
            "sub_industry": "Hotel Management Company",
            "employee_estimate": 33000,
            "location_city": "Plano",
            "location_state": "TX",
            "location_country": "US",
            "source": "seed_v2",
        },
        "signals": [
            ("labor_shortage", "Aimbridge manages 1,500+ hotels; housekeeping vacancy at 47% system-wide; single operator scale creates compelling robot buying opportunity", 0.91),
            ("capex",          "Aimbridge Hospitality investing $200M in portfolio-wide operations technology including centralised robot deployment programme", 0.87),
            ("strategic_hire", "Aimbridge appoints Chief Operations Technology Officer to lead robot purchasing and deployment across managed portfolio", 0.89),
            ("news",           "Aimbridge Hospitality announces master robot vendor agreement covering all 1,500+ managed properties", 0.88),
            ("expansion",      "Aimbridge adding 200 new managed hotel contracts annually; standardised automation spec in each management agreement", 0.82),
        ],
    },
    {
        "company": {
            "name": "Sonesta International Hotels",
            "website": "https://www.sonesta.com",
            "industry": "Hospitality",
            "sub_industry": "Hotel Chain",
            "employee_estimate": 16000,
            "location_city": "Newton",
            "location_state": "MA",
            "location_country": "US",
            "source": "seed_v2",
        },
        "signals": [
            ("labor_shortage", "Sonesta portfolio: 1,200 hotels post-merger with Red Lion; housekeeping vacancy averaging 44% system-wide", 0.89),
            ("capex",          "Sonesta committing $100M to brand modernisation programme including autonomous housekeeping and F&B delivery pilots", 0.82),
            ("news",           "Sonesta Hotels evaluating delivery robots and autonomous floor cleaners after 20-property pilot shows strong ROI metrics", 0.83),
        ],
    },
    {
        "company": {
            "name": "OYO Hotels USA",
            "website": "https://www.oyorooms.com/us",
            "industry": "Hospitality",
            "sub_industry": "Budget Hotel Franchise",
            "employee_estimate": 7000,
            "location_city": "Gurgaon",
            "location_state": "",
            "location_country": "IN",
            "source": "seed_v2",
        },
        "signals": [
            ("expansion",      "OYO Hotels USA portfolio growing to 500+ budget properties; lean model requires automation to maintain economy margins", 0.82),
            ("labor_shortage", "OYO US partner hotels: housekeeping vacancy 50%+ in suburban and highway markets; automation critical to viability", 0.88),
            ("job_posting",    "Head of US Hotel Operations Technology | housekeeping automation, delivery robots, self-service hotel innovation", 0.76),
        ],
    },
    {
        "company": {
            "name": "Loews Hotels & Co",
            "website": "https://www.loewshotels.com",
            "industry": "Hospitality",
            "sub_industry": "Upscale Hotel Chain",
            "employee_estimate": 12000,
            "location_city": "New York",
            "location_state": "NY",
            "location_country": "US",
            "source": "seed_v2",
        },
        "signals": [
            ("labor_shortage", "Loews Hotels upscale properties: banquet, rooms, F&B staff shortage driving service disruption and cost overruns", 0.83),
            ("capex",          "Loews Hotels committing $120M to hotel technology including F&B delivery robots and autonomous housekeeping systems", 0.79),
            ("news",           "Loews Hotels deploying room service delivery and lobby cleaning robots at Denver, Orlando, and New York flagship properties", 0.82),
        ],
    },

    # =========================================================================
    # ADDITIONAL HEALTHCARE
    # =========================================================================
    {
        "company": {
            "name": "Trinity Health",
            "website": "https://www.trinity-health.org",
            "industry": "Healthcare",
            "sub_industry": "Not-for-profit Health System",
            "employee_estimate": 125000,
            "location_city": "Livonia",
            "location_state": "MI",
            "location_country": "US",
            "source": "seed_v2",
        },
        "signals": [
            ("labor_shortage", "Trinity Health 88 hospitals: environmental services and patient transport vacancy 40%; EVS outsourcing costs escalating", 0.89),
            ("capex",          "Trinity Health approves $450M capital programme for hospital infrastructure including autonomous cleaning and logistics robots", 0.85),
            ("news",           "Trinity Health deploys UV disinfection robots and autonomous linen delivery systems at 12 Michigan and Ohio hospitals", 0.86),
            ("strategic_hire", "Trinity Health appoints Chief Digital Health Officer to lead clinical and non-clinical automation including robot deployment", 0.83),
        ],
    },
    {
        "company": {
            "name": "Bon Secours Mercy Health",
            "website": "https://www.bsmhealth.org",
            "industry": "Healthcare",
            "sub_industry": "Not-for-profit Health System",
            "employee_estimate": 60000,
            "location_city": "Cincinnati",
            "location_state": "OH",
            "location_country": "US",
            "source": "seed_v2",
        },
        "signals": [
            ("labor_shortage", "Bon Secours Mercy Health: EVS and dietary vacancy at 42% across 50 hospitals in 7 states; no solution in traditional hiring", 0.88),
            ("capex",          "Bon Secours Mercy Health committing $300M technology investment including autonomous hospital logistics robots at all locations", 0.84),
            ("news",           "Bon Secours Mercy Health signs agreement to deploy meal delivery and disinfection robots at 20 hospital campuses over 2025-2026", 0.85),
        ],
    },
    {
        "company": {
            "name": "Encompass Health",
            "website": "https://www.encompasshealth.com",
            "industry": "Healthcare",
            "sub_industry": "Rehabilitation Hospital",
            "employee_estimate": 46000,
            "location_city": "Birmingham",
            "location_state": "AL",
            "location_country": "US",
            "source": "seed_v2",
        },
        "signals": [
            ("labor_shortage", "Encompass Health rehab hospitals: therapy aide, dietary, and housekeeping 40% vacant nationwide; highest in company history", 0.87),
            ("capex",          "Encompass Health investing $200M in rehabilitation hospital upgrades including service robots for logistics and patient engagement", 0.82),
            ("expansion",      "Encompass Health building 15 new rehabilitation hospitals in 2025; robot integration in all new facility specs", 0.80),
            ("news",           "Encompass Health piloting autonomous medication and meal delivery robots at 8 rehabilitation hospital campuses", 0.83),
        ],
    },
    {
        "company": {
            "name": "Kindred Healthcare",
            "website": "https://www.kindredhealthcare.com",
            "industry": "Healthcare",
            "sub_industry": "Long-term Acute Care",
            "employee_estimate": 35000,
            "location_city": "Louisville",
            "location_state": "KY",
            "location_country": "US",
            "source": "seed_v2",
        },
        "signals": [
            ("labor_shortage", "Kindred Healthcare LTACH facilities: nursing support and dietary aide vacancy at 55%; PE ownership driving cost reduction mandate", 0.90),
            ("ma_activity",    "Kindred Healthcare acquired by LifePoint Health and ScionHealth; combined entity evaluating enterprise-wide automation programme", 0.83),
            ("news",           "Kindred Healthcare deploying delivery and cleaning robots at LTACH locations after nursing union agrees to robot co-deployment", 0.82),
        ],
    },
    {
        "company": {
            "name": "NHS Supply Chain (UK)",
            "website": "https://www.nhssupplychain.nhs.uk",
            "industry": "Healthcare",
            "sub_industry": "Hospital Logistics",
            "employee_estimate": 6000,
            "location_city": "Alfreton",
            "location_state": "",
            "location_country": "GB",
            "source": "seed_v2",
        },
        "signals": [
            ("capex",          "NHS Supply Chain investing GBP 150M in automated hospital logistics: autonomous delivery robots, smart storage, drone delivery pilots", 0.88),
            ("labor_shortage", "NHS Supply Chain warehouse and hospital distribution roles 35% under headcount; robot pilots at 8 NHS Trust hospital campuses", 0.86),
            ("news",           "NHS Supply Chain autonomous robot programme delivering sterile supplies at 12 NHS hospitals; expanding to 40 Trusts", 0.87),
            ("strategic_hire", "NHS Supply Chain appoints Director of Automation & Robotics to scale AMR deployment across NHS estate", 0.84),
        ],
    },
    {
        "company": {
            "name": "National Health Service (NHS) Trusts — Estates & Facilities",
            "website": "https://www.england.nhs.uk",
            "industry": "Healthcare",
            "sub_industry": "Public Health System",
            "employee_estimate": 1400000,
            "location_city": "London",
            "location_state": "",
            "location_country": "GB",
            "source": "seed_v2",
        },
        "signals": [
            ("labor_shortage", "NHS hospitals facing EVS, dietary, and patient transport vacancy of 35-50% across England, Wales, and Scotland", 0.92),
            ("capex",          "NHS England approves GBP 3.5B backlog maintenance and modernisation programme; hospital robot pilots included in 42 Integrated Care Systems", 0.88),
            ("news",           "26 NHS Trusts deploying autonomous cleaning, food delivery, and supply robots in 2025; NHS X programme accelerating rollout", 0.89),
            ("strategic_hire", "NHS England appoints National Director of Digital Transformation to lead hospital robot and automation programme", 0.85),
        ],
    },
    {
        "company": {
            "name": "Sunrise Medical Centers (Canada)",
            "website": "https://www.sunrisemedical.ca",
            "industry": "Healthcare",
            "sub_industry": "Diagnostic Imaging",
            "employee_estimate": 3000,
            "location_city": "Toronto",
            "location_state": "ON",
            "location_country": "CA",
            "source": "seed_v2",
        },
        "signals": [
            ("labor_shortage", "Diagnostic imaging clinics: patient transport, cleaning, and support staff 45% short across Ontario locations", 0.83),
            ("news",           "Sunrise clinics evaluating autonomous patient transport assist and cleaning robots across expanded Ontario network", 0.79),
        ],
    },

    # =========================================================================
    # ADDITIONAL FOOD SERVICE
    # =========================================================================
    {
        "company": {
            "name": "Bloomin' Brands",
            "website": "https://www.bloominbrands.com",
            "industry": "Food Service",
            "sub_industry": "Casual Dining",
            "employee_estimate": 90000,
            "location_city": "Tampa",
            "location_state": "FL",
            "location_country": "US",
            "source": "seed_v2",
        },
        "signals": [
            ("labor_shortage", "Bloomin' Brands (Outback, Carrabba's, Bonefish): busser, runner, dishwasher vacancy averaging 38% across casual dining portfolio", 0.86),
            ("news",           "Bloomin' Brands trialling table delivery and bussing robots at 25 Outback Steakhouse locations; reducing front-of-house labour dependency", 0.84),
            ("capex",          "Bloomin' launches $150M restaurant technology cycle; service robots and automated back-of-house equipment included", 0.80),
            ("strategic_hire", "Bloomin' Brands hires VP of Operations Innovation to evaluate and scale food service robot deployment", 0.82),
        ],
    },
    {
        "company": {
            "name": "Jack in the Box",
            "website": "https://www.jackinthebox.com",
            "industry": "Food Service",
            "sub_industry": "QSR",
            "employee_estimate": 6000,
            "location_city": "San Diego",
            "location_state": "CA",
            "location_country": "US",
            "source": "seed_v2",
        },
        "signals": [
            ("labor_shortage", "Jack in the Box franchisees in California facing $20+ minimum wage pressure; crew vacancy 35% driving late-night closure decisions", 0.88),
            ("capex",          "Jack in the Box investing $80M in franchise restaurant technology including automated fry stations and order fulfilment systems", 0.82),
            ("news",           "Jack in the Box pilots automated late-night kitchen operations with reduced crew; robot-assist products being evaluated", 0.83),
        ],
    },
    {
        "company": {
            "name": "Cracker Barrel Old Country Store",
            "website": "https://www.crackerbarrel.com",
            "industry": "Food Service",
            "sub_industry": "Family Dining",
            "employee_estimate": 70000,
            "location_city": "Lebanon",
            "location_state": "TN",
            "location_country": "US",
            "source": "seed_v2",
        },
        "signals": [
            ("labor_shortage", "Cracker Barrel: server and kitchen staff vacancy 35% at highway locations; rural labour markets structurally constrained", 0.85),
            ("job_posting",    "VP of Restaurant Operations Technology | back-of-house automation, server-assist robots, self-service innovation", 0.77),
            ("news",           "Cracker Barrel CEO publicly identifies labour as greatest operational threat, announces technology investment acceleration", 0.82),
            ("capex",          "Cracker Barrel approves $200M restaurant revitalisation programme; automation equipment and robotics included", 0.80),
        ],
    },
    {
        "company": {
            "name": "Noodles & Company",
            "website": "https://www.noodles.com",
            "industry": "Food Service",
            "sub_industry": "Fast Casual",
            "employee_estimate": 11000,
            "location_city": "Broomfield",
            "location_state": "CO",
            "location_country": "US",
            "source": "seed_v2",
        },
        "signals": [
            ("labor_shortage", "Noodles & Company kitchen crew vacancy 42%; crew scheduling unreliable leading to reduced operating hours", 0.84),
            ("job_posting",    "Director of Technology & Operations | kitchen automation, robotic food prep, restaurant efficiency technology", 0.78),
            ("news",           "Noodles & Company piloting automated pasta cooking station and tray delivery robot at Denver and Chicago test units", 0.80),
        ],
    },
    {
        "company": {
            "name": "Levy Restaurants (Compass Group Sports)",
            "website": "https://www.levyrestaurants.com",
            "industry": "Food Service",
            "sub_industry": "Sports & Entertainment Dining",
            "employee_estimate": 38000,
            "location_city": "Chicago",
            "location_state": "IL",
            "location_country": "US",
            "source": "seed_v2",
        },
        "signals": [
            ("labor_shortage", "Levy Restaurants event-day staffing 50% below target at NFL, NBA, MLB venues; unreliable gig labour hurting guest satisfaction", 0.89),
            ("news",           "Levy Restaurants deploys food delivery robots and automated beverage carts at 8 pro sports stadiums in 2025", 0.87),
            ("capex",          "Levy Restaurants and parent Compass Group investing $80M in sports venue food service automation", 0.82),
            ("strategic_hire", "Levy Restaurants appoints VP of Innovation & Technology to lead robot food service and autonomous concession stand deployment", 0.85),
        ],
    },
    {
        "company": {
            "name": "Elior Group",
            "website": "https://www.elior-group.com",
            "industry": "Food Service",
            "sub_industry": "Contract Food Service",
            "employee_estimate": 110000,
            "location_city": "Paris",
            "location_state": "",
            "location_country": "FR",
            "source": "seed_v2",
        },
        "signals": [
            ("labor_shortage", "Elior Group France, UK, Italy, Spain: contract catering staff 38% below budget across 25,000 client sites", 0.88),
            ("capex",          "Elior Group investing EUR 200M in food service automation: autonomous serving, kitchen robotics, and autonomous meal delivery", 0.85),
            ("strategic_hire", "Elior appoints Group Chief Digital Officer to lead robot-assisted food service deployment across European portfolio", 0.83),
            ("news",           "Elior Group deploys food delivery robots in French hospital and corporate dining contracts; expanding to healthcare segment", 0.84),
        ],
    },
    {
        "company": {
            "name": "Apetito Group (UK)",
            "website": "https://www.apetito.co.uk",
            "industry": "Food Service",
            "sub_industry": "Healthcare & Senior Dining",
            "employee_estimate": 6000,
            "location_city": "Trowbridge",
            "location_state": "",
            "location_country": "GB",
            "source": "seed_v2",
        },
        "signals": [
            ("labor_shortage", "Apetito UK: care home and hospital meal delivery staff 40% vacant; frozen meal logistics need autonomous last-yard delivery", 0.87),
            ("news",           "Apetito UK piloting autonomous meal trolley delivery robots at 15 NHS hospital wards and 8 care home clients", 0.84),
            ("capex",          "Apetito investing GBP 30M in meal production, packaging, and delivery automation for healthcare food service contracts", 0.79),
        ],
    },

    # =========================================================================
    # MORE US LOGISTICS (ADDITIONAL)
    # =========================================================================
    {
        "company": {
            "name": "HD Supply",
            "website": "https://www.hdsupply.com",
            "industry": "Logistics",
            "sub_industry": "MRO Distribution",
            "employee_estimate": 11000,
            "location_city": "Atlanta",
            "location_state": "GA",
            "location_country": "US",
            "source": "seed_v2",
        },
        "signals": [
            ("labor_shortage", "HD Supply distribution operations: MRO warehouse roles 32% vacant; Home Depot parent driving automation investment", 0.82),
            ("capex",          "HD Supply investing $200M in distribution centre automation under Home Depot parent company capital plan", 0.83),
            ("news",           "HD Supply deploying autonomous mobile robots at Atlanta, Phoenix, and New Jersey distribution facilities", 0.80),
        ],
    },
    {
        "company": {
            "name": "Radial Inc",
            "website": "https://www.radial.com",
            "industry": "Logistics",
            "sub_industry": "E-Commerce Fulfilment Outsourcing",
            "employee_estimate": 9000,
            "location_city": "King of Prussia",
            "location_state": "PA",
            "location_country": "US",
            "source": "seed_v2",
        },
        "signals": [
            ("labor_shortage", "Radial fulfilment centre staffing 40% below contract SLAs; seasonal surge hiring falls 50% short, driving automation mandate", 0.89),
            ("capex",          "Radial investing $150M in goods-to-person robots and robotic picking arms across 25 client fulfilment sites", 0.86),
            ("strategic_hire", "Radial appoints Chief Operations Technology Officer to lead AMR fleet and robotic picking deployment across FC network", 0.85),
            ("news",           "Radial announces robot-first fulfilment service model; all new client contracts include autonomous picking technology", 0.87),
        ],
    },
    {
        "company": {
            "name": "Saddle Creek Logistics Services",
            "website": "https://www.saddlecreek.com",
            "industry": "Logistics",
            "sub_industry": "3PL",
            "employee_estimate": 4500,
            "location_city": "Lakeland",
            "location_state": "FL",
            "location_country": "US",
            "source": "seed_v2",
        },
        "signals": [
            ("labor_shortage", "Saddle Creek 3PL: Florida and Midwest warehouse facilities running 35% below headcount; AMR deployment approved as strategic response", 0.85),
            ("capex",          "Saddle Creek investing $75M in warehouse automation: AMRs, robotic sortation, autonomous dock management across 40 facilities", 0.81),
            ("news",           "Saddle Creek announces robot-powered fulfilment pods for DTC e-commerce clients; 2-day ship time with 60% fewer pickers", 0.80),
        ],
    },
    {
        "company": {
            "name": "Kenco Logistics",
            "website": "https://www.kenco.com",
            "industry": "Logistics",
            "sub_industry": "3PL",
            "employee_estimate": 4000,
            "location_city": "Chattanooga",
            "location_state": "TN",
            "location_country": "US",
            "source": "seed_v2",
        },
        "signals": [
            ("labor_shortage", "Kenco Logistics Southeast US facilities: warehouse associate vacancy at 38%, highest since founding; automation now strategic priority", 0.84),
            ("capex",          "Kenco investing $60M in AMR and autonomous guided vehicle deployment across automotive and CPG client distribution centres", 0.80),
            ("strategic_hire", "Kenco appoints Director of Automation Engineering to manage robot fleet acquisition and client deployment programme", 0.82),
        ],
    },

    # =========================================================================
    # SENIOR LIVING ADDITIONAL
    # =========================================================================
    {
        "company": {
            "name": "Five Star Senior Living",
            "website": "https://www.fivestarseniorliving.com",
            "industry": "Healthcare",
            "sub_industry": "Senior Living",
            "employee_estimate": 19000,
            "location_city": "Newton",
            "location_state": "MA",
            "location_country": "US",
            "source": "seed_v2",
        },
        "signals": [
            ("labor_shortage", "Five Star Senior Living: dining services and housekeeping 52% vacant across independent and assisted living communities", 0.92),
            ("news",           "Five Star Senior Living pilots robot meal delivery and companion robots at 20 communities in New England and Mid-Atlantic", 0.86),
            ("capex",          "Five Star investing $60M in resident services technology including autonomous meal delivery and care assist robots", 0.81),
        ],
    },
    {
        "company": {
            "name": "Trilogy Health Services",
            "website": "https://www.trilogyhs.com",
            "industry": "Healthcare",
            "sub_industry": "Post-Acute & Senior Living",
            "employee_estimate": 19000,
            "location_city": "Louisville",
            "location_state": "KY",
            "location_country": "US",
            "source": "seed_v2",
        },
        "signals": [
            ("labor_shortage", "Trilogy Health Services SNF and senior living communities: CNA, dietary, housekeeping vacancy at 44% across Midwest campuses", 0.90),
            ("news",           "Trilogy Health tests meal delivery and companion robots at 15 Indiana and Kentucky skilled nursing communities", 0.83),
            ("capex",          "Trilogy investing $40M in campus technology including autonomous delivery robots and smart monitoring for resident wellbeing", 0.79),
            ("strategic_hire", "Trilogy appoints VP of Innovation & Senior Experience to lead robot care assist and dining delivery programme", 0.81),
        ],
    },
    {
        "company": {
            "name": "Brightspring Health Services",
            "website": "https://www.brightspringhealthservices.com",
            "industry": "Healthcare",
            "sub_industry": "Home Care & Senior Services",
            "employee_estimate": 110000,
            "location_city": "Louisville",
            "location_state": "KY",
            "location_country": "US",
            "source": "seed_v2",
        },
        "signals": [
            ("labor_shortage", "Brightspring home care and residential services: direct care worker vacancy at 48%; structural shortage with no traditional solution", 0.91),
            ("ma_activity",    "Brightspring IPO raises $700M; scale and PE-backing position company for technology investment in care automation", 0.85),
            ("news",           "Brightspring evaluating in-home and facility-based care assist robots for medication management and meal delivery", 0.84),
            ("strategic_hire", "Brightspring appoints Chief Technology Officer to lead care innovation including robot-assisted service delivery", 0.83),
        ],
    },
    {
        "company": {
            "name": "Amica Mature Lifestyles (Canada)",
            "website": "https://www.amica.ca",
            "industry": "Healthcare",
            "sub_industry": "Luxury Senior Living",
            "employee_estimate": 6000,
            "location_city": "Vancouver",
            "location_state": "BC",
            "location_country": "CA",
            "source": "seed_v2",
        },
        "signals": [
            ("labor_shortage", "Amica senior residences across BC and Ontario: dining and housekeeping vacancy at 45%; luxury positioning requires high service continuity", 0.88),
            ("news",           "Amica piloting meal delivery robots and autonomous cleaning equipment at flagship Vancouver and Toronto communities", 0.83),
            ("capex",          "Amica investing CAD 50M in resident services technology including robot-assisted dining and community living experience", 0.79),
        ],
    },
]


# ─────────────────────────────────────────────────────────────────────────────
def seed_database(db, dry_run=False):
    added_c = 0
    added_s = 0

    for entry in NEW_LEADS:
        c_data = entry["company"]
        existing = db.query(Company).filter(Company.name == c_data["name"]).first()
        if existing:
            company = existing
        else:
            if not dry_run:
                company = Company(**c_data)
                db.add(company)
                db.commit()
                db.refresh(company)
            added_c += 1
            if dry_run:
                continue

        for sig_type, sig_text, strength in entry["signals"]:
            dup = db.query(Signal).filter(
                Signal.company_id == company.id,
                Signal.signal_text == sig_text
            ).first()
            if not dup:
                if not dry_run:
                    sig = Signal(
                        company_id=company.id,
                        signal_type=sig_type,
                        signal_text=sig_text,
                        signal_strength=strength,
                        source_url="seed_v2",
                    )
                    db.add(sig)
                    db.commit()
                added_s += 1

    return added_c, added_s


def score_all(db):
    companies = db.query(Company).all()
    scored = 0
    for company in companies:
        signals = db.query(Signal).filter(Signal.company_id == company.id).all()
        if not signals:
            continue
        texts = [s.signal_text for s in signals]
        from app.services.inference_engine import analyze_signals
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
    return scored


if __name__ == "__main__":
    commit = "--commit" in sys.argv

    if not commit:
        # Dry-run: just count new entries without touching DB
        total_co = len(NEW_LEADS)
        total_sig = sum(len(e["signals"]) for e in NEW_LEADS)
        industries = {}
        countries = {}
        for e in NEW_LEADS:
            ind = e["company"]["industry"]
            cty = e["company"]["location_country"]
            industries[ind] = industries.get(ind, 0) + 1
            countries[cty] = countries.get(cty, 0) + 1
        print(f"\n=== seed_leads_v2 DRY RUN ===")
        print(f"  Companies : {total_co}")
        print(f"  Signals   : {total_sig}")
        print(f"\n  By industry:")
        for k, v in sorted(industries.items(), key=lambda x: -x[1]):
            print(f"    {k:<40} {v}")
        print(f"\n  By country:")
        for k, v in sorted(countries.items(), key=lambda x: -x[1]):
            print(f"    {k:<10} {v}")
        print(f"\nRun with --commit to write to database.\n")
        sys.exit(0)

    print("\n=== seed_leads_v2  COMMITTING TO DATABASE ===")
    db = SessionLocal()
    try:
        added_c, added_s = seed_database(db, dry_run=False)
        print(f"  Inserted  {added_c} new companies, {added_s} new signals")

        print("\n  Rescoring all companies...")
        scored = score_all(db)
        print(f"  Scored    {scored} companies")

        total_c = db.query(Company).count()
        total_s = db.query(Signal).count()
        print(f"\n  DB totals: {total_c} companies | {total_s} signals")
        print("  Done.\n")
    finally:
        db.close()
