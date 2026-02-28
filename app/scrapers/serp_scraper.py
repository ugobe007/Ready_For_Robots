"""
SERP Scraper — Expansion & Automation Intent Hunter
====================================================
Uses Google News RSS to run targeted SERP-style searches that surface
company-level expansion, automation, and buy-signal announcements.

Focus areas (vs. NewsScraper which is broad):
  - Specific city + industry expansion announcements
  - Automation pilot program launches
  - New warehouse/hotel/facility groundbreaking or ribbon-cutting
  - Department head / C-suite appointments in target accounts
  - CapEx announcements with dollar amounts

Uses urllib + Google News RSS (no Playwright, no API key needed).
"""
import logging
import time
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from typing import List, Optional

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.company import Company
from app.models.signal import Signal
from app.services.inference_engine import analyze
from app.scrapers.news_scraper import KNOWN_COMPANIES, _COMPANY_ANNOUNCE_RE

logger = logging.getLogger(__name__)

GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
DELAY = 1.8  # seconds between requests

# ─── Expansion-focused queries ─────────────────────────────────────────────────
EXPANSION_QUERIES = [
    # New warehouses / DCs
    "new distribution center groundbreaking 2025 2026",
    "new fulfillment center opens announces construction",
    "\"breaking ground\" warehouse distribution logistics 2026",
    "ribbon cutting new warehouse fulfillment operations 2026",
    "new cold storage facility logistics opens 2026",
    # New hotel openings
    "new hotel opens 2025 2026 grand opening ribbon cutting",
    "hotel renovation capital investment million upgrade 2026",
    "resort expansion new tower rooms construction 2026",
    # New restaurant / food service locations
    "restaurant chain opens new locations 2026 expansion",
    "fast food QSR new unit growth 2026 sites",
    # Hospital / healthcare new builds
    "new hospital campus opens construction 2026",
    "hospital expansion million new building wing",
    "senior living community opens new campus 2026",
    # Automation pilots
    "pilot program automation warehouse 2026 announces",
    "robot deployment pilot warehouse hotel restaurant 2026",
    "AGV AMR autonomous robot deployment 2026 facility",
    # Capital raise / capex announcements
    "\"capital investment\" million warehouse distribution 2026",
    "hotel chain capital investment technology upgrade 2026",
    "logistics company capital raise fund expansion 2026",
    # Exec / buyer-persona appointments
    "\"VP of Operations\" appointed logistics warehouse 2026",
    "\"Chief Operating Officer\" appointed hotel hospitality 2026",
    "\"Director of Facilities\" appointed hospital healthcare 2026",
    "\"VP Supply Chain\" joins named appointed 2026",
    # Labor pain + staffing (creates robot urgency)
    "hotel staffing shortage housekeeping 2026 workers",
    "warehouse labor shortage workers hard to hire 2026",
    "restaurant staffing crisis labor shortage 2026",
    "hospital nursing aide shortage 2026 staffing",
    "\"minimum wage\" increase operations labor cost pressure 2026",
]

_SIGNAL_KEYWORDS = {
    "expansion":      ["expand", "opening", "new facilit", "new propert", "groundbreak", "ribbon cut", "new hotel", "new warehouse", "construction", "new location"],
    "capex":          ["capex", "capital expenditure", "capital investment", "investing $", "million invest", "million capital"],
    "funding_round":  ["series ", "funding", "raised $", "private equity", "capital raise"],
    "ma_activity":    ["acqui", "merger", "merges with", "buyout", "joint venture"],
    "strategic_hire": ["vp ", "svp ", "director of", "head of", "chief ", "appoint", "joins as", "named as"],
    "labor_shortage": ["labor shortage", "staffing shortage", "worker shortage", "turnover", "staffing crisis", "understaffed"],
}


def _classify_signal(text: str) -> str:
    lower = text.lower()
    for sig_type, keywords in _SIGNAL_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return sig_type
    return "news"


def _is_relevant(text: str) -> bool:
    lower = text.lower()
    return any(kw.lower() in lower for kw in [
        "automat", "robot", "agv", "amr", "warehouse", "logistics", "fulfillment",
        "hotel", "hospitality", "restaurant", "food service", "hospital", "healthcare",
        "funding", "invest", "acqui", "merger", "expansion", "opening",
        "labor shortage", "staffing", "workforce", "capex", "capital",
        "vp", "director", "supply chain", "distribution",
    ])


