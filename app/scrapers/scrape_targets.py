"""
scrape_targets.py -- Scrape target registry for Ready for Robots.

PURPOSE: Find companies that NEED robots, not companies that BUILD them.

Signals we hunt:
  - Labor pain: companies mass-hiring manual workers in our verticals
  - Budget signals: funding rounds, CapEx, M&A (money to spend)
  - Expansion: new facilities, new locations, renovations (new contracts)
  - Buyer personas: ops/facilities/F&B/housekeeping decision-makers being hired
  - Labor shortage news: companies publicly struggling to staff operations

We are NOT interested in:
  - Robotics engineers / AMR software developers (those are competitors/builders)
  - Companies building their own robots (not buyers)

Richtech Robotics target verticals:
    Hospitality . Logistics . Healthcare . Food Service
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class ScrapeTarget:
    url: str
    label: str
    scraper: str        # job_board | hotel_dir | logistics_dir | rss_feed
    industries: List[str]
    signal_types: List[str]
    cadence: str = "daily"
    active: bool = True
    notes: str = ""


# -- Job Boards: search for LABOR PAIN, not robot engineers ------------------
# JobBoardScraper detects:
#   - High-volume operational roles (pickers, housekeepers, cooks) -> labor_pain
#   - Urgency language (immediate hire, sign-on bonus)             -> labor_shortage
#   - Operations decision-maker hires                              -> strategic_hire

JOB_BOARD_TARGETS: List[ScrapeTarget] = [

    # === LOGISTICS: volume labor pain ===
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=warehouse+associate+picker+packer&l=United+States&sort=date",
        label="Indeed - Warehouse Pickers / Packers (volume hiring)",
        scraper="job_board", cadence="daily",
        industries=["Logistics"],
        signal_types=["labor_pain", "labor_shortage"],
        notes="Mass hiring of pickers/packers = company is drowning in manual labor",
    ),
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=fulfillment+center+associate+distribution&l=United+States&sort=date",
        label="Indeed - Fulfillment Center Associates (volume hiring)",
        scraper="job_board", cadence="daily",
        industries=["Logistics"],
        signal_types=["labor_pain", "labor_shortage"],
    ),
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=freight+handler+dock+worker+material+handler&l=United+States&sort=date",
        label="Indeed - Freight / Dock / Material Handlers",
        scraper="job_board", cadence="daily",
        industries=["Logistics"],
        signal_types=["labor_pain"],
    ),
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=inventory+associate+shipping+receiving&l=United+States&sort=date",
        label="Indeed - Inventory / Shipping / Receiving Associates",
        scraper="job_board", cadence="daily",
        industries=["Logistics"],
        signal_types=["labor_pain"],
    ),
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=VP+Director+operations+distribution+fulfillment&l=United+States&sort=date",
        label="Indeed - VP/Director Operations & Distribution (buyer persona)",
        scraper="job_board", cadence="daily",
        industries=["Logistics"],
        signal_types=["strategic_hire"],
        notes="New ops leader = budget review cycle = robot sales opportunity",
    ),
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=Director+supply+chain+operations+logistics&l=United+States&sort=date",
        label="Indeed - Director Supply Chain Operations (buyer persona)",
        scraper="job_board", cadence="daily",
        industries=["Logistics"],
        signal_types=["strategic_hire"],
    ),

    # === HOSPITALITY: labor pain + buyer personas ===
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=housekeeper+room+attendant+hotel&l=United+States&sort=date",
        label="Indeed - Hotel Housekeepers / Room Attendants (volume hiring)",
        scraper="job_board", cadence="daily",
        industries=["Hospitality"],
        signal_types=["labor_pain", "labor_shortage"],
        notes="Housekeeping = #1 robot use case for hotels",
    ),
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=hotel+bellman+valet+porter+concierge&l=United+States&sort=date",
        label="Indeed - Hotel Guest-Facing Staff (bell/valet/porter)",
        scraper="job_board", cadence="daily",
        industries=["Hospitality"],
        signal_types=["labor_pain"],
        notes="Delivery robots can replace room service + porter runs",
    ),
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=hotel+front+desk+night+audit+multiple+openings&l=United+States&sort=date",
        label="Indeed - Hotel Front Desk Multiple Openings / Night Audit",
        scraper="job_board", cadence="daily",
        industries=["Hospitality"],
        signal_types=["labor_pain", "labor_shortage"],
    ),
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=General+Manager+hotel+resort+property&l=United+States&sort=date",
        label="Indeed - Hotel General Manager (buyer persona)",
        scraper="job_board", cadence="daily",
        industries=["Hospitality"],
        signal_types=["strategic_hire"],
        notes="New GM resets vendor relationships",
    ),
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=VP+Director+rooms+housekeeping+hotel&l=United+States&sort=date",
        label="Indeed - VP/Director Rooms & Housekeeping (buyer persona)",
        scraper="job_board", cadence="daily",
        industries=["Hospitality"],
        signal_types=["strategic_hire"],
    ),

    # === FOOD SERVICE: labor pain + buyer personas ===
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=line+cook+prep+cook+dishwasher+kitchen+staff&l=United+States&sort=date",
        label="Indeed - Line Cook / Dishwasher / Kitchen Staff (volume hiring)",
        scraper="job_board", cadence="daily",
        industries=["Food Service"],
        signal_types=["labor_pain", "labor_shortage"],
        notes="Kitchen labor pain = opportunity for food prep / delivery robots",
    ),
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=restaurant+crew+member+team+member+immediate+hire&l=United+States&sort=date",
        label="Indeed - Restaurant Crew - Urgent / Immediate Hire",
        scraper="job_board", cadence="daily",
        industries=["Food Service"],
        signal_types=["labor_shortage"],
        notes="Urgency language in mass postings = peak labor pain signal",
    ),
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=food+runner+busser+server+multiple+openings&l=United+States&sort=date",
        label="Indeed - Food Runner / Busser / Server Multiple Openings",
        scraper="job_board", cadence="daily",
        industries=["Food Service"],
        signal_types=["labor_pain"],
    ),
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=VP+Director+food+beverage+restaurant+operations&l=United+States&sort=date",
        label="Indeed - VP/Director F&B Operations (buyer persona)",
        scraper="job_board", cadence="daily",
        industries=["Food Service", "Hospitality"],
        signal_types=["strategic_hire"],
        notes="F&B director hire = upcoming ops review, potential robot pilot",
    ),
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=Chief+Operating+Officer+restaurant+chain+multi+unit&l=United+States&sort=date",
        label="Indeed - COO Restaurant Chain (buyer persona)",
        scraper="job_board", cadence="daily",
        industries=["Food Service"],
        signal_types=["strategic_hire"],
    ),

    # === HEALTHCARE: non-clinical labor pain ===
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=environmental+services+EVS+housekeeper+hospital&l=United+States&sort=date",
        label="Indeed - Hospital EVS / Environmental Services (volume hiring)",
        scraper="job_board", cadence="daily",
        industries=["Healthcare"],
        signal_types=["labor_pain", "labor_shortage"],
        notes="Hospital housekeeping = disinfection robot opportunity",
    ),
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=patient+transport+aide+hospital+porter&l=United+States&sort=date",
        label="Indeed - Patient Transport / Hospital Aide",
        scraper="job_board", cadence="daily",
        industries=["Healthcare"],
        signal_types=["labor_pain"],
        notes="Logistics robots can handle internal transport runs",
    ),
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=pharmacy+technician+sterile+processing+hospital&l=United+States&sort=date",
        label="Indeed - Pharmacy Tech / Sterile Processing (volume hiring)",
        scraper="job_board", cadence="daily",
        industries=["Healthcare"],
        signal_types=["labor_pain"],
    ),
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=dietary+aide+food+service+hospital+healthcare&l=United+States&sort=date",
        label="Indeed - Hospital Dietary Aide / Food Service",
        scraper="job_board", cadence="daily",
        industries=["Healthcare"],
        signal_types=["labor_pain"],
    ),
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=VP+Director+facilities+operations+hospital+health+system&l=United+States&sort=date",
        label="Indeed - VP/Director Facilities Hospital (buyer persona)",
        scraper="job_board", cadence="daily",
        industries=["Healthcare"],
        signal_types=["strategic_hire"],
    ),
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=Chief+Operating+Officer+hospital+health+system&l=United+States&sort=date",
        label="Indeed - COO Hospital / Health System (buyer persona)",
        scraper="job_board", cadence="daily",
        industries=["Healthcare"],
        signal_types=["strategic_hire"],
    ),

    # === CROSS-VERTICAL: Operational Efficiency & Automation Intent ===
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=Director+Manager+process+improvement+operational+excellence&l=United+States&sort=date",
        label="Indeed - Director/Manager Process Improvement & Operational Excellence",
        scraper="job_board", cadence="daily",
        industries=["Logistics", "Hospitality", "Food Service", "Healthcare"],
        signal_types=["automation_intent"],
        notes="Companies running efficiency programs are primed for automation budget",
    ),
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=VP+Director+lean+six+sigma+continuous+improvement+operations&l=United+States&sort=date",
        label="Indeed - VP/Director Lean / Six Sigma / Continuous Improvement",
        scraper="job_board", cadence="daily",
        industries=["Logistics", "Food Service", "Healthcare"],
        signal_types=["automation_intent"],
        notes="Lean/CI programs lead directly to automation budget discussions",
    ),
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=VP+Director+guest+experience+service+quality+hotel&l=United+States&sort=date",
        label="Indeed - VP/Director Guest Experience & Service Quality (hospitality)",
        scraper="job_board", cadence="daily",
        industries=["Hospitality"],
        signal_types=["service_consistency"],
        notes="Service consistency mandate → delivery robots, automated housekeeping",
    ),
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=Director+brand+standards+service+consistency+restaurant+chain&l=United+States&sort=date",
        label="Indeed - Director Brand Standards / Service Consistency (restaurant chains)",
        scraper="job_board", cadence="daily",
        industries=["Food Service"],
        signal_types=["service_consistency"],
        notes="Franchise brand ops + consistency → robot ROI argument",
    ),
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=VP+Director+operations+technology+digital+transformation+hospitality&l=United+States&sort=date",
        label="Indeed - VP/Director Operations Technology & Digital Transformation",
        scraper="job_board", cadence="daily",
        industries=["Hospitality", "Food Service", "Logistics"],
        signal_types=["automation_intent"],
        notes="Ops tech lead hire = active budget for technology integration",
    ),
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=systems+integration+manager+WMS+ERP+warehouse+operations&l=United+States&sort=date",
        label="Indeed - Systems Integration Manager (WMS / ERP) — equipment integration",
        scraper="job_board", cadence="daily",
        industries=["Logistics"],
        signal_types=["equipment_integration"],
        notes="Companies integrating WMS/ERP are infrastructure-ready for robots",
    ),

    # === SIMPLYHIRED: broader scraping reach beyond Indeed ===
    ScrapeTarget(
        url="https://www.simplyhired.com/search?q=housekeeper+room+attendant+hotel&l=United+States",
        label="SimplyHired - Hotel Housekeepers (volume hiring)",
        scraper="job_board", cadence="daily",
        industries=["Hospitality"],
        signal_types=["labor_pain", "labor_shortage"],
    ),
    ScrapeTarget(
        url="https://www.simplyhired.com/search?q=warehouse+associate+fulfillment+picker+packer&l=United+States",
        label="SimplyHired - Warehouse Associates / Fulfillment Pickers",
        scraper="job_board", cadence="daily",
        industries=["Logistics"],
        signal_types=["labor_pain", "labor_shortage"],
    ),
    ScrapeTarget(
        url="https://www.simplyhired.com/search?q=line+cook+prep+cook+dishwasher+restaurant&l=United+States",
        label="SimplyHired - Kitchen Staff (volume hiring)",
        scraper="job_board", cadence="daily",
        industries=["Food Service"],
        signal_types=["labor_pain", "labor_shortage"],
    ),
    ScrapeTarget(
        url="https://www.simplyhired.com/search?q=environmental+services+hospital+EVS+dietary+aide&l=United+States",
        label="SimplyHired - Hospital EVS / Dietary (volume hiring)",
        scraper="job_board", cadence="daily",
        industries=["Healthcare"],
        signal_types=["labor_pain", "labor_shortage"],
    ),
    ScrapeTarget(
        url="https://www.simplyhired.com/search?q=VP+Director+operations+hospitality+hotel+resort&l=United+States",
        label="SimplyHired - VP/Director Hotel Operations (buyer persona)",
        scraper="job_board", cadence="daily",
        industries=["Hospitality"],
        signal_types=["strategic_hire"],
    ),
    ScrapeTarget(
        url="https://www.simplyhired.com/search?q=VP+Director+supply+chain+operations+distribution&l=United+States",
        label="SimplyHired - VP/Director Supply Chain & Distribution (buyer persona)",
        scraper="job_board", cadence="daily",
        industries=["Logistics"],
        signal_types=["strategic_hire"],
    ),
    ScrapeTarget(
        url="https://www.simplyhired.com/search?q=dining+services+director+senior+living+assisted+living&l=United+States",
        label="SimplyHired - Dining Services Director Senior Living (buyer persona)",
        scraper="job_board", cadence="daily",
        industries=["Healthcare"],
        signal_types=["strategic_hire", "labor_pain"],
        notes="Senior living dining = delivery robot + kitchen automation sweet spot",
    ),
    ScrapeTarget(
        url="https://www.simplyhired.com/search?q=caregiver+home+health+aide+senior+living+immediate+hire&l=United+States",
        label="SimplyHired - Caregiver / Home Health Aide Urgent Hire",
        scraper="job_board", cadence="daily",
        industries=["Healthcare"],
        signal_types=["labor_shortage", "labor_pain"],
        notes="Senior care labor shortage = companion and assistance robot opportunity",
    ),
    ScrapeTarget(
        url="https://www.simplyhired.com/search?q=food+service+worker+cafeteria+cook+hospital+corporate&l=United+States",
        label="SimplyHired - Institutional Food Service Workers (hospitals / corporate)",
        scraper="job_board", cadence="daily",
        industries=["Food Service", "Healthcare"],
        signal_types=["labor_pain"],
    ),
    ScrapeTarget(
        url="https://www.simplyhired.com/search?q=Director+Manager+automation+operations+food+service+restaurant&l=United+States",
        label="SimplyHired - Director/Manager Automation Food Service (buyer persona)",
        scraper="job_board", cadence="daily",
        industries=["Food Service"],
        signal_types=["automation_intent", "strategic_hire"],
    ),
]


# -- Hotel & Hospitality Directories -----------------------------------------

HOTEL_DIRECTORY_TARGETS: List[ScrapeTarget] = [
    ScrapeTarget(
        url="https://www.yellowpages.com/search?search_terms=hotel+resort&geo_location_terms=Las+Vegas+NV",
        label="Yellow Pages - Hotels Las Vegas, NV",
        scraper="hotel_dir", cadence="weekly",
        industries=["Hospitality"], signal_types=["hospitality_fit"],
        notes="Priority market: highest hotel density + labor cost pressure",
    ),
    ScrapeTarget(
        url="https://www.yellowpages.com/search?search_terms=hotel+resort&geo_location_terms=New+York+NY",
        label="Yellow Pages - Hotels New York, NY",
        scraper="hotel_dir", cadence="weekly",
        industries=["Hospitality"], signal_types=["hospitality_fit"],
    ),
    ScrapeTarget(
        url="https://www.yellowpages.com/search?search_terms=hotel+resort&geo_location_terms=Los+Angeles+CA",
        label="Yellow Pages - Hotels Los Angeles, CA",
        scraper="hotel_dir", cadence="weekly",
        industries=["Hospitality"], signal_types=["hospitality_fit"],
    ),
    ScrapeTarget(
        url="https://www.yellowpages.com/search?search_terms=hotel+resort&geo_location_terms=Orlando+FL",
        label="Yellow Pages - Hotels Orlando, FL",
        scraper="hotel_dir", cadence="weekly",
        industries=["Hospitality"], signal_types=["hospitality_fit"],
        notes="High-volume tourism + convention market",
    ),
    ScrapeTarget(
        url="https://www.yellowpages.com/search?search_terms=hotel+resort&geo_location_terms=Chicago+IL",
        label="Yellow Pages - Hotels Chicago, IL",
        scraper="hotel_dir", cadence="weekly",
        industries=["Hospitality"], signal_types=["hospitality_fit"],
    ),
    ScrapeTarget(
        url="https://www.yellowpages.com/search?search_terms=hotel+resort&geo_location_terms=Houston+TX",
        label="Yellow Pages - Hotels Houston, TX",
        scraper="hotel_dir", cadence="weekly",
        industries=["Hospitality"], signal_types=["hospitality_fit"],
    ),
    ScrapeTarget(
        url="https://www.yellowpages.com/search?search_terms=hotel+resort&geo_location_terms=Dallas+TX",
        label="Yellow Pages - Hotels Dallas, TX",
        scraper="hotel_dir", cadence="weekly",
        industries=["Hospitality"], signal_types=["hospitality_fit"],
    ),
    ScrapeTarget(
        url="https://www.yellowpages.com/search?search_terms=hotel+resort&geo_location_terms=Miami+FL",
        label="Yellow Pages - Hotels Miami, FL",
        scraper="hotel_dir", cadence="weekly",
        industries=["Hospitality"], signal_types=["hospitality_fit"],
    ),
    ScrapeTarget(
        url="https://www.yellowpages.com/search?search_terms=hotel+resort&geo_location_terms=Atlanta+GA",
        label="Yellow Pages - Hotels Atlanta, GA",
        scraper="hotel_dir", cadence="weekly",
        industries=["Hospitality"], signal_types=["hospitality_fit"],
    ),
    ScrapeTarget(
        url="https://www.yellowpages.com/search?search_terms=hotel+resort&geo_location_terms=Seattle+WA",
        label="Yellow Pages - Hotels Seattle, WA",
        scraper="hotel_dir", cadence="weekly",
        industries=["Hospitality"], signal_types=["hospitality_fit"],
    ),
    ScrapeTarget(
        url="https://www.yellowpages.com/search?search_terms=restaurant+chain+fast+food&geo_location_terms=United+States",
        label="Yellow Pages - Restaurant Chains (US)",
        scraper="hotel_dir", cadence="weekly",
        industries=["Food Service"], signal_types=["hospitality_fit"],
    ),
    ScrapeTarget(
        url="https://www.yellowpages.com/search?search_terms=hotel+resort&geo_location_terms=Nashville+TN",
        label="Yellow Pages - Hotels Nashville, TN",
        scraper="hotel_dir", cadence="weekly",
        industries=["Hospitality"], signal_types=["hospitality_fit"],
        notes="Growing convention + music tourism market",
    ),
    ScrapeTarget(
        url="https://www.yellowpages.com/search?search_terms=hotel+resort&geo_location_terms=Phoenix+AZ",
        label="Yellow Pages - Hotels Phoenix, AZ",
        scraper="hotel_dir", cadence="weekly",
        industries=["Hospitality"], signal_types=["hospitality_fit"],
    ),
    ScrapeTarget(
        url="https://www.yellowpages.com/search?search_terms=hotel+resort&geo_location_terms=San+Francisco+CA",
        label="Yellow Pages - Hotels San Francisco, CA",
        scraper="hotel_dir", cadence="weekly",
        industries=["Hospitality"], signal_types=["hospitality_fit"],
        notes="High labor cost market; strong robot ROI",
    ),
    ScrapeTarget(
        url="https://www.yellowpages.com/search?search_terms=hotel+resort&geo_location_terms=Denver+CO",
        label="Yellow Pages - Hotels Denver, CO",
        scraper="hotel_dir", cadence="weekly",
        industries=["Hospitality"], signal_types=["hospitality_fit"],
    ),
    ScrapeTarget(
        url="https://www.yellowpages.com/search?search_terms=hotel+resort&geo_location_terms=Boston+MA",
        label="Yellow Pages - Hotels Boston, MA",
        scraper="hotel_dir", cadence="weekly",
        industries=["Hospitality"], signal_types=["hospitality_fit"],
    ),
    ScrapeTarget(
        url="https://www.yellowpages.com/search?search_terms=hotel+resort&geo_location_terms=Austin+TX",
        label="Yellow Pages - Hotels Austin, TX",
        scraper="hotel_dir", cadence="weekly",
        industries=["Hospitality"], signal_types=["hospitality_fit"],
    ),
    ScrapeTarget(
        url="https://www.yellowpages.com/search?search_terms=senior+living+assisted+living+community&geo_location_terms=United+States",
        label="Yellow Pages - Senior Living Communities (US)",
        scraper="hotel_dir", cadence="weekly",
        industries=["Healthcare"], signal_types=["hospitality_fit", "labor_shortage"],
        notes="Senior living = companion robot + delivery robot sweet spot",
    ),
    ScrapeTarget(
        url="https://www.yellowpages.com/search?search_terms=nursing+home+skilled+nursing+facility&geo_location_terms=United+States",
        label="Yellow Pages - Skilled Nursing Facilities (US)",
        scraper="hotel_dir", cadence="weekly",
        industries=["Healthcare"], signal_types=["hospitality_fit", "labor_shortage"],
        notes="SNFs: dietary, housekeeping, and patient transport = 3 robot use cases",
    ),
]


# -- Logistics & Healthcare Directories --------------------------------------

LOGISTICS_DIRECTORY_TARGETS: List[ScrapeTarget] = [
    ScrapeTarget(
        url="https://www.yellowpages.com/search?search_terms=warehouse+distribution+center&geo_location_terms=United+States",
        label="Yellow Pages - Warehouses / Distribution Centers",
        scraper="logistics_dir", cadence="weekly",
        industries=["Logistics"], signal_types=["expansion", "capex"],
    ),
    ScrapeTarget(
        url="https://www.yellowpages.com/search?search_terms=third+party+logistics+3PL+fulfillment&geo_location_terms=United+States",
        label="Yellow Pages - 3PL / Fulfillment Centers",
        scraper="logistics_dir", cadence="weekly",
        industries=["Logistics"], signal_types=["expansion"],
    ),
    ScrapeTarget(
        url="https://www.yellowpages.com/search?search_terms=cold+storage+frozen+warehouse&geo_location_terms=United+States",
        label="Yellow Pages - Cold Storage / Frozen Warehouses",
        scraper="logistics_dir", cadence="weekly",
        industries=["Logistics", "Food Service"], signal_types=["capex", "expansion"],
        notes="Cold-chain = hard to staff = strong robot fit",
    ),
    ScrapeTarget(
        url="https://www.yellowpages.com/search?search_terms=hospital+health+system&geo_location_terms=United+States",
        label="Yellow Pages - Hospitals & Health Systems",
        scraper="logistics_dir", cadence="weekly",
        industries=["Healthcare"], signal_types=["expansion", "capex"],
    ),
    ScrapeTarget(
        url="https://www.yellowpages.com/search?search_terms=food+distribution+food+service+distributor&geo_location_terms=United+States",
        label="Yellow Pages - Food Service Distributors",
        scraper="logistics_dir", cadence="weekly",
        industries=["Logistics", "Food Service"], signal_types=["expansion", "capex"],
        notes="Food distributors = cold chain + high-labor operations",
    ),
    ScrapeTarget(
        url="https://www.yellowpages.com/search?search_terms=freight+forwarder+customs+broker+logistics&geo_location_terms=United+States",
        label="Yellow Pages - Freight Forwarders & Brokers",
        scraper="logistics_dir", cadence="weekly",
        industries=["Logistics"], signal_types=["expansion"],
    ),
    ScrapeTarget(
        url="https://www.yellowpages.com/search?search_terms=grocery+distribution+supermarket+warehouse&geo_location_terms=United+States",
        label="Yellow Pages - Grocery Distribution Centers",
        scraper="logistics_dir", cadence="weekly",
        industries=["Logistics", "Food Service"], signal_types=["capex", "expansion"],
        notes="Grocery DCs: high SKU count + demanding throughput = strong robot fit",
    ),
]


# -- Trade RSS Feeds ---------------------------------------------------------

RSS_FEED_TARGETS: List[ScrapeTarget] = [
    ScrapeTarget(
        url="https://www.supplychaindive.com/feeds/news/",
        label="Supply Chain Dive",
        scraper="rss_feed", cadence="daily",
        industries=["Logistics"],
        signal_types=["funding_round", "expansion", "capex", "ma_activity"],
    ),
    ScrapeTarget(
        url="https://www.mhlnews.com/rss/all",
        label="MH&L News (Material Handling & Logistics)",
        scraper="rss_feed", cadence="daily",
        industries=["Logistics"],
        signal_types=["capex", "expansion", "funding_round"],
    ),
    ScrapeTarget(
        url="https://www.dcvelocity.com/rss/",
        label="DC Velocity",
        scraper="rss_feed", cadence="daily",
        industries=["Logistics"],
        signal_types=["expansion", "capex"],
    ),
    ScrapeTarget(
        url="https://www.freightwaves.com/news/feed",
        label="FreightWaves",
        scraper="rss_feed", cadence="daily",
        industries=["Logistics"],
        signal_types=["funding_round", "ma_activity", "expansion"],
    ),
    ScrapeTarget(
        url="https://www.logisticsmgmt.com/rss/news.xml",
        label="Logistics Management",
        scraper="rss_feed", cadence="daily",
        industries=["Logistics"],
        signal_types=["expansion", "capex", "strategic_hire"],
    ),
    ScrapeTarget(
        url="https://www.hotelmanagement.net/rss.xml",
        label="Hotel Management Magazine",
        scraper="rss_feed", cadence="daily",
        industries=["Hospitality"],
        signal_types=["funding_round", "expansion", "capex", "ma_activity"],
    ),
    ScrapeTarget(
        url="https://hospitalitytech.com/rss.xml",
        label="Hospitality Technology",
        scraper="rss_feed", cadence="daily",
        industries=["Hospitality"],
        signal_types=["capex", "strategic_hire", "expansion"],
        notes="Tracks technology investment decisions at hotel brands",
    ),
    ScrapeTarget(
        url="https://skift.com/feed/",
        label="Skift (Travel & Hospitality News)",
        scraper="rss_feed", cadence="daily",
        industries=["Hospitality"],
        signal_types=["funding_round", "ma_activity", "expansion"],
    ),
    ScrapeTarget(
        url="https://www.fooddive.com/feeds/news/",
        label="Food Dive",
        scraper="rss_feed", cadence="daily",
        industries=["Food Service"],
        signal_types=["funding_round", "expansion", "capex", "ma_activity"],
    ),
    ScrapeTarget(
        url="https://www.qsrmagazine.com/rss.xml",
        label="QSR Magazine",
        scraper="rss_feed", cadence="daily",
        industries=["Food Service"],
        signal_types=["expansion", "funding_round", "capex"],
        notes="QSR chains: high unit count, high labor cost pressure",
    ),
    ScrapeTarget(
        url="https://www.nrn.com/rss.xml",
        label="Nation's Restaurant News",
        scraper="rss_feed", cadence="daily",
        industries=["Food Service"],
        signal_types=["funding_round", "ma_activity", "expansion"],
    ),
    ScrapeTarget(
        url="https://modernrestaurantmanagement.com/feed/",
        label="Modern Restaurant Management",
        scraper="rss_feed", cadence="daily",
        industries=["Food Service"],
        signal_types=["expansion", "strategic_hire", "capex"],
    ),
    ScrapeTarget(
        url="https://www.modernhealthcare.com/section/feed",
        label="Modern Healthcare",
        scraper="rss_feed", cadence="daily",
        industries=["Healthcare"],
        signal_types=["funding_round", "expansion", "capex", "ma_activity"],
    ),
    ScrapeTarget(
        url="https://www.beckershospitalreview.com/feed",
        label="Becker's Hospital Review",
        scraper="rss_feed", cadence="daily",
        industries=["Healthcare"],
        signal_types=["funding_round", "expansion", "ma_activity"],
        notes="Strong M&A / consolidation coverage = budget unlock signals",
    ),
    ScrapeTarget(
        url="https://www.healthcareitnews.com/news/feed",
        label="Healthcare IT News",
        scraper="rss_feed", cadence="daily",
        industries=["Healthcare"],
        signal_types=["capex", "strategic_hire", "expansion"],
    ),
    ScrapeTarget(
        url="https://www.businesswire.com/rss/home/?rss=G22",
        label="BusinessWire - Technology Press Releases",
        scraper="rss_feed", cadence="daily",
        industries=["Logistics", "Hospitality", "Healthcare", "Food Service"],
        signal_types=["funding_round", "ma_activity", "expansion"],
        notes="Official PRs = confirmed budget events",
    ),
    ScrapeTarget(
        url="https://feeds.prnewswire.com/rnews/20130101/automation-robotics",
        label="PR Newswire - Automation & Robotics Announcements",
        scraper="rss_feed", cadence="daily",
        industries=["Logistics", "Hospitality", "Healthcare", "Food Service"],
        signal_types=["funding_round", "ma_activity", "capex", "expansion"],
    ),
    ScrapeTarget(
        url="https://techcrunch.com/tag/robotics/feed/",
        label="TechCrunch - Robotics (funding & deals)",
        scraper="rss_feed", cadence="daily",
        industries=["Logistics", "Hospitality", "Healthcare", "Food Service"],
        signal_types=["funding_round", "ma_activity"],
        notes="Tracks who is getting funded to buy / deploy robots",
    ),
    ScrapeTarget(
        url="https://www.restaurantbusinessonline.com/feed",
        label="Restaurant Business Online",
        scraper="rss_feed", cadence="daily",
        industries=["Food Service"],
        signal_types=["expansion", "capex", "automation_intent"],
        notes="Chain operator coverage: automation pilots, labor costs, brand standards",
    ),
    ScrapeTarget(
        url="https://www.facilitiesnet.com/rss/all.rss",
        label="Facilities Net (facility operations & technology)",
        scraper="rss_feed", cadence="daily",
        industries=["Healthcare", "Hospitality"],
        signal_types=["capex", "equipment_integration", "automation_intent"],
        notes="Facility investment signals: cleaning tech, automation, building systems",
    ),
    ScrapeTarget(
        url="https://chainstoreage.com/feed",
        label="Chain Store Age (multi-unit retail & food service ops)",
        scraper="rss_feed", cadence="daily",
        industries=["Food Service", "Logistics"],
        signal_types=["expansion", "capex", "service_consistency"],
        notes="Multi-unit operators: franchise expansion, technology investment, brand ops",
    ),
    # === ADDITIONAL RSS FEEDS: senior living, grocery, hospitality tech ===
    ScrapeTarget(
        url="https://www.mcknights.com/feed/",
        label="McKnight's Long-Term Care News",
        scraper="rss_feed", cadence="daily",
        industries=["Healthcare"],
        signal_types=["labor_shortage", "capex", "expansion", "strategic_hire"],
        notes="Top trade pub for skilled nursing + senior living: labor crisis + tech news",
    ),
    ScrapeTarget(
        url="https://www.seniorhousingnews.com/feed/",
        label="Senior Housing News",
        scraper="rss_feed", cadence="daily",
        industries=["Healthcare"],
        signal_types=["funding_round", "expansion", "ma_activity", "capex"],
        notes="Senior living M&A + new development = robot sales opportunities",
    ),
    ScrapeTarget(
        url="https://www.supermarketnews.com/rss/news",
        label="Supermarket News (Grocery Retail & Distribution)",
        scraper="rss_feed", cadence="daily",
        industries=["Logistics", "Food Service"],
        signal_types=["expansion", "capex", "automation_intent", "funding_round"],
        notes="Grocery DCs + store operations: automation investment coverage",
    ),
    ScrapeTarget(
        url="https://progressivegrocer.com/rss.xml",
        label="Progressive Grocer (Grocery Operations & Technology)",
        scraper="rss_feed", cadence="daily",
        industries=["Logistics", "Food Service"],
        signal_types=["capex", "expansion", "automation_intent"],
    ),
    ScrapeTarget(
        url="https://www.hospitalitynet.org/rss/4000062.xml",
        label="Hospitalitynet (Global Hotel Industry News)",
        scraper="rss_feed", cadence="daily",
        industries=["Hospitality"],
        signal_types=["funding_round", "expansion", "strategic_hire", "capex"],
        notes="International hotel brand investment + technology news",
    ),
    ScrapeTarget(
        url="https://www.hotelnewsresource.com/rss.xml",
        label="Hotel News Resource (Hotel Industry Operations)",
        scraper="rss_feed", cadence="daily",
        industries=["Hospitality"],
        signal_types=["expansion", "capex", "strategic_hire"],
    ),
    ScrapeTarget(
        url="https://www.modernhealthcare.com/section/facilities-management/feed",
        label="Modern Healthcare - Facilities Management",
        scraper="rss_feed", cadence="daily",
        industries=["Healthcare"],
        signal_types=["capex", "expansion", "automation_intent"],
        notes="Hospital facilities investment = disinfection + logistics robot opportunity",
    ),
    ScrapeTarget(
        url="https://www.industryweek.com/rss/all",
        label="Industry Week (Manufacturing & Operations)",
        scraper="rss_feed", cadence="daily",
        industries=["Logistics"],
        signal_types=["capex", "automation_intent", "expansion"],
        notes="Industrial operations: automation investment, operational efficiency programs",
    ),
    ScrapeTarget(
        url="https://www.qsrweb.com/rss/news/",
        label="QSRWeb (Quick Service Restaurant Technology)",
        scraper="rss_feed", cadence="daily",
        industries=["Food Service"],
        signal_types=["capex", "automation_intent", "equipment_integration"],
        notes="QSR tech: robot deployments, automated kitchen equipment, digital transformation",
    ),
    ScrapeTarget(
        url="https://www.restauranttechnology.news/feed/",
        label="Restaurant Technology News",
        scraper="rss_feed", cadence="daily",
        industries=["Food Service"],
        signal_types=["automation_intent", "capex", "equipment_integration"],
        notes="Focused on food service technology adoption and robot deployments",
    ),
    # ── NEW: Additional high-value RSS feeds added 2026 ─────────────────────
    ScrapeTarget(
        url="https://www.warehousingstorage.com/feed/",
        label="Warehousing & Storage (Operations & Tech)",
        scraper="rss_feed", cadence="daily",
        industries=["Logistics"],
        signal_types=["expansion", "capex", "automation_intent"],
        notes="Warehousing ops coverage — facility investment, tech upgrades",
    ),
    ScrapeTarget(
        url="https://www.inboundlogistics.com/rss/",
        label="Inbound Logistics",
        scraper="rss_feed", cadence="daily",
        industries=["Logistics"],
        signal_types=["capex", "expansion", "automation_intent"],
        notes="3PL and supply chain operations — sourcing new logistics providers",
    ),
    ScrapeTarget(
        url="https://www.foodlogistics.com/rss/all",
        label="Food Logistics (Cold Chain & Food Distribution)",
        scraper="rss_feed", cadence="daily",
        industries=["Logistics", "Food Service"],
        signal_types=["expansion", "capex", "automation_intent"],
        notes="Cold chain + food distribution tech — AGV/AMR opportunities",
    ),
    ScrapeTarget(
        url="https://www.ttnews.com/rss.xml",
        label="Transport Topics (Trucking & Fleet)",
        scraper="rss_feed", cadence="daily",
        industries=["Logistics"],
        signal_types=["expansion", "funding_round", "ma_activity"],
        notes="Fleet & trucking news — dock automation, new terminal construction",
    ),
    ScrapeTarget(
        url="https://www.ajot.com/rss/",
        label="American Journal of Transportation",
        scraper="rss_feed", cadence="daily",
        industries=["Logistics"],
        signal_types=["expansion", "capex", "ma_activity"],
    ),
    ScrapeTarget(
        url="https://www.automationworld.com/home/rss",
        label="Automation World (Industrial Automation)",
        scraper="rss_feed", cadence="daily",
        industries=["Logistics", "Healthcare", "Food Service"],
        signal_types=["automation_intent", "capex", "equipment_integration"],
        notes="Direct buyer-intent: companies announcing automation deployments",
    ),
    ScrapeTarget(
        url="https://www.materialshandling247.com/rss/news",
        label="Materials Handling 247 (MH&L)",
        scraper="rss_feed", cadence="daily",
        industries=["Logistics"],
        signal_types=["capex", "expansion", "automation_intent"],
    ),
    ScrapeTarget(
        url="https://www.therobotreport.com/feed/",
        label="The Robot Report (Robotics Industry News)",
        scraper="rss_feed", cadence="daily",
        industries=["Logistics", "Hospitality", "Healthcare", "Food Service"],
        signal_types=["automation_intent", "capex", "funding_round"],
        notes="Who is deploying or evaluating robots — direct buyer signals",
    ),
    ScrapeTarget(
        url="https://www.foodservicenews.com/feed/",
        label="Food Service News",
        scraper="rss_feed", cadence="daily",
        industries=["Food Service"],
        signal_types=["expansion", "capex", "labor_shortage"],
    ),
    ScrapeTarget(
        url="https://www.fohbo.com/feed/",
        label="FOHBo (Front-of-House Restaurant Operations)",
        scraper="rss_feed", cadence="daily",
        industries=["Food Service"],
        signal_types=["automation_intent", "labor_shortage", "capex"],
        notes="Restaurant labor + front-of-house tech deployment signals",
    ),
    ScrapeTarget(
        url="https://www.hotelsmag.com/feed/",
        label="Hotels Magazine (Global Hotel Brand News)",
        scraper="rss_feed", cadence="daily",
        industries=["Hospitality"],
        signal_types=["expansion", "funding_round", "ma_activity", "capex"],
    ),
    ScrapeTarget(
        url="https://www.hoteliermiddleeast.com/rss",
        label="Hotelier Middle East (International Expansion)",
        scraper="rss_feed", cadence="daily",
        industries=["Hospitality"],
        signal_types=["expansion", "capex", "strategic_hire"],
        notes="International hotel expansion — new properties often open-spec for robots",
    ),
    ScrapeTarget(
        url="https://www.lodgingmagazine.com/feed/",
        label="Lodging Magazine",
        scraper="rss_feed", cadence="daily",
        industries=["Hospitality"],
        signal_types=["capex", "expansion", "strategic_hire"],
    ),
    ScrapeTarget(
        url="https://www.healthcaredive.com/feeds/news/",
        label="Healthcare Dive",
        scraper="rss_feed", cadence="daily",
        industries=["Healthcare"],
        signal_types=["funding_round", "ma_activity", "expansion", "capex"],
        notes="Health system consolidation + new facility investment coverage",
    ),
    ScrapeTarget(
        url="https://www.hfmmagazine.com/rss",
        label="Health Facilities Management",
        scraper="rss_feed", cadence="daily",
        industries=["Healthcare"],
        signal_types=["capex", "expansion", "equipment_integration"],
        notes="Direct capital project signals: hospital renovations, new builds, equipment install",
    ),
    ScrapeTarget(
        url="https://www.providencejournalnews.com/feeds/robots.xml",
        label="Prologis Newsroom (via Google News)",
        scraper="rss_feed", cadence="daily",
        industries=["Logistics"],
        signal_types=["expansion", "capex"],
        notes="Prologis = largest industrial REIT; new facility = new robot sale opportunity",
    ),
    ScrapeTarget(
        url="https://www.multifamilyexecutive.com/rss.xml",
        label="Multifamily Executive (Property Management)",
        scraper="rss_feed", cadence="daily",
        industries=["Hospitality"],
        signal_types=["capex", "expansion", "strategic_hire"],
        notes="Property management tech investment often crosses into hospitality",
    ),
    ScrapeTarget(
        url="https://www.pymnts.com/category/restaurant/feed/",
        label="PYMNTS - Restaurant & Payments Intel",
        scraper="rss_feed", cadence="daily",
        industries=["Food Service"],
        signal_types=["funding_round", "capex", "automation_intent"],
        notes="FinTech + restaurant convergence: digital transformation, investment signals",
    ),
    ScrapeTarget(
        url="https://www.cnbc.com/id/10001148/device/rss/rss.html",
        label="CNBC - Retail & Consumer (chain operations)",
        scraper="rss_feed", cadence="daily",
        industries=["Logistics", "Food Service", "Hospitality"],
        signal_types=["funding_round", "expansion", "ma_activity"],
        notes="Mainstream financial news covers big expansion / M&A for target accounts",
    ),
    ScrapeTarget(
        url="https://globenewswire.com/RssFeed/organization/robotics",
        label="GlobeNewswire - Robotics & Automation",
        scraper="rss_feed", cadence="daily",
        industries=["Logistics", "Hospitality", "Healthcare", "Food Service"],
        signal_types=["funding_round", "capex", "automation_intent"],
        notes="Official press releases from companies deploying or evaluating robots",
    ),
]


# -- Google News Queries: buyer-intent only ----------------------------------
# Hunting for: pain, budget, expansion, new decision-makers.
# NOT hunting for: robotics engineers, robot builders.

NEWS_QUERIES = [

    # === Labor Pain & Staffing Shortage ===
    {"query": "hotel labor shortage housekeeping staff 2025",                "industries": ["Hospitality"],                  "signal_types": ["labor_shortage"]},
    {"query": "restaurant worker shortage staffing crisis 2025",             "industries": ["Food Service"],                 "signal_types": ["labor_shortage"]},
    {"query": "warehouse staffing shortage fulfillment workers",             "industries": ["Logistics"],                    "signal_types": ["labor_shortage"]},
    {"query": "hospital staffing shortage EVS housekeeping aides",           "industries": ["Healthcare"],                   "signal_types": ["labor_shortage"]},
    {"query": "hotel rising labor costs wages housekeeping pressure",        "industries": ["Hospitality"],                  "signal_types": ["labor_shortage", "capex"]},
    {"query": "restaurant minimum wage increase labor cost operators",       "industries": ["Food Service"],                 "signal_types": ["labor_shortage", "capex"]},
    {"query": "supply chain labor shortage driver worker 2025",              "industries": ["Logistics"],                    "signal_types": ["labor_shortage"]},
    {"query": "fast food high turnover staff retention crisis",              "industries": ["Food Service"],                 "signal_types": ["labor_shortage"]},

    # === Funding Rounds (companies with money to spend) ===
    {"query": "hotel brand funding investment capital raise 2025",           "industries": ["Hospitality"],                  "signal_types": ["funding_round"]},
    {"query": "restaurant chain funding series growth 2025",                 "industries": ["Food Service"],                 "signal_types": ["funding_round"]},
    {"query": "logistics company funding investment supply chain",           "industries": ["Logistics"],                    "signal_types": ["funding_round"]},
    {"query": "hospital health system capital raise bond investment",        "industries": ["Healthcare"],                   "signal_types": ["funding_round"]},
    {"query": "QSR quick service restaurant venture growth funding",         "industries": ["Food Service"],                 "signal_types": ["funding_round"]},

    # === M&A Activity (budget unlock + new leadership) ===
    {"query": "hotel chain acquisition merger brand 2025",                   "industries": ["Hospitality"],                  "signal_types": ["ma_activity"]},
    {"query": "restaurant chain acquired merger new owner operator",         "industries": ["Food Service"],                 "signal_types": ["ma_activity"]},
    {"query": "logistics 3PL company acquisition merger deal",               "industries": ["Logistics"],                    "signal_types": ["ma_activity"]},
    {"query": "hospital health system merger acquisition consolidation",     "industries": ["Healthcare"],                   "signal_types": ["ma_activity"]},

    # === Expansion & New Facilities (new locations = new robot sales) ===
    {"query": "hotel resort new property opening 2025 2026 grand opening",  "industries": ["Hospitality"],                  "signal_types": ["expansion"]},
    {"query": "new distribution center warehouse opening groundbreaking",   "industries": ["Logistics"],                    "signal_types": ["expansion", "capex"]},
    {"query": "restaurant chain new locations expansion opening sites",     "industries": ["Food Service"],                 "signal_types": ["expansion"]},
    {"query": "hospital new campus facility construction expansion",        "industries": ["Healthcare"],                   "signal_types": ["expansion", "capex"]},
    {"query": "hotel renovation investment upgrade rooms guest",            "industries": ["Hospitality"],                  "signal_types": ["capex"]},
    {"query": "fulfillment center expansion new warehouse facility 2025",   "industries": ["Logistics"],                    "signal_types": ["expansion", "capex"]},

    # === CapEx / Technology Budget ===
    {"query": "hotel technology upgrade investment guest experience",        "industries": ["Hospitality"],                  "signal_types": ["capex"]},
    {"query": "hospital technology capital expenditure clinical operations", "industries": ["Healthcare"],                   "signal_types": ["capex"]},
    {"query": "distribution center modernize upgrade technology investment", "industries": ["Logistics"],                    "signal_types": ["capex"]},
    {"query": "restaurant technology investment kitchen upgrade 2025",      "industries": ["Food Service"],                 "signal_types": ["capex"]},

    # === Buyer Persona Hires (ops decision-makers joining companies) ===
    {"query": "VP Operations appointed hotel hospitality brand",            "industries": ["Hospitality"],                  "signal_types": ["strategic_hire"]},
    {"query": "General Manager named appointed hotel resort brand 2025",    "industries": ["Hospitality"],                  "signal_types": ["strategic_hire"]},
    {"query": "VP Director Operations logistics distribution appointed",    "industries": ["Logistics"],                    "signal_types": ["strategic_hire"]},
    {"query": "COO Chief Operating Officer restaurant chain appointed",     "industries": ["Food Service"],                 "signal_types": ["strategic_hire"]},
    {"query": "VP Director facilities hospital health system named",        "industries": ["Healthcare"],                   "signal_types": ["strategic_hire"]},
    {"query": "Director food beverage operations appointed hospitality",    "industries": ["Hospitality", "Food Service"],  "signal_types": ["strategic_hire"]},

    # === Named Richtech Target Accounts ===
    {"query": "Marriott International labor staffing operations 2025",       "industries": ["Hospitality"],                  "signal_types": ["labor_shortage", "capex"]},
    {"query": "Hilton Hotels expansion new properties investment 2025",      "industries": ["Hospitality"],                  "signal_types": ["expansion", "capex"]},
    {"query": "DHL supply chain operations expansion new facility",          "industries": ["Logistics"],                    "signal_types": ["capex", "expansion"]},
    {"query": "XPO Logistics new distribution center facility",             "industries": ["Logistics"],                    "signal_types": ["capex", "expansion"]},
    {"query": "Amazon fulfillment new warehouse distribution center 2025",  "industries": ["Logistics"],                    "signal_types": ["expansion"]},
    {"query": "Prologis new property construction distribution",            "industries": ["Logistics"],                    "signal_types": ["expansion", "capex"]},
    {"query": "HCA Healthcare new facility hospital expansion 2025",        "industries": ["Healthcare"],                   "signal_types": ["expansion", "capex"]},
    {"query": "McDonald's Yum Brands Chipotle new locations expansion",     "industries": ["Food Service"],                 "signal_types": ["expansion"]},
    {"query": "Hyatt IHG Wyndham hotel staffing housekeeping challenges",   "industries": ["Hospitality"],                  "signal_types": ["labor_shortage"]},
    {"query": "Ryder J.B. Hunt warehouse operations new contract facility", "industries": ["Logistics"],                    "signal_types": ["expansion", "capex"]},

    # === Automation Intent & Operational Efficiency ===
    {"query": "hotel chain automation pilot program technology rollout 2025",                            "industries": ["Hospitality"],                 "signal_types": ["automation_intent"]},
    {"query": "restaurant chain kitchen automation digital transformation initiative",                   "industries": ["Food Service"],                "signal_types": ["automation_intent"]},
    {"query": "warehouse operational excellence continuous improvement lean program",                    "industries": ["Logistics"],                   "signal_types": ["automation_intent"]},
    {"query": "hospital lean operational efficiency improvement program JCI accreditation",              "industries": ["Healthcare"],                  "signal_types": ["automation_intent"]},
    {"query": "distribution center process improvement automation efficiency initiative",                "industries": ["Logistics"],                   "signal_types": ["automation_intent"]},

    # === Service Consistency & Brand Standards ===
    {"query": "hotel franchise brand standards service consistency guest experience technology",         "industries": ["Hospitality"],                 "signal_types": ["service_consistency"]},
    {"query": "restaurant franchise multi-unit service consistency brand standard operations",           "industries": ["Food Service"],                "signal_types": ["service_consistency"]},
    {"query": "QSR chain food service quality consistency technology investment brand",                  "industries": ["Food Service"],                "signal_types": ["service_consistency", "capex"]},
    {"query": "hotel guest experience service quality technology improvement program",                   "industries": ["Hospitality"],                 "signal_types": ["service_consistency", "capex"]},

    # === Equipment Integration & Tech Readiness ===
    {"query": "warehouse WMS ERP system go-live integration upgrade operations 2025",                   "industries": ["Logistics"],                   "signal_types": ["equipment_integration"]},
    {"query": "hotel property management system PMS technology platform upgrade integration",            "industries": ["Hospitality"],                 "signal_types": ["equipment_integration", "capex"]},
    {"query": "hospital EHR clinical system integration upgrade operational technology",                "industries": ["Healthcare"],                  "signal_types": ["equipment_integration", "capex"]},
    {"query": "restaurant POS technology upgrade system integration chain multi-unit",                  "industries": ["Food Service"],                "signal_types": ["equipment_integration"]},
    {"query": "fulfillment center automation technology integration existing equipment",                "industries": ["Logistics"],                   "signal_types": ["equipment_integration", "automation_intent"]},
]


# -- Master helpers ----------------------------------------------------------

ALL_TARGETS: List[ScrapeTarget] = (
    JOB_BOARD_TARGETS
    + HOTEL_DIRECTORY_TARGETS
    + LOGISTICS_DIRECTORY_TARGETS
    + RSS_FEED_TARGETS
)


def get_targets(
    scraper: str | None = None,
    industry: str | None = None,
    active_only: bool = True,
) -> List[ScrapeTarget]:
    result = ALL_TARGETS
    if active_only:
        result = [t for t in result if t.active]
    if scraper:
        result = [t for t in result if t.scraper == scraper]
    if industry:
        result = [t for t in result if industry in t.industries]
    return result


def get_urls(
    scraper: str | None = None,
    industry: str | None = None,
    active_only: bool = True,
) -> List[str]:
    return [t.url for t in get_targets(scraper, industry, active_only)]


def get_news_queries(
    industry: str | None = None,
    signal_type: str | None = None,
) -> List[str]:
    queries = NEWS_QUERIES
    if industry:
        queries = [q for q in queries if industry in q["industries"]]
    if signal_type:
        queries = [q for q in queries if signal_type in q["signal_types"]]
    return [q["query"] for q in queries]


def summary() -> dict:
    return {
        "job_board":     len(get_targets("job_board")),
        "hotel_dir":     len(get_targets("hotel_dir")),
        "logistics_dir": len(get_targets("logistics_dir")),
        "rss_feed":      len(get_targets("rss_feed")),
        "news_queries":  len(NEWS_QUERIES),
        "total_targets": len(ALL_TARGETS),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(summary(), indent=2))
    print("\nJob board targets (sample):")
    for t in get_targets("job_board")[:4]:
        print(f"  [{t.signal_types[0]}] {t.label}")
    print("\nNews queries -- labor pain:")
    for q in get_news_queries(signal_type="labor_shortage")[:5]:
        print("  ", q)
