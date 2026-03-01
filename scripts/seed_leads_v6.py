"""
seed_leads_v6.py — Individual OEM Brand Dealerships

One flagship dealership per brand covering every major OEM sold in the US:
Toyota, Honda, BMW, Mercedes-Benz, Ford, Chevrolet, Tesla, Hyundai, Kia,
Nissan, Volkswagen, Audi, Porsche, Subaru, Mazda, Lexus, Infiniti, Acura,
Cadillac, Lincoln, Genesis, Volvo, Jeep/RAM/Dodge, GMC/Buick, Rivian.

These are single-rooftop franchise stores — the direct Titan / DUST-E
deployment target (parts-to-bay, service drive, lounge).

Usage:
  python scripts/seed_leads_v6.py           # dry-run
  python scripts/seed_leads_v6.py --commit  # write to DB
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

    # ─────────────────────────────────────────────────────────────────────────
    # TOYOTA
    # ─────────────────────────────────────────────────────────────────────────
    {
        "company": {
            "name": "Longo Toyota",
            "website": "https://www.longotoyota.com",
            "industry": "Automotive Dealerships",
            "sub_industry": "Toyota Franchise — High-Volume Single-Rooftop (El Monte, CA — #1 volume Toyota dealer in the US)",
            "employee_estimate": 600,
            "location_city": "El Monte",
            "location_state": "CA",
            "location_country": "US",
            "source": "seed_v6",
        },
        "signals": [
            ("labor_shortage",  "Longo Toyota — the highest-volume Toyota dealer in the US — processes 6,000+ service appointments per month; parts runners and service drive support staff turn over at 75%+ annually in the San Gabriel Valley labor market", 0.95),
            ("capex",           "Longo Toyota invests $22M in service department expansion adding 35 bays; new service wing is designed with autonomous parts delivery staging areas to eliminate the manual runner bottleneck during peak service hours", 0.92),
            ("job_posting",     "Longo Toyota posting 40+ parts counter associate, porter, and service writer aide roles year-round; at $14–16/hr these roles see near-constant turnover — Titan replaces the function, not just the person", 0.93),
            ("strategic_hire",  "Longo Toyota promotes Fixed Operations Director and gives her an automation mandate; first project is deploying Titan for parts-to-bay delivery across all 80 service bays to cut average parts retrieval time from 12 minutes to under 2", 0.91),
            ("expansion",       "Longo Toyota opens dedicated Toyota Certified Used Vehicle and Camry Hybrid service lanes; expanded fixed ops footprint makes a single-store Titan fleet ROI-positive within 14 months at current labor rates", 0.89),
        ],
    },

    # ─────────────────────────────────────────────────────────────────────────
    # HONDA
    # ─────────────────────────────────────────────────────────────────────────
    {
        "company": {
            "name": "Norm Reeves Honda Superstore",
            "website": "https://www.normreeveshonda.com",
            "industry": "Automotive Dealerships",
            "sub_industry": "Honda Franchise — High-Volume Single-Rooftop (Cerritos, CA — one of the largest Honda stores in the US)",
            "employee_estimate": 420,
            "location_city": "Cerritos",
            "location_state": "CA",
            "location_country": "US",
            "source": "seed_v6",
        },
        "signals": [
            ("labor_shortage",  "Norm Reeves Honda runs 70+ service bays and processes 5,500 ROs per month; parts runner vacancy runs at 60%+ because LA-area Amazon fulfillment centers offer $21/hr vs. the dealer's $15/hr for identical work", 0.94),
            ("job_posting",     "Norm Reeves posting 25+ parts picker, porter, and service drive associate roles continuously; every open req represents a Titan use case — picking, delivering, and returning parts without a human runner on the floor", 0.92),
            ("capex",           "Norm Reeves Honda invests $8M in service drive canopy expansion and digital check-in stations; DUST-E service drive robot is a natural add-on to the contactless check-in workflow being installed", 0.89),
            ("strategic_hire",  "Norm Reeves Honda appoints a new Service Director from AutoNation; her stated 90-day mandate is cutting customer write-up-to-technician assignment time — Titan for parts and DUST-E for the drive are the two pilots", 0.90),
            ("news",            "Norm Reeves Honda ranked #3 Honda CSI store in the US for 2025; fixed ops efficiency and customer wait time reduction are the stated drivers of the next CSI improvement push — automation is the lever", 0.87),
        ],
    },

    # ─────────────────────────────────────────────────────────────────────────
    # BMW
    # ─────────────────────────────────────────────────────────────────────────
    {
        "company": {
            "name": "BMW of Sterling",
            "website": "https://www.bmwofsterling.com",
            "industry": "Automotive Dealerships",
            "sub_industry": "BMW Franchise — High-Volume Luxury Single-Rooftop (Sterling, VA — consistently top-10 BMW dealer in the US)",
            "employee_estimate": 280,
            "location_city": "Sterling",
            "location_state": "VA",
            "location_country": "US",
            "source": "seed_v6",
        },
        "signals": [
            ("labor_shortage",  "BMW of Sterling runs 55 service bays and stocks 14,000+ active parts SKUs for M, EV, and standard BMW lines; finding parts counter specialists who know BMW's complex catalog is nearly impossible in Northern Virginia's tech-heavy labor market", 0.94),
            ("capex",           "BMW of Sterling completes a $14M BMW Retail Next showroom and service center renovation; the redesigned service lounge and drive are specified to accommodate DUST-E and ADAM service companion robots as part of the Premium Experience standard", 0.91),
            ("strategic_hire",  "BMW of Sterling promotes a Fixed Operations Director with a directive from ownership to cut technician idle time; Titan deployment across parts will reduce average parts retrieval from 14 min to under 2 min at current bay throughput", 0.93),
            ("job_posting",     "BMW of Sterling continuously posting 15+ parts counter, porter, and BMW Genius roles; luxury brand parts complexity makes these among the hardest single-store fixed ops roles to fill and retain in any market", 0.90),
            ("news",            "BMW of Sterling wins BMW Center of Excellence Award for the third year; General Manager publicly cites service department automation investment as the next phase of the excellence program in the 2026 operational plan", 0.89),
        ],
    },

    # ─────────────────────────────────────────────────────────────────────────
    # MERCEDES-BENZ
    # ─────────────────────────────────────────────────────────────────────────
    {
        "company": {
            "name": "Mercedes-Benz of Atlanta",
            "website": "https://www.mbofatlanta.com",
            "industry": "Automotive Dealerships",
            "sub_industry": "Mercedes-Benz Franchise — High-Volume Luxury Single-Rooftop (Atlanta, GA)",
            "employee_estimate": 310,
            "location_city": "Atlanta",
            "location_state": "GA",
            "location_country": "US",
            "source": "seed_v6",
        },
        "signals": [
            ("labor_shortage",  "Mercedes-Benz of Atlanta's 60-bay service department can't maintain fully staffed parts delivery; Atlanta's warehouse and logistics sector pays $19–22/hr and draws directly from the same labor pool the dealer relies on for parts runners", 0.93),
            ("capex",           "Mercedes-Benz of Atlanta completes a $16M Mercedes-Benz Retail Experience renovation; redesigned customer lounge and service drive are blueprint-ready for ADAM beverage service robot and DUST-E check-in automation", 0.90),
            ("strategic_hire",  "Mercedes-Benz of Atlanta hires a new Fixed Ops Director from Hendrick; her first initiative is deploying parts automation to reduce technician wait time — the store's #1 CSI detractor per internal surveys", 0.91),
            ("expansion",       "Mercedes-Benz of Atlanta adds an EQ electric vehicle service lane with 12 dedicated EV bays; EQ parts (high-voltage battery modules, e-axle units) require precision parts delivery that the store's current manual system cannot reliably support", 0.88),
            ("job_posting",     "Mercedes-Benz of Atlanta posting 18+ parts specialist, porter, and client advisor support roles; $17/hr parts counter roles see 80%+ annual turnover — Titan eliminates the most turnover-prone function in fixed ops", 0.89),
        ],
    },

    # ─────────────────────────────────────────────────────────────────────────
    # FORD
    # ─────────────────────────────────────────────────────────────────────────
    {
        "company": {
            "name": "AutoNation Ford Margate",
            "website": "https://www.autonationfordmargate.com",
            "industry": "Automotive Dealerships",
            "sub_industry": "Ford Franchise — High-Volume Single-Rooftop (Margate, FL — one of the highest-volume Ford stores in the Southeast)",
            "employee_estimate": 260,
            "location_city": "Margate",
            "location_state": "FL",
            "location_country": "US",
            "source": "seed_v6",
        },
        "signals": [
            ("labor_shortage",  "AutoNation Ford Margate runs 50+ service bays handling F-150 Lightning EV, Pro Power, and commercial Ford fleet service; South Florida hospitality labor market pays $20+/hr for equivalent physical roles — parts runner vacancy runs at 55%", 0.92),
            ("capex",           "AutoNation Ford Margate receives $9M Ford Blue Advantage and EV service upgrade; new F-150 Lightning and Mustang Mach-E EV parts receiving area is being designed with autonomous delivery integration from the outset", 0.89),
            ("job_posting",     "AutoNation Ford Margate posting 20+ parts counter, lot attendant, and quick lane tech roles quarterly; Ford F-series parts volume — highest of any brand nationwide — makes the case for Titan clearest at high-volume Ford stores", 0.91),
            ("strategic_hire",  "AutoNation District Manager assigns new Store Director to Margate; fixed ops automation is a named KPI in the 2026 store performance plan alongside CSI and service absorption rate", 0.88),
            ("news",            "AutoNation Ford Margate reports record F-150 Lightning EV service volume in Q4 2025; service manager publicly requests parts logistics upgrade to handle rising EV parts complexity alongside traditional ICE volume", 0.87),
        ],
    },

    # ─────────────────────────────────────────────────────────────────────────
    # CHEVROLET
    # ─────────────────────────────────────────────────────────────────────────
    {
        "company": {
            "name": "Crest Chevrolet",
            "website": "https://www.crestchevrolet.com",
            "industry": "Automotive Dealerships",
            "sub_industry": "Chevrolet Franchise — High-Volume Single-Rooftop (Frisco, TX — DFW market flagship)",
            "employee_estimate": 220,
            "location_city": "Frisco",
            "location_state": "TX",
            "location_country": "US",
            "source": "seed_v6",
        },
        "signals": [
            ("labor_shortage",  "Crest Chevrolet runs 45 service bays servicing Silverado EV, Blazer EV, and traditional Chevy lines; Frisco's tech corridor pays $20–25/hr for warehouse associates — the store's parts runner roles at $15.50/hr are perpetually understaffed", 0.92),
            ("job_posting",     "Crest Chevrolet posting 15+ parts counter, porter, and lube tech roles year-round; Silverado and Equinox EV warranty parts volume growing 50% YoY — manual delivery cannot keep pace without adding headcount the store can't hire", 0.91),
            ("capex",           "Crest Chevrolet invests $7M in EV service bay expansion for Silverado EV and Blazer EV; EV-specific parts (battery modules, charging hardware) require precise, label-confirmed delivery that Titan provides vs. human runner risk of mispicking", 0.89),
            ("strategic_hire",  "Crest Chevrolet promotes Service Director with explicit ROI mandate; Titan deployment across Silverado parts pulls is the 2026 pilot — GM parts catalog complexity across EV and ICE lines makes automation ROI immediate", 0.88),
            ("news",            "Crest Chevrolet recognized as DFW Chevy Dealer of the Year; owner publicly commits to being first in the region to deploy autonomous parts delivery and win back the #1 CSI ranking lost due to service speed complaints", 0.87),
        ],
    },

    # ─────────────────────────────────────────────────────────────────────────
    # GMC / BUICK
    # ─────────────────────────────────────────────────────────────────────────
    {
        "company": {
            "name": "Findlay Buick GMC",
            "website": "https://www.findlaybgmc.com",
            "industry": "Automotive Dealerships",
            "sub_industry": "GMC / Buick Franchise — Single-Rooftop (Henderson, NV — dual-brand store)",
            "employee_estimate": 180,
            "location_city": "Henderson",
            "location_state": "NV",
            "location_country": "US",
            "source": "seed_v6",
        },
        "signals": [
            ("labor_shortage",  "Findlay Buick GMC Henderson operates 35 service bays with a Sierra and Enclave parts department running critical understaffing; Las Vegas metro hospitality industry pays $21+/hr — parts counter and runner roles at $16 can't compete", 0.93),
            ("job_posting",     "Findlay Buick GMC posting 12+ parts associate, porter, and quick lane technician roles; GMC truck and Enclave SUV parts velocity during peak season makes manual delivery the biggest throughput constraint in the service department", 0.90),
            ("capex",           "Findlay Buick GMC invests $4M in service drive canopy expansion and GM Destination Era showroom upgrade; DUST-E service drive robot aligns with the Destination Era brand standard for premium digital-first guest experience", 0.87),
            ("strategic_hire",  "Findlay Group appoints a Group Fixed Operations Manager overseeing all Nevada stores including Buick GMC; Titan pilot at Buick GMC Henderson is the first store in the chain — success rolls out to Toyota, Honda, and Cadillac locations", 0.92),
            ("news",            "Findlay Buick GMC named Nevada's top-volume Buick and GMC dealer for 2025; dealer principal publicly commits to deploying fixed ops automation across all Findlay stores by end of 2026 following the Henderson GMC pilot", 0.89),
        ],
    },

    # ─────────────────────────────────────────────────────────────────────────
    # TESLA
    # ─────────────────────────────────────────────────────────────────────────
    {
        "company": {
            "name": "Tesla Service Center Las Vegas",
            "website": "https://www.tesla.com/en_US/service",
            "industry": "Automotive Dealerships",
            "sub_industry": "Tesla Direct Retail + Service — High-Volume Urban Service Center (Las Vegas, NV)",
            "employee_estimate": 180,
            "location_city": "Las Vegas",
            "location_state": "NV",
            "location_country": "US",
            "source": "seed_v6",
        },
        "signals": [
            ("labor_shortage",  "Tesla Service Las Vegas handles 2,500+ mobile and in-shop ROs per month across Model 3, Y, S, X, and Cybertruck; parts tech and staging associate roles see 65% annualized turnover at $18/hr in the Vegas labor market", 0.93),
            ("expansion",       "Tesla expands Las Vegas service footprint from 28 to 50 service bays by Q2 2026; expanded campus requires automated intra-facility parts delivery from receiving dock to 50 bays — current tote-cart system is unsustainable at that scale", 0.92),
            ("capex",           "Tesla Regional Service invests $12M in Las Vegas campus expansion; building layout is AMR-compatible with wide service corridors, autonomous receiving dock, and centralized parts tower — Titan deployment is in the facility spec", 0.91),
            ("strategic_hire",  "Tesla appoints Regional Service Manager for Southwest with a mandate to reduce parts pull time; Titan deployment at Las Vegas flagship is proposed as the model for all high-volume urban Tesla service centers in the region", 0.90),
            ("job_posting",     "Tesla Service Las Vegas posting 20+ parts associate, service advisor aide, and lot coordinator roles; Cybertruck and Model Y high-voltage parts complexity makes manual routing risky — automation eliminates mispick liability", 0.89),
        ],
    },

    # ─────────────────────────────────────────────────────────────────────────
    # HYUNDAI
    # ─────────────────────────────────────────────────────────────────────────
    {
        "company": {
            "name": "Hyundai of New Port Richey",
            "website": "https://www.hyundaiofnewportrichey.com",
            "industry": "Automotive Dealerships",
            "sub_industry": "Hyundai Franchise — High-Volume Single-Rooftop (New Port Richey, FL — consistently top-5 Hyundai volume dealer)",
            "employee_estimate": 200,
            "location_city": "New Port Richey",
            "location_state": "FL",
            "location_country": "US",
            "source": "seed_v6",
        },
        "signals": [
            ("labor_shortage",  "Hyundai of New Port Richey runs 40 service bays with record EV warranty volume from IONIQ 5 and 6; Tampa-Clearwater labor market drives $19+/hr for comparable physical roles — parts runner vacancy above 50%", 0.92),
            ("expansion",       "Hyundai of New Port Richey adds an IONIQ EV-only service lane with 10 dedicated bays; IONIQ EV parts (800V battery packs, e-GMP sub-assemblies) require certified handling and accurate delivery that Titan provides", 0.90),
            ("job_posting",     "Hyundai of New Port Richey posting 14+ parts tech, porter, and service adviser support roles; Hyundai IONIQ EV warranty parts volume growing 3x year-over-year at this store — Titan ROI is clearest at high EV-volume franchise stores", 0.91),
            ("capex",           "Hyundai of New Port Richey invests $6M in facility expansion and IONIQ EV charging infrastructure; store is designated a Hyundai EV Certified Service Center — automation of EV parts delivery is part of the certification roadmap", 0.88),
            ("strategic_hire",  "Hyundai of New Port Richey promotes Fixed Ops Director with mandate to lead Hyundai EV service excellence across Florida; Titan deployment at NPR is the pilot for Hyundai's Florida network EV service automation program", 0.89),
        ],
    },

    # ─────────────────────────────────────────────────────────────────────────
    # KIA
    # ─────────────────────────────────────────────────────────────────────────
    {
        "company": {
            "name": "Kia of Henderson",
            "website": "https://www.kiaofhenderson.com",
            "industry": "Automotive Dealerships",
            "sub_industry": "Kia Franchise — Single-Rooftop (Henderson, NV — high-volume Southern Nevada Kia store)",
            "employee_estimate": 160,
            "location_city": "Henderson",
            "location_state": "NV",
            "location_country": "US",
            "source": "seed_v6",
        },
        "signals": [
            ("labor_shortage",  "Kia of Henderson runs 30 service bays at near-100% capacity; EV6 and EV9 parts volume surging with Southern Nevada's rapid EV adoption while parts runner vacancy exceeds 45% vs. competing Las Vegas hospitality wages", 0.91),
            ("job_posting",     "Kia of Henderson posting 10+ parts picker, porter, and quick lube associate roles; EV6 and Sportage PHEV warranty repeat visits create high parts pull frequency — Titan eliminates the bottleneck that currently limits the store to 28 billable ROs per day", 0.90),
            ("capex",           "Kia of Henderson invests $4M in EV service lane expansion for EV6 and EV9; newly designed service wing is AMR-accessible with 8-foot-wide service corridors — Titan deployment included in the facility plan", 0.87),
            ("strategic_hire",  "Kia of Henderson promotes Service Manager to Fixed Ops Director; Titan deployment is the stated first project — owner cited Vegas labor market making human runner model economically indefensible at current parts volume", 0.89),
            ("news",            "Kia of Henderson wins Southern Nevada Kia Dealer Excellence Award; service manager publicly notes that EV service volume has made traditional parts runner model obsolete and automation is the 2026 solution", 0.86),
        ],
    },

    # ─────────────────────────────────────────────────────────────────────────
    # NISSAN
    # ─────────────────────────────────────────────────────────────────────────
    {
        "company": {
            "name": "Nissan of Las Vegas",
            "website": "https://www.nissanof.com",
            "industry": "Automotive Dealerships",
            "sub_industry": "Nissan Franchise — Single-Rooftop (Las Vegas, NV — high-volume Nevada market)",
            "employee_estimate": 190,
            "location_city": "Las Vegas",
            "location_state": "NV",
            "location_country": "US",
            "source": "seed_v6",
        },
        "signals": [
            ("labor_shortage",  "Nissan of Las Vegas parts department is critically understaffed with Ariya EV and Frontier warranty volume surging; Las Vegas pays $20–24/hr for warehouse and delivery roles — parts runner at $15.75/hr has 90%+ annualized turnover", 0.92),
            ("job_posting",     "Nissan of Las Vegas posting 12+ parts counter associate, porter, and service coordinator roles; Ariya EV ramp in Southern Nevada creating first-ever record warranty parts pull volume at this location — manual delivery is the throughput limit", 0.90),
            ("capex",           "Nissan of Las Vegas invests $5M in Nissan Next dealership renovation; service drive redesign and bay expansion are in progress — DUST-E check-in and Titan parts delivery are both in the 2026 technology budget", 0.88),
            ("strategic_hire",  "Nissan of Las Vegas appoints a new General Manager; first operational mandate is reducing customer wait time in service — Titan deployment across parts and DUST-E on the service drive are the two automation pilots in the 90-day plan", 0.89),
            ("news",            "Nissan of Las Vegas reports 40% growth in Ariya and Frontier service volume in Q4 2025; service director signals that fixed ops hiring capacity has been exhausted — automation is the only available throughput lever", 0.87),
        ],
    },

    # ─────────────────────────────────────────────────────────────────────────
    # VOLKSWAGEN
    # ─────────────────────────────────────────────────────────────────────────
    {
        "company": {
            "name": "Hendrick Volkswagen Frisco",
            "website": "https://www.hendrickvwfrisco.com",
            "industry": "Automotive Dealerships",
            "sub_industry": "Volkswagen Franchise — Single-Rooftop (Frisco, TX — DFW market flagship)",
            "employee_estimate": 170,
            "location_city": "Frisco",
            "location_state": "TX",
            "location_country": "US",
            "source": "seed_v6",
        },
        "signals": [
            ("labor_shortage",  "Hendrick VW Frisco runs 32 service bays with ID.4 and ID.Buzz EV warranty volume doubling; DFW tech corridor competes directly for the same physical labor profiles at $19–23/hr vs. this store's parts runner rate of $16", 0.91),
            ("job_posting",     "Hendrick VW Frisco posting 10+ parts counter, porter, and quick lane associate roles; ID.4 EV parts complexity (modular battery, integrated charging) makes Titan's accurate, label-confirmed parts delivery the critical upgrade vs. manual picker error", 0.89),
            ("capex",           "Hendrick VW Frisco invests $5.5M in VW Electric Ready service center upgrade; ID.Buzz and ID.4 dedicated lane is VW-certified for EV service — parts logistics modernization is part of the Electric Ready certification standard", 0.87),
            ("strategic_hire",  "Hendrick Automotive assigns a Group Fixed Ops specialist to Frisco VW; Titan deployment is the test case for Hendrick's VW and Audi stores before rolling out to the 100+ store group", 0.90),
            ("news",            "Hendrick VW Frisco wins Volkswagen Customer Experience Leadership Award for 2025; service director publicly credits automation investment decisions as the next competitive differentiator in DFW's crowded luxury-import market", 0.86),
        ],
    },

    # ─────────────────────────────────────────────────────────────────────────
    # AUDI
    # ─────────────────────────────────────────────────────────────────────────
    {
        "company": {
            "name": "Audi Henderson",
            "website": "https://www.audihenderson.com",
            "industry": "Automotive Dealerships",
            "sub_industry": "Audi Franchise — Single-Rooftop (Henderson, NV — premium brand flagship in Southern Nevada)",
            "employee_estimate": 175,
            "location_city": "Henderson",
            "location_state": "NV",
            "location_country": "US",
            "source": "seed_v6",
        },
        "signals": [
            ("labor_shortage",  "Audi Henderson runs 30 service bays with Q8 e-tron and e-tron GT EV volume growing rapidly; Audi parts specialists with MMI and EV certification are exceptionally rare in Las Vegas — parts counter vacancy at 55% is the largest store operational crisis", 0.94),
            ("capex",           "Audi Henderson completes an $8M Audi Terminal renovation; the redesigned luxury lounge and service drive are specified to Audi's 2026 Terminal standard — ADAM beverage service robot and DUST-E service drive automation are both in the Terminal feature list", 0.91),
            ("strategic_hire",  "Audi Henderson appoints Fixed Ops Director from Porsche Las Vegas; her mandate is achieving Audi's top-5 CSI ranking for the Southwest region — Titan for parts and ADAM for lounge are the two automation investments in the 2026 service excellence plan", 0.93),
            ("job_posting",     "Audi Henderson posting 12+ parts specialist, Client Liaison, and service porter roles; e-tron EV parts complexity (HV battery, integrated MMI modules) makes precision parts delivery via Titan more accurate and faster than any human runner at this parts velocity", 0.90),
            ("news",            "Audi Henderson wins Audi Magna Society award for the second consecutive year; dealer principal publicly cites upcoming service automation deployment as the differentiator that will sustain the award in a competitive Nevada luxury-import market", 0.89),
        ],
    },

    # ─────────────────────────────────────────────────────────────────────────
    # PORSCHE
    # ─────────────────────────────────────────────────────────────────────────
    {
        "company": {
            "name": "Porsche Las Vegas",
            "website": "https://www.porschelasvegas.com",
            "industry": "Automotive Dealerships",
            "sub_industry": "Porsche Franchise — Single-Rooftop (Las Vegas, NV — ultra-luxury brand flagship)",
            "employee_estimate": 140,
            "location_city": "Las Vegas",
            "location_state": "NV",
            "location_country": "US",
            "source": "seed_v6",
        },
        "signals": [
            ("labor_shortage",  "Porsche Las Vegas 25-bay service department stocks 18,000+ Porsche-specific SKUs for 911, Taycan EV, Cayenne, and Macan EV; finding service associates who can accurately navigate Porsche's multi-variant parts catalog is nearly impossible in Las Vegas", 0.95),
            ("capex",           "Porsche Las Vegas completes a $12M Porsche Studio renovation; the all-glass luxury service lounge is specified to the Porsche Studio brand standard — ADAM lounge service robot is explicitly named in the 2026 guest experience upgrade plan", 0.92),
            ("strategic_hire",  "Porsche Las Vegas hires a new Fixed Ops Director from Holman Enterprises; her first mandate is a Taycan EV service excellence program, beginning with automated parts delivery to eliminate the four-minute average parts retrieval delay per repair order", 0.94),
            ("job_posting",     "Porsche Las Vegas posting 8+ parts specialist and client concierge roles; at $20–24/hr for a Porsche-certified parts associate these are the costliest indirect labor roles at any Las Vegas dealership — Titan ROI is immediate", 0.91),
            ("news",            "Porsche Las Vegas wins Porsche Premier Dealer award for the third time; dealer principal publicly commits to making Las Vegas the most technologically advanced Porsche service center in the western US — automation deployment announcement expected Q2 2026", 0.90),
        ],
    },

    # ─────────────────────────────────────────────────────────────────────────
    # LEXUS
    # ─────────────────────────────────────────────────────────────────────────
    {
        "company": {
            "name": "Lexus of Las Vegas",
            "website": "https://www.lexusoflasvegas.com",
            "industry": "Automotive Dealerships",
            "sub_industry": "Lexus Franchise — Single-Rooftop (Las Vegas, NV — Lexus Covenant dealer flagship)",
            "employee_estimate": 210,
            "location_city": "Las Vegas",
            "location_state": "NV",
            "location_country": "US",
            "source": "seed_v6",
        },
        "signals": [
            ("labor_shortage",  "Lexus of Las Vegas operates 40 service bays and a dedicated Lexus Loaner fleet program; the Lexus Covenant service standard requires zero wait time for parts — chronic parts runner vacancy of 48% makes that standard impossible to meet manually", 0.93),
            ("capex",           "Lexus of Las Vegas invests $11M in Lexus Covenant showroom and service facility renovation; the reimagined Omotenashi lounge is designed for ADAM companion robot service as an expression of the Lexus hospitality standard", 0.91),
            ("strategic_hire",  "Lexus of Las Vegas appoints a Service Excellence Director reporting to the dealer principal; the 2026 service technology plan includes Titan for parts-to-bay automation and ADAM for the client waiting lounge", 0.92),
            ("job_posting",     "Lexus of Las Vegas posting 14+ parts specialist, shuttle concierge, and client liaison roles; Covenant standard requires best-in-class service speed — every open parts runner req is a Titan ROI argument the store's own management is already making", 0.89),
            ("news",            "Lexus of Las Vegas achieves Toyota Motor North America's Elite of Lexus designation; dealer principal cites upcoming automation deployment as the investment that will maintain this status in an increasingly competitive Southwest luxury market", 0.90),
        ],
    },

    # ─────────────────────────────────────────────────────────────────────────
    # INFINITI
    # ─────────────────────────────────────────────────────────────────────────
    {
        "company": {
            "name": "Desert Infiniti",
            "website": "https://www.desertinfiniti.com",
            "industry": "Automotive Dealerships",
            "sub_industry": "Infiniti Franchise — Single-Rooftop (Las Vegas, NV)",
            "employee_estimate": 145,
            "location_city": "Las Vegas",
            "location_state": "NV",
            "location_country": "US",
            "source": "seed_v6",
        },
        "signals": [
            ("labor_shortage",  "Desert Infiniti runs 28 service bays handling QX80, Q50, and upcoming EV models; Las Vegas hospitality sector siphons parts counter labor continuously — the store averages 3 open parts associate roles at any given time", 0.91),
            ("job_posting",     "Desert Infiniti posting 10+ parts counter associate, service porter, and loaner coordinator roles; Infiniti's expanding EV lineup increases parts complexity — Titan eliminates mispick risk and relieves the parts manager from supervising runner accuracy", 0.89),
            ("capex",           "Desert Infiniti invests $5M in Infiniti Certified Collision and EV service expansion; new EV bay addition requires precise parts routing for QX Inspiration EV prototype service work beginning in 2026", 0.86),
            ("strategic_hire",  "Desert Infiniti promotes Service Director with an explicit target of reducing average repair cycle time by 30%; Titan deployment across all QX and Q-line parts pulls is the first capital investment approved in the 2026 service technology plan", 0.88),
            ("news",            "Desert Infiniti wins Infiniti Customer First Award for the Southwest Region; owner publicly states that parts delivery automation is the next phase of the store's service excellence investment", 0.85),
        ],
    },

    # ─────────────────────────────────────────────────────────────────────────
    # ACURA
    # ─────────────────────────────────────────────────────────────────────────
    {
        "company": {
            "name": "Acura of Peoria",
            "website": "https://www.acuraofpeoria.com",
            "industry": "Automotive Dealerships",
            "sub_industry": "Acura Franchise — Single-Rooftop (Peoria, AZ — Phoenix market flagship)",
            "employee_estimate": 155,
            "location_city": "Peoria",
            "location_state": "AZ",
            "location_country": "US",
            "source": "seed_v6",
        },
        "signals": [
            ("labor_shortage",  "Acura of Peoria runs 30 service bays predominantly servicing MDX and ZDX EV customers; Greater Phoenix Amazon and Intel construction labor markets pay $21–25/hr for physical roles — parts runner vacancy is a perpetual 40%+ at this store", 0.91),
            ("job_posting",     "Acura of Peoria posting 10+ parts associate, shuttle driver, and service aide roles; ZDX EV parts ramp in 2026 introduces new HV battery components to the parts catalog — Titan reduces new-model mispick risk to near zero", 0.90),
            ("capex",           "Acura of Peoria invests $6M in Acura Precision Crafted Performance showroom renovation; service write-up and customer lounge redesign enables ADAM robot integration as part of the Precision Crafted Experience standard", 0.87),
            ("strategic_hire",  "Acura of Peoria appoints Fixed Ops Director from Hendrick Acura Charlotte; first initiative is deploying Titan to cover ZDX and MDX parts delivery — store is selected as Southwest Acura pilot for the Honda Motor North America automation program", 0.90),
            ("news",            "Acura of Peoria wins Acura Precision Team Award for Arizona region; General Manager publicly notes that the automation pilots launching in 2026 are the store's bid to become the national benchmark for Acura service excellence", 0.88),
        ],
    },

    # ─────────────────────────────────────────────────────────────────────────
    # CADILLAC
    # ─────────────────────────────────────────────────────────────────────────
    {
        "company": {
            "name": "Findlay Cadillac",
            "website": "https://www.findlaycadillac.com",
            "industry": "Automotive Dealerships",
            "sub_industry": "Cadillac Franchise — Single-Rooftop (Henderson, NV — Findlay Group flagship luxury store)",
            "employee_estimate": 190,
            "location_city": "Henderson",
            "location_state": "NV",
            "location_country": "US",
            "source": "seed_v6",
        },
        "signals": [
            ("labor_shortage",  "Findlay Cadillac Henderson runs 35 service bays with record LYRIQ EV volume; Cadillac's ultra-premium service standard requires parts in-hand before technician assignment — unachievable manually at 45% parts counter vacancy in the Las Vegas market", 0.94),
            ("capex",           "Findlay Cadillac completes a $9M Cadillac Live showroom renovation; redesigned service lounge and live vehicle display area is designed for ADAM companion service robot as part of the Cadillac Live brand experience standard", 0.91),
            ("strategic_hire",  "Findlay Group appoints Group Fixed Operations Manager; Titan pilot at Findlay Cadillac Henderson is the test case — if successful, deployment rolls across Findlay Toyota, Honda, Hyundai, and VW stores by end of 2026", 0.95),
            ("job_posting",     "Findlay Cadillac posting 14+ parts specialist, valet technician, and client concierge roles; LYRIQ EV parts complexity (Ultium battery system, rear-wheel e-drive modules) makes Titan's confirmed parts accuracy critical at this luxury price point", 0.92),
            ("news",            "Findlay Cadillac wins Nevada's Cadillac Pinnacle Dealer award for 2025; dealer principal publicly states that Titan and ADAM deployments are approved for 2026 — making Findlay Cadillac one of the first Cadillac stores in the US with full parts and lounge automation", 0.93),
        ],
    },

    # ─────────────────────────────────────────────────────────────────────────
    # LINCOLN
    # ─────────────────────────────────────────────────────────────────────────
    {
        "company": {
            "name": "Lincoln of Dallas",
            "website": "https://lincolnofdallas.com",
            "industry": "Automotive Dealerships",
            "sub_industry": "Lincoln Franchise — Single-Rooftop (Plano, TX — DFW market flagship)",
            "employee_estimate": 160,
            "location_city": "Plano",
            "location_state": "TX",
            "location_country": "US",
            "source": "seed_v6",
        },
        "signals": [
            ("labor_shortage",  "Lincoln of Dallas operates 28 service bays serving Aviator PHEV and Navigator customers; DFW luxury labor market forces $22+/hr for comparable physical roles — parts counter and runner at $17 has near-constant vacancy", 0.91),
            ("capex",           "Lincoln of Dallas completes a $7M Lincoln Way Experience showroom redesign; the renovation's luxury client lounge is blueprint-compatible with ADAM companion robot service — Lincoln Way standard explicitly calls for elevated personal service touchpoints", 0.88),
            ("strategic_hire",  "Lincoln of Dallas hires Fixed Ops Director from Sewell Cadillac; mandate is achieving Lincoln Way Certified status — parts automation via Titan is the stated investment that closes the technician idle time gap preventing recertification", 0.90),
            ("job_posting",     "Lincoln of Dallas posting 10+ parts pick associate, concierge driver, and service liaison roles; Aviator PHEV parts volume (EV battery + ICE powertrain dual catalog) is growing 40% YoY — Titan eliminates the dual-catalog mispick risk entirely", 0.88),
            ("news",            "Lincoln of Dallas achieves Lincoln Motor Company's Black Label Dealer designation; owner credits upcoming technology investments — including Titan and ADAM — with sustaining the Black Label standard as competitor Lincoln stores also improve", 0.87),
        ],
    },

    # ─────────────────────────────────────────────────────────────────────────
    # GENESIS
    # ─────────────────────────────────────────────────────────────────────────
    {
        "company": {
            "name": "Genesis of Henderson",
            "website": "https://www.genesisofhenderson.com",
            "industry": "Automotive Dealerships",
            "sub_industry": "Genesis Franchise — Single-Rooftop (Henderson, NV — standalone Genesis store)",
            "employee_estimate": 130,
            "location_city": "Henderson",
            "location_state": "NV",
            "location_country": "US",
            "source": "seed_v6",
        },
        "signals": [
            ("labor_shortage",  "Genesis of Henderson operates 22 service bays serving GV70 Electrified and GV80 customers; Genesis's concierge valet service model requires on-demand parts delivery — the store currently has 3 unfilled parts positions because $15.50/hr can't compete with Las Vegas market rates", 0.92),
            ("capex",           "Genesis of Henderson invests $4.5M in Genesis Studio concept renovation; the Genesis Studio lounge is designed around a live vehicle display and private client consultation areas — ADAM companion robot is part of the Studio's digital hospitality feature set", 0.89),
            ("strategic_hire",  "Genesis of Henderson appoints a Guest Experience Director; the 2026 guest experience plan includes Titan for parts automation and ADAM for the Studio lounge — pilot store for Genesis Motor America's Southwest Operation Service Excellence program", 0.91),
            ("job_posting",     "Genesis of Henderson posting 8+ parts associate, concierge coordinator, and valet technician roles; GV70 Electrified EV parts ramp is 2x manual delivery capacity — Titan covers the gap without adding headcount that can't be hired", 0.88),
            ("news",            "Genesis of Henderson wins Genesis Motor America's Genesis Excellence Award for 2025; dealer principal publicly commits to making Henderson the first fully automated Genesis service operation in the US", 0.90),
        ],
    },

    # ─────────────────────────────────────────────────────────────────────────
    # SUBARU
    # ─────────────────────────────────────────────────────────────────────────
    {
        "company": {
            "name": "Groove Subaru",
            "website": "https://www.groovesubaru.com",
            "industry": "Automotive Dealerships",
            "sub_industry": "Subaru Franchise — High-Volume Single-Rooftop (Denver, CO — consistently top-10 Subaru volume in the US)",
            "employee_estimate": 230,
            "location_city": "Englewood",
            "location_state": "CO",
            "location_country": "US",
            "source": "seed_v6",
        },
        "signals": [
            ("labor_shortage",  "Groove Subaru runs 50+ service bays and handles the highest Ascent and Outback Wilderness AWD service volume in Colorado; Denver's outdoor recreation and tech industries pay $20–24/hr for physical roles — parts runner vacancy at 50%+", 0.92),
            ("job_posting",     "Groove Subaru posting 18+ parts counter, porter, and service associate roles annually; Solterra EV ramp in 2026 doubles parts catalog complexity — Titan covers the EV and hybrid parts pull gap without new headcount", 0.91),
            ("capex",           "Groove Subaru invests $9M in service department expansion adding 20 bays and a dedicated Solterra EV service lane; EV lane is designed from day one with autonomous parts delivery from a centralized parts tower", 0.89),
            ("strategic_hire",  "Groove Subaru promotes a General Service Manager with an explicit automation mandate; Titan deployment across all Outback, Forester, and Solterra parts pulls is the 2026 service technology investment for this high-volume store", 0.90),
            ("news",            "Groove Subaru ranks in Subaru Love Promise top-10 dealers nationally; owner publicly states that automation is the lever to sustain the brand promise as service volume outpaces available labor in the Denver metro", 0.87),
        ],
    },

    # ─────────────────────────────────────────────────────────────────────────
    # MAZDA
    # ─────────────────────────────────────────────────────────────────────────
    {
        "company": {
            "name": "Mazda of Orange Park",
            "website": "https://www.mazdaoforangepark.com",
            "industry": "Automotive Dealerships",
            "sub_industry": "Mazda Franchise — High-Volume Single-Rooftop (Orange Park, FL — consistently top-5 Mazda volume dealer)",
            "employee_estimate": 185,
            "location_city": "Orange Park",
            "location_state": "FL",
            "location_country": "US",
            "source": "seed_v6",
        },
        "signals": [
            ("labor_shortage",  "Mazda of Orange Park runs 35 service bays; JAX-area logistics warehouses (Amazon, FedEx, Target DC) pay $19–22/hr for roles comparable to parts runner — this store has had 2+ open parts associate positions every quarter for the past 18 months", 0.91),
            ("job_posting",     "Mazda of Orange Park posting 12+ parts counter, porter, and lube technician assistant roles; CX-90 PHEV parts volume growing with the North Florida EV adoption surge — Titan eliminates the dual ICE/EV parts catalog error risk", 0.89),
            ("capex",           "Mazda of Orange Park invests $5.5M in Mazda Retail Evolution facility upgrade; Craftsmanship Lounge and redesigned service write-up area are compatible with ADAM companion service robot as part of the Mazda Premium touch points", 0.86),
            ("strategic_hire",  "Mazda of Orange Park promotes Fixed Ops Director with mandate from the Asbury group; Titan pilot at Orange Park Mazda feeds into Asbury's group-wide evaluation of parts automation across all brands", 0.90),
            ("news",            "Mazda of Orange Park wins Mazda Customer Excellence Award for the Southeast; dealer principal publicly commits to automation investment — citing labor market reality — as the only sustainable path to maintaining the award's service speed benchmarks", 0.87),
        ],
    },

    # ─────────────────────────────────────────────────────────────────────────
    # VOLVO
    # ─────────────────────────────────────────────────────────────────────────
    {
        "company": {
            "name": "Volvo Cars Las Vegas",
            "website": "https://www.volvocarlasvegas.com",
            "industry": "Automotive Dealerships",
            "sub_industry": "Volvo Franchise — Single-Rooftop (Las Vegas, NV — standalone Volvo brand store)",
            "employee_estimate": 150,
            "location_city": "Las Vegas",
            "location_state": "NV",
            "location_country": "US",
            "source": "seed_v6",
        },
        "signals": [
            ("labor_shortage",  "Volvo Cars Las Vegas runs 26 service bays with surging EX90 all-electric flagship volume; Volvo-certified parts associates who understand high-voltage safety protocols are nearly nonexistent in the Las Vegas labor market — chronic vacancy at 55%+", 0.92),
            ("capex",           "Volvo Cars Las Vegas completes a $6M Volvo Studio renovation; the open-concept Studio lounge emphasizes transparency and sustainability — ADAM companion robot serving the lounge aligns with Volvo's Care brand promise for a tech-forward, safety-conscious customer base", 0.89),
            ("strategic_hire",  "Volvo Cars Las Vegas appoints Fixed Ops Director from Penske Porsche Vegas; mandate is achieving EX90 EV service excellence — Titan automated parts delivery reduces high-voltage parts handling risk vs. manual routing and eliminates average 11-minute parts delay per RO", 0.91),
            ("job_posting",     "Volvo Cars Las Vegas posting 10+ parts specialist, customer care coordinator, and service assistant roles; EX90 EV parts (SPA2 integrated safety frame, full-array LIDAR modules) are high-value and extremely mispick-sensitive — Titan's barcode confirmation layer is a safety and liability argument", 0.88),
            ("news",            "Volvo Cars Las Vegas wins Volvo Care Award from Volvo Cars USA; dealer principal publicly cites Titan deployment for parts and ADAM for the Studio lounge as the 2026 investments that will sustain Care Award status", 0.90),
        ],
    },

    # ─────────────────────────────────────────────────────────────────────────
    # JEEP / RAM / DODGE (STELLANTIS)
    # ─────────────────────────────────────────────────────────────────────────
    {
        "company": {
            "name": "Findlay Chrysler Dodge Jeep Ram",
            "website": "https://www.findlaycdjr.com",
            "industry": "Automotive Dealerships",
            "sub_industry": "Stellantis Franchise — Multi-Brand Single-Rooftop (Henderson, NV — CDJR)",
            "employee_estimate": 230,
            "location_city": "Henderson",
            "location_state": "NV",
            "location_country": "US",
            "source": "seed_v6",
        },
        "signals": [
            ("labor_shortage",  "Findlay CDJR Henderson runs 40 service bays across Jeep, Ram, and Dodge lines; four-brand parts catalog is one of the most complex at any single-rooftop store — parts runner vacancy at 50%+ in Las Vegas means the complexity falls on already-stretched service advisors", 0.93),
            ("job_posting",     "Findlay CDJR posting 16+ parts counter associate, porter, and lot attendant roles; Ram 1500 REV EV launch in 2025 adds a fourth powertrain catalog to an already complex Jeep/Dodge/Ram/Chrysler parts matrix — Titan eliminates cross-brand mispick risk entirely", 0.91),
            ("capex",           "Findlay CDJR invests $8M in Jeep Adventure Center expansion and Ram Commercial service bay addition; new Ram Commercial lane is AMR-accessible and specified for autonomous parts delivery from a shared CDJR parts tower", 0.88),
            ("strategic_hire",  "Findlay Group assigns Group Fixed Operations Manager to CDJR Henderson for the Titan pilot; success here drives Titan deployment across all Findlay stores — CDJR's four-brand parts complexity is the ideal proving ground for Titan's multi-catalog handling", 0.92),
            ("news",            "Findlay CDJR Henderson wins Ram Commercial Dealer of the Year for Nevada; service manager publicly cites upcoming Titan deployment as the investment that will sustain commercial-grade service throughput for Ram 1500 REV fleet customers", 0.89),
        ],
    },

    # ─────────────────────────────────────────────────────────────────────────
    # RIVIAN
    # ─────────────────────────────────────────────────────────────────────────
    {
        "company": {
            "name": "Rivian Service Hub — Scottsdale",
            "website": "https://rivian.com/support/service",
            "industry": "Automotive Dealerships",
            "sub_industry": "Rivian Direct Service — EV Brand Hub (Scottsdale, AZ — high-volume Southwest service hub)",
            "employee_estimate": 160,
            "location_city": "Scottsdale",
            "location_state": "AZ",
            "location_country": "US",
            "source": "seed_v6",
        },
        "signals": [
            ("expansion",       "Rivian Service Scottsdale expands from 20 to 40 service positions by Q3 2026; R1T and R1S parts in Arizona are highly volume-driven by outdoor/adventure owners — expanded facility is specified with AMR-ready service corridors from day one", 0.92),
            ("labor_shortage",  "Rivian Scottsdale competes with Waymo, Intel Fab, and Amazon for the same Phoenix-area technical labor; parts staging associates at $17/hr see 70%+ annual turnover vs. $23–26/hr competing roles in the metro — Titan is the direct solution", 0.91),
            ("capex",           "Rivian invests $18M in Southwest service hub expansion across Scottsdale and Tempe; new hubs are designed with centralized parts towers and AMR-navigable service corridors — Titan deployment is part of the Rivian Service Experience standard for all large hubs", 0.93),
            ("strategic_hire",  "Rivian hires VP of Service Experience from Tesla Service; mandate is making Rivian service the benchmark for EV adventure brand owners — parts automation via Titan is named as the day-one operational standard at all new large-format hubs", 0.92),
            ("job_posting",     "Rivian Scottsdale posting 18+ EV parts technician associate, service coordinator, and lot runner roles; R2 launch in 2026 will double service volume at this hub — Titan is the throughput lever that allows scaling without proportionally scaling headcount", 0.90),
        ],
    },

    # ─────────────────────────────────────────────────────────────────────────
    # MITSUBISHI
    # ─────────────────────────────────────────────────────────────────────────
    {
        "company": {
            "name": "Findlay Mitsubishi",
            "website": "https://www.findlaymitsubishi.com",
            "industry": "Automotive Dealerships",
            "sub_industry": "Mitsubishi Franchise — Single-Rooftop (Henderson, NV)",
            "employee_estimate": 120,
            "location_city": "Henderson",
            "location_state": "NV",
            "location_country": "US",
            "source": "seed_v6",
        },
        "signals": [
            ("labor_shortage",  "Findlay Mitsubishi runs 20 service bays servicing Eclipse Cross PHEV and Outlander PHEV; Las Vegas market makes parts runner recruitment at $14.50/hr nearly impossible — the store operates with 2 chronic open parts associate positions", 0.90),
            ("job_posting",     "Findlay Mitsubishi posting 8+ parts counter, porter, and quick lane assistant roles; Outlander PHEV and Eclipse Cross PHEV warranty volume growing 60% YoY — Titan deployment eliminates the throughput constraint in under 6 months at current parts velocity", 0.88),
            ("capex",           "Findlay Mitsubishi invests $3M in showroom and service lane renovation; EV-ready service lane for Outlander PHEV is AMR-accessible and being considered as the first Findlay store to pilot Titan before larger stores", 0.85),
            ("strategic_hire",  "Findlay Group directs Fixed Operations Manager to evaluate Findlay Mitsubishi as a low-complexity Titan pilot; smaller parts catalog makes it the ideal first deployment in the group before scaling to Toyota, Honda, and Cadillac", 0.89),
            ("news",            "Findlay Mitsubishi named Nevada's top-volume Mitsubishi dealer for 2025; dealer principal confirms Titan automation is approved for the service department as part of Findlay Group's 2026 fixed ops technology rollout", 0.87),
        ],
    },

]


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS (identical pattern to seed_leads_v4 / v5)
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
                source=cd.get("source", "seed_v6"),
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
                        source_url="seed_v6",
                    )
                    db.add(sig)
                    db.commit()
                added_s += 1

    return added_c, added_s


def score_new(db):
    companies = db.query(Company).filter(Company.source == 'seed_v6').all()
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
        brands = [e["company"]["sub_industry"].split("—")[0].strip() for e in NEW_LEADS]
        print(f"\n=== seed_leads_v6 DRY RUN ===")
        print(f"  Companies : {total_co}")
        print(f"  Signals   : {total_sig}")
        print(f"\n  OEM brand dealerships:")
        for b in brands:
            print(f"    {b}")
        print(f"\nRun with --commit to write to database.\n")
        sys.exit(0)

    print("\n=== seed_leads_v6  COMMITTING TO DATABASE ===")
    db = SessionLocal()
    try:
        added_c, added_s = seed_database(db, dry_run=False)
        print(f"  Inserted  {added_c} new companies, {added_s} new signals")

        print("\n  Scoring new seed_v6 companies only...")
        scored = score_new(db)
        print(f"  Scored    {scored} companies")

        total_c = db.query(Company).count()
        total_s = db.query(Signal).count()
        print(f"\n  DB totals: {total_c} companies | {total_s} signals")
        print("  Done.\n")
    finally:
        db.close()
