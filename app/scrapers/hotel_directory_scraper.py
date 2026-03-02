"""
Hotel Directory Scraper — Google News RSS
==========================================
Searches Google News for hotel/hospitality expansion, renovation, and
staffing-shortage signals in key US metro markets.

Previously used Playwright on Yellow Pages (fragile, blocked).
Now uses Google News RSS — same approach as serp_scraper.py.

For each market in the target URLs, we build Google News queries like:
  "hotel Las Vegas NV opening renovation expansion 2026"
and store resulting companies + signals.
"""
import logging
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from typing import List, Optional

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.company import Company
from app.models.signal import Signal
from app.scrapers.news_scraper import KNOWN_COMPANIES

logger = logging.getLogger(__name__)

DELAY = 1.5
GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"

HOTEL_SIGNAL_KEYWORDS = {
    "expansion":     ["expansion", "expand", "new hotel", "opens", "opening", "grand opening", "ribbon cutting", "new property", "construction", "new tower"],
    "capex":         ["renovation", "renovating", "refurbish", "capital investment", "investing", "upgrade", "million"],
    "labor_shortage": ["staffing shortage", "labor shortage", "hard to hire", "workforce", "housekeeping shortage", "turnover"],
    "strategic_hire": ["VP", "Director", "Chief", "General Manager", "appointed", "joins", "named"],
}

# Regex to pull a company name from news headlines
_HOTEL_NAME_RE = re.compile(
    r"([A-Z][A-Za-z0-9&'\- ]{3,40}(?:Hotel|Resort|Inn|Suites|Hilton|Marriott|Hyatt|IHG|Wyndham|Accor|Loews|Omni|Radisson|MGM)[A-Za-z0-9 ]*)"
)


def _extract_city_from_url(url: str) -> str:
    """Extract geo_location_terms from a Yellow Pages URL like:
    ...?search_terms=hotel+resort&geo_location_terms=Las+Vegas+NV
    Returns 'Las Vegas NV' or '' if not found.
    """
    try:
        params = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        loc = params.get("geo_location_terms", [""])[0]
        return urllib.parse.unquote_plus(loc)
    except Exception:
        return ""


def _extract_industry_from_url(url: str) -> str:
    lower = url.lower()
    if "senior" in lower or "nursing" in lower or "healthcare" in lower:
        return "Healthcare"
    if "restaurant" in lower or "food" in lower:
        return "Food Service"
    return "Hospitality"


class HotelDirectoryScraper:
    """Searches Google News for hotel/hospitality expansion signals in key metros."""

    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()
        self._leads_added = 0

    def run(self, urls: List[str]):
        """Accept the existing Yellow Pages target URLs; extract city and run news queries."""
        seen_cities: set = set()
        for url in urls:
            city = _extract_city_from_url(url)
            industry = _extract_industry_from_url(url)

            if not city or city in seen_cities:
                # For US-wide targets (no specific city), use a generic national query
                if not city and url not in seen_cities:
                    seen_cities.add(url)
                    self._run_query(
                        f"{industry.lower()} opening expansion renovation 2026",
                        industry, source_url=url,
                    )
                continue

            seen_cities.add(city)
            queries = [
                f"hotel {city} opening expansion renovation 2026",
                f"hotel {city} new property opens grand opening",
            ]
            if industry == "Healthcare":
                queries = [
                    f"senior living {city} opens expansion 2026",
                    f"nursing facility {city} new campus opens",
                ]
            elif industry == "Food Service":
                queries = [f"restaurant chain {city} new locations expansion 2026"]

            for q in queries:
                self._run_query(q, industry, source_url=url)
                time.sleep(DELAY)

    def _run_query(self, query: str, industry: str, source_url: str):
        rss_url = GOOGLE_NEWS_RSS.format(q=urllib.parse.quote(query))
        try:
            req = urllib.request.Request(
                rss_url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; RSS reader)"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                self._parse_rss(resp.read(), industry, source_url)
        except Exception as e:
            logger.warning("Hotel RSS query failed %r: %s", query, e)

    def _parse_rss(self, xml_bytes: bytes, industry: str, source_url: str):
        try:
            root = ET.fromstring(xml_bytes)
        except ET.ParseError:
            return

        channel = root.find("channel")
        if channel is None:
            return

        for item in channel.findall("item"):
            title_el = item.find("title")
            desc_el  = item.find("description")
            if title_el is None:
                continue

            title     = title_el.text or ""
            desc_text = (desc_el.text or "") if desc_el is not None else ""
            full_text = f"{title} {desc_text}"
            lower     = full_text.lower()

            # Determine signal type and strength
            sig_type = None
            strength  = 0.0
            for stype, keywords in HOTEL_SIGNAL_KEYWORDS.items():
                if any(kw.lower() in lower for kw in keywords):
                    sig_type = stype
                    strength = {"expansion": 0.75, "capex": 0.65, "labor_shortage": 0.60, "strategic_hire": 0.70}.get(stype, 0.50)
                    break

            if not sig_type:
                continue

            # Try to extract a company name
            company_name = None
            m = _HOTEL_NAME_RE.search(title)
            if m:
                company_name = m.group(1).strip()
            if not company_name:
                # Try known company lookup
                for key, (canon, _) in KNOWN_COMPANIES.items():
                    if key in lower:
                        company_name = canon
                        break

            if not company_name:
                continue

            existing = self.db.query(Company).filter(Company.name == company_name).first()
            if existing:
                company = existing
            else:
                company = Company(
                    name=company_name,
                    industry=industry,
                    source="google_news_rss",
                )
                self.db.add(company)
                self.db.flush()
                self._leads_added += 1

            self.db.add(Signal(
                company_id=company.id,
                signal_type=sig_type,
                signal_text=title[:500],
                signal_strength=strength,
                source_url=source_url,
            ))
            self.db.commit()

