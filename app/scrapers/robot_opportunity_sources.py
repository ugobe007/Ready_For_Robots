"""Robot opportunity source catalog — where to find work robots can be hired for.

Four lanes, most durable first:

  1. APIs (structured, no anti-bot):  Amazon Jobs JSON, Adzuna, Jooble, USAJOBS,
     SAM.gov tenders, and employer ATS boards (Greenhouse / Lever / Ashby /
     SmartRecruiters / Workday) — boards are also *discovered* automatically from
     apply links seen while scraping (see opportunity_feed_scraper).
  2. Job-board HTML search pages (Indeed / SimplyHired) for every workflow family
     in ``workflow_ontology`` — national plus robot-dense metros.
  3. Intent news (Google News RSS): deployments, automation programs, new
     DCs/plants, labor-shortage stories, RFPs — feeds the existing rss_feed pipeline.
  4. Procurement: SAM.gov keyword sweeps for robots / automation / scrubbers / AMRs.

Everything is generated from the ontology so adding a workflow family adds its
sources. ``catalog()`` returns the full list; ``scrape_targets()`` returns the
HTML + RSS subset as ``ScrapeTarget`` objects for the existing runners.

API lanes need free keys (skipped with a log line when missing):
    ADZUNA_APP_ID / ADZUNA_APP_KEY     https://developer.adzuna.com
    JOOBLE_API_KEY                     https://jooble.org/api/about
    USAJOBS_API_KEY / USAJOBS_EMAIL    https://developer.usajobs.gov
    SAM_GOV_API_KEY                    https://open.gsa.gov/api/get-opportunities-public-api/
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Optional
from urllib.parse import quote_plus

from app.services.workflow_ontology import FAMILIES, LEGACY_INDUSTRY_BY_CLASS


@dataclass(frozen=True)
class OpportunitySource:
    kind: str                      # job_board | rss_feed | amazon_jobs | adzuna | jooble | usajobs | sam_gov |
                                   # greenhouse | lever | ashby | smartrecruiters | workday
    label: str
    url: str = ""                  # html / rss sources
    params: tuple[tuple[str, Any], ...] = ()
    industries: tuple[str, ...] = ()
    families: tuple[str, ...] = ()
    lane: str = "posting"          # posting | intent_news | tender
    needs_env: tuple[str, ...] = ()
    verified: bool = False         # endpoint/format checked by a human or validator

    def param(self, key: str, default: Any = None) -> Any:
        return dict(self.params).get(key, default)

    @property
    def key(self) -> str:
        return f"{self.kind}:{self.url or dict(self.params)}"


# ─── Search vocabulary per family (what an employer actually titles the job) ──
# Hand-picked, board-friendly phrases. 2 per family nationally; metros get the first.
FAMILY_QUERIES: dict[str, tuple[str, ...]] = {
    "picking": ("order picker", "order selector warehouse"),
    "packing": ("packer warehouse", "pack out associate"),
    "palletizing": ("palletizer operator", "case stacker"),
    "truck_unloading": ("trailer unloader", "package handler"),
    "material_handling": ("material handler", "tugger driver"),
    "forklift": ("forklift operator", "reach truck operator"),
    "receiving": ("receiving clerk warehouse", "inventory cycle counter"),
    "sortation": ("parcel sorter", "mail processing clerk"),
    "cold_storage": ("freezer order selector", "cold storage warehouse associate"),
    "machine_tending": ("cnc machine operator", "injection molding operator"),
    "assembly": ("assembler production", "assembly line worker"),
    "welding": ("welder fabricator", "mig welder production"),
    "finishing": ("paint line operator", "sander deburr finisher"),
    "quality_inspection": ("quality inspector production", "visual inspector"),
    "food_processing": ("poultry processing worker", "food production line worker"),
    "lab_automation": ("specimen processor", "laboratory assistant accessioning"),
    "food_prep": ("line cook high volume", "prep cook"),
    "beverage": ("barista high volume", "beverage attendant"),
    "warewash": ("dishwasher", "steward kitchen utility"),
    "serving": ("food runner", "banquet server"),
    "cashier_ordering": ("drive thru cashier", "cashier crew member"),
    "housekeeping": ("room attendant hotel", "housekeeper hotel"),
    "laundry": ("laundry attendant", "linen attendant"),
    "guest_delivery": ("bellperson", "hotel runner amenities"),
    "front_desk": ("front desk agent hotel", "night auditor"),
    "parking": ("valet attendant", "parking attendant"),
    "cleaning": ("janitor", "floor technician scrubber"),
    "environmental_services": ("environmental services technician hospital", "evs tech"),
    "facade_cleaning": ("window washer high rise", "solar panel cleaner"),
    "pool_car_wash": ("car wash attendant", "tank cleaner industrial"),
    "waste_recycling": ("recycling sorter", "mrf sorter"),
    "security_patrol": ("security officer patrol", "fire watch guard"),
    "industrial_inspection": ("plant operator rounds", "data center technician"),
    "patient_transport": ("patient transporter", "hospital courier"),
    "hospital_logistics": ("hospital supply chain technician", "dietary aide tray line"),
    "pharmacy": ("central fill pharmacy technician", "pharmacy technician"),
    "sterile_processing": ("sterile processing technician", "decontamination technician"),
    "patient_assist": ("patient sitter", "patient care companion"),
    "replenishment": ("overnight stocker", "grocery stocker"),
    "last_mile": ("delivery driver package", "courier delivery"),
    "trucking": ("yard jockey", "cdl a driver local"),
    "harvest": ("farm worker harvest", "greenhouse worker"),
    "field_work": ("tractor operator farm", "pesticide applicator"),
    "dairy_livestock": ("dairy milker", "poultry farm worker"),
    "landscaping": ("groundskeeper", "mower operator"),
    "construction_labor": ("construction laborer", "drywall finisher"),
    "mining": ("haul truck operator", "underground miner"),
    "general_labor": ("general laborer warehouse", "production associate"),
}

# Robot-dense / labor-tight metros. Las Vegas first: casinos + hotels + DCs.
METROS: tuple[str, ...] = (
    "Las Vegas, NV", "Dallas, TX", "Ontario, CA", "Atlanta, GA", "Chicago, IL",
    "Phoenix, AZ", "Houston, TX", "Columbus, OH", "Indianapolis, IN", "Memphis, TN",
    "Reno, NV", "Allentown, PA", "Nashville, TN", "Orlando, FL", "Charlotte, NC",
)

# Families worth a metro sweep (high volume + high automatability).
METRO_FAMILIES: tuple[str, ...] = (
    "picking", "material_handling", "cleaning", "warewash", "housekeeping", "food_prep",
    "security_patrol", "palletizing", "serving", "forklift",
)

LAS_VEGAS_EXTRA: tuple[tuple[str, str], ...] = (
    ("casino porter", "cleaning"), ("casino utility porter", "cleaning"), ("banquet houseperson", "serving"),
    ("room service server", "serving"), ("casino steward", "warewash"), ("cocktail server casino", "serving"),
    ("convention center custodian", "cleaning"), ("public area attendant casino", "cleaning"),
    ("buffet attendant", "serving"), ("hotel laundry attendant", "laundry"),
)


def _indeed(q: str, loc: str = "United States") -> str:
    return f"https://www.indeed.com/jobs?q={quote_plus(q)}&l={quote_plus(loc)}&sort=date&fromage=14"


def _simplyhired(q: str, loc: str = "United States") -> str:
    return f"https://www.simplyhired.com/search?q={quote_plus(q)}&l={quote_plus(loc)}&t=14"


def _gnews(q: str) -> str:
    return f"https://news.google.com/rss/search?q={quote_plus(q)}+when:30d&hl=en-US&gl=US&ceid=US:en"


def _industries(family_key: str) -> tuple[str, ...]:
    fam = next((f for f in FAMILIES if f.key == family_key), None)
    if not fam:
        return ()
    legacy = LEGACY_INDUSTRY_BY_CLASS.get(fam.product_class)
    out = [legacy] if legacy else []
    out += [i for i in fam.industries[:2] if i not in out]
    return tuple(out)


def _job_board_sources() -> list[OpportunitySource]:
    out: list[OpportunitySource] = []
    for fam_key, queries in FAMILY_QUERIES.items():
        inds = _industries(fam_key)
        for q in queries:
            out.append(OpportunitySource("job_board", f"Indeed · {q}", _indeed(q), industries=inds, families=(fam_key,), verified=True))
        out.append(OpportunitySource("job_board", f"SimplyHired · {queries[0]}", _simplyhired(queries[0]),
                                     industries=inds, families=(fam_key,), verified=True))
    for metro in METROS:
        for fam_key in METRO_FAMILIES[: (10 if metro == "Las Vegas, NV" else 4)]:
            q = FAMILY_QUERIES[fam_key][0]
            out.append(OpportunitySource("job_board", f"Indeed · {q} · {metro}", _indeed(q, metro),
                                         industries=_industries(fam_key), families=(fam_key,), verified=True))
    for q, fam_key in LAS_VEGAS_EXTRA:
        out.append(OpportunitySource("job_board", f"Indeed · {q} · Las Vegas", _indeed(q, "Las Vegas, NV"),
                                     industries=_industries(fam_key) + ("Hospitality",), families=(fam_key,), verified=True))
    return out


# ─── Intent news (Google News RSS → existing rss_feed pipeline) ──────────────
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
    return [
        OpportunitySource("rss_feed", f"Google News · {q[:60]}", _gnews(q), industries=inds, lane="intent_news", verified=True)
        for q, inds in INTENT_NEWS_QUERIES
    ]


# ─── API lanes ───────────────────────────────────────────────────────────────
AMAZON_QUERIES = (
    "warehouse associate", "fulfillment center associate", "sortation center", "delivery station",
    "rme technician", "robotics technician", "amazon robotics", "grocery associate", "prime air ground",
    "cold storage associate", "air hub associate", "returns center associate",
)

USAJOBS_KEYWORDS = (
    "custodial worker", "warehouse worker", "materials handler", "food service worker", "laundry worker",
    "housekeeping aid", "sterile processing", "pharmacy technician", "motor vehicle operator", "mail clerk",
    "security guard", "laborer", "packer", "sales store checker", "equipment cleaner", "cook",
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
    for fam_key, queries in FAMILY_QUERIES.items():
        inds = _industries(fam_key)
        out.append(OpportunitySource("adzuna", f"Adzuna · {queries[0]}", params=(("what", queries[0]),),
                                     industries=inds, families=(fam_key,), needs_env=("ADZUNA_APP_ID", "ADZUNA_APP_KEY")))
        out.append(OpportunitySource("jooble", f"Jooble · {queries[0]}", params=(("keywords", queries[0]),),
                                     industries=inds, families=(fam_key,), needs_env=("JOOBLE_API_KEY",)))
    for kw in USAJOBS_KEYWORDS:
        out.append(OpportunitySource("usajobs", f"USAJOBS · {kw}", params=(("keyword", kw),),
                                     industries=("Government",), needs_env=("USAJOBS_API_KEY", "USAJOBS_EMAIL")))
    for kw in SAM_GOV_KEYWORDS:
        out.append(OpportunitySource("sam_gov", f"SAM.gov tenders · {kw}", params=(("keyword", kw),),
                                     industries=("Government",), lane="tender", needs_env=("SAM_GOV_API_KEY",)))
    for ats, token, company in SEED_ATS_BOARDS:
        out.append(OpportunitySource(ats, f"{company} ({ats})", params=(("token", token), ("company", company)),
                                     verified=True))
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
            signal_types=["robot_job"] if s.kind == "job_board" else ["automation_intent", "expansion", "labor_shortage"],
            cadence="daily", notes=f"robot_opportunity_sources families={','.join(s.families)}",
        ))
    return out


def summary() -> dict[str, int]:
    from collections import Counter

    return dict(Counter(s.kind for s in catalog()))
