"""
seed_leads_v4.py — Automotive OEMs + Tier 1 Suppliers

Target: Richtech AMR intra-facility use cases
  • OEMs:            Parts-to-line delivery, WIP movement, JIT replenishment on assembly floor
  • Tier 1 Suppliers: Warehouse AMRs, sub-assembly delivery, kitting, inbound logistics

Industry label: "Automotive Manufacturing"
Titan analog:   Replace manual parts runners / tugger operators / kitting associates
                with autonomous mobile robots on the factory floor and in parts stores.

Usage:
  python scripts/seed_leads_v4.py           # dry-run count
  python scripts/seed_leads_v4.py --commit  # write to DB
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
# LEAD DATA
# ─────────────────────────────────────────────────────────────────────────────
NEW_LEADS = [

    # =========================================================================
    # AUTOMOTIVE OEMs
    # =========================================================================

    {
        "company": {
            "name": "Toyota Motor North America",
            "website": "https://www.toyota.com",
            "industry": "Automotive Manufacturing",
            "sub_industry": "OEM — Full-Line Manufacturer",
            "employee_estimate": 136000,
            "location_city": "Plano",
            "location_state": "TX",
            "location_country": "US",
            "source": "seed_v4",
        },
        "signals": [
            ("capex",           "Toyota commits $13.9B to US manufacturing investment through 2026; smart factory and intra-facility logistics automation are key workstreams across Indiana, Kentucky, and Texas plants", 0.95),
            ("strategic_hire",  "Toyota North America appoints Director of Smart Manufacturing to lead autonomous material handling, parts delivery, and WIP movement across all US assembly plants", 0.91),
            ("labor_shortage",  "Toyota US plants report chronic shortage of tugger operators and parts runners; manual material delivery is the top constraint on assembly line throughput", 0.89),
            ("job_posting",     "Toyota Manufacturing actively hiring 400+ material handlers and parts delivery associates across Georgetown, KY and Princeton, IN plants; high turnover in these roles", 0.87),
            ("expansion",       "Toyota breaks ground on $1.3B battery plant in North Carolina; full intra-facility AMR deployment planned from day one of production operations", 0.90),
        ],
    },
    {
        "company": {
            "name": "Ford Motor Company",
            "website": "https://www.ford.com",
            "industry": "Automotive Manufacturing",
            "sub_industry": "OEM — Full-Line Manufacturer",
            "employee_estimate": 177000,
            "location_city": "Dearborn",
            "location_state": "MI",
            "location_country": "US",
            "source": "seed_v4",
        },
        "signals": [
            ("capex",           "Ford invests $50B in EV and manufacturing transformation through 2026; BlueOval City in Tennessee designed as a fully automated campus with autonomous intra-facility logistics", 0.96),
            ("strategic_hire",  "Ford hires VP of Advanced Manufacturing Technology from Toyota Production System Group; mandate includes autonomous parts delivery and zero-waste material flow on assembly lines", 0.93),
            ("labor_shortage",  "Ford assembly plants running 22% below target headcount for material handling and kitting roles; UAW contracts restrict outsourcing, creating internal automation urgency", 0.88),
            ("expansion",       "Ford BlueOval SK battery joint venture opens two gigafactories in Kentucky and Tennessee; intra-campus parts logistics handled by AMR fleets from production launch", 0.91),
            ("job_posting",     "Ford posting 600+ material handler and inventory associate roles across Michigan, Missouri, and Kentucky plants; annualized turnover rate exceeds 45% in these classifications", 0.86),
        ],
    },
    {
        "company": {
            "name": "General Motors",
            "website": "https://www.gm.com",
            "industry": "Automotive Manufacturing",
            "sub_industry": "OEM — Full-Line Manufacturer",
            "employee_estimate": 167000,
            "location_city": "Detroit",
            "location_state": "MI",
            "location_country": "US",
            "source": "seed_v4",
        },
        "signals": [
            ("capex",           "GM commits $35B to EV and AV manufacturing; Factory ZERO in Detroit and Orion re-tooling include full autonomous material handling and parts-to-line AMR deployment", 0.95),
            ("strategic_hire",  "GM names Chief Manufacturing Automation Officer reporting to COO; primary focus is replacing manual tugger trains and parts runners with AMR fleets across 50+ North American plants", 0.94),
            ("labor_shortage",  "GM manufacturing facing 28% vacancy rate in indirect labor roles including material handlers, line feeders, and kitting associates at multiple plant sites", 0.90),
            ("news",            "GM Ultium Cells joint venture plants deploy autonomous parts replenishment robots on battery module assembly lines; productivity up 31% vs manual delivery baseline", 0.92),
            ("expansion",       "GM announces Lansing Delta Township plant retooling for Silverado EV production; $2.6B investment includes fully automated intra-facility logistics from day one", 0.88),
        ],
    },
    {
        "company": {
            "name": "BMW Manufacturing",
            "website": "https://www.bmwusfactory.com",
            "industry": "Automotive Manufacturing",
            "sub_industry": "OEM — Premium Manufacturer",
            "employee_estimate": 11000,
            "location_city": "Spartanburg",
            "location_state": "SC",
            "location_country": "US",
            "source": "seed_v4",
        },
        "signals": [
            ("capex",           "BMW Group investing $1.7B in Spartanburg Plant X; largest BMW plant globally will expand AMR fleet for parts delivery, sub-assembly kitting, and sequenced line feeding", 0.93),
            ("strategic_hire",  "BMW Manufacturing SC appoints Head of Plant Logistics & Automation; scope includes autonomous tugger replacement and JIT parts delivery robots across all assembly halls", 0.90),
            ("expansion",       "BMW Spartanburg adding three new production halls for X electrified models; logistics planning specifies AMR-first material flow with no manual tugger operators", 0.92),
            ("labor_shortage",  "BMW SC plant unable to staff tugger operators and material handlers in Upstate South Carolina labor market; 180 unfilled indirect labor positions constraining line throughput", 0.87),
            ("news",            "BMW Group global pilot of autonomous line-side replenishment robots at Munich achieves 99.2% on-time delivery; program expanding to Spartanburg and Regensburg", 0.89),
        ],
    },
    {
        "company": {
            "name": "Mercedes-Benz US International",
            "website": "https://www.mbusi.com",
            "industry": "Automotive Manufacturing",
            "sub_industry": "OEM — Premium Manufacturer",
            "employee_estimate": 7000,
            "location_city": "Vance",
            "location_state": "AL",
            "location_country": "US",
            "source": "seed_v4",
        },
        "signals": [
            ("capex",           "Mercedes-Benz US International invests $1B to expand Vance, AL plant for EQS and EQE SUV production; automated parts logistics and AMR deployment included in factory redesign", 0.91),
            ("strategic_hire",  "MBUSI hires Director of Manufacturing Logistics from Volkswagen Group; immediate mandate to automate intra-plant parts delivery and reduce indirect headcount by 30%", 0.89),
            ("labor_shortage",  "MBUSI Vance plant struggling to fill 200+ material handling and sub-assembly delivery roles; rural Alabama labor market limits traditional hiring solutions", 0.88),
            ("expansion",       "Mercedes-Benz announces second Alabama EV assembly facility; green-field design specifies fully autonomous intra-facility logistics — no manual material handler roles planned", 0.90),
            ("news",            "Mercedes-Benz global Factory 56 in Sindelfingen achieves 100% autonomous parts delivery with AMR fleet; MBUSI Alabama replicating model for US SUV production", 0.87),
        ],
    },
    {
        "company": {
            "name": "Honda Manufacturing of America",
            "website": "https://www.hma.honda.com",
            "industry": "Automotive Manufacturing",
            "sub_industry": "OEM — Full-Line Manufacturer",
            "employee_estimate": 26000,
            "location_city": "Marysville",
            "location_state": "OH",
            "location_country": "US",
            "source": "seed_v4",
        },
        "signals": [
            ("capex",           "Honda and LG Energy Solution invest $4.4B in Jeffersonville, OH battery plant; intra-facility autonomous logistics specified in facility design for cell and module delivery", 0.92),
            ("strategic_hire",  "Honda Manufacturing of America promotes VP of Manufacturing Innovation; priority workstream is autonomous parts delivery and zero-touch material flow on ALL Ohio assembly lines", 0.89),
            ("job_posting",     "Honda Ohio plants posting 350+ material flow associate and tugger operator positions; chronic turnover in these classifications driving costs above $18M annually", 0.88),
            ("labor_shortage",  "Honda Marysville and East Liberty plants 25% understaffed in indirect manufacturing roles; overtime costs in material handling exceeded $30M in FY2025", 0.90),
            ("expansion",       "Honda Marysville plant retooling to build next-gen EVs; $700M investment redesigns production line with AMR-compatible parts delivery infrastructure from ground up", 0.86),
        ],
    },
    {
        "company": {
            "name": "Stellantis North America",
            "website": "https://www.stellantis.com",
            "industry": "Automotive Manufacturing",
            "sub_industry": "OEM — Full-Line Manufacturer",
            "employee_estimate": 170000,
            "location_city": "Auburn Hills",
            "location_state": "MI",
            "location_country": "US",
            "source": "seed_v4",
        },
        "signals": [
            ("capex",           "Stellantis invests $35B in electrification through 2025; US plants in Michigan, Indiana, Ohio, and Illinois receiving advanced manufacturing technology upgrades including autonomous intra-plant logistics", 0.93),
            ("labor_shortage",  "Stellantis facilities report 32% vacancy in material handling and line-feeding roles; STLA Star plant in Belvidere, IL restaffing after closure faces acute indirect labor shortage", 0.90),
            ("strategic_hire",  "Stellantis creates global Head of Manufacturing Smart Logistics role; focus on replacing manual material delivery with AMR fleets across Jeep, Ram, and Dodge production lines", 0.91),
            ("expansion",       "Stellantis reopens Belvidere Assembly for Ram commercial van production; $1.5B investment includes autonomous guided vehicle fleet for sequenced parts delivery", 0.89),
            ("job_posting",     "Stellantis posting 700+ material handler and parts flow associate roles across Michigan and Indiana plants; signing bonuses up to $3,000 indicate severe labor market difficulty", 0.87),
        ],
    },
    {
        "company": {
            "name": "Volkswagen Group of America",
            "website": "https://www.vw.com",
            "industry": "Automotive Manufacturing",
            "sub_industry": "OEM — Full-Line Manufacturer",
            "employee_estimate": 9900,
            "location_city": "Chattanooga",
            "location_state": "TN",
            "location_country": "US",
            "source": "seed_v4",
        },
        "signals": [
            ("capex",           "Volkswagen invests $800M to retool Chattanooga plant for ID.4 and ID. Buzz production; factory logistics redesigned around autonomous parts delivery and AMR-fed assembly line", 0.91),
            ("strategic_hire",  "VW Chattanooga appoints Head of Smart Factory Logistics; mandate to eliminate manual tugger routes and implement autonomous parts replenishment on all production halls", 0.90),
            ("expansion",       "VW Group announces Scout Motors EV manufacturing campus in South Carolina; 1,200-acre facility planned with fully autonomous intra-campus logistics from production start", 0.93),
            ("labor_shortage",  "VW Chattanooga plant faces chronic shortage of material handling associates; Tennessee labor market competition with nearby Amazon, FedEx facilities drives vacancy to 24%", 0.86),
            ("news",            "VW Group global manufacturing deploys 5,000+ AMRs across Zwickau and Wolfsburg EV plants; Chattanooga replication of this model confirmed by plant management", 0.88),
        ],
    },
    {
        "company": {
            "name": "Hyundai Motor America",
            "website": "https://www.hyundai.com",
            "industry": "Automotive Manufacturing",
            "sub_industry": "OEM — Full-Line Manufacturer",
            "employee_estimate": 6000,
            "location_city": "Montgomery",
            "location_state": "AL",
            "location_country": "US",
            "source": "seed_v4",
        },
        "signals": [
            ("capex",           "Hyundai Motor Group invests $12.6B in US operations; HMGMA plant in Bryan County, Georgia is largest single US auto investment in history — fully automated logistics from day one", 0.96),
            ("strategic_hire",  "Hyundai Metaplant America appoints Chief Manufacturing Technology Officer; autonomous material delivery and smart logistics cited as top manufacturing KPIs", 0.92),
            ("expansion",       "Hyundai Metaplant Georgia opens producing Ioniq 5 and 6; 8.2M sq ft facility uses AMR fleet for 100% of intra-facility parts and material delivery", 0.95),
            ("news",            "Hyundai Motor Group Robotics Lab deploys Boston Dynamics Spot and AMR fleets at HMGMA for factory inspections and parts delivery; expanding fleet by 200 units in 2026", 0.91),
            ("labor_shortage",  "HMGMA Georgia facing competition for skilled manufacturing labor from nearby Kia, Rivian, and SK Battery plants; indirect roles in material handling particularly difficult to staff", 0.85),
        ],
    },
    {
        "company": {
            "name": "Nissan North America",
            "website": "https://www.nissanusa.com",
            "industry": "Automotive Manufacturing",
            "sub_industry": "OEM — Full-Line Manufacturer",
            "employee_estimate": 14600,
            "location_city": "Franklin",
            "location_state": "TN",
            "location_country": "US",
            "source": "seed_v4",
        },
        "signals": [
            ("capex",           "Nissan invests $500M to electrify Smyrna, TN plant for Leaf and Ariya production; factory automation upgrade includes autonomous parts delivery replacing manual tugger fleet", 0.89),
            ("labor_shortage",  "Nissan Smyrna and Canton, MS plants report 22% vacancy in material handling; persistent indirect labor shortage limiting production at both North American assembly facilities", 0.88),
            ("strategic_hire",  "Nissan North America hires Director of Manufacturing Automation from Toyota Production Institute; scope covers every indirect labor process across Smyrna and Canton plants", 0.87),
            ("job_posting",     "Nissan posting 250+ material handler, forklift operator, and parts runner roles across Tennessee and Mississippi plants with accelerating turnover rate", 0.85),
            ("expansion",       "Nissan Smyrna plant retooling for EV production adds new battery module assembly hall; autonomous intra-building logistics requested in equipment specification", 0.86),
        ],
    },
    {
        "company": {
            "name": "Tesla",
            "website": "https://www.tesla.com",
            "industry": "Automotive Manufacturing",
            "sub_industry": "OEM — EV Manufacturer",
            "employee_estimate": 140000,
            "location_city": "Austin",
            "location_state": "TX",
            "location_country": "US",
            "source": "seed_v4",
        },
        "signals": [
            ("capex",           "Tesla Gigafactory Texas Phase 2 expansion adds 4M sq ft of production space; intra-facility logistics for battery, body, and final assembly planned with autonomous delivery infrastructure", 0.93),
            ("strategic_hire",  "Tesla hiring Director of Factory Logistics Robotics for Gigafactory Nevada and Texas; role specifies design and deployment of AMR fleets for parts-to-line and inter-building delivery", 0.91),
            ("expansion",       "Tesla Mexico City Gigafactory groundbreaking; massive 10M sq ft campus planned with full autonomous intra-facility logistics — no manual tugger operator job classifications in org design", 0.94),
            ("job_posting",     "Tesla posting 500+ material flow and manufacturing associates across Fremont and Texas Gigafactories; high turnover in indirect roles cited in internal manufacturing ops reviews", 0.88),
            ("news",            "Tesla autonomous material handling pilot at Gigafactory Nevada achieves 40% throughput improvement vs manual delivery; Elon Musk directs deployment at all factories by end of 2026", 0.92),
        ],
    },
    {
        "company": {
            "name": "Rivian Automotive",
            "website": "https://www.rivian.com",
            "industry": "Automotive Manufacturing",
            "sub_industry": "OEM — EV Manufacturer",
            "employee_estimate": 18000,
            "location_city": "Normal",
            "location_state": "IL",
            "location_country": "US",
            "source": "seed_v4",
        },
        "signals": [
            ("capex",           "Rivian secures $5B Volkswagen partnership and $6.6B DOE loan for Normal, IL plant expansion and new Georgia stag plant; AMR-first intra-facility logistics specified in all capital planning", 0.94),
            ("strategic_hire",  "Rivian appoints Vice President of Manufacturing Operations from Foxconn; immediate priority is automating parts delivery and kitting operations to support R2 production ramp", 0.91),
            ("expansion",       "Rivian breaks ground on Stanton Springs North Georgia plant; 7,700-acre campus with 5M sq ft of manufacturing designed around autonomous logistics — no manual material handler headcount in plan", 0.95),
            ("labor_shortage",  "Rivian Normal plant facing severe competition for indirect manufacturing labor from nearby Tesla and traditional OEM suppliers; material handling roles have 60% annualized turnover", 0.89),
            ("news",            "Rivian partners with AMR vendor to deploy 300 autonomous delivery robots at Normal, IL plant for sub-assembly and battery module delivery to R1T and R1S production lines", 0.92),
        ],
    },

    # =========================================================================
    # TIER 1 AUTOMOTIVE SUPPLIERS
    # =========================================================================

    {
        "company": {
            "name": "Magna International",
            "website": "https://www.magna.com",
            "industry": "Automotive Manufacturing",
            "sub_industry": "Tier 1 Supplier — Complete Vehicle & Systems",
            "employee_estimate": 172000,
            "location_city": "Troy",
            "location_state": "MI",
            "location_country": "US",
            "source": "seed_v4",
        },
        "signals": [
            ("capex",           "Magna International commits $1.2B to smart manufacturing transformation across 340 global facilities; autonomous intra-facility parts delivery and kitting automation are priority categories", 0.93),
            ("strategic_hire",  "Magna hires Global VP of Smart Manufacturing Systems; mandate to standardize AMR-based parts delivery across all Cosma, Seating, Exteriors, and Powertrain divisions worldwide", 0.91),
            ("labor_shortage",  "Magna North American plants face 29% vacancy in material handling and kitting roles across Ontario, Michigan, and Ohio facilities; chronic turnover in these classifications costs $40M+ annually", 0.90),
            ("job_posting",     "Magna posting 800+ material handler, kitting associate, and parts delivery operator roles across Michigan and Ontario plants; highest-volume indirect labor recruitment in company history", 0.88),
            ("expansion",       "Magna opens three new Tier 1 supply plants in Tennessee and Alabama to service HMGMA, Rivian, and VW Scout programs; all three facilities specify AMR-compatible logistics infrastructure", 0.89),
        ],
    },
    {
        "company": {
            "name": "Robert Bosch LLC",
            "website": "https://www.boschusa.com",
            "industry": "Automotive Manufacturing",
            "sub_industry": "Tier 1 Supplier — Electronics & Powertrain Systems",
            "employee_estimate": 32000,
            "location_city": "Farmington Hills",
            "location_state": "MI",
            "location_country": "US",
            "source": "seed_v4",
        },
        "signals": [
            ("capex",           "Bosch invests $3.2B in US semiconductor and electrification manufacturing; Anderson, SC and Charleston, SC plants receive autonomous intra-facility logistics as part of smart factory program", 0.92),
            ("strategic_hire",  "Bosch North America appoints Head of Manufacturing Automation and Logistics; responsible for AMR deployment across all US assembly, testing, and distribution facilities", 0.90),
            ("labor_shortage",  "Bosch US manufacturing plants struggling to fill 600+ material handling and parts replenishment roles; South Carolina and Michigan labor markets at near-full employment in manufacturing sector", 0.89),
            ("news",            "Bosch Rexroth deploys 200 AMRs for intra-facility parts delivery at Homburg, Germany plant; program being replicated at Anderson, SC and Juarez, Mexico facilities in 2026", 0.91),
            ("expansion",       "Bosch announces new $1.5B EV charging component plant in Virginia; designed from scratch with AMR-based intra-facility logistics — zero manual material handler job classifications", 0.88),
        ],
    },
    {
        "company": {
            "name": "Panasonic Automotive Systems",
            "website": "https://www.panasonicautomotive.com",
            "industry": "Automotive Manufacturing",
            "sub_industry": "Tier 1 Supplier — Battery & Electronics",
            "employee_estimate": 7500,
            "location_city": "Peachtree City",
            "location_state": "GA",
            "location_country": "US",
            "source": "seed_v4",
        },
        "signals": [
            ("capex",           "Panasonic Energy of North America invests $4B in second Kansas EV battery gigafactory in De Soto; autonomous intra-facility logistics for cell and module delivery in facility specification", 0.93),
            ("expansion",       "Panasonic Energy opens 4.3M sq ft De Soto, KS gigafactory; massive scale demands AMR fleet for intra-building parts delivery — manual handling not operationally viable at volume", 0.94),
            ("labor_shortage",  "Panasonic Gigafactory Nevada struggling to staff material handling and parts delivery roles; competition with Tesla, Switch, and Amazon creates persistent 25% vacancy in indirect labor", 0.91),
            ("strategic_hire",  "Panasonic Energy NA hires Director of Factory Automation and Logistics; first priority is automating cell transport and module delivery between production zones at all US battery plants", 0.89),
            ("news",            "Panasonic Energy pilots AMR fleet for battery cell inter-building transport at Sparks, NV facility; cycle time reduced 44%; management authorizing full deployment at De Soto plant", 0.92),
        ],
    },
    {
        "company": {
            "name": "Aptiv PLC",
            "website": "https://www.aptiv.com",
            "industry": "Automotive Manufacturing",
            "sub_industry": "Tier 1 Supplier — Electrical Architecture",
            "employee_estimate": 196000,
            "location_city": "Dublin",
            "location_state": "",
            "location_country": "IE",
            "source": "seed_v4",
        },
        "signals": [
            ("capex",           "Aptiv invests $1.8B in North American manufacturing capacity for high-voltage connectivity systems; Querétaro and El Paso facilities implementing autonomous parts delivery to wiring harness assembly lines", 0.90),
            ("strategic_hire",  "Aptiv appoints Chief Manufacturing Technology Officer; autonomous intra-facility logistics for wiring harness component delivery is a named priority in the corporate manufacturing strategy", 0.88),
            ("labor_shortage",  "Aptiv North American harness plants face persistent shortage of kitting and material handling associates; labor cost per vehicle wiring set increasing 18% year-over-year", 0.89),
            ("expansion",       "Aptiv opens new high-voltage cable assembly plant in Chihuahua, Mexico servicing GM, Ford, and Tesla EV programs; facility designed with AMR-compatible delivery lanes throughout", 0.87),
            ("job_posting",     "Aptiv posting 1,200+ material handler and kitting associate roles across Texas and Mexico border plants; highest indirect labor recruitment volume in company history", 0.86),
        ],
    },
    {
        "company": {
            "name": "Continental Automotive Americas",
            "website": "https://www.continental.com",
            "industry": "Automotive Manufacturing",
            "sub_industry": "Tier 1 Supplier — Chassis & Safety Systems",
            "employee_estimate": 10000,
            "location_city": "Auburn Hills",
            "location_state": "MI",
            "location_country": "US",
            "source": "seed_v4",
        },
        "signals": [
            ("capex",           "Continental AG invests EUR 1.7B in smart factory transformation; all North American plants in Michigan, South Carolina, and Tennessee included in autonomous logistics deployment rollout", 0.89),
            ("strategic_hire",  "Continental Americas names Director of Autonomous Factory Logistics; scope covers AMR-based parts delivery for tire, brake, and powertrain component assembly lines in US plants", 0.88),
            ("labor_shortage",  "Continental US manufacturing plants reporting 26% vacancy in material handler and line-feeder roles; indirect labor shortage increasing WIP and delivery cost across all product lines", 0.87),
            ("news",            "Continental Group deploys 800 AMRs for intra-plant parts delivery across Regensburg and Frankfurt plants; Americas division implementing identical model at Fort Mill, SC and New Braunfels, TX", 0.90),
            ("expansion",       "Continental opens new brake system manufacturing campus in Goldsboro, NC; $250M investment in facility designed with autonomous intra-facility logistics from day one of production", 0.85),
        ],
    },
    {
        "company": {
            "name": "Lear Corporation",
            "website": "https://www.lear.com",
            "industry": "Automotive Manufacturing",
            "sub_industry": "Tier 1 Supplier — Seating & Electrical",
            "employee_estimate": 186000,
            "location_city": "Southfield",
            "location_state": "MI",
            "location_country": "US",
            "source": "seed_v4",
        },
        "signals": [
            ("capex",           "Lear Corporation invests $1.1B in electrification and smart manufacturing; E-Systems and Seating divisions both deploying autonomous intra-plant parts delivery across North American footprint", 0.91),
            ("labor_shortage",  "Lear Michigan and Alabama seating plants face 31% vacancy in material handling and foam/cover assembly delivery roles; $25M incremental overtime cost in FY2025 from indirect labor gap", 0.90),
            ("strategic_hire",  "Lear appoints SVP of Global Manufacturing Technology; AMR-based parts delivery for seating component kitting is the top project in the 2026 capital plan", 0.88),
            ("job_posting",     "Lear posting 900+ material handler, kitting associate, and parts delivery roles across Michigan, Alabama, and Indiana; leading cause of delivery delays on GM and Ford seating programs", 0.87),
            ("expansion",       "Lear opens two new EV-focused seating plants in Georgia and Tennessee serving HMGMA and VW Scout programs; both facilities designed with AMR-first intra-plant logistics", 0.86),
        ],
    },
    {
        "company": {
            "name": "Denso Manufacturing America",
            "website": "https://www.denso.com",
            "industry": "Automotive Manufacturing",
            "sub_industry": "Tier 1 Supplier — Thermal, Powertrain & Safety",
            "employee_estimate": 17000,
            "location_city": "Battle Creek",
            "location_state": "MI",
            "location_country": "US",
            "source": "seed_v4",
        },
        "signals": [
            ("capex",           "Denso North America invests $1.4B in electrification components; Battle Creek and Athens, TN plants receiving autonomous parts delivery and inter-cell WIP transport systems as part of MONOZUKURI smart factory program", 0.91),
            ("strategic_hire",  "Denso Manufacturing Americas promotes Director of Innovative Production to VP; autonomous material delivery and zero-touch logistics are the top investment priorities for North American plants", 0.89),
            ("labor_shortage",  "Denso US plants consistently 20%+ understaffed in material handling and tugger operator roles; Toyota Production System efficiency targets cannot be met with current manual delivery model", 0.88),
            ("news",            "Denso global AMR deployment exceeds 2,000 units for intra-plant parts delivery in Japan; Americas division committed to full deployment at all major North American facilities by 2027", 0.90),
            ("expansion",       "Denso opens electrification component campus in Paris, TN to supply GM Ultium and Honda-LG battery programs; facility designed with dock-to-line AMR parts delivery from production launch", 0.87),
        ],
    },
    {
        "company": {
            "name": "BorgWarner",
            "website": "https://www.borgwarner.com",
            "industry": "Automotive Manufacturing",
            "sub_industry": "Tier 1 Supplier — Propulsion & Thermal Technology",
            "employee_estimate": 41000,
            "location_city": "Auburn Hills",
            "location_state": "MI",
            "location_country": "US",
            "source": "seed_v4",
        },
        "signals": [
            ("capex",           "BorgWarner invests $2.3B in EV drivetrain and battery management components; Hazel Park, MI and Tuscaloosa, AL plants receiving autonomous intra-plant logistics as part of Charging Forward transformation", 0.90),
            ("strategic_hire",  "BorgWarner hires Director of Manufacturing Operations from Delphi Technologies; primary mandate is automating parts delivery and WIP movement across eMotor and inverter assembly lines", 0.88),
            ("labor_shortage",  "BorgWarner Michigan and Indiana plants report 23% vacancy in material handling and line-feeder roles; indirect labor shortage constraining throughput on EV program launches", 0.87),
            ("ma_activity",     "BorgWarner acquires Delphi Technologies, Akasol, Hubei Surpass Sun Electric, and Santroll; 8+ integration events requiring standardized logistics infrastructure across all acquired manufacturing sites", 0.86),
            ("expansion",       "BorgWarner opens two new eMotor manufacturing plants in South Carolina and Tennessee to supply Ford, Stellantis, and Hyundai EV programs; both specify AMR parts delivery in facility design", 0.87),
        ],
    },
    {
        "company": {
            "name": "Valeo North America",
            "website": "https://www.valeo.com",
            "industry": "Automotive Manufacturing",
            "sub_industry": "Tier 1 Supplier — Powertrain & Thermal",
            "employee_estimate": 6500,
            "location_city": "Troy",
            "location_state": "MI",
            "location_country": "US",
            "source": "seed_v4",
        },
        "signals": [
            ("capex",           "Valeo invests EUR 2B in electrification; North American plants in Michigan, Tennessee, and Mexico receiving autonomous intra-facility logistics as part of Valeo Factory 4.0 program", 0.88),
            ("strategic_hire",  "Valeo North America appoints VP of Smart Manufacturing; autonomous parts delivery and zero-defect kitting are the top two manufacturing automation investments in the 2026 budget", 0.87),
            ("expansion",       "Valeo opens new 48V mild-hybrid and EV charging component plant in Monterrey, Mexico; 800,000 sq ft facility designed with AMR-compatible parts delivery infrastructure throughout", 0.86),
            ("labor_shortage",  "Valeo Michigan and Tennessee plants face 24% vacancy in material handling roles; labor shortages in automotive manufacturing corridor forcing $12M annual overtime cost", 0.85),
            ("news",            "Valeo Group deploys 1,200 AMRs for intra-plant parts delivery across French and German plants; Americas division rolling out identical program at all US and Mexico facilities in 2026", 0.88),
        ],
    },
    {
        "company": {
            "name": "Adient",
            "website": "https://www.adient.com",
            "industry": "Automotive Manufacturing",
            "sub_industry": "Tier 1 Supplier — Seating Systems",
            "employee_estimate": 85000,
            "location_city": "Plymouth",
            "location_state": "MI",
            "location_country": "US",
            "source": "seed_v4",
        },
        "signals": [
            ("labor_shortage",  "Adient North American seating plants chronically understaffed in foam, cover, and frame delivery roles; 35% vacancy in material handler classifications across Michigan, Indiana, and Alabama facilities", 0.91),
            ("capex",           "Adient invests $900M in JIT seating manufacturing transformation; autonomous parts delivery for frame, foam, and trim component kitting is the top capital investment category", 0.89),
            ("job_posting",     "Adient posting 1,100+ material handler and kitting associate roles across US seating plants; highest indirect labor posting volume in Adient history — cost per seat increasing 22% YoY", 0.88),
            ("strategic_hire",  "Adient appoints Chief Manufacturing Excellence Officer from Lear Corporation; first 90-day priority is automating sub-component delivery on sequenced seating assembly lines", 0.87),
            ("expansion",       "Adient opening three new JIT seating plants adjacent to GM, Ford, and Stellantis EV assembly facilities in Michigan and Ohio; all three designed with AMR-first intra-plant logistics", 0.85),
        ],
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS (same pattern as seed_leads_v2/v3)
# ─────────────────────────────────────────────────────────────────────────────

def seed_database(db, dry_run=True):
    added_c = added_s = 0
    for entry in NEW_LEADS:
        cd = entry["company"]
        existing = db.query(Company).filter(Company.name == cd["name"]).first()
        if existing:
            company = existing
        else:
            added_c += 1
            if dry_run:
                continue
            company = Company(
                name=cd["name"],
                website=cd.get("website"),
                industry=cd.get("industry", "Unknown"),
                sub_industry=cd.get("sub_industry"),
                employee_estimate=cd.get("employee_estimate"),
                location_city=cd.get("location_city"),
                location_state=cd.get("location_state"),
                location_country=cd.get("location_country", "US"),
                source=cd.get("source", "seed_v4"),
            )
            db.add(company)
            db.commit()
            db.refresh(company)

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
                        source_url="seed_v4",
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
        total_co = len(NEW_LEADS)
        total_sig = sum(len(e["signals"]) for e in NEW_LEADS)
        industries = {}
        countries = {}
        for e in NEW_LEADS:
            ind = e["company"]["industry"]
            cty = e["company"]["location_country"]
            industries[ind] = industries.get(ind, 0) + 1
            countries[cty] = countries.get(cty, 0) + 1
        print(f"\n=== seed_leads_v4 DRY RUN ===")
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

    print("\n=== seed_leads_v4  COMMITTING TO DATABASE ===")
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
