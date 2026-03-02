"""
News Scraper  — Google News RSS
================================
Searches Google News RSS for buying-intent signals:
  - Funding rounds / capital raises
  - Expansion announcements (new facilities, properties)
  - M&A activity (acquisitions, mergers, JVs)
  - Strategic automation / robotics hires
  - CapEx plans and investment announcements
  - Labor / staffing challenges

Uses urllib (no Playwright needed — RSS is plain XML).
Each news item becomes a Signal stored in the DB and scored
by the inference engine.

Usage:
    scraper = NewsScraper(db=db)

    # Search by company names
    scraper.run_company_queries(["Marriott", "DHL", "XPO Logistics"])

    # Search by open intent keywords
    scraper.run_intent_queries()
"""
import logging
import re
import time
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.company import Company
from app.models.signal import Signal
from app.services.inference_engine import analyze

logger = logging.getLogger(__name__)

# ── Signal-worthy keywords — article must contain at least one ────────────────
RELEVANCE_KEYWORDS = [
    "automat", "robot", "AGV", "AMR", "warehouse", "logistics", "fulfillment",
    "funding", "series", "raised", "invest", "acqui", "merger",
    "expansion", "opening", "new facilit", "new propert",
    "labor shortage", "staffing", "workforce", "turnover",
    "capex", "capital expenditure", "growth plan", "strategic hire",
    "VP of", "Director of", "Head of", "Chief ", "appoint",
    "supply chain", "distribution center", "hospitality", "hotel",
]

