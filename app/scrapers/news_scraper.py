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

# ── Open market intent queries (no specific company) ─────────────────────────
INTENT_QUERIES = [
    "warehouse automation funding round 2025",
    "logistics robotics investment acquisition",
    "hotel labor shortage automation solution",
    "fulfillment center expansion opening 2025",
    "warehouse robotics capex deployment",
    "supply chain automation merger acquisition",
    "VP automation director robotics hired appointed",
    "autonomous mobile robot AMR logistics deal",
    "hotel staffing crisis service robot pilot",
    "distribution center new construction opening",
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

    def run_intent_queries(self, max_per_query: int = 8):
        """
        Run INTENT_QUERIES to discover new companies showing buying intent.
        Creates company records for mentioned companies when possible.
        """
        for query in INTENT_QUERIES:
            logger.info("Intent query: %s", query)
            articles = self._fetch_rss(query)
            for article in articles[:max_per_query]:
                if self._is_relevant(article["text"]):
                    self._save_article_as_signal(article, company_name=None, query=query)
            time.sleep(self.DELAY_BETWEEN_REQUESTS)

    def run(self, company_names: List[str] = None, intent_queries: bool = True):
        """Main entry — run both modes."""
        if company_names:
            self.run_company_queries(company_names)
        if intent_queries:
            self.run_intent_queries()

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

    # ── DB persistence ────────────────────────────────────────────────────────

    def _get_or_create_company(self, name: str) -> Optional[Company]:
        """Look up or create a company record by name."""
        if not name:
            return None
        existing = self.db.query(Company).filter(Company.name == name).first()
        if existing:
            return existing
        company = Company(
            name=name,
            industry="Unknown",
            source="news_scraper",
        )
        self.db.add(company)
        self.db.commit()
        self.db.refresh(company)
        return company

    def _save_article_as_signal(self, article: dict, company_name: Optional[str], query: str):
        """Save one RSS article as a Signal row."""
        company = self._get_or_create_company(company_name) if company_name else None
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
