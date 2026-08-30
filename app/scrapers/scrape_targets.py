"""
scrape_targets.py -- Scrape target registry for Ready for Robots.

PURPOSE: Find Robot Jobs — human work a robot could be hired to do.

Fields we extract when the posting states them (unknown if not):
  - job function / title
  - compensation (wage range, signing bonus)
  - performance specs (throughput, payload, shift, openings)

Close-out: re-read public evidence. If a robot now performs that work at
that employer, mark the Robot Job filled_by_robot (not a CRM closed-won).

We are NOT interested in:
  - Robotics engineers / AMR software developers (builders)
  - Invented wages or FTE economics

Target verticals:
    Hospitality . Logistics . Healthcare . Food Service . Retail . Manufacturing
"""

from dataclasses import dataclass, field
from typing import List, Optional


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


# -- Job Boards: Robot Jobs (operational work), not robot engineers ----------
# JobBoardScraper detects:
#   - Operational roles → robot_job (title, pay, specs when evidenced)
#   - Close-out when later evidence shows a robot doing that work
#   - Ops decision-maker hires remain strategic_hire (SIGNAL leftover)

JOB_BOARD_TARGETS: List[ScrapeTarget] = [

    # === LOGISTICS: volume labor pain ===
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=warehouse+associate+picker+packer&l=United+States&sort=date",
        label="Indeed - Warehouse Pickers / Packers (volume hiring)",
        scraper="job_board", cadence="daily",
        industries=["Logistics"],
        signal_types=["robot_job"],
        notes="Operational hiring = Robot Job (extract title, pay, specs when stated)",
    ),
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=fulfillment+center+associate+distribution&l=United+States&sort=date",
        label="Indeed - Fulfillment Center Associates (volume hiring)",
        scraper="job_board", cadence="daily",
        industries=["Logistics"],
        signal_types=["robot_job"],
    ),
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=freight+handler+dock+worker+material+handler&l=United+States&sort=date",
        label="Indeed - Freight / Dock / Material Handlers",
        scraper="job_board", cadence="daily",
        industries=["Logistics"],
        signal_types=["robot_job"],
    ),
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=inventory+associate+shipping+receiving&l=United+States&sort=date",
        label="Indeed - Inventory / Shipping / Receiving Associates",
        scraper="job_board", cadence="daily",
        industries=["Logistics"],
        signal_types=["robot_job"],
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
        signal_types=["robot_job"],
        notes="Housekeeping = #1 robot use case for hotels",
    ),
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=hotel+bellman+valet+porter+concierge&l=United+States&sort=date",
        label="Indeed - Hotel Guest-Facing Staff (bell/valet/porter)",
        scraper="job_board", cadence="daily",
        industries=["Hospitality"],
        signal_types=["robot_job"],
        notes="Delivery robots can replace room service + porter runs",
    ),
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=hotel+front+desk+night+audit+multiple+openings&l=United+States&sort=date",
        label="Indeed - Hotel Front Desk Multiple Openings / Night Audit",
        scraper="job_board", cadence="daily",
        industries=["Hospitality"],
        signal_types=["robot_job"],
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
        signal_types=["robot_job"],
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
        signal_types=["robot_job"],
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
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=line+cook+make+line+bowl+assembly+grill+qsr&l=United+States&sort=date",
        label="Indeed - QSR / make-line / bowl assembly cooks (volume hiring)",
        scraper="job_board", cadence="daily",
        industries=["Food Service"],
        signal_types=["robot_job"],
        notes="Make-line and bowl assembly = food_prep FIND class, not hotel hospitality",
    ),
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=prep+cook+fast+casual+kitchen+automation+grill&l=United+States&sort=date",
        label="Indeed - Fast-casual prep cook / kitchen automation",
        scraper="job_board", cadence="daily",
        industries=["Food Service"],
        signal_types=["robot_job"],
        notes="Prep cook and kitchen automation operational roles — not VP of Culinary",
    ),
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=hotel+casino+airport+kitchen+cook+prep+cook&l=United+States&sort=date",
        label="Indeed - Hotel / casino / airport kitchen cooks",
        scraper="job_board", cadence="daily",
        industries=["Food Service", "Hospitality"],
        signal_types=["robot_job"],
        notes="Food prep in hotel, casino, and airport kitchens — not hotel housekeeping",
    ),
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=banquet+cook+commissary+kitchen+hotel&l=United+States&sort=date",
        label="Indeed - Banquet / commissary kitchen cooks",
        scraper="job_board", cadence="daily",
        industries=["Food Service", "Hospitality"],
        signal_types=["robot_job"],
        notes="Hotel banquet and commissary prep — kitchen work, not guest-room housekeeping",
    ),
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=food+runner+busser+server+restaurant+dining&l=United+States&sort=date",
        label="Indeed - Restaurant food runner / busser / server",
        scraper="job_board", cadence="daily",
        industries=["Food Service"],
        signal_types=["robot_job"],
        notes="Table/drink/bussing (ADAM / Matradee / Servi work) — not QSR-only, not housekeeping",
    ),
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=hotel+dining+banquet+server+food+runner+busser&l=United+States&sort=date",
        label="Indeed - Hotel dining / banquet servers",
        scraper="job_board", cadence="daily",
        industries=["Food Service", "Hospitality"],
        signal_types=["robot_job"],
        notes="Hotel dining service — not room attendant / housekeeper",
    ),
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=casino+cocktail+server+food+runner+busser&l=United+States&sort=date",
        label="Indeed - Casino cocktail / food runner / busser",
        scraper="job_board", cadence="daily",
        industries=["Food Service", "Hospitality"],
        signal_types=["robot_job"],
    ),
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=airport+restaurant+food+court+server+busser&l=United+States&sort=date",
        label="Indeed - Airport restaurant / food-court servers",
        scraper="job_board", cadence="daily",
        industries=["Food Service", "Hospitality"],
        signal_types=["robot_job"],
    ),
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=office+cafeteria+server+busser&l=United+States&sort=date",
        label="Indeed - Office cafeteria servers / bussers",
        scraper="job_board", cadence="daily",
        industries=["Food Service"],
        signal_types=["robot_job"],
    ),
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=mall+food+court+server+busser&l=United+States&sort=date",
        label="Indeed - Mall food-court servers / bussers",
        scraper="job_board", cadence="daily",
        industries=["Food Service"],
        signal_types=["robot_job"],
    ),
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=hotel+janitor+custodian+restroom+attendant&l=United+States&sort=date",
        label="Indeed - Hotel janitor / restroom attendant",
        scraper="job_board", cadence="daily",
        industries=["Hospitality"],
        signal_types=["robot_job"],
        notes="Hotel floor/restroom cleaning — not housekeeper / room attendant",
    ),
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=restaurant+janitor+kitchen+floor+cleaner&l=United+States&sort=date",
        label="Indeed - Restaurant janitor / kitchen floor cleaner",
        scraper="job_board", cadence="daily",
        industries=["Food Service"],
        signal_types=["robot_job"],
    ),
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=casino+janitor+custodian+restroom+attendant&l=United+States&sort=date",
        label="Indeed - Casino janitor / custodian / restroom",
        scraper="job_board", cadence="daily",
        industries=["Hospitality"],
        signal_types=["robot_job"],
    ),
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=airport+janitor+custodian+restroom+attendant&l=United+States&sort=date",
        label="Indeed - Airport janitor / restroom attendant",
        scraper="job_board", cadence="daily",
        industries=["Hospitality"],
        signal_types=["robot_job"],
    ),
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=office+janitor+custodian+vacuum&l=United+States&sort=date",
        label="Indeed - Office janitor / custodian / vacuum",
        scraper="job_board", cadence="daily",
        industries=["Hospitality"],
        signal_types=["robot_job"],
    ),
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=mall+janitor+custodian+restroom&l=United+States&sort=date",
        label="Indeed - Mall janitor / restroom cleaner",
        scraper="job_board", cadence="daily",
        industries=["Hospitality"],
        signal_types=["robot_job"],
    ),
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=data+center+janitor+custodian&l=United+States&sort=date",
        label="Indeed - Data center janitor / custodian",
        scraper="job_board", cadence="daily",
        industries=["Hospitality"],
        signal_types=["robot_job"],
        notes="Floor/restroom cleaning in data centers — not hospital EVS",
    ),
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=grill+cook+ingredient+dosing+tortilla+assembly+line+kitchen&l=United+States&sort=date",
        label="Indeed - Grill / tortilla / ingredient-dosing kitchen line",
        scraper="job_board", cadence="daily",
        industries=["Food Service"],
        signal_types=["robot_job"],
    ),
    ScrapeTarget(
        url="https://www.simplyhired.com/search?q=line+cook+make+line+qsr+bowl+assembly+grill&l=United+States",
        label="SimplyHired - QSR make-line / bowl assembly cooks",
        scraper="job_board", cadence="daily",
        industries=["Food Service"],
        signal_types=["robot_job"],
    ),
    ScrapeTarget(
        url="https://www.simplyhired.com/search?q=prep+cook+kitchen+automation+fast+casual+grill&l=United+States",
        label="SimplyHired - Kitchen automation / fast-casual prep cooks",
        scraper="job_board", cadence="daily",
        industries=["Food Service"],
        signal_types=["robot_job"],
    ),

    # === HEALTHCARE: non-clinical labor pain ===
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=environmental+services+EVS+housekeeper+hospital&l=United+States&sort=date",
        label="Indeed - Hospital EVS / Environmental Services (volume hiring)",
        scraper="job_board", cadence="daily",
        industries=["Healthcare"],
        signal_types=["robot_job"],
        notes="Hospital housekeeping = disinfection robot opportunity",
    ),
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=patient+transport+aide+hospital+porter&l=United+States&sort=date",
        label="Indeed - Patient Transport / Hospital Aide",
        scraper="job_board", cadence="daily",
        industries=["Healthcare"],
        signal_types=["robot_job"],
        notes="Logistics robots can handle internal transport runs",
    ),
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=pharmacy+technician+sterile+processing+hospital&l=United+States&sort=date",
        label="Indeed - Pharmacy Tech / Sterile Processing (volume hiring)",
        scraper="job_board", cadence="daily",
        industries=["Healthcare"],
        signal_types=["robot_job"],
    ),
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=dietary+aide+food+service+hospital+healthcare&l=United+States&sort=date",
        label="Indeed - Hospital Dietary Aide / Food Service",
        scraper="job_board", cadence="daily",
        industries=["Healthcare"],
        signal_types=["robot_job"],
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

    # === AGRICULTURE: field work a farm robot could be hired to do ===
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=farm+worker+harvest+orchard+vineyard&l=United+States&sort=date",
        label="Indeed - Farm / Harvest / Orchard Workers (volume hiring)",
        scraper="job_board", cadence="daily",
        industries=["Agriculture"],
        signal_types=["robot_job"],
        notes="Field harvest and orchard work = agriculture FIND class",
    ),
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=tractor+operator+agricultural+field&l=United+States&sort=date",
        label="Indeed - Agricultural Tractor Operators",
        scraper="job_board", cadence="daily",
        industries=["Agriculture"],
        signal_types=["robot_job"],
    ),
    ScrapeTarget(
        url="https://www.simplyhired.com/search?q=harvest+worker+farm+laborer+orchard&l=United+States",
        label="SimplyHired - Harvest / Farm Laborers",
        scraper="job_board", cadence="daily",
        industries=["Agriculture"],
        signal_types=["robot_job"],
    ),

    # === CONSTRUCTION: jobsite work ===
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=construction+laborer+drywall+framing&l=United+States&sort=date",
        label="Indeed - Construction Laborer / Drywall / Framing",
        scraper="job_board", cadence="daily",
        industries=["Construction"],
        signal_types=["robot_job"],
        notes="Jobsite finish and framing = construction FIND class",
    ),
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=bricklayer+mason+jobsite&l=United+States&sort=date",
        label="Indeed - Bricklayer / Mason (jobsite)",
        scraper="job_board", cadence="daily",
        industries=["Construction"],
        signal_types=["robot_job"],
    ),
    ScrapeTarget(
        url="https://www.simplyhired.com/search?q=drywall+finisher+construction+laborer&l=United+States",
        label="SimplyHired - Drywall / Construction Laborers",
        scraper="job_board", cadence="daily",
        industries=["Construction"],
        signal_types=["robot_job"],
    ),

    # === MINING: haulage / pit / underground ===
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=haul+truck+operator+mine&l=United+States&sort=date",
        label="Indeed - Mine Haul Truck Operators",
        scraper="job_board", cadence="daily",
        industries=["Mining"],
        signal_types=["robot_job"],
        notes="Haulage is the mining FIND class work",
    ),
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=underground+miner+equipment+operator&l=United+States&sort=date",
        label="Indeed - Underground Miner / Equipment Operator",
        scraper="job_board", cadence="daily",
        industries=["Mining"],
        signal_types=["robot_job"],
    ),
    ScrapeTarget(
        url="https://www.simplyhired.com/search?q=haul+truck+operator+mining&l=United+States",
        label="SimplyHired - Mining Haul Truck Operators",
        scraper="job_board", cadence="daily",
        industries=["Mining"],
        signal_types=["robot_job"],
    ),

    # === FACTORY: machine tend / CNC / packaging line ===
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=CNC+machine+tender+load+unload+operator&l=United+States&sort=date",
        label="Indeed - CNC / Machine Tender Load-Unload",
        scraper="job_board", cadence="daily",
        industries=["Factory", "Food Processing & Manufacturing"],
        signal_types=["robot_job"],
        notes="Machine tending = factory FIND class",
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

    # === END-OF-LINE / MANUFACTURING / CPG: labor pain + buyer personas ===
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=palletizer+operator+packaging+line+operator&l=United+States&sort=date",
        label="Indeed - Palletizer / Packaging Line Operators (volume hiring)",
        scraper="job_board", cadence="daily",
        industries=["Factory", "Food Processing & Manufacturing", "CPG & Consumer Goods"],
        signal_types=["robot_job", "labor_pain", "labor_shortage", "packaging_automation"],
        notes="Companies hiring palletizer/packaging operators at scale = EOL automation opportunity",
    ),
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=machine+operator+production+line+food+manufacturing&l=United+States&sort=date",
        label="Indeed - Machine / Production Line Operators Food Manufacturing",
        scraper="job_board", cadence="daily",
        industries=["Factory", "Food Processing & Manufacturing", "CPG & Consumer Goods"],
        signal_types=["robot_job", "labor_pain", "repetitive_process"],
        notes="High-volume manual machine operators = repetitive process automation signal",
    ),
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=pack+out+pack+in+operator+food+beverage+manufacturing&l=United+States&sort=date",
        label="Indeed - Pack-Out / Pack-In Operators (food & beverage manufacturing)",
        scraper="job_board", cadence="daily",
        industries=["Factory", "Food Processing & Manufacturing", "CPG & Consumer Goods"],
        signal_types=["robot_job", "labor_pain", "packaging_automation"],
        notes="Pack-in/pack-out roles = direct EOL automation use case",
    ),
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=material+handler+intralogistics+manufacturing+plant&l=United+States&sort=date",
        label="Indeed - Material Handlers / Intralogistics Manufacturing Plant",
        scraper="job_board", cadence="daily",
        industries=["Factory", "Food Processing & Manufacturing", "Contract Manufacturing"],
        signal_types=["robot_job", "labor_pain", "material_handling"],
        notes="Internal factory transport = AMR/AGV opportunity",
    ),
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=Director+VP+manufacturing+operations+plant+manager+food+beverage&l=United+States&sort=date",
        label="Indeed - Director/VP Manufacturing Operations Food & Beverage (buyer persona)",
        scraper="job_board", cadence="daily",
        industries=["Food Processing & Manufacturing", "CPG & Consumer Goods"],
        signal_types=["strategic_hire"],
        notes="New plant ops leader = automation budget review cycle",
    ),
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=Director+VP+engineering+automation+packaging+manufacturing&l=United+States&sort=date",
        label="Indeed - Director/VP Engineering & Automation Packaging (buyer persona)",
        scraper="job_board", cadence="daily",
        industries=["CPG & Consumer Goods", "Food Processing & Manufacturing", "Contract Manufacturing"],
        signal_types=["strategic_hire", "packaging_automation"],
        notes="Engineering/automation director hire = direct robot buyer",
    ),
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=continuous+improvement+manager+lean+manufacturing+food+plant&l=United+States&sort=date",
        label="Indeed - Continuous Improvement Manager Food / CPG Plant",
        scraper="job_board", cadence="daily",
        industries=["Food Processing & Manufacturing", "CPG & Consumer Goods"],
        signal_types=["repetitive_process", "production_capacity"],
        notes="CI hire in manufacturing = active automation evaluation underway",
    ),
    ScrapeTarget(
        url="https://www.indeed.com/jobs?q=maintenance+technician+packaging+equipment+filler+labeler&l=United+States&sort=date",
        label="Indeed - Packaging Equipment Maintenance (filler / labeler / palletizer)",
        scraper="job_board", cadence="daily",
        industries=["Food Processing & Manufacturing", "CPG & Consumer Goods"],
        signal_types=["labor_pain", "packaging_automation"],
        notes="Packaging equipment maintenance hiring = aging line / expansion signal",
    ),
    ScrapeTarget(
        url="https://www.simplyhired.com/search?q=palletizer+packaging+line+operator+production&l=United+States",
        label="SimplyHired - Palletizer / Packaging Line Operators",
        scraper="job_board", cadence="daily",
        industries=["Food Processing & Manufacturing", "CPG & Consumer Goods"],
        signal_types=["labor_pain", "packaging_automation"],
    ),
    ScrapeTarget(
        url="https://www.simplyhired.com/search?q=VP+Director+manufacturing+plant+operations+food+beverage&l=United+States",
        label="SimplyHired - VP/Director Manufacturing Operations (buyer persona)",
        scraper="job_board", cadence="daily",
        industries=["Food Processing & Manufacturing", "CPG & Consumer Goods"],
        signal_types=["strategic_hire"],
    ),

    # === SIMPLYHIRED: broader scraping reach beyond Indeed ===
    ScrapeTarget(
        url="https://www.simplyhired.com/search?q=housekeeper+room+attendant+hotel&l=United+States",
        label="SimplyHired - Hotel Housekeepers (volume hiring)",
        scraper="job_board", cadence="daily",
        industries=["Hospitality"],
        signal_types=["robot_job"],
    ),
    ScrapeTarget(
        url="https://www.simplyhired.com/search?q=warehouse+associate+fulfillment+picker+packer&l=United+States",
        label="SimplyHired - Warehouse Associates / Fulfillment Pickers",
        scraper="job_board", cadence="daily",
        industries=["Logistics"],
        signal_types=["robot_job"],
    ),
    ScrapeTarget(
        url="https://www.simplyhired.com/search?q=line+cook+prep+cook+dishwasher+restaurant&l=United+States",
        label="SimplyHired - Kitchen Staff (volume hiring)",
        scraper="job_board", cadence="daily",
        industries=["Food Service"],
        signal_types=["robot_job"],
    ),
    ScrapeTarget(
        url="https://www.simplyhired.com/search?q=environmental+services+hospital+EVS+dietary+aide&l=United+States",
        label="SimplyHired - Hospital EVS / Dietary (volume hiring)",
        scraper="job_board", cadence="daily",
        industries=["Healthcare"],
        signal_types=["robot_job"],
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
        signal_types=["robot_job"],
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
    # === END-OF-LINE: Manufacturing & CPG Directories ===
    ScrapeTarget(
        url="https://www.yellowpages.com/search?search_terms=food+manufacturing+food+processing+plant&geo_location_terms=United+States",
        label="Yellow Pages - Food Manufacturing & Processing Plants",
        scraper="logistics_dir", cadence="weekly",
        industries=["Food Processing & Manufacturing"], signal_types=["packaging_automation", "production_capacity"],
        notes="Food plants: EOL lines, palletizers, case packers, fillers — high robot fit",
    ),
    ScrapeTarget(
        url="https://www.yellowpages.com/search?search_terms=contract+manufacturer+contract+packaging&geo_location_terms=United+States",
        label="Yellow Pages - Contract Manufacturers & Contract Packagers",
        scraper="logistics_dir", cadence="weekly",
        industries=["Contract Manufacturing"], signal_types=["packaging_automation", "material_handling"],
        notes="Co-packers & CMOs: high SKU mix + rapid changeover = automation buying trigger",
    ),
    ScrapeTarget(
        url="https://www.yellowpages.com/search?search_terms=beverage+manufacturer+bottling+plant&geo_location_terms=United+States",
        label="Yellow Pages - Beverage Manufacturers & Bottling Plants",
        scraper="logistics_dir", cadence="weekly",
        industries=["CPG & Consumer Goods", "Food Processing & Manufacturing"], signal_types=["packaging_automation", "capex"],
        notes="Bottling & canning lines: filling, labeling, case packing, palletizing — EOL sweet spot",
    ),
    ScrapeTarget(
        url="https://www.yellowpages.com/search?search_terms=packaging+company+packaging+plant&geo_location_terms=United+States",
        label="Yellow Pages - Packaging Companies",
        scraper="logistics_dir", cadence="weekly",
        industries=["CPG & Consumer Goods"], signal_types=["packaging_automation", "capex", "expansion"],
        notes="Packaging plants themselves: flexible packaging, corrugated, containers — robot buyers",
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
    # ── END-OF-LINE / PACKAGING / FOOD MANUFACTURING (NEW) ───────────────────
    ScrapeTarget(
        url="https://www.packworld.com/rss.xml",
        label="Packaging World (PMMI Media — end-of-line packaging)",
        scraper="rss_feed", cadence="daily",
        industries=["Food Processing & Manufacturing", "CPG & Consumer Goods"],
        signal_types=["packaging_automation", "capex", "expansion", "automation_intent"],
        notes="Premier packaging trade pub — case packers, palletizers, fillers, labelers, EOL lines",
    ),
    ScrapeTarget(
        url="https://www.profoodworld.com/rss.xml",
        label="ProFood World (food & beverage manufacturing automation)",
        scraper="rss_feed", cadence="daily",
        industries=["Food Processing & Manufacturing", "CPG & Consumer Goods"],
        signal_types=["packaging_automation", "production_capacity", "capex", "automation_intent"],
        notes="Food plant automation: EOL lines, processing robots, palletizing",
    ),
    ScrapeTarget(
        url="https://www.foodmanufacturing.com/rss/news",
        label="Food Manufacturing Magazine",
        scraper="rss_feed", cadence="daily",
        industries=["Food Processing & Manufacturing", "CPG & Consumer Goods"],
        signal_types=["expansion", "capex", "automation_intent", "production_capacity"],
        notes="Food plant expansions, new lines, tech investments",
    ),
    ScrapeTarget(
        url="https://www.packagingdigest.com/rss.xml",
        label="Packaging Digest (packaging line technology)",
        scraper="rss_feed", cadence="daily",
        industries=["CPG & Consumer Goods", "Food Processing & Manufacturing"],
        signal_types=["packaging_automation", "capex", "equipment_integration"],
        notes="Packaging machinery buyers — shrink wrap, case packing, labeling, conveyor",
    ),
    ScrapeTarget(
        url="https://www.foodbusinessnews.net/rss/news",
        label="Food Business News (CPG & food industry)",
        scraper="rss_feed", cadence="daily",
        industries=["CPG & Consumer Goods", "Food Processing & Manufacturing"],
        signal_types=["funding_round", "expansion", "ma_activity", "capex"],
        notes="CPG company investment, M&A, new facility news",
    ),
    ScrapeTarget(
        url="https://www.bevindustry.com/rss/all",
        label="Beverage Industry Magazine",
        scraper="rss_feed", cadence="daily",
        industries=["CPG & Consumer Goods", "Food Processing & Manufacturing"],
        signal_types=["capex", "expansion", "packaging_automation", "production_capacity"],
        notes="Beverage plant expansions, new packaging lines, filling/labeling automation",
    ),
    ScrapeTarget(
        url="https://www.contractpharma.com/rss/news",
        label="Contract Pharma (contract manufacturing)",
        scraper="rss_feed", cadence="daily",
        industries=["Contract Manufacturing"],
        signal_types=["expansion", "capex", "packaging_automation", "automation_intent"],
        notes="CMOs/CDMOs: facility expansion = new packaging, filling, palletizing automation",
    ),
    ScrapeTarget(
        url="https://www.plantengineering.com/rss/",
        label="Plant Engineering (factory & facilities)",
        scraper="rss_feed", cadence="daily",
        industries=["Food Processing & Manufacturing", "CPG & Consumer Goods", "Contract Manufacturing"],
        signal_types=["capex", "automation_intent", "repetitive_process", "production_capacity"],
        notes="Plant-level automation investment, maintenance, production efficiency",
    ),
    ScrapeTarget(
        url="https://www.controleng.com/rss/all",
        label="Control Engineering (industrial automation)",
        scraper="rss_feed", cadence="daily",
        industries=["Food Processing & Manufacturing", "CPG & Consumer Goods"],
        signal_types=["automation_intent", "capex", "equipment_integration"],
        notes="Industrial control & automation: PLC, SCADA, robotics integration",
    ),
    ScrapeTarget(
        url="https://www.processindustryforum.com/feed",
        label="Process Industry Forum",
        scraper="rss_feed", cadence="daily",
        industries=["Food Processing & Manufacturing", "Contract Manufacturing"],
        signal_types=["automation_intent", "production_capacity", "capex"],
        notes="Process manufacturing: filling, mixing, packaging, intralogistics",
    ),

    # ── Industry news sources from user URL list (March 2026) ─────────────────
    ScrapeTarget(
        url="https://www.manufacturingdive.com/feeds/news/",
        label="Manufacturing Dive",
        scraper="rss_feed", cadence="daily",
        industries=["Logistics"],
        signal_types=["funding_round", "expansion", "capex", "ma_activity", "automation_intent"],
        notes="Manufacturing ops, automation, labor, expansion coverage",
    ),
    ScrapeTarget(
        url="https://www.retaildive.com/feeds/news/",
        label="Retail Dive",
        scraper="rss_feed", cadence="daily",
        industries=["Logistics", "Food Service"],
        signal_types=["funding_round", "expansion", "capex", "ma_activity"],
        notes="Retail supply chain, logistics, store ops, e-commerce fulfillment",
    ),
    ScrapeTarget(
        url="https://www.grocerydive.com/feeds/news/",
        label="Grocery Dive",
        scraper="rss_feed", cadence="daily",
        industries=["Logistics", "Food Service"],
        signal_types=["funding_round", "expansion", "capex", "automation_intent"],
        notes="Grocery DC, store automation, cold chain, labor",
    ),
    ScrapeTarget(
        url="https://www.supplychainbrain.com/rss",
        label="Supply Chain Brain",
        scraper="rss_feed", cadence="daily",
        industries=["Logistics"],
        signal_types=["capex", "expansion", "automation_intent", "funding_round"],
        notes="Supply chain news, logistics tech, warehousing",
    ),
    ScrapeTarget(
        url="https://www.joc.com/api/rssfeed",
        label="Journal of Commerce (JOC) - All News",
        scraper="rss_feed", cadence="daily",
        industries=["Logistics"],
        signal_types=["expansion", "capex", "ma_activity", "funding_round"],
        notes="Maritime, trucking, rail, ports, logistics technology",
    ),
    ScrapeTarget(
        url="https://www.healthcareitnews.com/home/feed",
        label="Healthcare IT News",
        scraper="rss_feed", cadence="daily",
        industries=["Healthcare"],
        signal_types=["capex", "expansion", "automation_intent", "equipment_integration"],
        notes="Hospital IT, clinical ops, facilities technology",
    ),
    ScrapeTarget(
        url="https://www.hoteldive.com/feeds/news/",
        label="Hotel Dive",
        scraper="rss_feed", cadence="daily",
        industries=["Hospitality"],
        signal_types=["funding_round", "expansion", "capex", "ma_activity"],
        notes="Hotel operations, technology, development",
    ),
    ScrapeTarget(
        url="https://theloadstar.com/feed/",
        label="The Loadstar",
        scraper="rss_feed", cadence="daily",
        industries=["Logistics"],
        signal_types=["expansion", "capex", "ma_activity"],
        notes="Supply chain, freight, shipping news",
    ),
]

# ── OEM / Robot Company Intelligence RSS Feeds (XBOT pipeline) ───────────────
# These feeds are for XBOT — discovering robot OEM companies attending shows.
# mode="oem_prospect" should be used when filtering leads from these sources.

OEM_INTELLIGENCE_TARGETS: List[ScrapeTarget] = [
    # ── Robotics Trade Media ──────────────────────────────────────────────────
    ScrapeTarget(
        url="https://www.therobotreport.com/feed/",
        label="The Robot Report",
        scraper="rss_feed", cadence="daily",
        industries=["Robotics", "Industrial", "Logistics", "Healthcare"],
        signal_types=["trade_show_attendance", "product_launch", "oem_company"],
        notes="Primary robotics trade press — covers exhibitors, show previews, product launches",
    ),
    ScrapeTarget(
        url="https://www.robotics247.com/feed",
        label="Robotics 24/7",
        scraper="rss_feed", cadence="daily",
        industries=["Robotics", "Industrial", "Logistics"],
        signal_types=["trade_show_attendance", "product_launch", "oem_company"],
        notes="Covers AMRs, humanoids, industrial robots — includes show exhibitor coverage",
    ),
    ScrapeTarget(
        url="https://spectrum.ieee.org/feeds/topic/robotics.rss",
        label="IEEE Spectrum Robotics",
        scraper="rss_feed", cadence="daily",
        industries=["Robotics", "Defense", "Healthcare"],
        signal_types=["product_launch", "oem_company", "research_signal"],
        notes="IEEE Spectrum robotics coverage — technically deep, catches new entrants",
    ),
    ScrapeTarget(
        url="https://www.automationworld.com/rss.xml",
        label="Automation World",
        scraper="rss_feed", cadence="daily",
        industries=["Industrial", "Robotics", "Logistics"],
        signal_types=["trade_show_attendance", "product_launch", "oem_company"],
        notes="Industrial automation and robotics — strong show coverage for Automate, MODEX",
    ),
    ScrapeTarget(
        url="https://www.a3automate.org/news/rss/",
        label="A3 Automate News",
        scraper="rss_feed", cadence="daily",
        industries=["Robotics", "Industrial"],
        signal_types=["trade_show_attendance", "exhibitor_list", "oem_company"],
        notes="A3 is the organizer of Automate — official exhibitor and show announcements",
    ),
    ScrapeTarget(
        url="https://www.massrobotics.org/news/feed/",
        label="MassRobotics",
        scraper="rss_feed", cadence="weekly",
        industries=["Robotics"],
        signal_types=["oem_company", "startup_signal", "trade_show_attendance"],
        notes="Boston robotics cluster — humanoid, AMR startups. Strong Robotics Summit coverage",
    ),
    # ── PR / Press Release Feeds ──────────────────────────────────────────────
    ScrapeTarget(
        url="https://www.prnewswire.com/rss/news-releases-list.rss?tagAbbr=ROB",
        label="PR Newswire — Robotics",
        scraper="rss_feed", cadence="daily",
        industries=["Robotics", "Industrial"],
        signal_types=["product_launch", "trade_show_attendance", "oem_company"],
        notes="Official press releases from robot OEMs — catches show attendance before exhibitor lists",
    ),
    ScrapeTarget(
        url="https://www.businesswire.com/rss/home/?rss=G17&rpcid=business_robotics",
        label="Business Wire — Robotics",
        scraper="rss_feed", cadence="daily",
        industries=["Robotics", "Industrial"],
        signal_types=["product_launch", "trade_show_attendance", "funding_round"],
        notes="BusinessWire robotics press releases — funding, show attendance announcements",
    ),
    # ── Defense / Drone Media ─────────────────────────────────────────────────
    ScrapeTarget(
        url="https://www.suasnews.com/feed/",
        label="sUAS News (Drone Industry)",
        scraper="rss_feed", cadence="daily",
        industries=["Defense", "Robotics"],
        signal_types=["trade_show_attendance", "oem_company", "product_launch"],
        notes="Commercial and defense drone OEM coverage — AUVSI attendee intelligence",
    ),
    ScrapeTarget(
        url="https://dronelife.com/feed/",
        label="Drone Life",
        scraper="rss_feed", cadence="daily",
        industries=["Defense", "Robotics", "Logistics"],
        signal_types=["trade_show_attendance", "oem_company"],
        notes="Drone industry news — covers CES, AUVSI exhibitors and announcements",
    ),
    # ── Show-Specific Intelligence ────────────────────────────────────────────
    ScrapeTarget(
        url="https://news.google.com/rss/search?q=CES+2027+robot+exhibitor&hl=en-US&gl=US&ceid=US:en",
        label="Google News — CES robot exhibitors",
        scraper="rss_feed", cadence="weekly",
        industries=["Robotics"],
        signal_types=["trade_show_attendance", "exhibitor_list"],
        notes="Live news monitoring for CES robot exhibitor announcements",
    ),
    ScrapeTarget(
        url="https://news.google.com/rss/search?q=Automate+2026+2027+robot+booth&hl=en-US&gl=US&ceid=US:en",
        label="Google News — Automate robot booths",
        scraper="rss_feed", cadence="weekly",
        industries=["Robotics", "Industrial"],
        signal_types=["trade_show_attendance", "exhibitor_list"],
        notes="Automate show robot exhibitor monitoring",
    ),
    ScrapeTarget(
        url="https://news.google.com/rss/search?q=humanoid+robot+%22Las+Vegas%22+2026+2027&hl=en-US&gl=US&ceid=US:en",
        label="Google News — humanoids Las Vegas",
        scraper="rss_feed", cadence="weekly",
        industries=["Robotics"],
        signal_types=["trade_show_attendance", "oem_company", "intl_company"],
        notes="Humanoid robot companies heading to Las Vegas shows — prime StageGate targets",
    ),
    # ── Show Ecosystem (shared with StageGate — partner + organizer intel) ───
    ScrapeTarget(
        url="https://www.tsnn.com/feed/",
        label="TSNN (Trade Show News Network)",
        scraper="rss_feed", cadence="daily",
        industries=["Robotics", "Hospitality"],
        signal_types=["trade_show_attendance", "exhibitor_list", "oem_company"],
        notes="Trade show industry news — exhibitor announcements, GC coverage",
    ),
    ScrapeTarget(
        url="https://www.exhibitoronline.com/feed/",
        label="EXHIBITOR Magazine",
        scraper="rss_feed", cadence="daily",
        industries=["Robotics"],
        signal_types=["trade_show_attendance", "exhibitor_list"],
        notes="Exhibit design and show floor news — robot booth coverage",
    ),
    ScrapeTarget(
        url="https://www.eventmarketer.com/feed/",
        label="Event Marketer",
        scraper="rss_feed", cadence="daily",
        industries=["Robotics", "Hospitality"],
        signal_types=["trade_show_attendance", "product_launch"],
        notes="Experiential marketing — robot activations at trade shows",
    ),
    ScrapeTarget(
        url="https://www.meetingsnet.com/rss.xml",
        label="Meetings Net",
        scraper="rss_feed", cadence="daily",
        industries=["Hospitality"],
        signal_types=["expansion", "trade_show_attendance"],
        notes="Meetings and conventions industry — show organizer intel",
    ),
    ScrapeTarget(
        url="https://www.avnetwork.com/rss",
        label="AV Network",
        scraper="rss_feed", cadence="daily",
        industries=["Robotics"],
        signal_types=["trade_show_attendance", "capex"],
        notes="AV / power / booth tech — robot demo infrastructure partners",
    ),
    ScrapeTarget(
        url="https://www.livedesignonline.com/rss/feed/all",
        label="Live Design",
        scraper="rss_feed", cadence="daily",
        industries=["Robotics", "Hospitality"],
        signal_types=["trade_show_attendance", "product_launch"],
        notes="Live events staging and production — robot activation coverage",
    ),
    ScrapeTarget(
        url="https://www.tradeshownews.com/feed/",
        label="Trade Show News",
        scraper="rss_feed", cadence="daily",
        industries=["Robotics"],
        signal_types=["trade_show_attendance", "exhibitor_list"],
    ),
    ScrapeTarget(
        url="https://www.roboticsbusinessreview.com/feed/",
        label="Robotics Business Review",
        scraper="rss_feed", cadence="daily",
        industries=["Robotics", "Industrial", "Logistics"],
        signal_types=["trade_show_attendance", "product_launch", "oem_company"],
    ),
    ScrapeTarget(
        url="https://www.modernmaterialhandling.com/rss/news",
        label="Modern Materials Handling",
        scraper="rss_feed", cadence="daily",
        industries=["Robotics", "Logistics"],
        signal_types=["trade_show_attendance", "product_launch", "oem_company"],
        notes="MODEX / ProMat AMR and warehouse robot coverage",
    ),
    ScrapeTarget(
        url="https://globenewswire.com/RssFeed/organization/robotics",
        label="GlobeNewswire — Robotics",
        scraper="rss_feed", cadence="daily",
        industries=["Robotics", "Industrial"],
        signal_types=["product_launch", "trade_show_attendance", "funding_round"],
    ),
    ScrapeTarget(
        url="https://techcrunch.com/tag/robotics/feed/",
        label="TechCrunch Robotics",
        scraper="rss_feed", cadence="daily",
        industries=["Robotics"],
        signal_types=["funding_round", "oem_company", "product_launch"],
        notes="Funding rounds — OEM companies with budget for trade show activations",
    ),
    ScrapeTarget(
        url="https://news.google.com/rss/search?q=NAB+Show+robot+exhibitor+2026&hl=en-US&gl=US&ceid=US:en",
        label="Google News — NAB robot exhibitors",
        scraper="rss_feed", cadence="weekly",
        industries=["Robotics"],
        signal_types=["trade_show_attendance", "exhibitor_list"],
    ),
    ScrapeTarget(
        url="https://news.google.com/rss/search?q=trade+show+exhibitor+robot+warehouse+staging&hl=en-US&gl=US&ceid=US:en",
        label="Google News — trade show robot logistics",
        scraper="rss_feed", cadence="weekly",
        industries=["Robotics", "Logistics"],
        signal_types=["trade_show_attendance", "oem_company"],
    ),
    ScrapeTarget(
        url="https://news.google.com/rss/search?q=Freeman+GES+exhibit+house+robot+CES&hl=en-US&gl=US&ceid=US:en",
        label="Google News — exhibit house robotics",
        scraper="rss_feed", cadence="weekly",
        industries=["Robotics"],
        signal_types=["trade_show_attendance", "exhibitor_list"],
        notes="Freeman, GES, exhibit house robot booth coverage",
    ),
]


# -- Google News Queries: Robot Jobs + close-out evidence --------------------
# Operational work discovery first. Buyer-intent queries below are SIGNAL leftovers.

NEWS_QUERIES = [

    # === Close-out: robot already doing the work ===
    {"query": "warehouse AMR deployed picking robots live",                 "industries": ["Logistics"],    "signal_types": ["robot_job_closed", "robot_installation"]},
    {"query": "humanoid robot warehouse deployment Digit GXO",              "industries": ["Logistics"],    "signal_types": ["robot_job_closed", "robot_installation"]},
    {"query": "hospital delivery robot live deployment TUG Aethon",         "industries": ["Healthcare"],   "signal_types": ["robot_job_closed", "robot_installation"]},
    {"query": "hotel housekeeping robot deployed commercial",               "industries": ["Hospitality"],  "signal_types": ["robot_job_closed"]},
    {"query": "autonomous floor scrubber robot commercial deployment",      "industries": ["Healthcare", "Hospitality"], "signal_types": ["robot_job_closed"]},
    {"query": "robots replaced warehouse associates picking packing",       "industries": ["Logistics"],    "signal_types": ["robot_job_closed"]},

    # === Labor Pain & Staffing Shortage (still work evidence, extract as Robot Jobs) ===
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
    {"query": "restaurant chain kitchen automation robot deployment pilot 2025", "industries": ["Food Service"],                 "signal_types": ["automation_intent", "capex"]},
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

    # === High-Value Target Accounts ===
    {"query": "Marriott International labor staffing operations 2025",       "industries": ["Hospitality"],                  "signal_types": ["labor_shortage", "capex"]},
    {"query": "Hilton Hotels expansion new properties investment 2025",      "industries": ["Hospitality"],                  "signal_types": ["expansion", "capex"]},
    {"query": "DHL supply chain operations expansion new facility",          "industries": ["Logistics"],                    "signal_types": ["capex", "expansion"]},
    {"query": "XPO Logistics new distribution center facility",             "industries": ["Logistics"],                    "signal_types": ["capex", "expansion"]},
    {"query": "Amazon fulfillment new warehouse distribution center 2025",  "industries": ["Logistics"],                    "signal_types": ["expansion"]},
    {"query": "Prologis new property construction distribution",            "industries": ["Logistics"],                    "signal_types": ["expansion", "capex"]},
    {"query": "HCA Healthcare new facility hospital expansion 2025",        "industries": ["Healthcare"],                   "signal_types": ["expansion", "capex"]},
    {"query": "McDonald's Chipotle Yum Brands kitchen automation robot deployment", "industries": ["Food Service"],                 "signal_types": ["automation_intent"]},
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

    # === END-OF-LINE / CPG / FOOD MANUFACTURING SIGNALS ===
    # Labor pain at food & CPG plants
    {"query": "food manufacturing plant labor shortage worker hiring 2025 2026",                    "industries": ["Food Processing & Manufacturing", "CPG & Consumer Goods"],  "signal_types": ["labor_shortage", "labor_pain"]},
    {"query": "beverage plant staffing operator shortage production line workers",                  "industries": ["CPG & Consumer Goods"],                                       "signal_types": ["labor_shortage", "labor_pain"]},
    {"query": "contract manufacturer labor shortage packaging operator hiring",                    "industries": ["Contract Manufacturing"],                                      "signal_types": ["labor_shortage", "packaging_automation"]},
    # EOL / Packaging automation buyer intent
    {"query": "food plant end-of-line packaging automation robotic palletizer investment 2025",    "industries": ["Food Processing & Manufacturing", "CPG & Consumer Goods"],  "signal_types": ["packaging_automation", "capex"]},
    {"query": "CPG company robotic case packer palletizer installation 2025 2026",                 "industries": ["CPG & Consumer Goods"],                                       "signal_types": ["packaging_automation", "automation_intent"]},
    {"query": "beverage bottling plant packaging line automation robotic upgrade",                  "industries": ["CPG & Consumer Goods", "Food Processing & Manufacturing"],  "signal_types": ["packaging_automation", "capex"]},
    {"query": "contract packager co-packer automation robot palletizer case packing",              "industries": ["Contract Manufacturing"],                                      "signal_types": ["packaging_automation", "automation_intent"]},
    {"query": "food manufacturing intralogistics AGV AMR internal transport robot",                "industries": ["Food Processing & Manufacturing"],                            "signal_types": ["material_handling", "automation_intent"]},
    # Pack-in / pack-out / pack line pain
    {"query": "pack out pack in manual line operator throughput bottleneck food plant",             "industries": ["Food Processing & Manufacturing", "CPG & Consumer Goods"],  "signal_types": ["repetitive_process", "production_capacity"]},
    {"query": "packaging line efficiency improvement throughput investment food beverage",          "industries": ["Food Processing & Manufacturing", "CPG & Consumer Goods"],  "signal_types": ["production_capacity", "packaging_automation"]},
    # Expansions & capex
    {"query": "food manufacturing plant expansion new facility investment groundbreaking 2025",    "industries": ["Food Processing & Manufacturing"],                            "signal_types": ["expansion", "capex"]},
    {"query": "CPG company new production line capacity expansion 2025 2026",                     "industries": ["CPG & Consumer Goods"],                                       "signal_types": ["production_capacity", "expansion", "capex"]},
    {"query": "food beverage plant modernization upgrade capital investment automation",            "industries": ["Food Processing & Manufacturing", "CPG & Consumer Goods"],  "signal_types": ["capex", "automation_intent"]},
    # Buyer persona hires
    {"query": "VP Director engineering automation food beverage plant appointed 2025",             "industries": ["Food Processing & Manufacturing", "CPG & Consumer Goods"],  "signal_types": ["strategic_hire"]},
    {"query": "plant manager director manufacturing operations food company appointed",            "industries": ["Food Processing & Manufacturing"],                            "signal_types": ["strategic_hire"]},
    {"query": "VP operations CPG consumer goods company appointed hired 2025",                    "industries": ["CPG & Consumer Goods"],                                       "signal_types": ["strategic_hire"]},
    # Named CPG / food manufacturer targets
    {"query": "Kraft Heinz Mondelez Nestle plant automation investment operations",               "industries": ["CPG & Consumer Goods"],                                       "signal_types": ["capex", "automation_intent"]},
    {"query": "Tyson Foods JBS Cargill Smithfield plant labor automation investment",             "industries": ["Food Processing & Manufacturing"],                            "signal_types": ["labor_shortage", "capex"]},
    {"query": "General Mills Campbell Conagra plant expansion new facility 2025",                 "industries": ["CPG & Consumer Goods"],                                       "signal_types": ["expansion", "capex"]},
    {"query": "Anheuser-Busch Molson Coors Constellation Brands brewery plant automation",       "industries": ["CPG & Consumer Goods"],                                       "signal_types": ["packaging_automation", "capex"]},

    # === MANUFACTURING OPERATIONAL SIGNALS (NEW) ===
    # Quality Bottlenecks
    {"query": "manufacturing quality issues defect rate scrap reduction initiative 2025",               "industries": ["Manufacturing", "Logistics"],  "signal_types": ["quality_bottleneck"]},
    {"query": "factory quality control problems inspection failure reject rate improvement",            "industries": ["Manufacturing"],               "signal_types": ["quality_bottleneck"]},
    {"query": "production line rework scrap waste reduction quality improvement program",               "industries": ["Manufacturing"],               "signal_types": ["quality_bottleneck"]},
    {"query": "packaging quality defects damage rate quality assurance automation",                     "industries": ["Manufacturing", "Logistics"],  "signal_types": ["quality_bottleneck", "packaging_automation"]},
    
    # Safety Incidents
    {"query": "manufacturing workplace injury OSHA ergonomic repetitive strain worker safety",          "industries": ["Manufacturing", "Logistics"],  "signal_types": ["safety_incident"]},
    {"query": "warehouse forklift accident worker injury safety incident automation solution",          "industries": ["Logistics"],                   "signal_types": ["safety_incident", "material_handling"]},
    {"query": "factory back injury lifting repetitive motion ergonomic workplace safety 2025",          "industries": ["Manufacturing"],               "signal_types": ["safety_incident"]},
    {"query": "distribution center safety violation OSHA fine penalty workplace injury prevention",     "industries": ["Logistics"],                   "signal_types": ["safety_incident"]},
    
    # Production Capacity Constraints
    {"query": "manufacturing running at capacity bottleneck production expansion 24/7 operations",      "industries": ["Manufacturing"],               "signal_types": ["production_capacity"]},
    {"query": "factory maxed out capacity overtime production constraint throughput limit 2025",        "industries": ["Manufacturing"],               "signal_types": ["production_capacity"]},
    {"query": "production capacity expansion investment new line manufacturing throughput",             "industries": ["Manufacturing"],               "signal_types": ["production_capacity", "capex"]},
    {"query": "assembly line bottleneck capacity constraint production efficiency improvement",         "industries": ["Manufacturing"],               "signal_types": ["production_capacity", "repetitive_process"]},
    
    # Warehouse Throughput Issues
    {"query": "warehouse throughput pick rate fulfillment delay shipping backlog efficiency",           "industries": ["Logistics"],                   "signal_types": ["warehouse_throughput"]},
    {"query": "distribution center order backlog processing capacity picking productivity improvement", "industries": ["Logistics"],                   "signal_types": ["warehouse_throughput"]},
    {"query": "fulfillment center efficiency throughput improvement pick pack automation 2025",         "industries": ["Logistics"],                   "signal_types": ["warehouse_throughput", "automation_intent"]},
    {"query": "warehouse picking speed productivity picking accuracy efficiency technology investment",  "industries": ["Logistics"],                   "signal_types": ["warehouse_throughput", "capex"]},
    
    # Packaging Automation
    {"query": "packaging line automation end-of-line palletizing case packing investment 2025",         "industries": ["Manufacturing", "Logistics"],  "signal_types": ["packaging_automation"]},
    {"query": "automated packaging system palletizer robotic case packer manufacturing facility",       "industries": ["Manufacturing"],               "signal_types": ["packaging_automation"]},
    {"query": "end-of-line packaging automation efficiency improvement throughput production",          "industries": ["Manufacturing", "Logistics"],  "signal_types": ["packaging_automation"]},
    {"query": "palletizing automation robotic packaging line investment warehouse distribution",        "industries": ["Logistics"],                   "signal_types": ["packaging_automation", "capex"]},
    
    # Repetitive Processes
    {"query": "manufacturing repetitive task manual process assembly line automation opportunity",      "industries": ["Manufacturing"],               "signal_types": ["repetitive_process"]},
    {"query": "factory repetitive motion manual handling ergonomic automation solution 2025",           "industries": ["Manufacturing"],               "signal_types": ["repetitive_process", "safety_incident"]},
    {"query": "warehouse repetitive picking manual process automation efficiency improvement",          "industries": ["Logistics"],                   "signal_types": ["repetitive_process", "warehouse_throughput"]},
    {"query": "assembly line manual work repetitive operations automation robotics deployment",         "industries": ["Manufacturing"],               "signal_types": ["repetitive_process"]},
    
    # Material Handling & Intralogistics
    {"query": "warehouse forklift operations material handling AGV AMR autonomous solution",            "industries": ["Logistics"],                   "signal_types": ["material_handling"]},
    {"query": "factory internal logistics material transport intralogistics automation investment",     "industries": ["Manufacturing"],               "signal_types": ["material_handling"]},
    {"query": "distribution center material handling equipment upgrade automation technology 2025",     "industries": ["Logistics"],                   "signal_types": ["material_handling", "capex"]},
    {"query": "manufacturing material movement warehouse transport autonomous mobile robots AMR",       "industries": ["Manufacturing", "Logistics"],  "signal_types": ["material_handling"]},
]

# -- RFP & Project Marketplaces: HIGH-VALUE DIRECT BUYER INTENT --------------
# Companies actively posting automation projects = ready to buy

RFP_MARKETPLACE_TARGETS: List[ScrapeTarget] = [
    # Qviro - Automation Project Marketplace
    ScrapeTarget(
        url="https://qviro.com/match/projects",
        label="Qviro - Automation Project Marketplace",
        scraper="rfp_marketplace",
        cadence="daily",
        industries=["Manufacturing", "Logistics", "Food Service"],
        signal_types=["automation_intent", "rfp_posted", "budget_allocated"],
        notes="Companies posting automation projects = direct vendor selection phase. Robot + integrator opportunities."
    ),
    
    # JobToRob - Global Robotics RFP Database
    ScrapeTarget(
        url="https://jobtorob.com/global-robotics-command-center-tenders",
        label="JobToRob - Global Robotics Tenders & RFPs",
        scraper="rfp_marketplace",
        cadence="daily",
        industries=["Manufacturing", "Healthcare", "Logistics", "Government"],
        signal_types=["rfp_posted", "government_contract", "budget_allocated"],
        notes="Government + commercial robotics tenders: delivery robots, AMRs, surgical robots, facility management"
    ),
    
    # Automate America - Industrial Automation RFQs
    ScrapeTarget(
        url="https://automateamerica.com/automation-rfqs-and-projects/",
        label="Automate America - Factory Automation RFQs",
        scraper="rfp_marketplace",
        cadence="daily",
        industries=["Manufacturing", "Automotive"],
        signal_types=["rfp_posted", "automation_intent", "factory_automation"],
        notes="Assembly automation, robotic machine tending, factory equipment. Automotive + heavy industry."
    ),
    
    # RFPBot - RFP Discovery Platform
    ScrapeTarget(
        url="https://rfpbot.com/search?keywords=robotics+automation+cobot",
        label="RFPBot - Automation RFP Scanner",
        scraper="rfp_marketplace",
        cadence="daily",
        industries=["Manufacturing", "Logistics", "Healthcare", "Government"],
        signal_types=["rfp_posted", "automation_intent", "government_contract", "budget_allocated"],
        notes="PREMIUM SOURCE: Scans thousands of RFP portals. Set keywords: robotics, robotic automation, cobot, industrial robot, warehouse automation"
    ),
]


# -- Government Tender Websites: HIGH-VALUE CONTRACTS ------------------------
# Government procurement = large budgets, transparent requirements, multi-year contracts

GOVERNMENT_TENDER_TARGETS: List[ScrapeTarget] = [
    # United States - SAM.gov (System for Award Management)
    ScrapeTarget(
        url="https://sam.gov/search?index=opp&page=1&keywords=robotics+automation+unmanned",
        label="SAM.gov - US Federal Contract Opportunities",
        scraper="rfp_marketplace",
        cadence="daily",
        industries=["Government", "Defense", "Infrastructure"],
        signal_types=["government_contract", "rfp_posted", "budget_allocated"],
        notes="US federal procurement. Keywords: robotics, inspection robot, warehouse automation, unmanned systems, robotic automation. HUGE budgets."
    ),
    
    # United States - GSA.gov
    ScrapeTarget(
        url="https://www.gsa.gov/buy-through-us/purchasing-programs/gsa-schedules",
        label="GSA.gov - General Services Administration",
        scraper="rfp_marketplace",
        cadence="daily",
        industries=["Government"],
        signal_types=["government_contract", "rfp_posted"],
        notes="GSA Schedule opportunities for government automation projects. Pre-approved vendor programs."
    ),
    
    # Europe - TED (Tenders Electronic Daily)
    ScrapeTarget(
        url="https://ted.europa.eu/en/search?q=robotics+automation",
        label="TED - EU Tenders Electronic Daily",
        scraper="rfp_marketplace",
        cadence="daily",
        industries=["Government", "Infrastructure", "Manufacturing"],
        signal_types=["government_contract", "rfp_posted", "budget_allocated"],
        notes="EU publishes THOUSANDS of automation/robotics tenders yearly. All EU member states. Massive market."
    ),
    
    # Global - TendersInfo
    ScrapeTarget(
        url="https://www.tendersinfo.com/search/robotics-automation",
        label="TendersInfo - Global Tender Database",
        scraper="rfp_marketplace",
        cadence="daily",
        industries=["Government", "Defense", "Agriculture", "Infrastructure"],
        signal_types=["government_contract", "rfp_posted", "automation_intent"],
        notes="Global government tenders: defense, infrastructure, agriculture, smart cities. Multi-country coverage."
    ),
    
    # Global - Biddingo
    ScrapeTarget(
        url="https://www.biddingo.com/tenders/robotics",
        label="Biddingo - Global Procurement Platform",
        scraper="rfp_marketplace",
        cadence="daily",
        industries=["Government", "Manufacturing", "Infrastructure"],
        signal_types=["government_contract", "rfp_posted"],
        notes="Worldwide government + enterprise procurement. Robotics for defense, smart cities, industrial automation."
    ),
    
    # Canada/North America - MERX
    ScrapeTarget(
        url="https://www.merx.com/search/?keywords=robotics+automation",
        label="MERX - Canadian Government Procurement",
        scraper="rfp_marketplace",
        cadence="daily",
        industries=["Government", "Infrastructure"],
        signal_types=["government_contract", "rfp_posted"],
        notes="Canadian federal, provincial, municipal procurement. Also covers some US state/local contracts."
    ),
]


# -- LinkedIn Search Queries: SOCIAL BUYING SIGNALS --------------------------
# LinkedIn posts reveal projects before official RFPs

LINKEDIN_SEARCH_QUERIES: List[dict] = [
    # Project announcement signals
    {"query": "robot automation project",          "signal_types": ["automation_intent", "project_planning"]},
    {"query": "robotics RFP",                      "signal_types": ["rfp_posted", "vendor_selection"]},
    {"query": "automation system integrator",      "signal_types": ["automation_intent", "vendor_search"]},
    {"query": "factory automation upgrade",        "signal_types": ["capex", "automation_intent"]},
    {"query": "looking for cobot",                 "signal_types": ["automation_intent", "vendor_search"]},
    {"query": "warehouse automation project",      "signal_types": ["automation_intent", "logistics"]},
    {"query": "AMR implementation",                "signal_types": ["automation_intent", "mobile_robots"]},
    {"query": "robotic process automation budget", "signal_types": ["budget_allocated", "automation_intent"]},
]

# ── OEM Discovery Queries (XBOT / StageGate pipeline) ────────────────────────
# Purpose: find robot COMPANIES (OEMs) attending or exhibiting at trade shows.
# These are the prospects StageGate pitches logistics and staging services to.
# Used by XBOT in StageGate — NOT filtered by the buyer-mode junk filter.

OEM_DISCOVERY_QUERIES = [
    # Humanoids
    {"query": "humanoid robot company exhibiting trade show 2026", "robot_type": "humanoid"},
    {"query": "humanoid robot CES NAB Automate show floor demo 2026", "robot_type": "humanoid"},
    {"query": "bipedal robot startup attending conference Las Vegas", "robot_type": "humanoid"},
    # AMR / Wheeled
    {"query": "autonomous mobile robot AMR company trade show exhibit 2026", "robot_type": "wheeled_amr"},
    {"query": "warehouse robot AMR exhibiting MODEX Automate ProMat 2026", "robot_type": "wheeled_amr"},
    {"query": "last mile delivery robot company show floor 2026", "robot_type": "wheeled_amr"},
    # Drones / UAV
    {"query": "drone company exhibiting trade show 2026 NAB CES AUVSI", "robot_type": "drone"},
    {"query": "UAV UAS company conference demo display 2026", "robot_type": "drone"},
    {"query": "commercial drone startup trade show attendee 2026", "robot_type": "drone"},
    # Industrial Arms / Cobots
    {"query": "cobot collaborative robot company exhibiting Automate 2026", "robot_type": "cobot"},
    {"query": "industrial robot arm trade show exhibit 2026 IMTS Automate", "robot_type": "industrial_arm"},
    {"query": "Fanuc KUKA ABB Universal Robots trade show 2026", "robot_type": "industrial_arm"},
    # Medical / Surgical
    {"query": "surgical robot company medical robotics trade show HIMSS 2026", "robot_type": "surgical_robot"},
    {"query": "medical robot exhibiting conference 2026 RSNA SAGES", "robot_type": "surgical_robot"},
    # Service Robots
    {"query": "service robot hospitality hotel robot company trade show 2026", "robot_type": "service_robot"},
    {"query": "cleaning disinfection robot company conference exhibit 2026", "robot_type": "service_robot"},
    # 3D Printing / Additive
    {"query": "3D printing company additive manufacturing trade show 2026", "robot_type": "3d_printer"},
    {"query": "large format 3D printer company conference exhibit IMTS 2026", "robot_type": "3d_printer"},
    # General OEM discovery
    {"query": "robotics company Las Vegas trade show logistics support 2026", "robot_type": "general"},
    {"query": "robot company shipping robots to Las Vegas conference 2026", "robot_type": "general"},
    {"query": "robot OEM attending CES Automate Manifest 2026 2027", "robot_type": "general"},
    {"query": "robotics startup trade show booth exhibitor 2026", "robot_type": "general"},

    # ── PR / Pre-Show Announcement Monitoring ─────────────────────────────────
    # These catch companies BEFORE the exhibitor list is published
    {"query": '"will unveil at CES" robot 2026', "robot_type": "pr_signal"},
    {"query": '"debuting at CES" robot 2026', "robot_type": "pr_signal"},
    {"query": '"showcasing at CES" robot 2026', "robot_type": "pr_signal"},
    {"query": '"Las Vegas demo" robot company 2026', "robot_type": "pr_signal"},
    {"query": '"Automate 2026" robot company exhibiting', "robot_type": "pr_signal"},
    {"query": '"MODEX 2026" robot company booth', "robot_type": "pr_signal"},
    {"query": '"Manifest 2026" robot logistics demo', "robot_type": "pr_signal"},
    {"query": 'site:prnewswire.com robot CES 2026 exhibit', "robot_type": "pr_signal"},
    {"query": 'site:businesswire.com robot CES 2026 showcase', "robot_type": "pr_signal"},
    {"query": 'site:globenewswire.com humanoid robot CES 2026', "robot_type": "pr_signal"},

    # ── Country Pavilion Discovery ─────────────────────────────────────────────
    # International first-timers: highest StageGate need (no local support)
    {"query": "Japan Pavilion CES 2026 robotics company", "robot_type": "intl_pavilion"},
    {"query": "Korea Pavilion CES 2026 humanoid robot startup", "robot_type": "intl_pavilion"},
    {"query": "France Pavilion CES 2026 robot company", "robot_type": "intl_pavilion"},
    {"query": "Hong Kong Pavilion CES 2026 robotics exhibitor", "robot_type": "intl_pavilion"},
    {"query": "China Pavilion CES 2026 robot company exhibitor", "robot_type": "intl_pavilion"},
    {"query": "German Pavilion Hannover Messe robot company Las Vegas", "robot_type": "intl_pavilion"},
    {"query": "Israeli Pavilion CES 2026 robotics startup", "robot_type": "intl_pavilion"},
    {"query": "Taiwan Pavilion Computex robot company CES", "robot_type": "intl_pavilion"},
    {"query": "first time US trade show robot company international exhibitor", "robot_type": "intl_pavilion"},

    # ── Freight / Logistics Risk Signals ──────────────────────────────────────
    # Companies shipping robots internationally = strong StageGate fit
    {"query": "robot company ATA carnet trade show Las Vegas", "robot_type": "shipping_signal"},
    {"query": "robot lithium battery shipping trade show 2026", "robot_type": "shipping_signal"},
    {"query": "robot temporary import bond trade show US", "robot_type": "shipping_signal"},
    {"query": "robot company bonded warehouse Las Vegas trade show", "robot_type": "shipping_signal"},
    {"query": "shipping humanoid robot international trade show customs", "robot_type": "shipping_signal"},

    # ── Exhibit Builder / Show Service Intel ──────────────────────────────────
    # Freeman/GES partnerships — companies with complex booths need robot ops support
    {"query": "Freeman GES robot exhibitor CES MODEX Automate 2026", "robot_type": "exhibit_signal"},
    {"query": "large booth robot company CES Automate 2026 rigging", "robot_type": "exhibit_signal"},
    {"query": "robot demo booth installation CES Las Vegas 2026", "robot_type": "exhibit_signal"},

    # ── LinkedIn / Social Monitoring Patterns ─────────────────────────────────
    {"query": '"See us at CES" robot company 2026', "robot_type": "social_signal"},
    {"query": '"demoing our robot" CES Las Vegas 2026', "robot_type": "social_signal"},
    {"query": '"Eureka Park" robot startup CES 2026', "robot_type": "social_signal"},
    {"query": '"coming to CES" humanoid robot company 2026', "robot_type": "social_signal"},
    {"query": "robot company attending Automate 2026 Chicago booth", "robot_type": "social_signal"},

    # ── Robotics Media RSS Monitoring ─────────────────────────────────────────
    {"query": 'site:therobotreport.com CES 2026 exhibitor', "robot_type": "media_signal"},
    {"query": 'site:robotics24x7.com trade show robot 2026 exhibitor', "robot_type": "media_signal"},
    {"query": 'site:ieee.org spectrum robotics CES 2026', "robot_type": "media_signal"},
    {"query": "automate.org robot exhibitor 2026 announcement", "robot_type": "media_signal"},

    # ── ICP 1: CES Eureka Park startups ───────────────────────────────────────
    {"query": "Eureka Park CES 2026 2027 robot startup", "robot_type": "eureka_park"},
    {"query": "CES 2026 innovation award robotics startup exhibitor", "robot_type": "eureka_park"},
    {"query": "CES 2026 startup pavilion robot company first time", "robot_type": "eureka_park"},
    {"query": "robotics seed startup CES exhibitor Las Vegas 2026 2027", "robot_type": "eureka_park"},

    # ── ICP 2: Foreign humanoid robot companies ────────────────────────────────
    {"query": "Chinese humanoid robot company CES Las Vegas US market entry 2026", "robot_type": "foreign_humanoid"},
    {"query": "Korean humanoid robot startup CES 2026 exhibitor US debut", "robot_type": "foreign_humanoid"},
    {"query": "Japanese robot company first US trade show CES 2026 humanoid", "robot_type": "foreign_humanoid"},
    {"query": "European humanoid robot company CES Automate US entry 2026", "robot_type": "foreign_humanoid"},
    {"query": "China humanoid robot export US trade show market entry 2026 2027", "robot_type": "foreign_humanoid"},

    # ── ICP 3: Medical robot companies ────────────────────────────────────────
    {"query": "surgical robot company trade show HIMSS CES Automate 2026 exhibit", "robot_type": "medical_robot"},
    {"query": "medical robot exhibiting Las Vegas HIMSS 2026 convention center", "robot_type": "medical_robot"},
    {"query": "rehabilitation robot exoskeleton medical CES trade show 2026", "robot_type": "medical_robot"},

    # ── ICP 4: Hospitality / service robots ───────────────────────────────────
    {"query": "hotel service robot company CES 2026 exhibitor delivery", "robot_type": "hospitality_robot"},
    {"query": "restaurant robot food delivery robot CES Las Vegas trade show 2026", "robot_type": "hospitality_robot"},
    {"query": "hospitality robot company HIMSS CES trade show booth 2026", "robot_type": "hospitality_robot"},

    # ── ICP 5: Security robots ────────────────────────────────────────────────
    {"query": "security patrol robot company CES trade show 2026 exhibitor", "robot_type": "security_robot"},
    {"query": "autonomous security robot knightscope cobalt CES ISC West 2026", "robot_type": "security_robot"},

    # ── ICP 6: Warehouse AMR companies ────────────────────────────────────────
    {"query": "warehouse AMR company MODEX Automate 2026 exhibitor autonomous mobile robot", "robot_type": "warehouse_amr"},
    {"query": "fulfillment robot AMR company trade show Las Vegas CES Manifest 2026", "robot_type": "warehouse_amr"},
    {"query": "Geekplus Hikrobot Hai Robotics Quicktron trade show US 2026", "robot_type": "warehouse_amr"},

    # ── ICP 7: Chinese robot firms entering US ────────────────────────────────
    {"query": "Chinese robot company US market entry CES trade show 2026 2027", "robot_type": "china_us_entry"},
    {"query": "China robotics startup first US exhibitor CES Las Vegas 2026", "robot_type": "china_us_entry"},
    {"query": "Chinese humanoid manufacturer entering American market trade show", "robot_type": "china_us_entry"},
    {"query": "China robot OEM US distribution partner trade show 2026", "robot_type": "china_us_entry"},
]


def get_oem_discovery_queries(robot_type: Optional[str] = None) -> List[str]:
    """Return OEM discovery queries for XBOT/StageGate pipeline (oem_prospect mode)."""
    queries = OEM_DISCOVERY_QUERIES
    if robot_type:
        queries = [q for q in queries if q.get("robot_type") in (robot_type, "general")]
    return [q["query"] for q in queries]


# -- Master helpers ----------------------------------------------------------

ALL_TARGETS: List[ScrapeTarget] = (
    JOB_BOARD_TARGETS
    + HOTEL_DIRECTORY_TARGETS
    + LOGISTICS_DIRECTORY_TARGETS
    + RSS_FEED_TARGETS
    + RFP_MARKETPLACE_TARGETS
    + GOVERNMENT_TENDER_TARGETS
)


def get_targets(
    scraper: Optional[str] = None,
    industry: Optional[str] = None,
    active_only: bool = True,
) -> List[ScrapeTarget]:
    result = ALL_TARGETS
    if active_only:
        result = [t for t in result if t.active]
    if scraper:
        result = [t for t in result if t.scraper == scraper]
    if industry:
        needle = str(industry).strip().lower()
        result = [
            t
            for t in result
            if any(str(tag).strip().lower() == needle for tag in t.industries)
        ]
    return result


def get_urls(
    scraper: Optional[str] = None,
    industry: Optional[str] = None,
    active_only: bool = True,
) -> List[str]:
    return [t.url for t in get_targets(scraper, industry, active_only)]


def get_news_queries(
    industry: Optional[str] = None,
    signal_type: Optional[str] = None,
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
        "rfp_marketplace": len(get_targets("rfp_marketplace")),
        "government_tenders": len(GOVERNMENT_TENDER_TARGETS),
        "news_queries":  len(NEWS_QUERIES),
        "linkedin_queries": len(LINKEDIN_SEARCH_QUERIES),
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