# ── Known company → (canonical name, industry) for entity extraction ──────────
KNOWN_COMPANIES: dict = {
    # Logistics
    "xpo logistics": ("XPO Logistics", "Logistics"),
    "xpo": ("XPO Logistics", "Logistics"),
    "dhl supply chain": ("DHL Supply Chain", "Logistics"),
    "dhl": ("DHL Supply Chain", "Logistics"),
    "prologis": ("Prologis", "Logistics"),
    "amazon fulfillment": ("Amazon Fulfillment", "Logistics"),
    "amazon logistics": ("Amazon Fulfillment", "Logistics"),
    "amazon": ("Amazon Fulfillment", "Logistics"),
    "ryder": ("Ryder System", "Logistics"),
    "ryder system": ("Ryder System", "Logistics"),
    "fedex ground": ("FedEx Ground", "Logistics"),
    "fedex": ("FedEx Ground", "Logistics"),
    "ups supply chain": ("UPS Supply Chain Solutions", "Logistics"),
    "ups": ("UPS Supply Chain Solutions", "Logistics"),
    "gxo logistics": ("GXO Logistics", "Logistics"),
    "gxo": ("GXO Logistics", "Logistics"),
    "c.h. robinson": ("C.H. Robinson Worldwide", "Logistics"),
    "ch robinson": ("C.H. Robinson Worldwide", "Logistics"),
    "j.b. hunt": ("J.B. Hunt Transport Services", "Logistics"),
    "jb hunt": ("J.B. Hunt Transport Services", "Logistics"),
    "lineage logistics": ("Lineage Logistics", "Logistics"),
    "americold": ("Americold Realty Trust", "Logistics"),
    "performance food group": ("Performance Food Group", "Logistics"),
    "pfg": ("Performance Food Group", "Logistics"),
    "sysco": ("Sysco Corporation", "Logistics"),
    "us foods": ("US Foods", "Logistics"),
    "nfi industries": ("NFI Industries", "Logistics"),
    "saddle creek": ("Saddle Creek Logistics", "Logistics"),
    "kenco": ("Kenco Logistics", "Logistics"),
    "ceva logistics": ("CEVA Logistics", "Logistics"),
    "target": ("Target Corporation", "Logistics"),
    "kroger": ("Kroger Company", "Logistics"),
    "walmart": ("Walmart", "Logistics"),
    "costco": ("Costco Wholesale", "Logistics"),
    # Hospitality
    "marriott": ("Marriott International", "Hospitality"),
    "hilton": ("Hilton Worldwide Holdings", "Hospitality"),
    "ihg": ("IHG Hotels & Resorts", "Hospitality"),
    "intercontinental": ("IHG Hotels & Resorts", "Hospitality"),
    "wyndham": ("Wyndham Hotels & Resorts", "Hospitality"),
    "choice hotels": ("Choice Hotels International", "Hospitality"),
    "hyatt": ("Hyatt Hotels Corporation", "Hospitality"),
    "mgm resorts": ("MGM Resorts International", "Hospitality"),
    "mgm": ("MGM Resorts International", "Hospitality"),
    "omni hotels": ("Omni Hotels & Resorts", "Hospitality"),
    "loews hotels": ("Loews Hotels & Co", "Hospitality"),
    "aimbridge": ("Aimbridge Hospitality", "Hospitality"),
    "sage hospitality": ("Sage Hospitality Group", "Hospitality"),
    "extended stay america": ("Extended Stay America", "Hospitality"),
    "best western": ("Best Western Hotels & Resorts", "Hospitality"),
    "accor": ("Accor Hotels", "Hospitality"),
    "four seasons": ("Four Seasons Hotels & Resorts", "Hospitality"),
    "radisson": ("Radisson Hotel Group", "Hospitality"),
    # Food Service
    "mcdonald": ("McDonald's Corporation", "Food Service"),
    "starbucks": ("Starbucks Corporation", "Food Service"),
    "yum brands": ("Yum! Brands", "Food Service"),
    "yum!": ("Yum! Brands", "Food Service"),
    "restaurant brands": ("Restaurant Brands International", "Food Service"),
    "rbi": ("Restaurant Brands International", "Food Service"),
    "burger king": ("Restaurant Brands International", "Food Service"),
    "tim hortons": ("Restaurant Brands International", "Food Service"),
    "darden": ("Darden Restaurants", "Food Service"),
    "olive garden": ("Darden Restaurants", "Food Service"),
    "longhorn steakhouse": ("Darden Restaurants", "Food Service"),
    "compass group": ("Compass Group USA", "Food Service"),
    "aramark": ("Aramark Corporation", "Food Service"),
    "sodexo": ("Sodexo USA", "Food Service"),
    "delaware north": ("Delaware North Companies", "Food Service"),
    "shake shack": ("Shake Shack", "Food Service"),
    "sweetgreen": ("Sweetgreen", "Food Service"),
    "wingstop": ("Wingstop Restaurants", "Food Service"),
    "panera": ("Panera Bread", "Food Service"),
    "brinker": ("Brinker International", "Food Service"),
    "chili's": ("Brinker International", "Food Service"),
    "texas roadhouse": ("Texas Roadhouse", "Food Service"),
    "jack in the box": ("Jack in the Box", "Food Service"),
    "taco bell": ("Yum! Brands", "Food Service"),
    "kfc": ("Yum! Brands", "Food Service"),
    "pizza hut": ("Yum! Brands", "Food Service"),
    # Healthcare
    "hca healthcare": ("HCA Healthcare", "Healthcare"),
    "hca": ("HCA Healthcare", "Healthcare"),
    "brookdale": ("Brookdale Senior Living", "Healthcare"),
    "commonspirit": ("CommonSpirit Health", "Healthcare"),
    "ascension": ("Ascension Health", "Healthcare"),
    "advocate aurora": ("Advocate Aurora Health", "Healthcare"),
    "kaiser permanente": ("Kaiser Permanente", "Healthcare"),
    "kaiser": ("Kaiser Permanente", "Healthcare"),
    "mayo clinic": ("Mayo Clinic", "Healthcare"),
    "tenet healthcare": ("Tenet Healthcare", "Healthcare"),
    "tenet": ("Tenet Healthcare", "Healthcare"),
    "lifepoint": ("LifePoint Health", "Healthcare"),
    "genesis healthcare": ("Genesis Healthcare", "Healthcare"),
    "banner health": ("Banner Health", "Healthcare"),
    "providence": ("Providence Health & Services", "Healthcare"),
    "sunrise senior living": ("Sunrise Senior Living", "Healthcare"),
    "sunrise": ("Sunrise Senior Living", "Healthcare"),
    "atria senior living": ("Atria Senior Living", "Healthcare"),
    "atria": ("Atria Senior Living", "Healthcare"),
    # Casinos & Gaming
    "caesars": ("Caesars Entertainment", "Casinos & Gaming"),
    "caesars entertainment": ("Caesars Entertainment", "Casinos & Gaming"),
    "las vegas sands": ("Las Vegas Sands Corp", "Casinos & Gaming"),
    "sands": ("Las Vegas Sands Corp", "Casinos & Gaming"),
    "wynn resorts": ("Wynn Resorts", "Casinos & Gaming"),
    "wynn": ("Wynn Resorts", "Casinos & Gaming"),
    "hard rock": ("Hard Rock International", "Casinos & Gaming"),
    "penn entertainment": ("Penn Entertainment", "Casinos & Gaming"),
    "penn national": ("Penn Entertainment", "Casinos & Gaming"),
    "boyd gaming": ("Boyd Gaming Corporation", "Casinos & Gaming"),
    "boyd": ("Boyd Gaming Corporation", "Casinos & Gaming"),
    "melco resorts": ("Melco Resorts & Entertainment", "Casinos & Gaming"),
    "melco": ("Melco Resorts & Entertainment", "Casinos & Gaming"),
    "galaxy entertainment": ("Galaxy Entertainment Group", "Casinos & Gaming"),
    "galaxy macau": ("Galaxy Entertainment Group", "Casinos & Gaming"),
    # Cruise Lines
    "carnival corporation": ("Carnival Corporation", "Cruise Lines"),
    "carnival cruise": ("Carnival Corporation", "Cruise Lines"),
    "carnival": ("Carnival Corporation", "Cruise Lines"),
    "royal caribbean": ("Royal Caribbean Group", "Cruise Lines"),
    "norwegian cruise": ("Norwegian Cruise Line Holdings", "Cruise Lines"),
    "ncl": ("Norwegian Cruise Line Holdings", "Cruise Lines"),
    "msc cruises": ("MSC Cruises", "Cruise Lines"),
    "msc": ("MSC Cruises", "Cruise Lines"),
    "viking cruises": ("Viking Cruises", "Cruise Lines"),
    "viking": ("Viking Cruises", "Cruise Lines"),
    "virgin voyages": ("Virgin Voyages", "Cruise Lines"),
    # Theme Parks & Entertainment
    "disney parks": ("Walt Disney Parks & Resorts", "Theme Parks & Entertainment"),
    "walt disney world": ("Walt Disney Parks & Resorts", "Theme Parks & Entertainment"),
    "disneyland": ("Walt Disney Parks & Resorts", "Theme Parks & Entertainment"),
    "universal parks": ("Universal Parks & Resorts", "Theme Parks & Entertainment"),
    "universal studios": ("Universal Parks & Resorts", "Theme Parks & Entertainment"),
    "seaworld": ("SeaWorld Entertainment", "Theme Parks & Entertainment"),
    "sea world": ("SeaWorld Entertainment", "Theme Parks & Entertainment"),
    "six flags": ("Six Flags Entertainment", "Theme Parks & Entertainment"),
    "cedar fair": ("Cedar Fair", "Theme Parks & Entertainment"),
    "merlin entertainments": ("Merlin Entertainments", "Theme Parks & Entertainment"),
    "legoland": ("Merlin Entertainments", "Theme Parks & Entertainment"),
    "vail resorts": ("Vail Resorts", "Theme Parks & Entertainment"),
    "vail": ("Vail Resorts", "Theme Parks & Entertainment"),
    "dollywood": ("Herschend Family Entertainment", "Theme Parks & Entertainment"),
    "herschend": ("Herschend Family Entertainment", "Theme Parks & Entertainment"),
    # Real Estate & Facilities
    "cbre": ("CBRE Group", "Real Estate & Facilities"),
    "jll": ("Jones Lang LaSalle (JLL)", "Real Estate & Facilities"),
    "jones lang lasalle": ("Jones Lang LaSalle (JLL)", "Real Estate & Facilities"),
    "cushman wakefield": ("Cushman & Wakefield", "Real Estate & Facilities"),
    "cushman & wakefield": ("Cushman & Wakefield", "Real Estate & Facilities"),
    "greystar": ("Greystar Real Estate Partners", "Real Estate & Facilities"),
    "abm industries": ("ABM Industries", "Real Estate & Facilities"),
    "abm": ("ABM Industries", "Real Estate & Facilities"),
    # Automotive Dealerships
    "autonation": ("AutoNation", "Automotive Dealerships"),
    "auto nation": ("AutoNation", "Automotive Dealerships"),
    "penske automotive": ("Penske Automotive Group", "Automotive Dealerships"),
    "sonic automotive": ("Sonic Automotive", "Automotive Dealerships"),
    "lithia motors": ("Lithia Motors", "Automotive Dealerships"),
    "lithia": ("Lithia Motors", "Automotive Dealerships"),
    "group 1 automotive": ("Group 1 Automotive", "Automotive Dealerships"),
    "group 1": ("Group 1 Automotive", "Automotive Dealerships"),
    "asbury automotive": ("Asbury Automotive Group", "Automotive Dealerships"),
    "asbury": ("Asbury Automotive Group", "Automotive Dealerships"),
    "ken garff": ("Ken Garff Automotive Group", "Automotive Dealerships"),
    "hendrick automotive": ("Hendrick Automotive Group", "Automotive Dealerships"),
    "hendrick": ("Hendrick Automotive Group", "Automotive Dealerships"),
    "holman enterprises": ("Holman Enterprises", "Automotive Dealerships"),
    "holman": ("Holman Enterprises", "Automotive Dealerships"),
    "cox automotive": ("Cox Automotive", "Automotive Dealerships"),
    "manheim": ("Manheim (Cox Automotive)", "Automotive Dealerships"),
    "oreilly auto": ("O'Reilly Auto Parts", "Automotive Dealerships"),
    "o'reilly auto": ("O'Reilly Auto Parts", "Automotive Dealerships"),
    "advance auto": ("Advance Auto Parts", "Automotive Dealerships"),
    "autozone": ("AutoZone", "Automotive Dealerships"),
    "napa auto": ("NAPA Auto Parts", "Automotive Dealerships"),
    # Additional dealership groups (seed_v5)
    "findlay automotive": ("Findlay Automotive Group", "Automotive Dealerships"),
    "findlay auto": ("Findlay Automotive Group", "Automotive Dealerships"),
    "larry h miller": ("Larry H. Miller Dealerships", "Automotive Dealerships"),
    "lhm auto": ("Larry H. Miller Dealerships", "Automotive Dealerships"),
    "jm family": ("JM Family Enterprises", "Automotive Dealerships"),
    "park place dealerships": ("Park Place Dealerships", "Automotive Dealerships"),
    "sewell automotive": ("Sewell Automotive Companies", "Automotive Dealerships"),
    "sewell auto": ("Sewell Automotive Companies", "Automotive Dealerships"),
    "berkshire hathaway automotive": ("Berkshire Hathaway Automotive", "Automotive Dealerships"),
    "bh automotive": ("Berkshire Hathaway Automotive", "Automotive Dealerships"),
    "herb chambers": ("Herb Chambers Companies", "Automotive Dealerships"),
    "flow automotive": ("Flow Automotive", "Automotive Dealerships"),
    "keyes auto": ("Keyes Automotive Group", "Automotive Dealerships"),
    "keyes automotive": ("Keyes Automotive Group", "Automotive Dealerships"),
    "bergstrom auto": ("Bergstrom Automotive", "Automotive Dealerships"),
    "galpin motors": ("Galpin Motors", "Automotive Dealerships"),
    "galpin ford": ("Galpin Motors", "Automotive Dealerships"),
    "lucid motors retail": ("Lucid Motors Retail & Service Centers", "Automotive Dealerships"),
    "lucid service center": ("Lucid Motors Retail & Service Centers", "Automotive Dealerships"),
    # OEM Innovation & Ventures (seed_v5)
    "toyota ventures": ("Toyota Ventures", "Automotive Innovation & Ventures"),
    "gm ventures": ("GM Ventures", "Automotive Innovation & Ventures"),
    "ford motor ventures": ("Ford Motor Company Ventures", "Automotive Innovation & Ventures"),
    "ford ventures": ("Ford Motor Company Ventures", "Automotive Innovation & Ventures"),
    "bmw iventures": ("BMW i Ventures", "Automotive Innovation & Ventures"),
    "bmw i ventures": ("BMW i Ventures", "Automotive Innovation & Ventures"),
    "hyundai cradle": ("Hyundai CRADLE", "Automotive Innovation & Ventures"),
    "stellantis ventures": ("Stellantis Ventures", "Automotive Innovation & Ventures"),
    # Aerospace & Defense (seed_v5)
    "boeing commercial": ("Boeing Commercial Airplanes", "Aerospace & Defense"),
    "boeing manufacturing": ("Boeing Commercial Airplanes", "Aerospace & Defense"),
    "lockheed martin": ("Lockheed Martin", "Aerospace & Defense"),
    "raytheon": ("RTX (Raytheon Technologies)", "Aerospace & Defense"),
    "rtx corporation": ("RTX (Raytheon Technologies)", "Aerospace & Defense"),
    "pratt & whitney": ("RTX (Raytheon Technologies)", "Aerospace & Defense"),
    "collins aerospace": ("RTX (Raytheon Technologies)", "Aerospace & Defense"),
    "northrop grumman": ("Northrop Grumman", "Aerospace & Defense"),
    "airbus americas": ("Airbus Americas", "Aerospace & Defense"),
    "airbus mobile": ("Airbus Americas", "Aerospace & Defense"),
    "spacex": ("SpaceX", "Aerospace & Defense"),
    "general dynamics land": ("General Dynamics Land Systems", "Aerospace & Defense"),
    "gdls": ("General Dynamics Land Systems", "Aerospace & Defense"),
    # Individual OEM brand dealerships (seed_v6)
    "longo toyota": ("Longo Toyota", "Automotive Dealerships"),
    "norm reeves honda": ("Norm Reeves Honda Superstore", "Automotive Dealerships"),
    "bmw of sterling": ("BMW of Sterling", "Automotive Dealerships"),
    "mercedes-benz of atlanta": ("Mercedes-Benz of Atlanta", "Automotive Dealerships"),
    "mercedes benz of atlanta": ("Mercedes-Benz of Atlanta", "Automotive Dealerships"),
    "autonation ford margate": ("AutoNation Ford Margate", "Automotive Dealerships"),
    "crest chevrolet": ("Crest Chevrolet", "Automotive Dealerships"),
    "findlay buick gmc": ("Findlay Buick GMC", "Automotive Dealerships"),
    "findlay gmc": ("Findlay Buick GMC", "Automotive Dealerships"),
    "tesla service center las vegas": ("Tesla Service Center Las Vegas", "Automotive Dealerships"),
    "tesla service las vegas": ("Tesla Service Center Las Vegas", "Automotive Dealerships"),
    "hyundai of new port richey": ("Hyundai of New Port Richey", "Automotive Dealerships"),
    "kia of henderson": ("Kia of Henderson", "Automotive Dealerships"),
    "nissan of las vegas": ("Nissan of Las Vegas", "Automotive Dealerships"),
    "hendrick volkswagen frisco": ("Hendrick Volkswagen Frisco", "Automotive Dealerships"),
    "hendrick vw frisco": ("Hendrick Volkswagen Frisco", "Automotive Dealerships"),
    "audi henderson": ("Audi Henderson", "Automotive Dealerships"),
    "porsche las vegas": ("Porsche Las Vegas", "Automotive Dealerships"),
    "lexus of las vegas": ("Lexus of Las Vegas", "Automotive Dealerships"),
    "desert infiniti": ("Desert Infiniti", "Automotive Dealerships"),
    "acura of peoria": ("Acura of Peoria", "Automotive Dealerships"),
    "findlay cadillac": ("Findlay Cadillac", "Automotive Dealerships"),
    "lincoln of dallas": ("Lincoln of Dallas", "Automotive Dealerships"),
    "genesis of henderson": ("Genesis of Henderson", "Automotive Dealerships"),
    "groove subaru": ("Groove Subaru", "Automotive Dealerships"),
    "mazda of orange park": ("Mazda of Orange Park", "Automotive Dealerships"),
    "volvo cars las vegas": ("Volvo Cars Las Vegas", "Automotive Dealerships"),
    "findlay chrysler dodge jeep ram": ("Findlay Chrysler Dodge Jeep Ram", "Automotive Dealerships"),
    "findlay cdjr": ("Findlay Chrysler Dodge Jeep Ram", "Automotive Dealerships"),
    "rivian service hub": ("Rivian Service Hub — Scottsdale", "Automotive Dealerships"),
    "rivian scottsdale": ("Rivian Service Hub — Scottsdale", "Automotive Dealerships"),
    "findlay mitsubishi": ("Findlay Mitsubishi", "Automotive Dealerships"),
}