def _infer_industry(text: str) -> str:
    lower = text.lower()
    if any(w in lower for w in ["hotel", "resort", "hospitality", "lodging"]):
        return "Hospitality"
    if any(w in lower for w in ["restaurant", "food service", "kitchen", "qsr", "fast food"]):
        return "Food Service"
    if any(w in lower for w in ["hospital", "health system", "healthcare", "clinic", "senior living", "nursing"]):
        return "Healthcare"
    if any(w in lower for w in ["warehouse", "logistics", "fulfillment", "distribution", "supply chain", "3pl"]):
        return "Logistics"
    return "Unknown"


class SerpScraper:
    """
    Targeted SERP-style news scraper for expansion + automation-intent signals.
    Runs a curated list of high-signal queries against Google News RSS.
    """

    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()

    def run(self, queries: List[str] = None, max_results_per_query: int = 6):
        """Run all queries and save signals."""
        active_queries = queries or EXPANSION_QUERIES
        total_saved = 0
        logger.info("[SerpScraper] Starting — %d queries", len(active_queries))
        for query in active_queries:
            articles = self._fetch_rss(query)
            for article in articles[:max_results_per_query]:
                if not _is_relevant(article["text"]):
                    continue
                company_name, industry = self._extract_company(article["text"])
                if company_name:
                    saved = self._save_signal(article, company_name, industry or "Unknown")
                    if saved:
                        total_saved += 1
            time.sleep(DELAY)
        logger.info("[SerpScraper] Done — %d new signals saved", total_saved)

    def _fetch_rss(self, query: str) -> List[dict]:
        encoded = urllib.parse.quote(query)
        url = GOOGLE_NEWS_RSS.format(query=encoded)
        articles = []
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (compatible; RFR-Intel/1.0)"
            })
            with urllib.request.urlopen(req, timeout=15) as resp:
                xml_bytes = resp.read()
            root = ET.fromstring(xml_bytes)
            channel = root.find("channel")
            if channel is None:
                return []
            for item in channel.findall("item"):
                title = (item.findtext("title") or "").strip()
                desc  = (item.findtext("description") or "").strip()
                link  = (item.findtext("link") or "").strip()
                articles.append({
                    "title": title,
                    "text": f"{title}. {desc}",
                    "url": link,
                    "query": query,
                })
        except ET.ParseError as e:
            logger.warning("[SerpScraper] XML parse error '%s': %s", query, e)
        except Exception as e:
            logger.warning("[SerpScraper] Fetch failed '%s': %s", query, e)
        return articles

    def _extract_company(self, text: str):
        lower = text.lower()
        for key in sorted(KNOWN_COMPANIES.keys(), key=len, reverse=True):
            if key in lower:
                return KNOWN_COMPANIES[key]
        match = _COMPANY_ANNOUNCE_RE.search(text)
        if match:
            extracted = match.group(1).strip()
            if 2 < len(extracted) <= 60 and extracted.lower() not in ("the", "a", "an", "this", "our"):
                return extracted, _infer_industry(text)
        return None, None

    def _get_or_create_company(self, name: str, industry: str) -> Optional[Company]:
        if not name:
            return None
        existing = self.db.query(Company).filter(Company.name == name).first()
        if existing:
            return existing
        company = Company(name=name, industry=industry, source="serp_scraper")
        self.db.add(company)
        self.db.commit()
        self.db.refresh(company)
        return company

    def _save_signal(self, article: dict, company_name: str, industry: str) -> bool:
        company = self._get_or_create_company(company_name, industry)
        if not company:
            return False
        signal_text = article["text"][:600]
        existing = self.db.query(Signal).filter(
            Signal.company_id == company.id,
            Signal.signal_text == signal_text,
        ).first()
        if existing:
            return False
        result = analyze(f"{company_name} {industry} {article['text']}", industry=industry)
        strength = round(min(result.overall_intent, 1.0), 4)
        if strength < 0.05:
            return False
        signal = Signal(
            company_id=company.id,
            signal_type=_classify_signal(article["text"]),
            signal_text=signal_text,
            signal_strength=strength,
            source_url=article.get("url", ""),
        )
        self.db.add(signal)
        self.db.commit()
        logger.debug("[SerpScraper] Saved [%s] for %s (%.2f)",
                     signal.signal_type, company_name, strength)
        return True
