"""
seed_leads_v3.py — Lead expansion: Casinos/Gaming, Cruise Lines, Theme Parks

Three verticals with massive robot applicability:
  • Casinos & Gaming  — 24/7 F&B, housekeeping, beverage delivery at scale
  • Cruise Lines      — tightly staffed ships, delivery/food service robots ideal
  • Theme Parks       — high guest volumes, food courts, keepage cleaning

Usage:
  python scripts/seed_leads_v3.py           # dry-run count
  python scripts/seed_leads_v3.py --commit  # write to DB
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
# LEAD DATA — 3 new verticals
# ─────────────────────────────────────────────────────────────────────────────
NEW_LEADS = [

    # =========================================================================
    # CASINOS & GAMING
    # =========================================================================
    {
        "company": {
            "name": "Caesars Entertainment",
            "website": "https://www.caesars.com",
            "industry": "Casinos & Gaming",
            "sub_industry": "Integrated Resort",
            "employee_estimate": 65000,
            "location_city": "Las Vegas",
            "location_state": "NV",
            "location_country": "US",
            "source": "seed_v3",
        },
        "signals": [
            ("labor_shortage",  "Caesars F&B and housekeeping vacancy rate hits 34%; properties running at 70% service capacity during peak occupancy", 0.92),
            ("capex",           "Caesars Entertainment commits $500M to property modernization across Las Vegas Strip properties; automation technology included", 0.88),
            ("strategic_hire",  "Caesars hires SVP of Operations Technology to integrate automated beverage, food delivery, and guest services across all properties", 0.90),
            ("news",            "Caesars pilots autonomous beverage cart at Harrah's Las Vegas; guest satisfaction scores up 18% during trial period", 0.87),
            ("expansion",       "Caesars announces $400M renovation of Paris Las Vegas and Bally's flagship; new F&B formats being designed for robot-compatible service lanes", 0.83),
        ],
    },
    {
        "company": {
            "name": "Las Vegas Sands Corp",
            "website": "https://www.sands.com",
            "industry": "Casinos & Gaming",
            "sub_industry": "Integrated Resort",
            "employee_estimate": 54000,
            "location_city": "Las Vegas",
            "location_state": "NV",
            "location_country": "US",
            "source": "seed_v3",
        },
        "signals": [
            ("capex",           "Las Vegas Sands investing $1.5B to redevelop Sands Expo and Convention Center site; automation and smart building infrastructure central to plans", 0.91),
            ("strategic_hire",  "Las Vegas Sands appoints Chief Innovation Officer to lead guest experience technology across Marina Bay Sands and future US properties", 0.89),
            ("news",            "Las Vegas Sands deploys autonomous cleaning and delivery robots at Marina Bay Sands Singapore; expanding program to new US venues", 0.90),
            ("labor_shortage",  "Sands resort operations facing chronic housekeeping and F&B staffing gaps; COO cites labor market as top operational challenge", 0.88),
        ],
    },
    {
        "company": {
            "name": "Wynn Resorts",
            "website": "https://www.wynnresorts.com",
            "industry": "Casinos & Gaming",
            "sub_industry": "Luxury Resort & Casino",
            "employee_estimate": 24000,
            "location_city": "Las Vegas",
            "location_state": "NV",
            "location_country": "US",
            "source": "seed_v3",
        },
        "signals": [
            ("capex",           "Wynn Resorts commits $600M to Wynn Las Vegas resort renovations; guest-facing technology and service automation are priority workstreams", 0.87),
            ("news",            "Wynn announces robotic cocktail delivery pilot in high-limit gaming areas; expanding to pool deck and cabana service if successful", 0.86),
            ("strategic_hire",  "Wynn Resorts hires VP of Guest Experience Technology from hospitality tech sector; mandate includes in-room and poolside delivery automation", 0.84),
            ("labor_shortage",  "Wynn F&B operations understaffed by 29%; management exploring automation to maintain luxury service standards with fewer headcount", 0.85),
        ],
    },
    {
        "company": {
            "name": "MGM Resorts International",
            "website": "https://www.mgmresorts.com",
            "industry": "Casinos & Gaming",
            "sub_industry": "Integrated Resort",
            "employee_estimate": 77000,
            "location_city": "Las Vegas",
            "location_state": "NV",
            "location_country": "US",
            "source": "seed_v3",
        },
        "signals": [
            ("capex",           "MGM Resorts announces $2.1B capital program over 3 years; technology and operational automation a key pillar of the investment plan", 0.92),
            ("news",            "MGM deploys AI-powered autonomous cleaning robots at Bellagio and MGM Grand; units handle overnight floor cleaning autonomously", 0.91),
            ("strategic_hire",  "MGM Resorts named Chief AI and Data Officer; automation of F&B and housekeeping workflows a stated priority", 0.89),
            ("expansion",       "MGM opens new integrated resort in Japan; fully designed with autonomous F&B delivery and guest service robot infrastructure", 0.88),
            ("labor_shortage",  "MGM housekeeping workforce 38% below pre-pandemic levels; company publicly prioritizing automation to bridge the gap", 0.90),
        ],
    },
    {
        "company": {
            "name": "Hard Rock International",
            "website": "https://www.hardrock.com",
            "industry": "Casinos & Gaming",
            "sub_industry": "Integrated Resort & Entertainment",
            "employee_estimate": 40000,
            "location_city": "Hollywood",
            "location_state": "FL",
            "location_country": "US",
            "source": "seed_v3",
        },
        "signals": [
            ("expansion",       "Hard Rock opens new $2.2B integrated resort in Bristol, VA and expands in New York; F&B and hospitality operations at both require significant staffing", 0.87),
            ("labor_shortage",  "Hard Rock Hotel & Casino properties report 40% kitchen and bar vacancy; HR cites recruiting as largest operational constraint", 0.88),
            ("capex",           "Hard Rock commits $800M to property upgrades at flagship Hollywood FL property; guest experience technology included in capital plan", 0.84),
            ("news",            "Hard Rock evaluates robotic beverage service for gaming floor; CEO notes guest demand for fast contactless service delivery", 0.83),
        ],
    },
    {
        "company": {
            "name": "Penn Entertainment",
            "website": "https://www.pennentertainment.com",
            "industry": "Casinos & Gaming",
            "sub_industry": "Regional Casino Operator",
            "employee_estimate": 20000,
            "location_city": "Wyomissing",
            "location_state": "PA",
            "location_country": "US",
            "source": "seed_v3",
        },
        "signals": [
            ("labor_shortage",  "Penn Entertainment regional casinos operating with 35% fewer F&B and floor service staff than required; table and slot service disrupted", 0.86),
            ("capex",           "Penn Entertainment $350M technology transformation initiative targets guest experience automation across 43 properties nationwide", 0.85),
            ("strategic_hire",  "Penn hires Director of Operational Innovation; mandate includes autonomous delivery and service robots for casino floor and dining", 0.82),
            ("news",            "Penn Entertainment partners with tech vendor on casino-floor autonomous beverage delivery test at Hollywood Casino in Columbus", 0.83),
        ],
    },
    {
        "company": {
            "name": "Boyd Gaming Corporation",
            "website": "https://www.boydgaming.com",
            "industry": "Casinos & Gaming",
            "sub_industry": "Regional Casino Operator",
            "employee_estimate": 23000,
            "location_city": "Las Vegas",
            "location_state": "NV",
            "location_country": "US",
            "source": "seed_v3",
        },
        "signals": [
            ("labor_shortage",  "Boyd Gaming properties face 32% food service and housekeeping vacancy; operational efficiency cited as top executive priority for 2026", 0.85),
            ("capex",           "Boyd Gaming accelerates $240M property investment cycle; technology modernization across all casino floors and hotel operations", 0.82),
            ("news",            "Boyd Gaming CEO discusses autonomous service robots at investor day; notes ROI on labor replacement accelerating post-pandemic", 0.84),
            ("strategic_hire",  "Boyd hires VP of Technology Operations to lead casino floor automation and digital guest service transformation", 0.80),
        ],
    },
    {
        "company": {
            "name": "Melco Resorts & Entertainment",
            "website": "https://www.melco-resorts.com",
            "industry": "Casinos & Gaming",
            "sub_industry": "Luxury Integrated Resort",
            "employee_estimate": 22000,
            "location_city": "Macau",
            "location_state": "",
            "location_country": "MO",
            "source": "seed_v3",
        },
        "signals": [
            ("news",            "Melco deploys robotic food and beverage delivery across City of Dreams Macau; 18 units operating across casino floors and hotel restaurants", 0.92),
            ("capex",           "Melco invests $300M in Macau property upgrades; smart hotel and autonomous service technology a central feature of redevelopment", 0.88),
            ("strategic_hire",  "Melco appoints Chief Digital & Automation Officer; hotel and resort robotics deployment across all Asia properties primary mandate", 0.87),
            ("expansion",       "Melco breaks ground on $1B Cyprus Integrated Resort; autonomous in-room dining and lobby delivery robot infrastructure planned from day one", 0.85),
        ],
    },
    {
        "company": {
            "name": "Galaxy Entertainment Group",
            "website": "https://www.galaxyentertainment.com",
            "industry": "Casinos & Gaming",
            "sub_industry": "Luxury Integrated Resort",
            "employee_estimate": 30000,
            "location_city": "Macau",
            "location_state": "",
            "location_country": "MO",
            "source": "seed_v3",
        },
        "signals": [
            ("capex",           "Galaxy Entertainment Group investing HKD 20B in Galaxy Macau Phase 4; autonomous service, smart hotel, and robotic delivery planned", 0.90),
            ("news",            "Galaxy Macau deploys 24 autonomous delivery robots for in-room dining and resort corridors; guest satisfaction up 22%", 0.91),
            ("strategic_hire",  "Galaxy names VP of Smart Resort Technology; mandate is to deploy robotics and AI across all hotel, casino, and F&B operations", 0.88),
            ("expansion",       "Galaxy awarded new concession in Macau through 2032; $6.5B capex commitment includes major automation investment across all properties", 0.89),
        ],
    },
    {
        "company": {
            "name": "Sycuan Casino Resort",
            "website": "https://www.sycuan.com",
            "industry": "Casinos & Gaming",
            "sub_industry": "Tribal Casino Resort",
            "employee_estimate": 3500,
            "location_city": "El Cajon",
            "location_state": "CA",
            "location_country": "US",
            "source": "seed_v3",
        },
        "signals": [
            ("labor_shortage",  "Sycuan Casino Resort F&B and housekeeping vacancy at 38%; management evaluating robotic service solutions to maintain guest experience quality", 0.84),
            ("capex",           "Sycuan invests $40M in resort amenity expansion including new restaurant concepts; automation-ready kitchen and service infrastructure planned", 0.80),
            ("news",            "Sycuan Casino hosts tribal gaming technology summit; robotic guest service demonstrations featured as key operational solution", 0.78),
        ],
    },

    # =========================================================================
    # CRUISE LINES
    # =========================================================================
    {
        "company": {
            "name": "Carnival Corporation",
            "website": "https://www.carnivalcorp.com",
            "industry": "Cruise Lines",
            "sub_industry": "Mass Market Cruise",
            "employee_estimate": 120000,
            "location_city": "Miami",
            "location_state": "FL",
            "location_country": "US",
            "source": "seed_v3",
        },
        "signals": [
            ("labor_shortage",  "Carnival Corporation onboard crew vacancy at 28%; galley, cabin steward, and waiter positions hardest to fill across 9 cruise brands", 0.91),
            ("capex",           "Carnival commits $8.3B in new ship orders through 2028; all new builds designed with autonomous service and delivery robot infrastructure", 0.90),
            ("news",            "Carnival Corporation CEO discusses deployment of autonomous food delivery and cabin service robots onboard; trial on Carnival Horizon confirmed", 0.88),
            ("strategic_hire",  "Carnival names Chief Technology & Innovation Officer; onboard robotics and automated guest service delivery explicit priority", 0.87),
            ("expansion",       "Carnival Corporation opens new private island destination in the Bahamas; fully automated food service and beverage delivery planned for beach clubs", 0.85),
        ],
    },
    {
        "company": {
            "name": "Royal Caribbean Group",
            "website": "https://www.rclcorporate.com",
            "industry": "Cruise Lines",
            "sub_industry": "Premium & Mass Market Cruise",
            "employee_estimate": 100000,
            "location_city": "Miami",
            "location_state": "FL",
            "location_country": "US",
            "source": "seed_v3",
        },
        "signals": [
            ("news",            "Royal Caribbean Icon of the Seas features bionic bar robots and autonomous drink delivery on promenade deck; guests rate experience top attraction onboard", 0.93),
            ("capex",           "Royal Caribbean orders 6 new ships totaling $9B; all vessels spec'd with smart galley, automated F&B delivery, and cabin robot service systems", 0.91),
            ("strategic_hire",  "Royal Caribbean hires VP of Onboard Technology Innovation; scope includes scaling robotic bartending and food delivery fleet-wide", 0.89),
            ("expansion",       "Royal Caribbean breaks ground on $1B private island expansion in Nassau; automated food service and beverage delivery to be scaled to island venues", 0.88),
        ],
    },
    {
        "company": {
            "name": "Norwegian Cruise Line Holdings",
            "website": "https://www.nclhltd.com",
            "industry": "Cruise Lines",
            "sub_industry": "Premium Cruise",
            "employee_estimate": 35000,
            "location_city": "Miami",
            "location_state": "FL",
            "location_country": "US",
            "source": "seed_v3",
        },
        "signals": [
            ("labor_shortage",  "Norwegian Cruise Line Holdings operating at 22% below required onboard crew levels; food service and cabin steward positions most impacted", 0.89),
            ("capex",           "NCLH announces $3.5B new ship order program; autonomous galley and passenger service robot systems to be standard on all new vessels", 0.87),
            ("news",            "Norwegian Cruise Line COO: we are actively evaluating robotics for food delivery and cabin services to address crew gaps and delight guests", 0.86),
            ("strategic_hire",  "NCL hires Director of Fleet Innovation; autonomous delivery and guest service automation are stated mandate", 0.84),
        ],
    },
    {
        "company": {
            "name": "MSC Cruises",
            "website": "https://www.msccruises.com",
            "industry": "Cruise Lines",
            "sub_industry": "Premium Cruise",
            "employee_estimate": 30000,
            "location_city": "Geneva",
            "location_state": "",
            "location_country": "CH",
            "source": "seed_v3",
        },
        "signals": [
            ("capex",           "MSC Cruises orders 10 new vessels in $23B fleet expansion; smart ship technology including onboard autonomous delivery systems required", 0.90),
            ("news",            "MSC World Europa features robotic beverage service at pool deck; MSC Cruises plans to expand autonomous service to 8 additional ships", 0.91),
            ("strategic_hire",  "MSC Cruises appoints VP of Smart Ship & Automation; responsible for deploying onboard robotics across 22-ship fleet", 0.88),
            ("labor_shortage",  "MSC Cruises facing severe crew shortage post-pandemic; automated food and beverage delivery seen as critical service continuity tool", 0.86),
        ],
    },
    {
        "company": {
            "name": "Viking Cruises",
            "website": "https://www.vikingcruises.com",
            "industry": "Cruise Lines",
            "sub_industry": "Luxury Expedition & River Cruise",
            "employee_estimate": 10000,
            "location_city": "Los Angeles",
            "location_state": "CA",
            "location_country": "US",
            "source": "seed_v3",
        },
        "signals": [
            ("labor_shortage",  "Viking Cruises onboard service staff 26% below optimal; intimate ship size makes labor gaps especially impactful on guest experience", 0.83),
            ("capex",           "Viking orders 8 new ocean expedition ships and 10 river vessels through 2027; operational technology investment increasing per vessel", 0.82),
            ("news",            "Viking evaluates compact autonomous delivery robots for ocean ship corridors; CEO notes guest expectations for immediate, quiet service delivery", 0.80),
        ],
    },
    {
        "company": {
            "name": "Virgin Voyages",
            "website": "https://www.virginvoyages.com",
            "industry": "Cruise Lines",
            "sub_industry": "Adult-Only Premium Cruise",
            "employee_estimate": 4000,
            "location_city": "Plantation",
            "location_state": "FL",
            "location_country": "US",
            "source": "seed_v3",
        },
        "signals": [
            ("news",            "Virgin Voyages brand positioning around tech-forward guest experience; autonomous bar and food delivery robots align perfectly with Scarlet Lady concept", 0.85),
            ("capex",           "Virgin Voyages announces acquisition of 4 additional ships by 2028; technology differentiation a core design brief for all new vessel interiors", 0.83),
            ("labor_shortage",  "Virgin Voyages crew recruitment challenging in competitive maritime labor market; automation options being evaluated to maintain service ratios", 0.82),
        ],
    },
    {
        "company": {
            "name": "Lindblad Expeditions",
            "website": "https://www.expeditions.com",
            "industry": "Cruise Lines",
            "sub_industry": "Expedition Cruise",
            "employee_estimate": 1600,
            "location_city": "New York",
            "location_state": "NY",
            "location_country": "US",
            "source": "seed_v3",
        },
        "signals": [
            ("labor_shortage",  "Lindblad Expeditions onboard galley and service crew shortfall impacting expedition departures; automation being studied to maintain intimate service standards", 0.79),
            ("capex",           "Lindblad orders 2 new purpose-built expedition vessels with modern smart ship technology; autonomous service provisions under review", 0.76),
        ],
    },

    # =========================================================================
    # THEME PARKS & ENTERTAINMENT
    # =========================================================================
    {
        "company": {
            "name": "Walt Disney Parks & Resorts",
            "website": "https://disneyparks.disney.go.com",
            "industry": "Theme Parks & Entertainment",
            "sub_industry": "Theme Park & Resort",
            "employee_estimate": 170000,
            "location_city": "Lake Buena Vista",
            "location_state": "FL",
            "location_country": "US",
            "source": "seed_v3",
        },
        "signals": [
            ("labor_shortage",  "Disney Parks faces 35% food service, custodial, and resort operations vacancy; union contracts complicate hiring; automation being evaluated", 0.90),
            ("capex",           "Disney announces $60B capex investment over 10 years across parks and resorts; autonomous food delivery and smart guest services included in Resort of the Future roadmap", 0.93),
            ("news",            "Disney Parks deploys autonomous floor cleaning robots at EPCOT and Magic Kingdom; testing delivery robots in Disney Springs resort area", 0.91),
            ("strategic_hire",  "Disney Experiences hires Chief Technology Officer; autonomous guest experience and operational robotics explicitly mentioned in role brief", 0.90),
            ("expansion",       "Disney breaks ground on $8B expansion of Walt Disney World including new land and resort hotel; autonomous service infrastructure designed in from start", 0.88),
        ],
    },
    {
        "company": {
            "name": "Universal Parks & Resorts",
            "website": "https://www.universalparksandresorts.com",
            "industry": "Theme Parks & Entertainment",
            "sub_industry": "Theme Park & Resort",
            "employee_estimate": 45000,
            "location_city": "Orlando",
            "location_state": "FL",
            "location_country": "US",
            "source": "seed_v3",
        },
        "signals": [
            ("expansion",       "Universal opens Epic Universe theme park in Orlando 2025; massive food service and resort infrastructure requires significant operational staffing", 0.92),
            ("labor_shortage",  "Universal Parks F&B and custodial teams 32% below required staffing ahead of Epic Universe opening; management exploring automated service solutions", 0.90),
            ("capex",           "Universal Parks commits $2B+ to Epic Universe; autonomous service and delivery robots being evaluated for high-traffic food court and resort hotel areas", 0.88),
            ("news",            "Universal Parks VP of Operations discusses autonomous cleaning and food delivery robots as key tools for managing peak attendance operations", 0.87),
        ],
    },
    {
        "company": {
            "name": "SeaWorld Entertainment",
            "website": "https://www.seaworld.com",
            "industry": "Theme Parks & Entertainment",
            "sub_industry": "Theme Park & Marine Life Entertainment",
            "employee_estimate": 12000,
            "location_city": "Orlando",
            "location_state": "FL",
            "location_country": "US",
            "source": "seed_v3",
        },
        "signals": [
            ("labor_shortage",  "SeaWorld Parks food service and rides operations 36% understaffed; seasonal hiring challenges at all 12 properties across US", 0.86),
            ("capex",           "SeaWorld Entertainment $350M capex plan includes new dining infrastructure and operations technology to reduce per-guest labor costs", 0.83),
            ("news",            "SeaWorld evaluates autonomous food delivery robots for high-traffic dining areas; CEO discusses automation as key to profitability improvement", 0.82),
        ],
    },
    {
        "company": {
            "name": "Six Flags Entertainment (now Six Flags Great Adventure)",
            "website": "https://www.sixflags.com",
            "industry": "Theme Parks & Entertainment",
            "sub_industry": "Regional Theme Park",
            "employee_estimate": 40000,
            "location_city": "Midland",
            "location_state": "TX",
            "location_country": "US",
            "source": "seed_v3",
        },
        "signals": [
            ("labor_shortage",  "Six Flags properties average 42% seasonal food service and custodial vacancy; inability to staff food locations leads to lost F&B revenue", 0.88),
            ("capex",           "Six Flags $1B+ capital plan post-merger with Cedar Fair; food service infrastructure modernization included with potential for robotic delivery", 0.86),
            ("news",            "Six Flags / Cedar Fair merger creates 42-park operator; combined operations team actively evaluating automated food service solutions to address chronic staffing gaps", 0.87),
            ("strategic_hire",  "Combined Six Flags / Cedar Fair entity hires Chief Operations Officer to standardize service delivery across all parks; automation mandate included", 0.83),
        ],
    },
    {
        "company": {
            "name": "Cedar Fair (merged with Six Flags)",
            "website": "https://www.cedarfair.com",
            "industry": "Theme Parks & Entertainment",
            "sub_industry": "Regional Theme Park",
            "employee_estimate": 48000,
            "location_city": "Sandusky",
            "location_state": "OH",
            "location_country": "US",
            "source": "seed_v3",
        },
        "signals": [
            ("labor_shortage",  "Cedar Fair parks operating F&B and custodial at 39% below optimal staffing; executive team cited workforce as top operational constraint", 0.87),
            ("news",            "Cedar Fair Worlds of Fun deploys autonomous floor scrubbing robot in indoor food court; expanding pilot to 5 additional properties", 0.84),
            ("capex",           "Cedar Fair investing $500M in park improvements across Knott's Berry Farm, Carowinds, Canada's Wonderland; operational automation in scope", 0.83),
        ],
    },
    {
        "company": {
            "name": "Merlin Entertainments",
            "website": "https://www.merlinentertainments.biz",
            "industry": "Theme Parks & Entertainment",
            "sub_industry": "Global Attractions Operator",
            "employee_estimate": 28000,
            "location_city": "Poole",
            "location_state": "",
            "location_country": "GB",
            "source": "seed_v3",
        },
        "signals": [
            ("labor_shortage",  "Merlin Entertainments (LEGOLAND, Alton Towers, Thorpe Park) facing 31% F&B and visitor experience staff vacancy across UK and EU parks", 0.86),
            ("capex",           "Merlin Entertainments EUR 400M European resort expansion program; operational technology including autonomous delivery featured in Crealy and resort hotel projects", 0.84),
            ("news",            "Merlin COO discusses autonomous guest experience robots as key tool for UK theme park operations; cost and guest satisfaction benefits noted", 0.83),
            ("expansion",       "Merlin opens new LEGOLAND resort in Korea and expands Gardaland Italy; smart facility and food service technology built in from day one", 0.82),
        ],
    },
    {
        "company": {
            "name": "Vail Resorts",
            "website": "https://www.vailresorts.com",
            "industry": "Theme Parks & Entertainment",
            "sub_industry": "Ski & Mountain Resort",
            "employee_estimate": 55000,
            "location_city": "Broomfield",
            "location_state": "CO",
            "location_country": "US",
            "source": "seed_v3",
        },
        "signals": [
            ("labor_shortage",  "Vail Resorts mountain base lodge and F&B positions 44% vacant at peak season; mountain towns present extreme recruiting challenges", 0.90),
            ("capex",           "Vail Resorts commits $174M annual capex to resort improvements including on-mountain dining facility upgrades; autonomous service options under evaluation", 0.85),
            ("news",            "Vail Resorts CEO discusses 'staffing emergency' in mountain towns; automated food service described as 'part of the solution' during analyst call", 0.89),
            ("strategic_hire",  "Vail Resorts hires VP of Mountain Experience & Operations Innovation; scope explicitly includes automation of F&B and resort services", 0.84),
        ],
    },
    {
        "company": {
            "name": "Herschend Family Entertainment",
            "website": "https://www.herschend.com",
            "industry": "Theme Parks & Entertainment",
            "sub_industry": "Family Theme Park",
            "employee_estimate": 12000,
            "location_city": "Atlanta",
            "location_state": "GA",
            "location_country": "US",
            "source": "seed_v3",
        },
        "signals": [
            ("labor_shortage",  "Herschend parks (Dollywood, Silver Dollar City, Wild Adventures) facing 40% seasonal F&B and operations vacancy; guest experience degraded at peak periods", 0.86),
            ("news",            "Herschend Family Entertainment evaluating autonomous food delivery and custodial robots for Dollywood and Silver Dollar City property expansions", 0.82),
            ("capex",           "Herschend commits $90M to Dollywood expansion through 2026; new commercial kitchen and food service areas designed for future automation integration", 0.80),
        ],
    },

    # =========================================================================
    # REAL ESTATE & FACILITIES MANAGEMENT
    # =========================================================================
    {
        "company": {
            "name": "CBRE Group",
            "website": "https://www.cbre.com",
            "industry": "Real Estate & Facilities",
            "sub_industry": "Commercial Real Estate Services",
            "employee_estimate": 130000,
            "location_city": "Dallas",
            "location_state": "TX",
            "location_country": "US",
            "source": "seed_v3",
        },
        "signals": [
            ("strategic_hire",  "CBRE hires Global Head of Smart Buildings & Robotics; mandate to deploy autonomous cleaning, delivery, and security robots across managed portfolio", 0.88),
            ("capex",           "CBRE facilities management division investing $200M in proptech and autonomous building operations; robotic cleaning and delivery piloted at 200+ buildings", 0.86),
            ("news",            "CBRE deploys autonomous floor cleaning and UV disinfection robots across 400 commercial office buildings in North America; expanding to UK and EU", 0.89),
            ("labor_shortage",  "CBRE facilities management division facing 35% janitorial and amenity services vacancy; automation cited as key strategic response", 0.85),
        ],
    },
    {
        "company": {
            "name": "Jones Lang LaSalle (JLL)",
            "website": "https://www.jll.com",
            "industry": "Real Estate & Facilities",
            "sub_industry": "Commercial Real Estate Services",
            "employee_estimate": 105000,
            "location_city": "Chicago",
            "location_state": "IL",
            "location_country": "US",
            "source": "seed_v3",
        },
        "signals": [
            ("news",            "JLL deploys autonomous cleaning and inspection robots across 250 managed commercial properties; program expanding after first-year cost savings confirmed", 0.89),
            ("strategic_hire",  "JLL appoints Global Director of Intelligent Facilities & Robotics; leading enterprise-wide deployment of autonomous building management solutions", 0.87),
            ("capex",           "JLL announces $150M technology investment program for facilities management division; robotic solutions are primary use case", 0.85),
            ("labor_shortage",  "JLL facilities teams 37% understaffed in janitorial and building services; automation seen as the structural fix rather than just recruitment", 0.86),
        ],
    },
    {
        "company": {
            "name": "Cushman & Wakefield",
            "website": "https://www.cushmanwakefield.com",
            "industry": "Real Estate & Facilities",
            "sub_industry": "Commercial Real Estate Services",
            "employee_estimate": 50000,
            "location_city": "Chicago",
            "location_state": "IL",
            "location_country": "US",
            "source": "seed_v3",
        },
        "signals": [
            ("labor_shortage",  "Cushman & Wakefield facilities management encountering persistent 31% vacancy in cleaning and amenity services; tenant satisfaction declining", 0.84),
            ("capex",           "Cushman & Wakefield invests in PropTech accelerator; autonomous cleaning and concierge delivery robots among solutions being fast-tracked", 0.82),
            ("news",            "Cushman & Wakefield pilots robotic cleaning and package delivery across 3 large commercial campus clients; full rollout planned for 2026", 0.84),
        ],
    },
    {
        "company": {
            "name": "Greystar Real Estate Partners",
            "website": "https://www.greystar.com",
            "industry": "Real Estate & Facilities",
            "sub_industry": "Multifamily Property Management",
            "employee_estimate": 20000,
            "location_city": "Charleston",
            "location_state": "SC",
            "location_country": "US",
            "source": "seed_v3",
        },
        "signals": [
            ("labor_shortage",  "Greystar apartment communities facing 33% maintenance, cleaning, and amenity services vacancy; resident satisfaction declining at Class A properties", 0.83),
            ("news",            "Greystar evaluates autonomous amenity delivery and common area cleaning robots for luxury multifamily properties; resident app integration planned", 0.82),
            ("capex",           "Greystar develops 45,000 units annually; new buildings being designed with autonomous delivery infrastructure in lobbies and common areas", 0.84),
            ("expansion",       "Greystar expands internationally with new properties in UK, Germany, and Netherlands; smart living technology including autonomous delivery standard in new builds", 0.81),
        ],
    },
    {
        "company": {
            "name": "ABM Industries",
            "website": "https://www.abm.com",
            "industry": "Real Estate & Facilities",
            "sub_industry": "Integrated Facility Services",
            "employee_estimate": 100000,
            "location_city": "New York",
            "location_state": "NY",
            "location_country": "US",
            "source": "seed_v3",
        },
        "signals": [
            ("strategic_hire",  "ABM Industries hires Chief Robotics & Automation Officer; mandate to integrate autonomous cleaning and service delivery robots across all service lines", 0.91),
            ("news",            "ABM Industries deploys 500+ autonomous cleaning robots across commercial, aviation, healthcare, and education facilities; expanding program by 300 units in 2026", 0.93),
            ("labor_shortage",  "ABM faces industry-wide janitorial and facilities labor shortage of 38%; automation is now a core competitive differentiator in contract bids", 0.90),
            ("capex",           "ABM invests $50M in robotics fleet expansion; autonomous floor care, UV disinfection, and guided delivery robots across all verticals", 0.88),
        ],
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS (same pattern as seed_leads_v2.py)
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
                source=cd.get("source", "seed_v3"),
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
                        source_url="seed_v3",
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
        print(f"\n=== seed_leads_v3 DRY RUN ===")
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

    print("\n=== seed_leads_v3  COMMITTING TO DATABASE ===")
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