# ── Junk headline patterns — never save listicles / how-to advice as signals ──
# Headlines matching these are editorial content, not company-event news.
_JUNK_HEADLINE_PATTERNS = [
    r"^\d+\s+(?:ways?|strategies?|tips?|tricks?|ideas?|steps?|reasons?|mistakes?|secrets?|things?|questions?|examples?|factors?|hacks?|methods?|tactics?)\s+(?:to|for|that|you|on|about|every|when)",
    r"^top\s+\d+",                         # Top 10 …
    r"^\d+\s+(?:best|great|key|simple|easy|proven|powerful|effective)",
    r"^how\s+to\b",                         # How to …
    r"^why\s+(?:you|your|every|hotels?|restaurants?|companies)",
    r"^what\s+(?:is|are|hotel|restaurant)\b",
    r"^the\s+(?:ultimate|complete|definitive|best|top)\s+guide",
    r"^(?:a\s+)?guide\s+to\b",
    r"combat\s+(?:restaurant|labor|wage|cost|inflation)",  # "… to combat restaurants"
    r"^(?:everything|all)\s+you\s+(?:need|should|must|want)",
]
_JUNK_HEADLINE_RE = [re.compile(p, re.IGNORECASE) for p in _JUNK_HEADLINE_PATTERNS]

