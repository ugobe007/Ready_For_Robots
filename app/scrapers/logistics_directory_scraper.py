"""
Logistics Directory Scraper
============================
Scrapes logistics company news pages, press-release sections, and
industry directories using lightweight HTTP requests (no Playwright).

Sources:
  - BusinessWire logistics/supply-chain press releases
  - PR Newswire logistics feeds
  - Prologis / GLP newsroom
  - Major 3PL / WMS company news sections
  - Industry directories (IWLA, CSCMP member pages via Google News RSS)

Each result is stored as a Signal (expansion | capex | strategic_hire | funding_round).
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
DELAY = 1.5

# ─── Target account news queries (named logistics companies) ───────────────────
LOGISTICS_COMPANY_QUERIES = [
    "Prologis new facility expansion construction 2026",
    "DHL Supply Chain new warehouse facility 2026",
    "XPO Logistics expansion distribution center 2026",
    "GXO Logistics new contract facility expansion",
    "Ryder System new facility operations 2026",
    "J.B. Hunt Transport new operations 2026",
    "Lineage Logistics cold storage expansion 2026",
    "Americold new cold storage facility 2026",
    "C.H. Robinson operations expansion 2026",
    "FedEx Ground opens new facility 2026",
    "UPS Supply Chain new distribution facility",
    "Maersk logistics new warehouse US operations",
    "CEVA Logistics new facility contract 2026",
    "NFI Industries new warehouse distribution center",
    "Saddle Creek Logistics expansion new facility",
    "Kenco Logistics new warehouse operations 2026",
    # Grocery / retail DCs
    "Walmart new distribution center automation 2026",
    "Target new distribution center fulfillment 2026",
    "Kroger fulfillment center expansion new facility",
    "Costco new distribution facility operations 2026",
    "Amazon fulfillment center new opens construction 2026",
    # 3PL / contract logistics
    "third party logistics 3PL new contract facility 2026",
    "contract logistics new facility multi-tenant 2026",
    "cold chain logistics new facility investment 2026",
    # Labor + capacity pain
    "logistics company labor shortage operations worker",
    "fulfillment center hiring operations worker shortage 2026",
    "supply chain staffing challenge workforce 2026",
    # CapEx / technology initiatives
    "logistics technology investment automation WMS 2026",
    "warehouse management system implementation new facility",
    "supply chain automation investment capital 2026",
]

_INDUSTRY = "Logistics"

_SIGNAL_MAP = {
    "expansion":      ["expand", "opening", "new facilit", "new warehouse", "groundbreak", "ribbon cut", "construction", "new location"],
    "capex":          ["capex", "capital expenditure", "capital investment", "million invest", "$ million", "technology invest"],
    "funding_round":  ["series ", "funding", "raised $", "private equity", "ipo", "capital raise"],
    "ma_activity":    ["acqui", "merger", "buyout", "joint venture"],
    "strategic_hire": ["vp ", "svp ", "director of", "head of", "chief ", "appoint", "joins as", "named as"],
    "labor_shortage": ["labor shortage", "staffing shortage", "worker shortage", "turnover", "understaffed"],
}


def _classify(text: str) -> str:
    lower = text.lower()
    for sig_type, kws in _SIGNAL_MAP.items():
        if any(kw in lower for kw in kws):
            return sig_type
    return "news"


def _is_relevant(text: str) -> bool:
    lower = text.lower()
    return any(w in lower for w in [
        "warehouse", "logistics", "fulfillment", "distribution", "supply chain",
        "3pl", "cold storage", "freight", "transport", "shipping", "dock",
        "invest", "expand", "capex", "facility", "labor", "automat", "robot",
    ])


class LogisticsDirectoryScraper:
    """
    News + press-release scraper focused entirely on the Logistics vertical.
    Uses Google News RSS (no Playwright required) to surface high-value signals
    from named logistics accounts and industry-wide expansion announcements.
    """

    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()

    def run(self, queries: List[str] = None, max_per_query: int = 8):
        active = queries or LOGISTICS_COMPANY_QUERIES
        total = 0
        logger.info("[LogisticsScraper] Starting — %d queries", len(active))
        for query in active:
            articles = self._fetch_rss(query)
            for art in articles[:max_per_query]:
                if not _is_relevant(art["text"]):
                    continue
                company_name, industry = self._extract_company(art["text"])
                if company_name:
                    saved = self._save(art, company_name, industry or _INDUSTRY)
                    if saved:
                        total += 1
            time.sleep(DELAY)
        logger.info("[LogisticsScraper] Done — %d new signals", total)

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
            ch = root.find("channel")
            if ch is None:
                return []
            for item in ch.findall("item"):
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
            logger.warning("[LogisticsScraper] XML parse error '%s': %s", query, e)
        except Exception as e:
            logger.warning("[LogisticsScraper] Fetch failed '%s': %s", query, e)
        return articles

    def _extract_company(self, text: str):
        lower = text.lower()
        for key in sorted(KNOWN_COMPANIES.keys(), key=len, reverse=True):
            if key in lower:
                return KNOWN_COMPANIES[key]
        match = _COMPANY_ANNOUNCE_RE.search(text)
        if match:
            name = match.group(1).strip()
            if 2 < len(name) <= 60 and name.lower() not in ("the", "a", "an", "this", "our"):
                return name, _INDUSTRY
        return None, None

    def _get_or_create_company(self, name: str, industry: str) -> Optional[Company]:
        if not name:
            return None
        existing = self.db.query(Company).filter(Company.name == name).first()
        if existing:
            return existing
        company = Company(name=name, industry=industry, source="logistics_directory_scraper")
        self.db.add(company)
        self.db.commit()
        self.db.refresh(company)
        return company

    def _save(self, article: dict, company_name: str, industry: str) -> bool:
        company = self._get_or_create_company(company_name, industry)
        if not company:
            return False
        signal_text = article["text"][:600]
        dup = self.db.query(Signal).filter(
            Signal.company_id == company.id,
            Signal.signal_text == signal_text,
        ).first()
        if dup:
            return False
        result = analyze(f"{company_name} {industry} {article['text']}", industry=industry)
        strength = round(min(result.overall_intent, 1.0), 4)
        if strength < 0.05:
            return False
        signal = Signal(
            company_id=company.id,
            signal_type=_classify(article["text"]),
            signal_text=signal_text,
            signal_strength=strength,
            source_url=article.get("url", ""),
        )
        self.db.add(signal)
        self.db.commit()
        logger.debug("[LogisticsScraper] Saved [%s] for %s (%.2f)",
                     signal.signal_type, company_name, strength)
        return True
