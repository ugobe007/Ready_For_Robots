"""
seed_leads_v5.py — Automotive Dealership Groups (all OEM brands), OEM Innovation/VC,
                    Additional Tier 1 Suppliers, Aerospace & Defense

Dealership products: Titan (parts-to-bay), DUST-E (service drive), Dex (parts counter),
                     ADAM / Matradee (customer lounge / waiting area service)
OEM Innovation:      Richtech as investment target + co-development partner
Tier 1 Suppliers:    Intra-facility AMR fleet (kitting, WIP, sub-assembly delivery)
Aerospace:           Factory floor AMR, maintenance logistics, supply chain automation

Usage:
  python scripts/seed_leads_v5.py           # dry-run count
  python scripts/seed_leads_v5.py --commit  # write to DB
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

NEW_LEADS = [

    # =========================================================================
    # AUTOMOTIVE DEALERSHIPS — Large Public Groups (multi-brand)
    # =========================================================================

    {
        "company": {
            "name": "AutoNation",
            "website": "https://www.autonation.com",
            "industry": "Automotive Dealerships",
            "sub_industry": "Public Dealer Group — Multi-Brand (Toyota, BMW, Mercedes, Honda, Ford, GM)",
            "employee_estimate": 26000,
            "location_city": "Fort Lauderdale",
            "location_state": "FL",
            "location_country": "US",
            "source": "seed_v5",
        },
        "signals": [
            ("labor_shortage",  "AutoNation reports 31% vacancy rate in parts counter, service drive, and porter roles across 250+ franchise stores; parts runners and counter associates are the hardest roles to fill and retain", 0.92),
            ("capex",           "AutoNation commits $680M to AutoNation USA used-car expansion and store renovation program; service drive technology and parts logistics infrastructure are key capital line items", 0.89),
            ("strategic_hire",  "AutoNation appoints Chief Operations & Technology Officer; reducing parts delivery cycle time and automating service drive workflow across all brands is a stated priority", 0.91),
            ("expansion",       "AutoNation opens 9 new franchise rooftops in 2025 covering Toyota, BMW, Mercedes-Benz, and Honda; each new store is designed with modern service bay layout and parts automation readiness", 0.87),
            ("job_posting",     "AutoNation posting 1,200+ parts counter, porter, service advisor, and lube technician roles nationally; highest indirect labor vacancy rate in company history driving interest in Titan deployment", 0.90),
        ],
    },
    {
        "company": {
            "name": "Lithia Motors",
            "website": "https://www.lithiamotors.com",
            "industry": "Automotive Dealerships",
            "sub_industry": "Public Dealer Group — Multi-Brand (Toyota, Ford, BMW, Honda, Stellantis + 30 more)",
            "employee_estimate": 27000,
            "location_city": "Medford",
            "location_state": "OR",
            "location_country": "US",
            "source": "seed_v5",
        },
        "signals": [
            ("expansion",       "Lithia Motors / Driveway operates 330+ stores across 48 states and Canada covering every major OEM brand; ongoing acquisition program adds 20–30 rooftops per year — each needs parts automation onboarding", 0.91),
            ("ma_activity",     "Lithia acquires Pfaff Automotive (Canada), Pendragon PLC (UK), and multiple regional dealer groups; integration of parts and service workflows across acquired stores requires scalable logistics solution", 0.90),
            ("labor_shortage",  "Lithia fixed ops teams report 28% vacancy in parts fulfillment and service drive across acquired stores; turnover in porter and parts runner roles exceeds 70% annually", 0.89),
            ("capex",           "Lithia invests $1.2B in Driveway digital retail and store modernization; service technology and parts counter automation included in all new facility build-outs", 0.87),
            ("strategic_hire",  "Lithia names Chief Fixed Operations Officer to standardize service and parts workflows across all 330 stores; automation of parts-to-bay delivery is the top fixed ops initiative", 0.88),
        ],
    },
    {
        "company": {
            "name": "Penske Automotive Group",
            "website": "https://www.penskecars.com",
            "industry": "Automotive Dealerships",
            "sub_industry": "Public Dealer Group — Luxury Focus (BMW, Porsche, Audi, Mercedes, Lexus, Ferrari)",
            "employee_estimate": 27000,
            "location_city": "Bloomfield Hills",
            "location_state": "MI",
            "location_country": "US",
            "source": "seed_v5",
        },
        "signals": [
            ("capex",           "Penske Automotive invests $780M in UK and US dealership renovations; flagship BMW, Porsche, and Audi stores receive dedicated parts automation and service drive technology upgrades", 0.90),
            ("labor_shortage",  "Penske luxury stores struggle to hire and retain parts counter specialists for high-SKU BMW, Porsche, and Audi parts inventories; turnover in parts department exceeds 55% annually", 0.89),
            ("expansion",       "Penske acquires 12 luxury franchise rooftops in the US and UK including Porsche, Audi, and BMW stores; all acquired locations flagged for service operations modernization", 0.88),
            ("strategic_hire",  "Penske appoints VP of Fixed Operations; Titan-class parts delivery automation is a named priority to reduce technician idle time waiting for parts across premium brand stores", 0.87),
            ("job_posting",     "Penske posting 600+ parts specialist, warehouse associate, and service porter roles across BMW, Porsche, and Audi stores; premium brand parts complexity makes manual delivery unsustainable", 0.86),
        ],
    },
    {
        "company": {
            "name": "Group 1 Automotive",
            "website": "https://www.group1auto.com",
            "industry": "Automotive Dealerships",
            "sub_industry": "Public Dealer Group — Multi-Brand (Toyota, BMW, Mercedes, Honda, Ford, VW)",
            "employee_estimate": 14000,
            "location_city": "Houston",
            "location_state": "TX",
            "location_country": "US",
            "source": "seed_v5",
        },
        "signals": [
            ("expansion",       "Group 1 Automotive operates 200+ dealerships in the US, UK, and Brazil; active acquisition program targeting Toyota, BMW, Mercedes, and Honda stores in Sun Belt and Southeast markets", 0.88),
            ("labor_shortage",  "Group 1 US operations report 26% vacancy in fixed operations support roles; South Texas and UK labor markets make parts runner and service porter recruitment particularly difficult", 0.87),
            ("capex",           "Group 1 invests $410M to modernize US and UK store facilities; service drive technology, parts counter digitization, and customer experience improvements are investment priorities", 0.86),
            ("strategic_hire",  "Group 1 Automotive hires VP of Operations Transformation from AutoNation; first priority is standardizing parts workflow and delivery across all US franchise stores", 0.85),
            ("ma_activity",     "Group 1 acquires Prime Automotive Group (New England) adding Toyota, BMW, Honda, and Volvo stores; integration includes parts and service operations standardization across all acquired rooftops", 0.84),
        ],
    },
    {
        "company": {
            "name": "Asbury Automotive Group",
            "website": "https://www.asburyauto.com",
            "industry": "Automotive Dealerships",
            "sub_industry": "Public Dealer Group — Multi-Brand (Toyota, Honda, BMW, Subaru, Hyundai, Cadillac)",
            "employee_estimate": 15000,
            "location_city": "Duluth",
            "location_state": "GA",
            "location_country": "US",
            "source": "seed_v5",
        },
        "signals": [
            ("ma_activity",     "Asbury acquires Larry H. Miller Dealerships (90+ stores, Toyota/Honda/VW/Audi/BMW), Planet Automotive Group, and Park Place Dealerships; largest acquisition spree in company history requires parts ops standardization across 200+ stores", 0.92),
            ("labor_shortage",  "Asbury fixed operations capacity constrained by 29% vacancy in parts and service support roles; retention crisis costs $28M annually in overtime and training for parts runner and lube tech categories", 0.90),
            ("capex",           "Asbury commits $925M to Clicklane digital platform and store facility upgrades; service lane technology and parts delivery automation are key efficiency investments in the roadmap", 0.88),
            ("strategic_hire",  "Asbury names Chief Customer Experience Officer; automated parts-to-bay delivery and customer lounge service robotics (Matradee) are named use cases in the 2026 innovation plan", 0.87),
            ("expansion",       "Asbury opens 8 new Toyota and BMW stores in Georgia, Texas, and Colorado; all new facilities designed with modern service bays and parts automation staging areas", 0.85),
        ],
    },
    {
        "company": {
            "name": "Sonic Automotive / EchoPark",
            "website": "https://www.sonicautomotive.com",
            "industry": "Automotive Dealerships",
            "sub_industry": "Public Dealer Group — Multi-Brand + EV (BMW, Honda, Toyota, Cadillac, Mercedes)",
            "employee_estimate": 10000,
            "location_city": "Charlotte",
            "location_state": "NC",
            "location_country": "US",
            "source": "seed_v5",
        },
        "signals": [
            ("expansion",       "Sonic Automotive expanding EchoPark used-vehicle superstore chain to 50 markets; high-velocity inventory and parts throughput demands automated delivery from receiving dock to sales floor", 0.88),
            ("labor_shortage",  "Sonic franchise stores report 27% vacancy in fixed ops support; BMW, Mercedes, and Cadillac parts complexity exacerbates the shortage as counter specialists require extensive product training", 0.87),
            ("strategic_hire",  "Sonic Automotive hires Chief Technology & Innovation Officer; deploying automation in the parts department and service write-up process is a named Q2 2026 initiative", 0.86),
            ("capex",           "Sonic invests $340M in EchoPark expansion and franchise store upgrades; parts counter automation and service drive technology flagged as efficiency investments across BMW and Honda stores", 0.84),
            ("job_posting",     "Sonic posting 500+ parts technician, porter, and service advisor roles across BMW, Honda, Toyota, and Cadillac stores; EchoPark high-volume used stores also posting inventory associates", 0.83),
        ],
    },

    # =========================================================================
    # AUTOMOTIVE DEALERSHIPS — Large Private Groups (Brand-Specific)
    # =========================================================================

    {
        "company": {
            "name": "Hendrick Automotive Group",
            "website": "https://www.hendrickauto.com",
            "industry": "Automotive Dealerships",
            "sub_industry": "Private Dealer Group — Multi-Brand (Chevrolet, Honda, Toyota, BMW, Cadillac, Acura)",
            "employee_estimate": 11000,
            "location_city": "Charlotte",
            "location_state": "NC",
            "location_country": "US",
            "source": "seed_v5",
        },
        "signals": [
            ("labor_shortage",  "Hendrick Automotive 100+ stores in the Southeast report 33% vacancy in parts runners and service drive support; Charlotte-area labor market competition from Amazon and logistics hubs drives chronic understaffing", 0.91),
            ("expansion",       "Hendrick opens 6 new stores in 2025 covering Chevrolet, Honda, BMW, and Toyota; largest private dealer group expansion in the Southeast — all new locations specify modern parts automation layout", 0.88),
            ("strategic_hire",  "Hendrick names VP of Fixed Operations Technology; Titan deployment for parts-to-bay automation is the top initiative — replacing manual parts runners across 100+ store footprint", 0.90),
            ("capex",           "Hendrick Automotive invests $220M in store renovations and EV service readiness; BMW and Cadillac EV parts complexity makes automated delivery ROI compelling across the fleet", 0.87),
            ("job_posting",     "Hendrick posting 800+ parts counter and service support roles nationally; highest fixed ops vacancy rate in 15 years due to industry-wide shortage of trained dealership support staff", 0.89),
        ],
    },
    {
        "company": {
            "name": "Larry H. Miller Dealerships",
            "website": "https://www.lhmauto.com",
            "industry": "Automotive Dealerships",
            "sub_industry": "Private Dealer Group — Multi-Brand (Toyota, Honda, Nissan, Chevrolet, Hyundai, Audi, VW, Lexus, Acura)",
            "employee_estimate": 8000,
            "location_city": "Sandy",
            "location_state": "UT",
            "location_country": "US",
            "source": "seed_v5",
        },
        "signals": [
            ("ma_activity",     "Larry H. Miller Dealerships acquired by Asbury Automotive in $3.2B deal; 90+ stores covering Toyota, Honda, Nissan, Audi, Hyundai across Utah, Arizona, Colorado being integrated — parts standardization across all brands needed", 0.91),
            ("labor_shortage",  "LHM Utah and Arizona stores chronically understaffed in parts runners, porters, and lube techs; Wasatch Front labor market heavily competitive with tech industry for entry-level roles", 0.89),
            ("expansion",       "LHM group adding 12 new Toyota, Hyundai, and Honda stores in Intermountain West; parts logistics modernization flagged as day-one requirement in new store operational plan", 0.87),
            ("capex",           "LHM invests $180M in store renovations and EV infrastructure; high-volume Toyota stores in Utah are natural Titan use cases with 30+ service bays and large parts departments", 0.86),
            ("job_posting",     "LHM posting 400+ parts counter specialist, service porter, and quick lube tech roles across UT, AZ, CO; in-market competition from outdoor recreation and hospitality industries worsens vacancy", 0.85),
        ],
    },
    {
        "company": {
            "name": "Findlay Automotive Group",
            "website": "https://www.findlayauto.com",
            "industry": "Automotive Dealerships",
            "sub_industry": "Private Dealer Group — Multi-Brand (Toyota, Honda, Cadillac, VW, Hyundai, Audi, Mitsubishi, CDJR)",
            "employee_estimate": 2500,
            "location_city": "Henderson",
            "location_state": "NV",
            "location_country": "US",
            "source": "seed_v5",
        },
        "signals": [
            ("labor_shortage",  "Findlay Toyota Henderson and Findlay Honda parts departments operating with 40% vacancy; Las Vegas metro labor market is one of the most competitive for dealership support roles nationally", 0.93),
            ("expansion",       "Findlay Automotive adding 4 new stores in Nevada and Utah including VW, Hyundai, and CDJR franchise points; all new stores under construction with service bay count exceeding 30 — Titan deployment ready", 0.89),
            ("capex",           "Findlay invests $85M in store upgrades across Henderson, Las Vegas, and St. George locations; Cadillac EV and VW ID. series service readiness includes parts storage automation planning", 0.87),
            ("strategic_hire",  "Findlay Automotive hires Group Fixed Operations Director tasked with standardizing parts delivery and reducing technician wait time across all 18 Nevada/Utah rooftops", 0.88),
            ("job_posting",     "Findlay Toyota, Honda, and Cadillac posting 140+ parts runner, porter, and service tech aide roles; Las Vegas hospitality and warehouse pay rates force dealerships to compete on schedule flexibility and automation", 0.86),
        ],
    },
    {
        "company": {
            "name": "Ken Garff Automotive Group",
            "website": "https://www.kengarff.com",
            "industry": "Automotive Dealerships",
            "sub_industry": "Private Dealer Group — Multi-Brand (Honda, Toyota, Nissan, Hyundai, Buick, BMW, Ram/Jeep)",
            "employee_estimate": 5500,
            "location_city": "Salt Lake City",
            "location_state": "UT",
            "location_country": "US",
            "source": "seed_v5",
        },
        "signals": [
            ("labor_shortage",  "Ken Garff Utah, Iowa, and Texas stores report 35% vacancy in parts and service support roles; Wasatch Front labor market dominated by tech, logistics, and ski resort industries", 0.90),
            ("expansion",       "Ken Garff adds BMW, Honda, and Hyundai franchise points in Texas and Iowa; multi-state expansion now covers 60+ rooftops across 5 states requiring standardized parts automation", 0.87),
            ("strategic_hire",  "Ken Garff promotes VP of Operations with explicit mandate to deploy service automation at all Honda, Toyota, and BMW stores — Titan cited in internal operational improvement plan", 0.89),
            ("capex",           "Ken Garff invests $120M in store facility upgrades; newest stores feature dedicated parts automation staging areas and wider service drives designed for robot navigation", 0.85),
            ("job_posting",     "Ken Garff posting 300+ parts runner, porter, and service advisor roles across Honda and Toyota stores quarterly; highest-volume indirect labor recruitment in 20-year company history", 0.87),
        ],
    },
    {
        "company": {
            "name": "JM Family Enterprises",
            "website": "https://www.jmfamily.com",
            "industry": "Automotive Dealerships",
            "sub_industry": "Private Dealer Group — Toyota / Lexus Focus (Southeast Toyota Distributor + Dealer)",
            "employee_estimate": 5300,
            "location_city": "Deerfield Beach",
            "location_state": "FL",
            "location_country": "US",
            "source": "seed_v5",
        },
        "signals": [
            ("capex",           "JM Family Enterprises invests $300M in Southeast Toyota and Lexus dealership modernization; Southeast Toyota Distributors processes 200,000+ vehicles per year through its Jacksonville logistics campus — parts delivery automation critical", 0.91),
            ("labor_shortage",  "JM Family Toyota and Lexus stores in Florida report 30% vacancy in parts and service logistics; Southeast Florida labor market makes dealership support roles among the most difficult to fill in the US", 0.90),
            ("strategic_hire",  "JM Family Enterprises appoints VP of Operational Excellence; Titan-class parts delivery automation is a Q1 2026 pilot across Southeast Toyota flagship stores in Florida and Georgia", 0.89),
            ("expansion",       "JM Family opens 5 new Toyota and Lexus stores in Florida, Georgia, and the Carolinas; Southeast Toyota distribution hub in Jacksonville expanded by 800,000 sq ft requiring automated intra-facility parts logistics", 0.87),
            ("news",            "JM Family Enterprises Southeast Toyota Distributors division named Toyota's top North American distributor; modernizing parts delivery and warehouse operations to maintain that ranking — AMR deployment in active evaluation", 0.88),
        ],
    },
    {
        "company": {
            "name": "Park Place Dealerships",
            "website": "https://www.parkplace.com",
            "industry": "Automotive Dealerships",
            "sub_industry": "Private Dealer Group — Luxury (BMW, Lexus, Porsche, Mercedes, Volvo, Jaguar, Land Rover)",
            "employee_estimate": 2800,
            "location_city": "Dallas",
            "location_state": "TX",
            "location_country": "US",
            "source": "seed_v5",
        },
        "signals": [
            ("strategic_hire",  "Park Place Dealerships (acquired by Asbury) names Director of Fixed Operations Innovation; luxury brand parts complexity (BMW, Porsche, Lexus, Mercedes) makes Titan ROI immediate — 50+ parts SKUs per repair order", 0.91),
            ("labor_shortage",  "Park Place BMW, Lexus, and Porsche stores struggle to hire and retain parts specialists who understand luxury parts catalogs; turnover in parts counter and runner roles costs $3.5M annually in lost productivity", 0.92),
            ("capex",           "Park Place invests $95M in Dallas luxury store expansion and renovation; Porsche and BMW service departments designed with 40+ bays — parts delivery automation is ROI-positive from day one", 0.88),
            ("job_posting",     "Park Place posting 200+ luxury parts counter, concierge service, and valet technician roles across Texas BMW, Lexus, and Porsche stores; luxury clients demand faster parts availability, amplifying automation urgency", 0.87),
            ("expansion",       "Park Place adds Aston Martin, Genesis, and Bentley franchise points under the Asbury portfolio; expanding luxury portfolio increases parts SKU complexity — exactly the use case where DUST-E and Titan differentiate", 0.86),
        ],
    },
    {
        "company": {
            "name": "Herb Chambers Companies",
            "website": "https://www.herbchambers.com",
            "industry": "Automotive Dealerships",
            "sub_industry": "Private Dealer Group — Luxury New England (BMW, Toyota, Mercedes, Porsche, Volvo, Rolls-Royce)",
            "employee_estimate": 3000,
            "location_city": "Boston",
            "location_state": "MA",
            "location_country": "US",
            "source": "seed_v5",
        },
        "signals": [
            ("labor_shortage",  "Herb Chambers Boston-area BMW, Mercedes, and Porsche stores face a 38% vacancy crisis in parts and service support; Greater Boston minimum wage and tech industry competition make dealership entry-level roles nearly impossible to fill", 0.93),
            ("capex",           "Herb Chambers invests $130M in Route 9 auto campus expansion covering BMW, Toyota, Mercedes, and Porsche; new builds feature 50+ service bays and dedicated parts logistics infrastructure designed for automation", 0.88),
            ("strategic_hire",  "Herb Chambers appoints Group Service Director with a mandate to reduce parts wait time across all 60+ New England stores; automation of parts runner function is the stated solution to the technician idle time problem", 0.90),
            ("job_posting",     "Herb Chambers posting 350+ parts counter associate, porter, and quick lube technician roles; Boston cost-of-living and competing employers force above-market wages for roles well-suited to robot replacement", 0.89),
            ("expansion",       "Herb Chambers adds Genesis and Lucid franchise points in the Boston metro; first luxury Lucid service center in New England opens with dedicated parts and technology support requirements", 0.85),
        ],
    },
    {
        "company": {
            "name": "Berkshire Hathaway Automotive",
            "website": "https://www.bhauto.com",
            "industry": "Automotive Dealerships",
            "sub_industry": "Private Dealer Group — Multi-Brand (Chevrolet, Toyota, Honda, Ford, Nissan, BMW, 30+ brands)",
            "employee_estimate": 12000,
            "location_city": "Omaha",
            "location_state": "NE",
            "location_country": "US",
            "source": "seed_v5",
        },
        "signals": [
            ("capex",           "Berkshire Hathaway Automotive (former Van Tuyl Group, acquired by Buffett) managing 100+ stores across 10 states; $450M facility modernization plan includes fixed ops efficiency technology across Toyota, Ford, and Chevrolet franchise mix", 0.90),
            ("labor_shortage",  "BH Automotive Midwest and Southwest stores report 29% vacancy in fixed operations support; Plains state labor markets increasingly competitive with energy and logistics sectors", 0.88),
            ("expansion",       "BH Automotive expanding into EV-focused service by adding Tesla-certified collision and EV service capabilities at 20 existing stores; EV parts complexity accelerates automation urgency", 0.86),
            ("strategic_hire",  "BH Automotive hires Head of Dealership Operations Technology; priority is deploying scalable parts automation across the 100+ store portfolio to reduce per-store parts labor costs by 40%", 0.89),
            ("ma_activity",     "Berkshire Hathaway signals appetite for additional dealer group acquisitions; integration playbook requires standardizing parts and service operations — Titan as a standard deployment across all acquired stores", 0.85),
        ],
    },
    {
        "company": {
            "name": "Holman Enterprises",
            "website": "https://www.holman.com",
            "industry": "Automotive Dealerships",
            "sub_industry": "Private Dealer Group — Luxury (BMW, Rolls-Royce, Bentley, Lamborghini, Audi, Porsche, Land Rover)",
            "employee_estimate": 6500,
            "location_city": "Mount Laurel",
            "location_state": "NJ",
            "location_country": "US",
            "source": "seed_v5",
        },
        "signals": [
            ("labor_shortage",  "Holman luxury stores (Rolls-Royce, Bentley, BMW, Lamborghini) require ultra-specialized parts counter staff who understand six-figure vehicle components; vacancy rates exceed 45% for these roles in New Jersey and Florida", 0.92),
            ("capex",           "Holman Enterprises invests $175M in NJ and FL flagship campus expansions for BMW, Audi, and Land Rover; ultra-luxury Rolls-Royce and Bentley service suites designed with private customer experience areas — ADAM robot for lounge service", 0.89),
            ("strategic_hire",  "Holman Automotive appoints VP of Client Experience Innovation; deploying service companion robots (ADAM/Matradee) in luxury waiting lounges and automating parts delivery with Titan across all brands", 0.91),
            ("expansion",       "Holman adds Ferrari, McLaren, and Koenigsegg dealership points; ultra-luxury brand expansion increases Holman's reputation as the go-to operator for next-generation dealership innovation", 0.87),
            ("job_posting",     "Holman posting 180+ parts specialist, client advisor, and concierge roles across BMW, Bentley, and Rolls-Royce stores; luxury client expectations demand zero wait time for parts — automation ROI is immediate", 0.88),
        ],
    },
    {
        "company": {
            "name": "Sewell Automotive Companies",
            "website": "https://www.sewell.com",
            "industry": "Automotive Dealerships",
            "sub_industry": "Private Dealer Group — Luxury Texas (Cadillac, Lexus, BMW, Infiniti, Mercedes, Buick/GMC, Ford)",
            "employee_estimate": 1800,
            "location_city": "Dallas",
            "location_state": "TX",
            "location_country": "US",
            "source": "seed_v5",
        },
        "signals": [
            ("strategic_hire",  "Sewell Automotive COO initiates service operations review; Sewell Famous Service program requires same-day parts availability — Titan deployment in all DFW stores budgeted for 2026 to fulfill this brand promise at scale", 0.93),
            ("labor_shortage",  "Sewell Cadillac, Lexus, and BMW DFW stores perennially understaffed in parts; DFW tech economy drives wages above $22/hr for parts counter roles that Titan can replace at a fraction of the annual cost", 0.92),
            ("capex",           "Sewell invests $110M in new Lexus Dallas and BMW San Antonio flagships; both feature 45+ bay service departments, valet check-in, and luxury customer lounges — Titan + ADAM natural fit for the Sewell service promise", 0.89),
            ("news",            "Sewell Automotive recognized nationally for customer service excellence; COO publicly committed to deploying technology that maintains Sewell standards as labor market tightens in Texas", 0.88),
            ("job_posting",     "Sewell posting 120+ parts associate, shuttle driver, and customer lounge host roles quarterly; customer-facing hospitality roles in Sewell's luxury lounge are being evaluated for ADAM / Matradee deployment", 0.87),
        ],
    },
    {
        "company": {
            "name": "Keyes Automotive Group",
            "website": "https://www.keyescars.com",
            "industry": "Automotive Dealerships",
            "sub_industry": "Private Dealer Group — Multi-Brand LA Market (Toyota, Honda, BMW, Hyundai, Kia, VW, Audi)",
            "employee_estimate": 1800,
            "location_city": "Van Nuys",
            "location_state": "CA",
            "location_country": "US",
            "source": "seed_v5",
        },
        "signals": [
            ("labor_shortage",  "Keyes Van Nuys and Woodland Hills Toyota, Honda, and BMW stores face 42% vacancy in parts and service support; Los Angeles minimum wage of $17.28/hr and competition from entertainment/tech industries make dealership hires challenging", 0.93),
            ("capex",           "Keyes Automotive invests $95M in Van Nuys campus renovation and EV service build-out for Hyundai, Kia, and VW; California EV mandate drives service expansion requiring modern parts automation from opening day", 0.88),
            ("strategic_hire",  "Keyes names Group Service Director with California Dealers Association board seat; publicly advocating for technology solutions to the state's dealership labor crisis — Titan pilot authorized for Van Nuys Toyota campus", 0.90),
            ("job_posting",     "Keyes posting 200+ parts specialist, driver, and service support roles in LA; California AB5 and minimum wage pressures make automation ROI compelling compared to hired contractor parts delivery model", 0.89),
            ("expansion",       "Keyes adds Genesis of Van Nuys and VW of North LA franchise points; expanding Korean and European brand mix adds catalog complexity that makes Titan even more compelling for parts accuracy and speed", 0.85),
        ],
    },
    {
        "company": {
            "name": "Bergstrom Automotive",
            "website": "https://www.bergstromauto.com",
            "industry": "Automotive Dealerships",
            "sub_industry": "Private Dealer Group — Midwest Multi-Brand (Kia, Hyundai, Genesis, Toyota, Honda, Chevrolet, Nissan, BMW)",
            "employee_estimate": 3500,
            "location_city": "Oshkosh",
            "location_state": "WI",
            "location_country": "US",
            "source": "seed_v5",
        },
        "signals": [
            ("labor_shortage",  "Bergstrom Wisconsin stores report 34% vacancy in parts runners, porters, and quick-lube techs; Fox Valley and Green Bay manufacturing competition makes entry-level dealership hiring particularly difficult", 0.91),
            ("expansion",       "Bergstrom opens 4 new stores in 2025 including Kia, Genesis, and Chevrolet franchise points; Wisconsin expansion plan calls for standardized fixed ops technology across all new and existing 50+ rooftops", 0.87),
            ("strategic_hire",  "Bergstrom Automotive appoints Group VP of Technology & Innovation with mandate to modernize the parts and service workflow across all Kia, Hyundai, Toyota, and Honda stores — Titan on the 2026 budget", 0.89),
            ("capex",           "Bergstrom invests $80M in campus expansions and EV service readiness; Kia and Hyundai EV growth in the Midwest drives service bay expansion requiring modern parts logistics infrastructure", 0.86),
            ("job_posting",     "Bergstrom posting 250+ parts counter, lot porter, and service tech aide roles quarterly across all 50 Wisconsin and Illinois stores; Kia/Hyundai/Genesis warranty parts volume growing 40% year-over-year", 0.85),
        ],
    },
    {
        "company": {
            "name": "Galpin Motors",
            "website": "https://www.galpin.com",
            "industry": "Automotive Dealerships",
            "sub_industry": "Private Dealership — Large Volume (Ford, Honda, Subaru, VW, Nissan, BMW, Mazda, Jaguar/Land Rover)",
            "employee_estimate": 1200,
            "location_city": "North Hills",
            "location_state": "CA",
            "location_country": "US",
            "source": "seed_v5",
        },
        "signals": [
            ("labor_shortage",  "Galpin Ford — the world's highest-volume Ford dealer — and adjacent Honda and VW stores chronically short-staffed in parts runners; San Fernando Valley labor market entirely dominated by entertainment and tech industries", 0.92),
            ("capex",           "Galpin Motors invests $70M in campus modernization across North Hills Ford, Honda, and Subaru stores; high-volume Ford parts department processes 3,000+ SKUs daily — Titan deployment modeled to save $1.2M in annual labor", 0.90),
            ("news",            "Galpin Ford retains world's top-selling Ford dealer title for 30th consecutive year; General Manager confirms automation pilot for parts department as next-generation efficiency initiative", 0.91),
            ("strategic_hire",  "Galpin hires Head of Service Operations from Group 1 Automotive; first mandate is deploying parts automation at Galpin Ford and Honda to eliminate manual runner delays during peak service hours", 0.88),
            ("job_posting",     "Galpin posting 150+ parts counter associate, porter, and detail technician roles in LA; peak volume of 700+ service appointments per day makes Titan ROI argument immediate for Galpin management", 0.89),
        ],
    },
    {
        "company": {
            "name": "Subaru of Indiana Automotive (SIA) Dealers",
            "website": "https://www.subaru.com",
            "industry": "Automotive Dealerships",
            "sub_industry": "Subaru Franchise Network — Growth Brand (Rapid dealer network expansion, EV/hybrid service growth)",
            "employee_estimate": 900,
            "location_city": "Lafayette",
            "location_state": "IN",
            "location_country": "US",
            "source": "seed_v5",
        },
        "signals": [
            ("expansion",       "Subaru of America dealer network grows by 120 new franchise points in 4 years as brand overtakes Mazda and Mitsubishi in US sales; all new Dealership Standard stores require modern service bay and parts infrastructure", 0.88),
            ("labor_shortage",  "Subaru franchise dealers nationally report 31% vacancy in parts counter and service support roles; brand's strong AWD and EV push creates high warranty parts volume that manual delivery cannot sustain", 0.87),
            ("capex",           "Subaru Corporate Affairs fund subsidizes $850M in Dealer Facility Upgrade Program in 2025; Titan-compatible parts workflow is part of the modern dealership standard being promoted by SOA", 0.86),
            ("strategic_hire",  "Subaru of America appoints VP of Dealer Operations Technology; smart parts delivery and reducing technician idle time at franchise stores is the #1 fixed ops priority in Subaru's 2026 dealer development program", 0.89),
            ("news",            "Subaru Crosstrek Hybrid and Solterra EV driving record warranty parts volumes at franchise stores; dealers publicly call for automation solutions to manage growing fixed ops workload with flat staffing", 0.85),
        ],
    },
    {
        "company": {
            "name": "Lucid Motors Retail & Service Centers",
            "website": "https://www.lucidmotors.com",
            "industry": "Automotive Dealerships",
            "sub_industry": "EV Brand — Direct Retail + Service Network (Luxury EV, High-Parts-Complexity Service)",
            "employee_estimate": 8000,
            "location_city": "Newark",
            "location_state": "CA",
            "location_country": "US",
            "source": "seed_v5",
        },
        "signals": [
            ("expansion",       "Lucid Motors expanding service studio network from 30 to 75 US locations by end of 2026; each new service center designed as a brand flagship with luxury customer experience — ADAM lounge service robot is natural fit", 0.90),
            ("labor_shortage",  "Lucid service centers struggle to hire EV-certified technician assistants and parts logistics staff; luxury EV parts complexity (air suspension, battery modules, drive units) makes manual parts runner model financially unsustainable", 0.89),
            ("capex",           "Lucid Motors secures $1B+ in Saudi PIF capital injection for US manufacturing and retail expansion; new service studios in Dallas, Miami, and NYC budgeted with technology-forward customer experience including robotics", 0.88),
            ("strategic_hire",  "Lucid Motors hires VP of Service Operations from Tesla Service; mandate is creating the most efficient and technology-forward luxury EV service experience — Titan automation cited in the VP's public job posting", 0.91),
            ("news",            "Lucid Air Grand Touring wins Motor Trend EV of the Year; growing owner base in Texas, Florida, and California driving demand for service capacity expansion — parts automation critical to scale", 0.86),
        ],
    },


    # =========================================================================
    # OEM INNOVATION & VENTURE CAPITAL GROUPS
    # =========================================================================

    {
        "company": {
            "name": "Toyota Ventures",
            "website": "https://www.toyotaventures.com",
            "industry": "Automotive Innovation & Ventures",
            "sub_industry": "OEM Corporate VC — Robotics, Autonomy, Mobility Technology",
            "employee_estimate": 150,
            "location_city": "Los Altos",
            "location_state": "CA",
            "location_country": "US",
            "source": "seed_v5",
        },
        "signals": [
            ("funding_round",   "Toyota Ventures closes $500M Fund II with explicit thesis on robotics, material handling automation, and sustainable mobility technology; actively sourcing investments in AMR and service robot companies", 0.94),
            ("strategic_hire",  "Toyota Ventures hires Managing Partner from Khosla Ventures with focus on warehouse robotics and manufacturing automation; Richtech's Titan platform aligns with Toyota's internal factory use case at US plants", 0.91),
            ("news",            "Toyota Ventures portfolio company deployment at Toyota Manufacturing Kentucky demonstrates 35% throughput improvement; Toyota Ventures doubling down on robotics investments for Toyota factory and dealership applications", 0.92),
            ("capex",           "Toyota Ventures partners with Toyota Research Institute to co-invest in robot companies that can be deployed directly at Toyota, Lexus, and dealer network facilities — commercialization path accelerates investment thesis", 0.90),
            ("expansion",       "Toyota Ventures opens Singapore and Silicon Valley offices to source global robotics investments; Southeast Asian manufacturing and US automotive segments are primary deployment targets for portfolio companies", 0.88),
        ],
    },
    {
        "company": {
            "name": "GM Ventures",
            "website": "https://www.gmventures.com",
            "industry": "Automotive Innovation & Ventures",
            "sub_industry": "OEM Corporate VC — Robotics, Electrification, Manufacturing Technology",
            "employee_estimate": 80,
            "location_city": "Detroit",
            "location_state": "MI",
            "location_country": "US",
            "source": "seed_v5",
        },
        "signals": [
            ("funding_round",   "GM Ventures closes $300M fund with thesis covering factory automation, EV supply chain robotics, and manufacturing AI; investments are expected to generate deployable technology at GM facilities globally", 0.93),
            ("strategic_hire",  "GM Ventures promotes Principal to Managing Director for Manufacturing Technology; portfolio focus shifting to material handling robots and intra-factory logistics following internal Ultium plant AMR success", 0.90),
            ("news",            "GM Ventures portfolio company TinyMile deploys autonomous delivery robots at GM Technical Center campus; program expanding to production plants — demonstrates GM's intent to deploy portfolio investments internally", 0.91),
            ("capex",           "GM Ventures syndicates $80M robotics deal with DCVC and Toyota Ventures; AMR company targeting automotive factory material handling is confirmed portfolio target aligned with GM's Factory ZERO deployment needs", 0.89),
            ("expansion",       "GM Ventures opens Detroit and San Francisco offices to source robotics, AI, and smart manufacturing investments; automotive factory and dealership automation are the top sector theses for 2026 pipeline", 0.87),
        ],
    },
    {
        "company": {
            "name": "Ford Motor Company Ventures",
            "website": "https://www.ford.com/about/fordventures",
            "industry": "Automotive Innovation & Ventures",
            "sub_industry": "OEM Corporate VC — Smart Manufacturing, EV Technology, Mobility",
            "employee_estimate": 60,
            "location_city": "Dearborn",
            "location_state": "MI",
            "location_country": "US",
            "source": "seed_v5",
        },
        "signals": [
            ("funding_round",   "Ford Motor Company Ventures deploys $200M in smart factory, EV infrastructure, and autonomous logistics portfolio; manufacturing automation companies with Ford plant deployment potential get priority investments", 0.92),
            ("strategic_hire",  "Ford Ventures hires VP of Industrial Technology Investments from GE Ventures; mandate is finding robot companies deployable at BlueOval City, Dearborn Truck, and Ford dealership network", 0.89),
            ("news",            "Ford Ventures-backed autonomous warehouse robot deployed at Ford distribution center in Flat Rock, MI; pilot results drive Ford's recommendation across the dealer network parts operations", 0.91),
            ("capex",           "Ford Ventures co-invests with Ford Pro to accelerate commercial robotics for Ford dealership fixed operations; Titan-class parts delivery automation is a named use case in the 2026 Ford Pro innovation program", 0.90),
            ("expansion",       "Ford Ventures partners with Ford Pro Commercial Vehicles to source robotics investments targeting dealer service networks; AMR companies with fleet management capabilities get first-look meetings with Ford Ventures partners", 0.88),
        ],
    },
    {
        "company": {
            "name": "BMW i Ventures",
            "website": "https://www.bmwiventures.com",
            "industry": "Automotive Innovation & Ventures",
            "sub_industry": "OEM Corporate VC — Mobility, Robotics, Smart Manufacturing, Sustainability",
            "employee_estimate": 80,
            "location_city": "Mountain View",
            "location_state": "CA",
            "location_country": "US",
            "source": "seed_v5",
        },
        "signals": [
            ("funding_round",   "BMW i Ventures closes $300M fund with explicit mandate on production robotics and intra-factory logistics; Spartanburg plant AMR deployment success drives automotive manufacturing as top investment vertical", 0.93),
            ("strategic_hire",  "BMW i Ventures appoints Partner for Industrial Automation from Playground Global; Titan-class service robot companies are priority pipeline given BMW's luxury dealership parts delivery pain point globally", 0.91),
            ("news",            "BMW i Ventures portfolio company NAVYA deploys autonomous shuttle and material delivery at BMW Spartanburg; BMW i Ventures actively adding manufacturing and dealership automation companies to portfolio", 0.90),
            ("capex",           "BMW i Ventures syndicates $55M into AMR and humanoid robot companies targeting luxury OEM plants and dealerships; Richtech's product line — covering dealership, factory, and service use cases — matches the portfolio thesis exactly", 0.92),
            ("expansion",       "BMW i Ventures opens Munich office for European manufacturing robotics investments; US portfolio companies with BMW Spartanburg deployment relationships get fast-track partnership consideration", 0.87),
        ],
    },
    {
        "company": {
            "name": "Hyundai CRADLE",
            "website": "https://www.hyundaicradle.com",
            "industry": "Automotive Innovation & Ventures",
            "sub_industry": "OEM Corporate VC — Robotics, Autonomous Vehicles, Smart Factory (Hyundai + Boston Dynamics owner)",
            "employee_estimate": 120,
            "location_city": "San Francisco",
            "location_state": "CA",
            "location_country": "US",
            "source": "seed_v5",
        },
        "signals": [
            ("funding_round",   "Hyundai CRADLE (Center for Robotic-Augmented Design in Living Experiences) invests in autonomous delivery, logistics robots, and service automation with deployment pipeline to Hyundai dealer network and HMGMA factory floor", 0.95),
            ("strategic_hire",  "Hyundai CRADLE hires Managing Director of Americas from SoftBank Robotics; mandate focuses on AMR and service robot investments that can be deployed at Hyundai-Kia dealer service networks in North America", 0.92),
            ("news",            "Hyundai Motor Group acquires Boston Dynamics; CRADLE accelerates investment in AMR and humanoid robot startups that complement Boston Dynamics portfolio — Richtech occupies adjacent and complementary market position", 0.94),
            ("capex",           "CRADLE commits $500M in robotics and automation investments through 2027; factory robotics and dealership service automation are the two operational deployment vectors for CRADLE portfolio companies", 0.91),
            ("expansion",       "Hyundai CRADLE opens Singapore and Detroit investment offices; Detroit hub sources manufacturing automation investments for HMGMA, Kia, and Genesis factory deployments across North America", 0.89),
        ],
    },
    {
        "company": {
            "name": "Stellantis Ventures",
            "website": "https://www.stellantis.com/en/innovation",
            "industry": "Automotive Innovation & Ventures",
            "sub_industry": "OEM Corporate VC — Electrification, Smart Factory, Dealer Technology",
            "employee_estimate": 60,
            "location_city": "Auburn Hills",
            "location_state": "MI",
            "location_country": "US",
            "source": "seed_v5",
        },
        "signals": [
            ("funding_round",   "Stellantis Ventures launches EUR 300M fund covering smart manufacturing, EV supply chain, and dealer operations technology; Ram, Jeep, and Dodge franchise operations automation is an active investment thesis", 0.90),
            ("strategic_hire",  "Stellantis Ventures hires Partner for Manufacturing & Operations Technology from BASF Ventures; dealership fixed ops automation and factory AMR are named investment priorities in the 2026 deal pipeline", 0.88),
            ("news",            "Stellantis announces DARE Forward 2030 innovation strategy; Stellantis Ventures portfolio companies with automotive factory and dealership deployment potential get priority consideration for internal use", 0.89),
            ("capex",           "Stellantis Ventures co-invests alongside Foxconn in autonomous manufacturing logistics company; validates Stellantis's intent to deploy AMR across Belvidere, Windsor, and Warren Truck plants", 0.87),
            ("expansion",       "Stellantis Ventures opens investment office in Detroit and Silicon Valley; dealer-focused technology companies targeting Ram and Jeep franchise networks are an active sourcing priority", 0.85),
        ],
    },

    # =========================================================================
    # ADDITIONAL TIER 1 / TIER 2 AUTOMOTIVE SUPPLIERS
    # =========================================================================

    {
        "company": {
            "name": "FORVIA (Faurecia + Hella)",
            "website": "https://www.forvia.com",
            "industry": "Automotive Manufacturing",
            "sub_industry": "Tier 1 Supplier — Interiors, Seating, Clean Mobility, Lighting",
            "employee_estimate": 300000,
            "location_city": "Auburn Hills",
            "location_state": "MI",
            "location_country": "US",
            "source": "seed_v5",
        },
        "signals": [
            ("ma_activity",     "Faurecia merges with Hella to form FORVIA, world's 7th largest automotive supplier; integration of 300 global plants requires standardized intra-facility logistics — AMR fleet for parts delivery across all divisions", 0.93),
            ("capex",           "FORVIA invests EUR 2.5B in electrification and smart manufacturing; North American plants in Michigan, Indiana, and Tennessee receiving autonomous parts delivery and WIP movement systems", 0.91),
            ("labor_shortage",  "FORVIA North American facilities face 27% vacancy in material handling and sub-assembly delivery roles; combined Faurecia and Hella North American workforce cannot fill indirect labor roles in current labor market", 0.89),
            ("strategic_hire",  "FORVIA appoints Chief Manufacturing Transformation Officer; first priority is deploying unified AMR standard across all Faurecia seating and Hella electronics assembly plants in North America", 0.90),
            ("expansion",       "FORVIA opens 8 new plants in North America to supply EV-specific seating, lighting, and clean mobility components; all new facilities in Alabama, Tennessee, and Georgia designed with AMR-compatible logistics infrastructure", 0.87),
        ],
    },
    {
        "company": {
            "name": "ZF Group Americas",
            "website": "https://www.zf.com",
            "industry": "Automotive Manufacturing",
            "sub_industry": "Tier 1 Supplier — Driveline, Chassis, ADAS Systems",
            "employee_estimate": 22000,
            "location_city": "Northville",
            "location_state": "MI",
            "location_country": "US",
            "source": "seed_v5",
        },
        "signals": [
            ("capex",           "ZF Group invests EUR 3.5B in electrification and ADAS; North American plants in South Carolina, Michigan, and Kentucky receiving autonomous intra-facility logistics as part of ZF's Factory of the Future program", 0.91),
            ("strategic_hire",  "ZF Americas appoints VP of Smart Manufacturing; deploying AMR fleets for parts delivery, sub-assembly kitting, and dock-to-line logistics across all North American driveline and ADAS assembly plants", 0.89),
            ("labor_shortage",  "ZF North American plants report 24% vacancy in material handling and indirect manufacturing roles; Midwest automotive labor market competition with Amazon, Stellantis, and GM plants drives chronic understaffing", 0.88),
            ("ma_activity",     "ZF acquires WABCO, Lidar company Ibeo, and multiple ADAS companies; integration of acquired manufacturing sites requires standardized logistics infrastructure across the expanded ZF North American footprint", 0.86),
            ("expansion",       "ZF opens new EV drivetrain assembly plant in Tuscaloosa, AL to supply HMGMA and Mercedes Vance; 1.2M sq ft facility designed with AMR-first intra-facility logistics from production launch", 0.87),
        ],
    },
    {
        "company": {
            "name": "Samsung SDI America",
            "website": "https://www.samsungsdi.com",
            "industry": "Automotive Manufacturing",
            "sub_industry": "Tier 1 Supplier — EV Battery Cells & Modules",
            "employee_estimate": 3000,
            "location_city": "Auburn Hills",
            "location_state": "MI",
            "location_country": "US",
            "source": "seed_v5",
        },
        "signals": [
            ("capex",           "Samsung SDI invests $3.1B in Kokomo, Indiana battery gigafactory joint venture with Stellantis; massive 3.5M sq ft facility requires AMR fleet for cell-to-module delivery and intra-building parts logistics", 0.94),
            ("expansion",       "Samsung SDI announces second Indiana gigafactory and evaluates third US site; gigafactory scale makes autonomous intra-facility logistics the only operationally viable parts delivery approach", 0.93),
            ("labor_shortage",  "Samsung SDI Indiana gigafactory competing for indirect manufacturing labor with Stellantis Kokomo, Chrysler Kokomo, and Amazon distribution centers; material handling roles have 50%+ annualized turnover", 0.90),
            ("strategic_hire",  "Samsung SDI America hires VP of Manufacturing Operations from LG Energy Solution; first mandate is deploying AMR fleet for battery cell and module delivery across Indiana production lines", 0.89),
            ("news",            "Samsung SDI global AMR deployment at Cheonan factory achieves zero-touch battery module delivery; Korea program being replicated at Kokomo gigafactory with 400 autonomous delivery robots planned for 2026", 0.92),
        ],
    },
    {
        "company": {
            "name": "LG Energy Solution Michigan",
            "website": "https://www.lgenergysolution.com",
            "industry": "Automotive Manufacturing",
            "sub_industry": "Tier 1 Supplier — EV Battery Cells, Modules & Packs",
            "employee_estimate": 5000,
            "location_city": "Holland",
            "location_state": "MI",
            "location_country": "US",
            "source": "seed_v5",
        },
        "signals": [
            ("capex",           "LG Energy Solution invests $5.5B in US battery manufacturing; joint venture plants with GM (Ultium Cells) in Ohio and Tennessee and Honda (L-H Battery Company) in Ohio all require autonomous intra-facility logistics", 0.95),
            ("expansion",       "LG Energy Solution opens Queen Creek, AZ gigafactory for EV cylindrical cells; all US LGES gigafactories use AMR fleet for cell and module delivery — 500+ robots per facility in standard specification", 0.94),
            ("labor_shortage",  "LGES Michigan and Ohio plants competing for material handling labor with Ford, GM, and Amazon; indirect labor vacancy above 28% at Holland and Spring Hill facilities", 0.90),
            ("strategic_hire",  "LG Energy Solution Americas appoints Chief Operating Officer; standardizing autonomous parts delivery across all US gigafactories is the top operational efficiency investment in the 2026 capital plan", 0.91),
            ("news",            "LGES Ultium Cells joint venture in Warren, OH deploys 300 AMRs for battery module delivery to GM assembly line; LGES reports 38% improvement in cell-to-module cycle time vs manual delivery baseline", 0.92),
        ],
    },
    {
        "company": {
            "name": "Autoliv North America",
            "website": "https://www.autoliv.com",
            "industry": "Automotive Manufacturing",
            "sub_industry": "Tier 1 Supplier — Airbags, Seatbelts, Safety Electronics",
            "employee_estimate": 15000,
            "location_city": "Ogden",
            "location_state": "UT",
            "location_country": "US",
            "source": "seed_v5",
        },
        "signals": [
            ("capex",           "Autoliv invests $800M in US airbag and seatbelt manufacturing; Ogden, UT and Brigham City, UT plants receiving autonomous intra-facility parts delivery as part of Autoliv Production System lean manufacturing upgrade", 0.89),
            ("labor_shortage",  "Autoliv Utah plants face 26% vacancy in material handling roles; intricate airbag component assembly requires precise part delivery timing — manual delivery creates production bottlenecks on every shift", 0.88),
            ("strategic_hire",  "Autoliv North America appoints Director of Manufacturing Automation; AMR-based parts replenishment for airbag and seatbelt assembly lines is the priority investment to eliminate assembly line starvation events", 0.87),
            ("expansion",       "Autoliv opens new safety electronics plant in Kentucky to supply Ford, GM, and Stellantis EV programs; facility specified with dock-to-line AMR parts delivery as core production logistics infrastructure", 0.85),
            ("news",            "Autoliv global AMR deployment at Vargarda Sweden achieves 99.4% on-time line-side delivery; Americas division replicating Sweden model at all North American airbag assembly facilities in 2026", 0.88),
        ],
    },

    # =========================================================================
    # AEROSPACE & DEFENSE
    # =========================================================================

    {
        "company": {
            "name": "Boeing Commercial Airplanes",
            "website": "https://www.boeing.com",
            "industry": "Aerospace & Defense",
            "sub_industry": "Commercial Aircraft Manufacturing — Intra-Factory Logistics & Maintenance",
            "employee_estimate": 150000,
            "location_city": "Everett",
            "location_state": "WA",
            "location_country": "US",
            "source": "seed_v5",
        },
        "signals": [
            ("capex",           "Boeing invests $4.5B in factory modernization at Everett and Renton; Renton 737 MAX line and Everett 787 campus deploying autonomous material handling for sub-assembly delivery, tooling transport, and parts replenishment to production lines", 0.93),
            ("labor_shortage",  "Boeing manufacturing workforce 25% below target in material handler, stock clerk, and production support roles; Puget Sound labor market competition with Amazon, Microsoft, and defense contractors drives 40%+ vacancy in indirect roles", 0.91),
            ("strategic_hire",  "Boeing appoints VP of Manufacturing Technology & Automation; intra-factory autonomous delivery for parts, tooling, and sub-assemblies across all commercial production lines is the top manufacturing efficiency investment", 0.90),
            ("expansion",       "Boeing opens new 787 composite parts campus in Utah; autonomous intra-facility logistics specified from ground up to move wing panels, fuselage sections, and sub-assembly components without manual fork-lift or tugger operators", 0.89),
            ("news",            "Boeing Manufacturing deploys autonomous guided vehicles at Everett factory for fuselage section transport; program expanding to Renton 737 plant with AMR fleet for tooling and parts delivery to all production positions", 0.91),
        ],
    },
    {
        "company": {
            "name": "Lockheed Martin",
            "website": "https://www.lockheedmartin.com",
            "industry": "Aerospace & Defense",
            "sub_industry": "Defense & Space Manufacturing — Factory AMR + Maintenance Logistics",
            "employee_estimate": 116000,
            "location_city": "Bethesda",
            "location_state": "MD",
            "location_country": "US",
            "source": "seed_v5",
        },
        "signals": [
            ("capex",           "Lockheed Martin invests $2.1B in Fort Worth F-35 production modernization and Sikorsky helicopter factory upgrades; autonomous parts delivery and tooling replenishment to production positions is a key element of the Next Generation Manufacturing initiative", 0.91),
            ("strategic_hire",  "Lockheed Martin promotes Chief Manufacturing Officer with mandate to reduce production cycle time through factory automation; AMR-based parts delivery to F-35, F-16, and Sikorsky assembly positions is the top manufacturing automation priority", 0.89),
            ("labor_shortage",  "Lockheed Fort Worth and Marietta plants 22% understaffed in production support and material handling roles; defense labor market shortages are worsening as DoD budget grows and more contractors compete for same workforce", 0.88),
            ("news",            "Lockheed Martin MFC deploys autonomous robot for missile sub-component delivery at Camden, AR facility; program expanding to Missiles and Fire Control plants across Texas and Florida in 2026", 0.90),
            ("expansion",       "Lockheed Martin opens new hypersonic weapons production facility in Troy, AL; classified production environment specified with autonomous intra-facility logistics to reduce human movement in sensitive areas", 0.87),
        ],
    },
    {
        "company": {
            "name": "RTX (Raytheon Technologies)",
            "website": "https://www.rtx.com",
            "industry": "Aerospace & Defense",
            "sub_industry": "Defense & Propulsion Manufacturing — Pratt & Whitney + Collins Aerospace",
            "employee_estimate": 185000,
            "location_city": "Farmington",
            "location_state": "CT",
            "location_country": "US",
            "source": "seed_v5",
        },
        "signals": [
            ("capex",           "RTX invests $6.2B in Pratt & Whitney engine production capacity; Middletown CT and Columbus GA P&W plants expanding to meet F135 and GTF demand — autonomous intra-facility parts delivery for engine module assembly is a critical bottleneck solution", 0.92),
            ("labor_shortage",  "Pratt & Whitney Connecticut and Georgia plants report 28% vacancy in production support and material handling roles; aerospace precision manufacturing labor market is critically short nationally", 0.90),
            ("strategic_hire",  "RTX appoints Head of Digital Manufacturing for Pratt & Whitney and Collins Aerospace divisions; autonomous parts delivery and digital twin-enabled logistics are the top capital investments in the RTX Manufacturing Excellence program", 0.89),
            ("expansion",       "Collins Aerospace opens advanced actuation and avionics assembly plants in North Carolina and Texas; both facilities utilize AMR-based parts delivery as core production logistics infrastructure from day one", 0.88),
            ("news",            "RTX Manufacturing Excellence program deploys AMR fleet at Collins Aerospace Windsor Locks, CT; cycle time for parts delivery to assembly positions reduced 42%; RTX mandating program expansion across all 12 major facilities", 0.91),
        ],
    },
    {
        "company": {
            "name": "Northrop Grumman",
            "website": "https://www.northropgrumman.com",
            "industry": "Aerospace & Defense",
            "sub_industry": "Defense Manufacturing — B-21, Missiles, Space Systems",
            "employee_estimate": 101000,
            "location_city": "Falls Church",
            "location_state": "VA",
            "location_country": "US",
            "source": "seed_v5",
        },
        "signals": [
            ("capex",           "Northrop Grumman invests $1.5B in B-21 Raider production at Palmdale, CA; classified factory design incorporates autonomous intra-facility logistics to minimize human movement in secure production areas and deliver components to assembly positions", 0.90),
            ("labor_shortage",  "Northrop Palmdale, Redondo Beach, and Roy, UT facilities report severe shortage of production support and material handling staff; defense manufacturing labor market competing with commercial aerospace drives vacancy above 30%", 0.89),
            ("strategic_hire",  "Northrop Grumman appoints VP of Advanced Manufacturing Technology; AMR-based parts and tooling delivery for B-21, missile, and space systems production is an active procurement program for 2026", 0.88),
            ("expansion",       "Northrop expands Rocket Center, WV solid motor production for hypersonic and interceptor programs; new production halls designed with autonomous material handling for propellant handling and sub-assembly delivery", 0.87),
            ("news",            "Northrop Grumman Mission Systems deploys autonomous delivery robot for classified circuit board and electronic sub-assembly delivery at Rolling Meadows, IL facility; expanding program to all Mission Systems campuses", 0.88),
        ],
    },
    {
        "company": {
            "name": "Airbus Americas",
            "website": "https://www.airbus.com",
            "industry": "Aerospace & Defense",
            "sub_industry": "Commercial Aircraft Manufacturing — Final Assembly + MRO",
            "employee_estimate": 13000,
            "location_city": "Mobile",
            "location_state": "AL",
            "location_country": "US",
            "source": "seed_v5",
        },
        "signals": [
            ("capex",           "Airbus invests $1.2B to expand Mobile, AL A320 and A220 final assembly campus; second A320 family line adds 3M sq ft requiring autonomous intra-facility logistics for fuselage sections, wing components, and aircraft parts delivery", 0.91),
            ("labor_shortage",  "Airbus Mobile facing 29% vacancy in production support and material handling at Alabama campus; competing with neighboring Mercedes-Benz MBUSI and Hyundai HMGMA for manufacturing labor", 0.90),
            ("strategic_hire",  "Airbus Americas appoints Head of Mobile Production Technology; deploying intra-facility AMR fleet for component delivery between receiving, pre-assembly, and final assembly positions across the expanded campus", 0.88),
            ("expansion",       "Airbus breaks ground on A220 delivery hangar campus expansion in Mobile; logistics infrastructure for the expanded campus specifies autonomous delivery for aircraft parts, tooling, and consumables throughout", 0.87),
            ("news",            "Airbus Hamburg factory deploys 200 autonomous tugger robots for component delivery; Mobile program manager confirms Alabama facility adopting identical AMR deployment in 2026 campus expansion", 0.89),
        ],
    },
    {
        "company": {
            "name": "SpaceX",
            "website": "https://www.spacex.com",
            "industry": "Aerospace & Defense",
            "sub_industry": "Launch Vehicle & Spacecraft Manufacturing — Starship + Starlink Production",
            "employee_estimate": 13000,
            "location_city": "Hawthorne",
            "location_state": "CA",
            "location_country": "US",
            "source": "seed_v5",
        },
        "signals": [
            ("capex",           "SpaceX investing billions in Starbase Boca Chica Starship production scale-up; Hawthorne Falcon 9 factory and Boca Chica Starship campus both deploying autonomous intra-facility logistics for Raptor engine components and spacecraft parts delivery", 0.93),
            ("labor_shortage",  "SpaceX Hawthorne, Boca Chica, and Cape Canaveral facilities face acute shortage of production support and inventory management staff; extreme Starship production ramp rate creates demand for autonomous material delivery", 0.91),
            ("strategic_hire",  "SpaceX hires VP of Manufacturing Operations from Tesla Gigafactory; mandate is applying Tesla-style autonomous factory logistics to Starship and Falcon production — AMR fleet deployment is named Day 1 initiative", 0.92),
            ("expansion",       "SpaceX building Starlink satellite production mega-factory in Bastrop, TX; facility producing 1,000 satellites per month requires automated intra-facility logistics for satellite components, antennas, and electronics delivery", 0.94),
            ("news",            "SpaceX deploys autonomous tugger robots at Hawthorne factory for Falcon 9 first stage and fairing component delivery; program expanding to Starbase Boca Chica for Starship Super Heavy production logistics", 0.90),
        ],
    },
    {
        "company": {
            "name": "General Dynamics Land Systems",
            "website": "https://www.gdls.com",
            "industry": "Aerospace & Defense",
            "sub_industry": "Defense Manufacturing — Armored Vehicles, Combat Systems",
            "employee_estimate": 12000,
            "location_city": "Sterling Heights",
            "location_state": "MI",
            "location_country": "US",
            "source": "seed_v5",
        },
        "signals": [
            ("capex",           "GDLS invests $600M in Abrams tank and Stryker production modernization at Sterling Heights factory; Army's multi-year vehicle procurement drives factory expansion requiring autonomous intra-facility logistics for armor components and sub-assembly delivery", 0.89),
            ("labor_shortage",  "GDLS Sterling Heights facility 25% understaffed in material handling and production support roles; metro Detroit automotive OEM competition makes indirect manufacturing labor recruitment exceptionally difficult", 0.88),
            ("strategic_hire",  "GDLS hires Director of Lean Manufacturing & Automation; deploying AMR fleet for hull, turret, and drivetrain component delivery across Abrams and Stryker production lines is the top manufacturing investment for 2026", 0.87),
            ("expansion",       "GDLS opens new combat vehicle integration facility in Woodbridge, VA; defense-sensitive facility designed with autonomous intra-plant delivery to minimize human movement in classified vehicle integration areas", 0.86),
            ("news",            "GDLS Toledo tank plant deploys autonomous material handling cart for Abrams hull component delivery; unit reduces parts runner headcount by 60% — program expanding to Sterling Heights assembly facility", 0.88),
        ],
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
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
                source=cd.get("source", "seed_v5"),
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
                        source_url="seed_v5",
                    )
                    db.add(sig)
                    db.commit()
                added_s += 1

    return added_c, added_s


def score_new(db):
    """Score only the seed_v5 companies (avoids re-scoring all 180+ existing)."""
    from sqlalchemy import exists as sa_exists
    companies = db.query(Company).filter(Company.source == 'seed_v5').all()
    scored = 0
    for company in companies:
        signals = db.query(Signal).filter(Signal.company_id == company.id).all()
        if not signals:
            continue
        texts = [s.signal_text for s in signals]
        result = analyze_signals(texts, company_name=company.name, industry=company.industry)
        score_data = result.to_score_dict()
        existing = db.query(Score).filter(Score.company_id == company.id).first()
        if existing:
            for k, v in score_data.items():
                setattr(existing, k, v)
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
        print(f"\n=== seed_leads_v5 DRY RUN ===")
        print(f"  Companies : {total_co}")
        print(f"  Signals   : {total_sig}")
        print(f"\n  By industry:")
        for k, v in sorted(industries.items(), key=lambda x: -x[1]):
            print(f"    {k:<45} {v}")
        print(f"\n  By country:")
        for k, v in sorted(countries.items(), key=lambda x: -x[1]):
            print(f"    {k:<10} {v}")
        print(f"\nRun with --commit to write to database.\n")
        sys.exit(0)

    print("\n=== seed_leads_v5  COMMITTING TO DATABASE ===")
    db = SessionLocal()
    try:
        added_c, added_s = seed_database(db, dry_run=False)
        print(f"  Inserted  {added_c} new companies, {added_s} new signals")

        print("\n  Scoring new seed_v5 companies only...")
        scored = score_new(db)
        print(f"  Scored    {scored} companies")

        total_c = db.query(Company).count()
        total_s = db.query(Signal).count()
        print(f"\n  DB totals: {total_c} companies | {total_s} signals")
        print("  Done.\n")
    finally:
        db.close()