# ── Vendor / tech-company name keywords — NEVER treat these as buyers ─────────
# If a regex-extracted company name contains any of these, skip it.
# (We want BUYERS of robots, not robot/AI vendors)
VENDOR_NAME_KEYWORDS = [
    "robotics", "robot", " ai ", "a.i.", "autonomous", "drone",
    "lidar", "semiconductor", "startup", "maker miso",
]

# First words of a regex match that indicate non-company text was captured
_NON_COMPANY_STARTS = frozenset([
    "slated", "set", "expected", "scheduled", "our", "your",
    "their", "its", "by", "for", "from", "on", "at", "in",
    "as", "with", "after", "before", "while", "when", "if",
    "so", "but", "yet", "and", "or", "nor",
])

# Exact phrases (lowercased) that are definitely not company names
_NON_COMPANY_EXACT = frozenset([
    "ice cream", "food service", "supply chain", "labor shortage",
    "real estate", "last year", "last week", "first quarter",
    "second quarter", "third quarter", "fourth quarter",
])

# Regex to find "Company X announces/says/reports/invests/opens" patterns
_COMPANY_ANNOUNCE_RE = re.compile(
    r'\b([A-Z][A-Za-z0-9&\.\' ]{2,40}?)\s+(?:announces?|says?|reports?|invests?|opens?|launches?|deploys?|hires?|appoints?|raises?|acquires?|pilots?)\b'
)

