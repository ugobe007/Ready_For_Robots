"""Buyer-intent source catalog — find COMPANIES ready to buy or pilot robots.

We are not collecting labor postings. Every source here is aimed at evidence that
a named company is buying, evaluating, or already running robots:

  1. Tenders     SAM.gov keyword sweeps (robots, AMRs, scrubbers, conveyors…) +
                 RFP news. → stage buying_now
  2. Deployments Google News: "<vendor> deploys/selects/partners" (customers named
                 in vendor press), "<industry> pilots robots", automation programs,
                 new automated facilities. → buying_now / evaluating / expanding
  3. Automation hiring at operators (job boards, Amazon Jobs, Adzuna/Jooble):
                 AMR / robotics / automation technicians, automation engineers and
                 managers, CI leaders at warehouses, plants, hotels, hospitals —
                 a company staffing robot ops is buying robots. → evaluating / expanding
  4. ATS boards  auto-discovered from apply links (Greenhouse/Lever/Ashby/
                 SmartRecruiters/Workday), polled for the same automation roles.

Roll-up per company: app/services/buyer_readiness.py, scripts/rank_buyers.py.

API lanes need free keys (skipped with a log line when missing):
    ADZUNA_APP_ID / ADZUNA_APP_KEY     https://developer.adzuna.com
    JOOBLE_API_KEY                     https://jooble.org/api/about
    SAM_GOV_API_KEY                    https://open.gsa.gov/api/get-opportunities-public-api/
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Optional
from urllib.parse import quote_plus


@dataclass(frozen=True)
class OpportunitySource:
    kind: str                      # job_board | rss_feed | amazon_jobs | adzuna | jooble | sam_gov |
                                   # greenhouse | lever | ashby | smartrecruiters | workday
    label: str
    url: str = ""                  # html / rss sources
    params: tuple[tuple[str, Any], ...] = ()
    industries: tuple[str, ...] = ()
    families: tuple[str, ...] = ()
    lane: str = "automation_hiring"   # tender | deployment_news | automation_hiring | ats
    needs_env: tuple[str, ...] = ()
    verified: bool = False         # URL/API format matches a known-working source

    def param(self, key: str, default: Any = None) -> Any:
        return dict(self.params).get(key, default)

    @property
    def key(self) -> str:
        return f"{self.kind}:{self.url or dict(self.params)}"


# ─── Automation hiring at operators ──────────────────────────────────────────
# (query, industries). Titles an OPERATOR posts when robots are arriving or running.
AUTOMATION_HIRING_QUERIES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("AMR technician warehouse", ("Logistics",)),
    ("autonomous mobile robot technician", ("Logistics",)),
    ("robotics technician distribution center", ("Logistics",)),
    ("automation technician distribution center", ("Logistics",)),
    ("automation technician warehouse conveyor sortation", ("Logistics",)),
    ("ASRS technician", ("Logistics",)),
    ("AutoStore technician", ("Logistics", "Retail")),
    ("MHE technician automation", ("Logistics",)),
    ("automation engineer distribution center", ("Logistics",)),
    ("automation manager warehouse", ("Logistics",)),
    ("director of automation supply chain", ("Logistics",)),
    ("automation project manager fulfillment", ("Logistics",)),
    ("robotics engineer operations warehouse", ("Logistics",)),
    ("autonomous forklift", ("Logistics",)),
    ("robot operator warehouse", ("Logistics",)),
    ("robotic palletizer technician", ("Factory",)),
    ("robot technician manufacturing plant", ("Factory",)),
    ("cobot operator", ("Factory",)),
    ("robotic welding operator", ("Factory",)),
    ("robot programmer production", ("Factory",)),
    ("automation engineer food manufacturing", ("Factory",)),
    ("automation specialist packaging", ("Factory",)),
    ("controls engineer automation plant", ("Factory",)),
    ("director of automation manufacturing", ("Factory",)),
    ("continuous improvement manager automation", ("Factory", "Logistics")),
    ("industrial engineer automation", ("Factory", "Logistics")),
    ("hotel robot", ("Hospitality",)),
    ("robot attendant hotel", ("Hospitality",)),
    ("hospitality innovation technology director", ("Hospitality",)),
    ("casino technology innovation", ("Hospitality",)),
    ("robot server restaurant", ("Food Service",)),
    ("kitchen automation", ("Food Service",)),
    ("restaurant innovation automation", ("Food Service",)),
    ("food service robotics", ("Food Service",)),
    ("cleaning robot operator", ("Cleaning",)),
    ("autonomous floor scrubber", ("Cleaning",)),
    ("robotic cleaning technician", ("Cleaning",)),
    ("janitorial technology robotics", ("Cleaning",)),
    ("hospital robotics coordinator", ("Healthcare",)),
    ("pharmacy automation technician", ("Healthcare",)),
    ("hospital automation supply chain", ("Healthcare",)),
    ("lab automation specialist", ("Healthcare",)),
    ("UV disinfection robot", ("Healthcare",)),
    ("security robot", ("Facilities",)),
    ("drone program manager inspection", ("Facilities",)),
    ("data center robotics", ("Facilities",)),
    ("agricultural robotics operations", ("Agriculture",)),
    ("autonomous tractor operator", ("Agriculture",)),
    ("construction robotics", ("Construction",)),
    ("retail store automation inventory robot", ("Retail",)),
)

# Robot-dense metros (Las Vegas first). Metro sweeps use the first queries below.
METROS: tuple[str, ...] = (
    "Las Vegas, NV", "Dallas, TX", "Ontario, CA", "Atlanta, GA", "Chicago, IL",
    "Phoenix, AZ", "Houston, TX", "Columbus, OH", "Indianapolis, IN", "Memphis, TN",
    "Reno, NV", "Allentown, PA", "Nashville, TN", "Orlando, FL", "Charlotte, NC",
)
METRO_QUERIES: tuple[str, ...] = (
    "robotics technician", "automation technician", "automation engineer", "AMR technician",
)
LAS_VEGAS_EXTRA: tuple[str, ...] = (
    "hotel robot", "casino technology innovation", "kitchen automation", "cleaning robot",
    "robot server", "security robot",
)


def _indeed(q: str, loc: str = "United States") -> str:
    return f"https://www.indeed.com/jobs?q={quote_plus(q)}&l={quote_plus(loc)}&sort=date&fromage=30"


def _simplyhired(q: str, loc: str = "United States") -> str:
    return f"https://www.simplyhired.com/search?q={quote_plus(q)}&l={quote_plus(loc)}&t=30"


def _gnews(q: str) -> str:
    return f"https://news.google.com/rss/search?q={quote_plus(q)}+when:30d&hl=en-US&gl=US&ceid=US:en"


def _job_board_sources() -> list[OpportunitySource]:
    out: list[OpportunitySource] = []
    for q, inds in AUTOMATION_HIRING_QUERIES:
        out.append(OpportunitySource("job_board", f"Indeed · {q}", _indeed(q), industries=inds, verified=True))
        out.append(OpportunitySource("job_board", f"SimplyHired · {q}", _simplyhired(q), industries=inds, verified=True))
    for metro in METROS:
        for q in METRO_QUERIES:
            out.append(OpportunitySource("job_board", f"Indeed · {q} · {metro}", _indeed(q, metro),
                                         industries=("Logistics", "Factory"), verified=True))
    for q in LAS_VEGAS_EXTRA:
        out.append(OpportunitySource("job_board", f"Indeed · {q} · Las Vegas", _indeed(q, "Las Vegas, NV"),
                                     industries=("Hospitality",), verified=True))
    return out


# ─── Deployment / intent news (Google News RSS → existing rss_feed pipeline) ─
# Robot vendors name their customers in press releases. Each query surfaces buyers.
VENDOR_CUSTOMER_QUERIES: tuple[tuple[str, tuple[str, ...]], ...] = tuple(
    (f'"{v}" (deploys OR selects OR "partners with" OR customer OR pilot OR rollout)', inds)
    for v, inds in (
        ("Locus Robotics", ("Logistics",)), ("Symbotic", ("Logistics", "Retail")), ("GreyOrange", ("Logistics",)),
        ("Geek+", ("Logistics",)), ("AutoStore", ("Logistics", "Retail")), ("Dexterity", ("Logistics",)),
        ("Plus One Robotics", ("Logistics",)), ("Fox Robotics", ("Logistics",)), ("Seegrid", ("Logistics", "Factory")),
        ("Vecna Robotics", ("Logistics",)), ("OTTO Motors", ("Factory",)), ("Agility Robotics", ("Logistics",)),
        ("Figure AI", ("Factory",)), ("Apptronik", ("Logistics", "Factory")), ("Boston Dynamics Stretch", ("Logistics",)),
        ("Brain Corp", ("Cleaning", "Retail")), ("Avidbots", ("Cleaning",)), ("Simbe Robotics", ("Retail",)),
        ("Knightscope", ("Facilities",)), ("Bear Robotics", ("Food Service",)), ("Pudu Robotics", ("Food Service", "Hospitality")),
        ("Keenon Robotics", ("Food Service", "Hospitality")), ("Miso Robotics", ("Food Service",)),
        ("Serve Robotics", ("Food Service",)), ("Starship Technologies", ("Food Service",)),
        ("Diligent Robotics", ("Healthcare",)), ("Aethon TUG", ("Healthcare",)), ("Universal Robots", ("Factory",)),
        ("Path Robotics", ("Factory",)), ("Carbon Robotics", ("Agriculture",)),
    )
)

INTENT_NEWS_QUERIES: tuple[tuple[str, tuple[str, ...]], ...] = (
    # Deployments / programs (named operator buying robots now)
    ('"deploys robots" OR "deployed robots" warehouse', ("Logistics",)),
    ('"autonomous mobile robots" distribution center rollout', ("Logistics",)),
    ('"robotic palletizing" plant investment', ("Factory",)),
    ('"automated storage and retrieval" new facility', ("Logistics",)),
    ('"goods-to-person" OR AutoStore installs grocer OR retailer', ("Retail", "Logistics")),
    ('"cleaning robots" airport OR mall OR casino', ("Cleaning", "Hospitality")),
    ('"floor scrubbing robots" deploy', ("Cleaning",)),
    ('hotel "delivery robot" OR "service robot" guests', ("Hospitality",)),
    ('casino robots Las Vegas', ("Hospitality",)),
    ('restaurant "robot" kitchen fry OR bowl OR burger chain', ("Food Service",)),
    ('"robot servers" OR "serving robots" restaurant chain', ("Food Service",)),
    ('hospital "robots" deliver medications OR linens OR meals', ("Healthcare",)),
    ('"UV disinfection robots" hospital', ("Healthcare",)),
    ('pharmacy automation "central fill" new', ("Healthcare",)),
    ('"security robots" patrol property OR campus OR parking', ("Facilities",)),
    ('"robotic welding" manufacturer expands', ("Factory",)),
    ('"cobots" machine tending manufacturer', ("Factory",)),
    ('"humanoid robots" pilot warehouse OR factory OR retailer', ("Logistics", "Factory")),
    ('"robotic harvesting" OR "harvest robots" growers', ("Agriculture",)),
    ('"recycling robots" MRF', ("Factory",)),
    ('"construction robots" contractor jobsite', ("Construction",)),
    ('"autonomous forklifts" deploy', ("Logistics",)),
    ('"automated truck unloading"', ("Logistics",)),
    ('"lights-out" factory investment', ("Factory",)),
    ('"automation investment" food processing plant', ("Factory",)),
    # Strategy / budget language
    ('"automation strategy" CEO earnings warehouse OR stores', ("Logistics", "Retail")),
    ('"invest in automation" labor costs', ("Logistics", "Factory")),
    ('"to automate" distribution center million', ("Logistics",)),
    ('"chief automation officer" OR "head of robotics" appointed', ("Logistics", "Factory")),
    ('"vice president of automation" named', ("Logistics", "Factory")),
    # New capacity (new DC/plant = automation spec window)
    ('"new distribution center" "jobs" 2026', ("Logistics",)),
    ('"breaks ground" fulfillment center', ("Logistics",)),
    ('"new manufacturing plant" "jobs" announce', ("Factory",)),
    ('"cold storage facility" new construction', ("Logistics",)),
    ('new hotel casino opening Las Vegas hiring', ("Hospitality",)),
    ('"new hospital tower" opening', ("Healthcare",)),
    ('"central kitchen" OR commissary new facility chain', ("Food Service",)),
    # Labor pain (shortage → buyer)
    ('"labor shortage" warehouse workers', ("Logistics",)),
    ('"labor shortage" hotel housekeepers', ("Hospitality",)),
    ('"staffing shortage" restaurant kitchen', ("Food Service",)),
    ('"staffing shortage" hospital environmental services OR transporters', ("Healthcare",)),
    ('"labor shortage" farm harvest growers', ("Agriculture",)),
    ('"worker shortage" manufacturing plant', ("Factory",)),
    ('"janitorial" staffing shortage', ("Cleaning",)),
    ('"security guard shortage"', ("Facilities",)),
    ('"turnover" warehouse associates automation', ("Logistics",)),
    ('Culinary Union Las Vegas staffing', ("Hospitality",)),
    # Procurement in the news
    ('RFP robotic OR robots county OR city OR airport', ("Facilities",)),
    ('"request for proposals" automation warehouse OR conveyor', ("Logistics",)),
    ('"request for proposals" cleaning robots OR "autonomous scrubber"', ("Cleaning",)),
    ('school district robots cleaning OR delivery bid', ("Cleaning",)),
    ('airport "robot" pilot terminal', ("Facilities", "Cleaning")),
    ('"pilot program" robots city', ("Facilities",)),
    ('university campus "delivery robots"', ("Food Service",)),
    ('"senior living" robots pilot', ("Healthcare",)),
    ('grocery "shelf-scanning robots" OR "inventory robots"', ("Retail",)),
    ('"robotic car wash" OR "automated car wash" chain expands', ("Cleaning",)),
    ('"robotic lawn mowers" commercial OR municipal', ("Facilities",)),
    ('data center "robots" operations', ("Facilities",)),
    ('"automated parking" garage', ("Facilities",)),
)


def _news_sources() -> list[OpportunitySource]:
    out = [OpportunitySource("rss_feed", f"Google News · {q[:60]}", _gnews(q), industries=inds,
                             lane="deployment_news", verified=True) for q, inds in INTENT_NEWS_QUERIES]
    out += [OpportunitySource("rss_feed", f"Google News · {q[:60]}", _gnews(q), industries=inds,
                              lane="deployment_news", verified=True) for q, inds in VENDOR_CUSTOMER_QUERIES]
    return out


# ─── API lanes ───────────────────────────────────────────────────────────────
AMAZON_QUERIES = (
    "rme technician", "robotics technician", "amazon robotics", "automation technician",
    "controls engineer", "automation engineer",
)

SAM_GOV_KEYWORDS = (
    "robot", "robotic", "autonomous", "autonomous mobile robot", "automated guided vehicle", "conveyor",
    "automated storage", "palletizer", "floor scrubber", "cleaning robot", "disinfection robot", "UV disinfection",
    "material handling system", "sortation", "security robot", "delivery robot", "pharmacy automation",
    "automated dispensing", "food service automation", "automated warehouse", "automated parking",
    "drone inspection", "window cleaning", "robotic lawn", "automation", "cobot",
)

# Verified via the public API (Oct 2026). Others are discovered from apply links.
SEED_ATS_BOARDS: tuple[tuple[str, str, str], ...] = (
    ("greenhouse", "sweetgreen", "Sweetgreen"),
)


def _api_sources() -> list[OpportunitySource]:
    out: list[OpportunitySource] = []
    for q in AMAZON_QUERIES:
        out.append(OpportunitySource("amazon_jobs", f"Amazon Jobs · {q}", params=(("query", q),),
                                     industries=("Logistics",), verified=True))
    for q, inds in AUTOMATION_HIRING_QUERIES:
        out.append(OpportunitySource("adzuna", f"Adzuna · {q}", params=(("what", q),), industries=inds,
                                     needs_env=("ADZUNA_APP_ID", "ADZUNA_APP_KEY")))
        out.append(OpportunitySource("jooble", f"Jooble · {q}", params=(("keywords", q),), industries=inds,
                                     needs_env=("JOOBLE_API_KEY",)))
    for kw in SAM_GOV_KEYWORDS:
        out.append(OpportunitySource("sam_gov", f"SAM.gov tenders · {kw}", params=(("keyword", kw),),
                                     industries=("Government",), lane="tender", needs_env=("SAM_GOV_API_KEY",)))
    for ats, token, company in SEED_ATS_BOARDS:
        out.append(OpportunitySource(ats, f"{company} ({ats})", params=(("token", token), ("company", company)),
                                     lane="ats", verified=True))
    return out


def catalog() -> list[OpportunitySource]:
    seen: set[str] = set()
    out: list[OpportunitySource] = []
    for src in _api_sources() + _job_board_sources() + _news_sources():
        if src.key in seen:
            continue
        seen.add(src.key)
        out.append(src)
    return out


def api_sources(kinds: Optional[Iterable[str]] = None) -> list[OpportunitySource]:
    wanted = set(kinds or ())
    return [s for s in catalog() if s.kind not in ("job_board", "rss_feed") and (not wanted or s.kind in wanted)]


def scrape_targets(existing_urls: Iterable[str] = ()) -> list:
    """HTML + RSS lanes as ScrapeTargets for the existing job_board / rss_feed runners."""
    from app.scrapers.scrape_targets import ScrapeTarget

    skip = set(existing_urls)
    out = []
    for s in catalog():
        if s.kind not in ("job_board", "rss_feed") or s.url in skip:
            continue
        out.append(ScrapeTarget(
            url=s.url, label=s.label, scraper=s.kind, industries=list(s.industries),
            signal_types=["robot_job"] if s.kind == "job_board" else ["automation_intent", "deployment", "rfp_posted"],
            cadence="daily", notes=f"robot_opportunity_sources lane={s.lane}",
        ))
    return out


def summary() -> dict[str, int]:
    from collections import Counter

    return dict(Counter(s.kind for s in catalog()))