# ── Open market intent queries (no specific company) ─────────────────────────
INTENT_QUERIES = [
    "warehouse automation funding round 2026",
    "logistics robotics investment acquisition 2026",
    "hotel labor shortage automation solution 2026",
    "fulfillment center expansion opening 2026",
    "warehouse robotics capex deployment 2026",
    "supply chain automation merger acquisition",
    "VP automation director robotics hired appointed",
    "autonomous mobile robot AMR logistics deal 2026",
    "hotel staffing crisis service robot pilot 2026",
    "distribution center new construction opening 2026",
    "restaurant labor shortage automation kitchen 2026",
    "hospital staffing shortage disinfection robot 2026",
    "senior living caregiver shortage robot companion 2026",
    "food service delivery robot deployment chain 2026",
    "grocery distribution center automation investment 2026",
    "hotels minimum wage labor cost operations 2026",
    "warehouse worker shortage overtime staffing pressure 2026",
    "healthcare EVS housekeeping staffing shortage robot",
    "3PL logistics new distribution center expansion 2026",
    "restaurant chain automation pilot program technology 2026",
    # New verticals
    "casino robotics automation beverage delivery 2026",
    "casino labor shortage staffing F&B robot pilot",
    "cruise ship robotic delivery onboard automation 2026",
    "cruise line crew shortage autonomous service 2026",
    "theme park food service robot automation 2026",
    "theme park labor shortage custodial operations 2026",
    "facilities management robotic cleaning autonomous building 2026",
    "commercial real estate robot cleaning janitorial automation 2026",
]

# ── Per-company query templates ───────────────────────────────────────────────
COMPANY_QUERY_TEMPLATES = [
    "{name} warehouse automation",
    "{name} funding round investment",
    "{name} expansion new facility",
    "{name} merger acquisition",
    "{name} automation robotics hire director",
]


class NewsScraper:
    """
    Fetches Google News RSS articles and converts them into
    buying-intent signals stored in the database.
    """

    GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
    DELAY_BETWEEN_REQUESTS = 1.5   # seconds — be polite to Google

    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()

    # ── Public API ────────────────────────────────────────────────────────────

    def run_company_queries(self, company_names: List[str], max_per_company: int = 5):
        """
        For each company name, run COMPANY_QUERY_TEMPLATES and save relevant signals.
        """
        for name in company_names:
            logger.info("Fetching news for: %s", name)
            for template in COMPANY_QUERY_TEMPLATES:
                query = template.format(name=name)
                articles = self._fetch_rss(query)
                saved = 0
                for article in articles[:max_per_company]:
                    if self._is_relevant(article["text"]):
                        self._save_article_as_signal(article, company_name=name, query=query)
                        saved += 1
                if saved:
                    logger.info("  [%s] '%s' → %d signals", name, query, saved)
                time.sleep(self.DELAY_BETWEEN_REQUESTS)

    def run_intent_queries(self, queries: List[str] = None, max_per_query: int = 8):
        """
        Run open-market intent queries to discover new companies showing buying intent.
        Pass a custom `queries` list or defaults to the built-in INTENT_QUERIES.
        """
        effective_queries = queries if queries is not None else INTENT_QUERIES
        for query in effective_queries:
            logger.info("Intent query: %s", query)
            articles = self._fetch_rss(query)
            for article in articles[:max_per_query]:
                if not self._is_relevant(article["text"]):
                    continue
                company_name, industry = self._extract_company_from_text(article["text"])
                if company_name:
                    # Skip companies with no identifiable buyer industry —
                    # these are almost always robot/AI vendors found via regex fallback,
                    # not buyer companies (e.g. ZaiNar, AI2 Robotics, Wayve)
                    if not industry or industry == "Unknown":
                        logger.debug("  Skipping Unknown-industry company: %s", company_name)
                        continue
                    self._save_article_as_signal(article, company_name=company_name,
                                                  query=query, inferred_industry=industry)
            time.sleep(self.DELAY_BETWEEN_REQUESTS)

    def run(self, company_names: List[str] = None, intent_queries: bool = True):
        """Main entry — run both Google News modes."""
        if company_names:
            self.run_company_queries(company_names)
        if intent_queries:
            self.run_intent_queries()

    def run_rss_feeds(self, feed_urls: List[str], max_per_feed: int = 20):
        """
        Directly fetch external RSS/Atom feed URLs (e.g. supplychaindive.com/feeds/news/)
        and save relevant articles as signals.
        This is distinct from run_intent_queries() which searches Google News RSS.
        """
        for feed_url in feed_urls:
            logger.info("Fetching RSS feed: %s", feed_url)
            articles = self._fetch_direct_rss(feed_url)
            saved = 0
            for article in articles[:max_per_feed]:
                if not self._is_relevant(article["text"]):
                    continue
                company_name, industry = self._extract_company_from_text(article["text"])
                if company_name:
                    # Skip Unknown-industry (vendor/tech company) same as intent queries
                    if not industry or industry == "Unknown":
                        logger.debug("  Skipping Unknown-industry company: %s", company_name)
                        continue
                    self._save_article_as_signal(article, company_name=company_name,
                                                  query=feed_url, inferred_industry=industry)
                    saved += 1
            logger.info("  [%s] → %d signals", feed_url.split("/")[2], saved)
            time.sleep(self.DELAY_BETWEEN_REQUESTS)

    def _fetch_direct_rss(self, feed_url: str) -> List[dict]:
        """Fetch a direct RSS/Atom URL (not a Google News query)."""
        articles = []
        try:
            req = urllib.request.Request(feed_url, headers={
                "User-Agent": "Mozilla/5.0 (compatible; RobotsLeadIntel/1.0)",
                "Accept": "application/rss+xml, application/atom+xml, text/xml, */*",
            })
            with urllib.request.urlopen(req, timeout=20) as resp:
                xml_bytes = resp.read()
            root = ET.fromstring(xml_bytes)
            # RSS 2.0
            channel = root.find("channel")
            items = channel.findall("item") if channel is not None else []
            # Atom
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            if not items:
                items = root.findall("atom:entry", ns) or root.findall("entry")
            for item in items:
                title = (item.findtext("title") or
                         (item.find("{http://www.w3.org/2005/Atom}title") or item).text or "").strip()
                desc  = (item.findtext("description") or
                         item.findtext("{http://www.w3.org/2005/Atom}summary") or
                         item.findtext("{http://www.w3.org/2005/Atom}content") or "").strip()
                link  = (item.findtext("link") or
                         (item.find("{http://www.w3.org/2005/Atom}link") or None) and
                         item.find("{http://www.w3.org/2005/Atom}link").get("href", "") or "")
                articles.append({
                    "title": title,
                    "description": desc,
                    "text": f"{title}. {desc}",
                    "url": link or feed_url,
                    "published": "",
                    "source": feed_url,
                    "query": feed_url,
                })
        except ET.ParseError as e:
            logger.warning("XML parse error for feed '%s': %s", feed_url, e)
        except Exception as e:
            logger.warning("Feed fetch failed '%s': %s", feed_url, e)
        return articles

    # ── RSS Fetching ──────────────────────────────────────────────────────────

    def _fetch_rss(self, query: str) -> List[dict]:
        """Fetch Google News RSS and return list of article dicts."""
        encoded = urllib.parse.quote(query)
        url = self.GOOGLE_NEWS_RSS.format(query=encoded)
        articles = []
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (compatible; RobotsLeadIntel/1.0)"
            })
            with urllib.request.urlopen(req, timeout=15) as resp:
                xml_bytes = resp.read()
            root = ET.fromstring(xml_bytes)
            channel = root.find("channel")
            if channel is None:
                return []
            for item in channel.findall("item"):
                title   = (item.findtext("title") or "").strip()
                desc    = (item.findtext("description") or "").strip()
                link    = (item.findtext("link") or "").strip()
                pub     = (item.findtext("pubDate") or "").strip()
                source_el = item.find("source")
                source  = source_el.text.strip() if source_el is not None else ""
                full_text = f"{title}. {desc}"
                articles.append({
                    "title": title,
                    "description": desc,
                    "text": full_text,
                    "url": link,
                    "published": pub,
                    "source": source,
                    "query": query,
                })
        except ET.ParseError as e:
            logger.warning("XML parse error for query '%s': %s", query, e)
        except Exception as e:
            logger.warning("RSS fetch failed for query '%s': %s", query, e)
        return articles

    # ── Signal relevance & scoring ────────────────────────────────────────────

    def _is_relevant(self, text: str) -> bool:
        """True if article contains at least one relevance keyword."""
        lower = text.lower()
        return any(kw.lower() in lower for kw in RELEVANCE_KEYWORDS)

    def _is_junk_headline(self, title: str) -> bool:
        """True if the headline is a listicle, how-to, or opinion piece—not company-event news."""
        t = (title or "").strip()
        return any(rx.search(t) for rx in _JUNK_HEADLINE_RE)

    def _score_article(self, text: str, company_name: str = "", industry: str = "") -> float:
        """Run inference engine on article text → overall_intent as signal strength."""
        combined = f"{company_name} {industry} {text}"
        result = analyze(combined, industry=industry or None)
        # Normalize: overall_intent is 0.0–1.0 inside the engine (×100 in to_score_dict)
        return round(result.overall_intent, 4)

    def _classify_signal_type(self, text: str) -> str:
        """Heuristic: pick the most prominent signal type for the article."""
        lower = text.lower()
        if any(w in lower for w in ["series ", "funding", "raised", "invest", "vc ", "private equity", "ipo"]):
            return "funding_round"
        if any(w in lower for w in ["acqui", "merger", "merges with", "buyout", "joint venture"]):
            return "ma_activity"
        if any(w in lower for w in ["vp ", "svp ", "director of", "head of", "chief ", "appoint", "hire", "hired", "joins as"]):
            return "strategic_hire"
        if any(w in lower for w in ["capex", "capital expenditure", "capital investment", "committing $", "allocated $"]):
            return "capex"
        if any(w in lower for w in ["expand", "opening", "new facilit", "new propert", "new warehouse", "new hotel", "breaking ground"]):
            return "expansion"
        if any(w in lower for w in ["labor shortage", "staffing", "worker shortage", "cant find", "turnover"]):
            return "labor_signal"
        return "news"

    # ── Entity extraction ─────────────────────────────────────────────────────

    def _extract_company_from_text(self, text: str) -> tuple[Optional[str], Optional[str]]:
        """
        Try to identify a known company in the article text.
        Returns (canonical_name, industry) or (None, None).
        Priority: longer matches first (so 'dhl supply chain' beats 'dhl').
        """
        lower = text.lower()
        # Sort keys longest-first to prefer specific names over abbreviations
        for key in sorted(KNOWN_COMPANIES.keys(), key=len, reverse=True):
            if key in lower:
                return KNOWN_COMPANIES[key]
        # Regex fallback: look for "Company Name announces/invests/opens ..."
        match = _COMPANY_ANNOUNCE_RE.search(text)
        if match:
            extracted = match.group(1).strip()
            extracted_lower = extracted.lower()
            first_word = extracted_lower.split()[0] if extracted_lower.split() else ""
            valid_name = (
                len(extracted) > 3
                and extracted_lower not in ("the", "a", "an", "this")
                and first_word not in _NON_COMPANY_STARTS
                and extracted_lower not in _NON_COMPANY_EXACT
            )
            if valid_name:
                # Skip robotics/AI/tech vendors — we want buyers, not sellers
                if any(kw in extracted_lower for kw in VENDOR_NAME_KEYWORDS):
                    return None, None
                industry = self._infer_industry_from_text(text)
                return extracted, industry
        return None, None

    def _infer_industry_from_text(self, text: str) -> str:
        """Infer industry from article keywords."""
        lower = text.lower()
        if any(w in lower for w in ["hotel", "resort", "hospitality", "housekeep", "lodging", "motel", "inn"]):
            return "Hospitality"
        if any(w in lower for w in ["restaurant", "food service", "kitchen", "dining", "qsr", "fast food", "cafe"]):
            return "Food Service"
        if any(w in lower for w in ["hospital", "health system", "healthcare", "clinic", "patient", "senior living", "nursing"]):
            return "Healthcare"
        if any(w in lower for w in ["warehouse", "logistics", "fulfillment", "distribution", "supply chain", "cold storage", "3pl"]):
            return "Logistics"
        if any(w in lower for w in ["casino", "gaming", "resort casino", "slot", "table game", "integrated resort"]):
            return "Casinos & Gaming"
        if any(w in lower for w in ["cruise", "cruise ship", "cruise line", "onboard", "vessel"]):
            return "Cruise Lines"
        if any(w in lower for w in ["theme park", "amusement park", "theme park", "roller coaster", "disney", "universal studios", "sea world"]):
            return "Theme Parks & Entertainment"
        if any(w in lower for w in ["facilities management", "property management", "commercial real estate", "building services", "janitorial"]):
            return "Real Estate & Facilities"
        if any(w in lower for w in ["auto dealer", "car dealer", "dealership", "fixed ops", "parts department",
                                     "service department", "dealer group", "automotive dealer",
                                     "parts resupply", "autonation", "penske auto", "sonic automotive",
                                     "lithia motors", "dealer"]):
            return "Automotive Dealerships"
        return "Unknown"

    # ── DB persistence ────────────────────────────────────────────────────────

    def _get_or_create_company(self, name: str, industry: str = "Unknown") -> Optional[Company]:
        """Look up or create a company record by name. Thread-safe: handles race conditions."""
        if not name:
            return None
        existing = self.db.query(Company).filter(Company.name == name).first()
        if existing:
            if existing.industry == "Unknown" and industry != "Unknown":
                existing.industry = industry
                try:
                    self.db.commit()
                except Exception:
                    self.db.rollback()
            return existing
        company = Company(
            name=name,
            industry=industry,
            source="news_scraper",
        )
        self.db.add(company)
        try:
            self.db.commit()
            self.db.refresh(company)
            return company
        except Exception:
            # Race condition: another thread inserted the same company
            self.db.rollback()
            return self.db.query(Company).filter(Company.name == name).first()

    def _save_article_as_signal(self, article: dict, company_name: Optional[str],
                                  query: str, inferred_industry: Optional[str] = None):
        """Save one RSS article as a Signal row."""
        # ── Headline junk guard ────────────────────────────────────────────────
        title = article.get("title", "")
        if self._is_junk_headline(title):
            logger.debug("  Skipping junk headline: %s", title)
            return

        industry = inferred_industry or "Unknown"
        company = self._get_or_create_company(company_name, industry) if company_name else None
        if company is None:
            return  # skip articles with no identifiable company

        # De-duplicate by signal_text (truncated title)
        signal_text = article["text"][:600]
        existing = self.db.query(Signal).filter(
            Signal.company_id == company.id,
            Signal.signal_text == signal_text,
        ).first()
        if existing:
            return

        strength = self._score_article(
            article["text"],
            company_name=company_name or "",
            industry=company.industry or "",
        )
        if strength < 0.05:
            return  # discard noise

        sig_type = self._classify_signal_type(article["text"])

        signal = Signal(
            company_id=company.id,
            signal_type=sig_type,
            signal_text=signal_text,
            signal_strength=min(strength, 1.0),
            source_url=article.get("url", ""),
        )
        self.db.add(signal)
        self.db.commit()
        logger.debug("  Saved [%s] signal for %s (strength=%.2f)", sig_type, company_name, strength)
