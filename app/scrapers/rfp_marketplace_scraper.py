"""
RFP Marketplace & Government Tender Scraper
============================================
Scrapes automation RFP marketplaces and government procurement sites for direct buyer intent.

Sources:
  API-based (reliable, no auth required for basic usage):
    - SAM.gov Opportunities v2 API   — US federal contracts
    - TED.europa.eu Open Data API    — EU public tenders

  RSS / Atom feeds (lightweight, no JS rendering):
    - SAM.gov ATOM feed search
    - USASpending.gov

  HTML scraping (Playwright for JS-rendered, requests+BS4 for static):
    - Qviro.com                      — automation project marketplace
    - JobToRob.com                   — global robotics tenders
    - Automate America               — factory automation RFQs
    - Biddingo.com                   — worldwide procurement

These are HIGHEST-VALUE leads — government + enterprise contracts with confirmed budgets.

Notes on removed targets:
  - SAM.gov HTML: replaced by SAM.gov API below (much more reliable)
  - GSA.gov: redirects to SAM.gov; covered by SAM API
  - RFPBot.com: requires paid subscription; not scraped
  - MERX.com: Canadian tenders — low relevance vs. Las Vegas show market
  - TendersInfo.com: requires login for detail pages; low ROI
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode, urljoin

import requests
from bs4 import BeautifulSoup

from app.scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

# ─── Shared constants ─────────────────────────────────────────────────────────

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) "
        "AppleWebKit/605.1.15 Safari/605.1.15"
    ),
    "Accept": "application/json, text/html, */*",
}

# Keywords used to gate relevance across all sources
_ROBOT_KEYWORDS = [
    "robot", "robotics", "cobot", "autonomous", "amr", "agv",
    "drone", "uav", "uas", "unmanned", "exoskeleton",
    "automated guided", "humanoid", "additive manufactur", "3d print",
    "surgical robot", "material handling", "warehouse automation",
    "computer vision", "machine vision",
]

_ROBOT_RE = re.compile("|".join(_ROBOT_KEYWORDS), re.I)


def _is_robot_related(text: str) -> bool:
    return bool(_ROBOT_RE.search(text))


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ─── SAM.gov (US Federal Contracts) ──────────────────────────────────────────

_SAM_API_BASE = "https://api.sam.gov/opportunities/v2/search"
_SAM_DATE_FMT = "%m/%d/%Y"


def scrape_sam_gov(
    api_key: str = "DEMO_KEY",
    days_back: int = 30,
    limit: int = 25,
) -> List[Dict[str, Any]]:
    """
    Query the SAM.gov Opportunities v2 API for robot/automation contracts.

    DEMO_KEY works for ≤10 requests/hour / 40/day; set SAM_API_KEY env var
    for higher limits (free registration at api.data.gov).
    """
    import os
    api_key = os.getenv("SAM_API_KEY", api_key)

    posted_from = (_now() - timedelta(days=days_back)).strftime(_SAM_DATE_FMT)
    posted_to   = _now().strftime(_SAM_DATE_FMT)

    results: List[Dict[str, Any]] = []

    for query in ["robot", "autonomous system", "drone UAV", "exoskeleton", "additive manufacturing"]:
        params = {
            "api_key":    api_key,
            "q":          query,
            "postedFrom": posted_from,
            "postedTo":   posted_to,
            "limit":      limit,
            "sort":       "-modifiedDate",
        }
        try:
            resp = requests.get(_SAM_API_BASE, params=params, headers=_HEADERS, timeout=20)
            if resp.status_code == 429:
                logger.warning("SAM.gov rate limited — try setting SAM_API_KEY env var")
                break
            resp.raise_for_status()
            data = resp.json()
            opps = data.get("opportunitiesData", [])
            for opp in opps:
                title = opp.get("title", "")
                desc  = opp.get("description", "") or ""
                dept  = opp.get("departmentName", "") or opp.get("organizationName", "")
                if not _is_robot_related(f"{title} {desc}"):
                    continue
                results.append({
                    "company_name": dept or "US Federal Agency",
                    "signal_type":  "government_contract",
                    "signal_text":  f"SAM.gov Contract: {title}",
                    "url": f"https://sam.gov/opp/{opp.get('noticeId', '')}",
                    "detected_at":  _now(),
                    "source":       "SAM.gov Federal Contracts",
                    "industry":     "Government",
                    "confidence":   0.95,
                })
        except Exception as exc:
            logger.error(f"SAM.gov API error (query={query!r}): {exc}")

    logger.info(f"SAM.gov: {len(results)} robot-related contracts")
    return results


# ─── TED.europa.eu (EU Public Tenders) ───────────────────────────────────────

_TED_API_BASE = "https://ted.europa.eu/api/v3.0/notices/search"


def scrape_ted_europa(days_back: int = 30, page_size: int = 25) -> List[Dict[str, Any]]:
    """
    Search the TED Open Data API for EU automation/robotics public tenders.
    No authentication required for read access.
    """
    results: List[Dict[str, Any]] = []
    cutoff = (_now() - timedelta(days=days_back)).strftime("%Y%m%d")

    for query in ["robot automation", "autonomous drone", "exoskeleton", "additive manufacturing"]:
        params = {
            "q":         query,
            "scope":     3,          # 3 = full notice text
            "language":  "EN",
            "pageSize":  page_size,
            "fields":    "title,publicationDate,contractingAuthorityName,description",
        }
        try:
            resp = requests.get(_TED_API_BASE, params=params, headers=_HEADERS, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            notices = data.get("results", []) or data.get("notices", [])
            for notice in notices:
                pub_date = str(notice.get("publicationDate", "") or "")
                if pub_date.replace("-", "") < cutoff:
                    continue
                title    = notice.get("title", {})
                title_en = title.get("EN", "") if isinstance(title, dict) else str(title)
                authority = notice.get("contractingAuthorityName", "") or "EU Agency"
                desc_raw  = notice.get("description", {})
                desc_en   = (desc_raw.get("EN", "") if isinstance(desc_raw, dict) else str(desc_raw)) or ""
                if not _is_robot_related(f"{title_en} {desc_en}"):
                    continue
                results.append({
                    "company_name": authority,
                    "signal_type":  "government_contract",
                    "signal_text":  f"EU Tender: {title_en}",
                    "url":          f"https://ted.europa.eu/en/notice/{notice.get('noticeId', '')}",
                    "detected_at":  _now(),
                    "source":       "TED EU Public Tenders",
                    "industry":     "Government",
                    "confidence":   0.92,
                })
        except Exception as exc:
            logger.error(f"TED API error (query={query!r}): {exc}")

    logger.info(f"TED: {len(results)} robot-related EU tenders")
    return results


# ─── Qviro (Automation project marketplace) ───────────────────────────────────

def scrape_qviro(url: str = "https://qviro.com/match/projects") -> List[Dict[str, Any]]:
    """
    Qviro renders via React — try the JSON data endpoint first, fall back to HTML.
    The public project listing JSON lives at /api/projects (undocumented but stable).
    """
    results: List[Dict[str, Any]] = []

    # Try JSON API first
    json_url = "https://qviro.com/api/projects?limit=20&status=open"
    try:
        resp = requests.get(json_url, headers=_HEADERS, timeout=20)
        if resp.ok:
            items = resp.json() if isinstance(resp.json(), list) else resp.json().get("projects", [])
            for item in items[:20]:
                title   = item.get("title", "") or item.get("name", "")
                company = item.get("company", "") or item.get("buyerName", "Unknown Company")
                desc    = item.get("description", "") or ""
                if not _is_robot_related(f"{title} {desc}"):
                    continue
                results.append({
                    "company_name": company,
                    "signal_type":  "rfp_posted",
                    "signal_text":  f"Qviro Project: {title}",
                    "url":          item.get("url", url),
                    "detected_at":  _now(),
                    "source":       "Qviro Automation Marketplace",
                    "industry":     "Manufacturing",
                    "confidence":   0.93,
                })
            if results:
                logger.info(f"Qviro JSON API: {len(results)} projects")
                return results
    except Exception:
        pass

    # HTML fallback — Qviro uses data-testid attributes on their project cards
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Try multiple selector strategies for React-rendered content
        cards = (
            soup.find_all(attrs={"data-testid": re.compile(r"project", re.I)})
            or soup.find_all("article")
            or soup.find_all("div", class_=re.compile(r"project|listing|card", re.I))
        )
        for card in cards[:15]:
            heading = card.find(["h2", "h3", "h4"])
            if not heading:
                continue
            title = heading.get_text(strip=True)
            if not _is_robot_related(title):
                continue
            company_el = card.find(class_=re.compile(r"company|buyer|client", re.I))
            results.append({
                "company_name": company_el.get_text(strip=True) if company_el else "Unknown Company",
                "signal_type":  "rfp_posted",
                "signal_text":  f"Qviro Project: {title}",
                "url":          url,
                "detected_at":  _now(),
                "source":       "Qviro Automation Marketplace",
                "industry":     "Manufacturing",
                "confidence":   0.93,
            })
    except Exception as exc:
        logger.error(f"Qviro HTML scrape failed: {exc}")

    logger.info(f"Qviro HTML: {len(results)} projects")
    return results


# ─── JobToRob (Global robotics tenders) ──────────────────────────────────────

def scrape_jobtorob(
    url: str = "https://jobtorob.com/global-robotics-command-center-tenders",
) -> List[Dict[str, Any]]:
    """
    JobToRob tender database. Uses table-based HTML layout (no JS required for list view).
    """
    results: List[Dict[str, Any]] = []
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # JobToRob wraps tenders in <table> rows or <div class="views-row">
        rows = (
            soup.find_all("div", class_=re.compile(r"views.row|tender.row|result.item", re.I))
            or soup.find_all("tr", class_=re.compile(r"odd|even", re.I))
            or soup.find_all("article")
        )
        for row in rows[:20]:
            # Title is usually in the first <a> or <h3>/<h4>
            link = row.find("a", href=True)
            heading = row.find(["h3", "h4", "h2"])
            title = (heading or link or row).get_text(strip=True)
            if not title or not _is_robot_related(title):
                continue

            # Organization / issuing body
            org_el = row.find(class_=re.compile(r"organ|agency|buyer|issuer", re.I))
            org = org_el.get_text(strip=True) if org_el else "Government / Industrial Body"

            href = link["href"] if link else url
            full_url = href if href.startswith("http") else urljoin("https://jobtorob.com", href)

            results.append({
                "company_name": org,
                "signal_type":  "government_contract",
                "signal_text":  f"Robotics Tender: {title}",
                "url":          full_url,
                "detected_at":  _now(),
                "source":       "JobToRob Global Tenders",
                "industry":     "Government",
                "confidence":   0.90,
            })
    except Exception as exc:
        logger.error(f"JobToRob scrape failed: {exc}")

    logger.info(f"JobToRob: {len(results)} tenders")
    return results


# ─── Automate America (Factory automation RFQs) ──────────────────────────────

def scrape_automate_america(
    url: str = "https://automateamerica.com/automation-rfqs-and-projects/",
) -> List[Dict[str, Any]]:
    """
    Automate America's RFQ board. Static HTML listing.
    """
    results: List[Dict[str, Any]] = []
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Page uses WordPress-style post listings
        posts = (
            soup.find_all("article")
            or soup.find_all("div", class_=re.compile(r"post|rfq|listing|entry", re.I))
        )
        for post in posts[:15]:
            heading = post.find(["h2", "h3", "h4"])
            if not heading:
                continue
            title = heading.get_text(strip=True)
            if not _is_robot_related(title):
                continue
            link = heading.find("a", href=True) or post.find("a", href=True)
            href = link["href"] if link else url
            excerpt = post.find(class_=re.compile(r"excerpt|summary|content", re.I))
            desc = excerpt.get_text(strip=True)[:200] if excerpt else ""

            results.append({
                "company_name": "Manufacturer",
                "signal_type":  "factory_automation",
                "signal_text":  f"Factory RFQ: {title}. {desc}",
                "url":          href if href.startswith("http") else urljoin(url, href),
                "detected_at":  _now(),
                "source":       "Automate America RFQs",
                "industry":     "Manufacturing",
                "confidence":   0.95,
            })
    except Exception as exc:
        logger.error(f"Automate America scrape failed: {exc}")

    logger.info(f"Automate America: {len(results)} RFQs")
    return results


# ─── Biddingo (Worldwide procurement) ────────────────────────────────────────

def scrape_biddingo(
    base_url: str = "https://www.biddingo.com/search",
) -> List[Dict[str, Any]]:
    """
    Biddingo public tender search — static paginated HTML.
    """
    results: List[Dict[str, Any]] = []
    for query in ["robot", "automation", "drone"]:
        try:
            resp = requests.get(
                base_url,
                params={"q": query, "st": "op"},
                headers=_HEADERS,
                timeout=20,
            )
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            rows = (
                soup.find_all("div", class_=re.compile(r"tender|bid|result|listing", re.I))
                or soup.find_all("article")
                or soup.find_all("li", class_=re.compile(r"item|result", re.I))
            )
            for row in rows[:15]:
                heading = row.find(["h2", "h3", "h4", "a"])
                if not heading:
                    continue
                title = heading.get_text(strip=True)
                if not _is_robot_related(title):
                    continue
                org_el = row.find(class_=re.compile(r"org|agency|buyer|issuer", re.I))
                org = org_el.get_text(strip=True) if org_el else "Government Agency"
                link = row.find("a", href=True)
                href = link["href"] if link else base_url
                results.append({
                    "company_name": org,
                    "signal_type":  "government_contract",
                    "signal_text":  f"Biddingo Tender: {title}",
                    "url":          href if href.startswith("http") else urljoin("https://www.biddingo.com", href),
                    "detected_at":  _now(),
                    "source":       "Biddingo Procurement",
                    "industry":     "Government",
                    "confidence":   0.88,
                })
        except Exception as exc:
            logger.error(f"Biddingo scrape failed (query={query!r}): {exc}")

    logger.info(f"Biddingo: {len(results)} tenders")
    return results


# ─── Main class (BaseScraper compat) ─────────────────────────────────────────

class RFPMarketplaceScraper(BaseScraper):
    """
    Unified RFP / tender scraper with per-source routing.
    Uses requests+BS4 for HTML sites and REST APIs for SAM.gov and TED.
    """

    def __init__(self, db=None):
        super().__init__(db=db)

    def scrape(self, url: str, **kwargs) -> List[Dict[str, Any]]:
        if "sam.gov" in url:
            return scrape_sam_gov()
        elif "ted.europa.eu" in url:
            return scrape_ted_europa()
        elif "qviro.com" in url:
            return scrape_qviro(url)
        elif "jobtorob.com" in url:
            return scrape_jobtorob(url)
        elif "automateamerica.com" in url:
            return scrape_automate_america(url)
        elif "biddingo.com" in url:
            return scrape_biddingo()
        else:
            logger.warning(f"Unknown RFP marketplace URL: {url}")
            return []

    def parse(self, html: str, url: str):
        """No-op: RFP scraper uses direct requests/API, not Playwright. Required by BaseScraper."""
        pass


# ─── Standalone runner ────────────────────────────────────────────────────────

def scrape_rfp_marketplaces() -> List[Dict[str, Any]]:
    """
    Run all RFP/tender sources and return the merged signal list.
    Called by the Celery worker and the scraper_control API.
    """
    all_signals: List[Dict[str, Any]] = []

    runners = [
        ("SAM.gov",           scrape_sam_gov),
        ("TED EU",            scrape_ted_europa),
        ("Qviro",             scrape_qviro),
        ("JobToRob",          scrape_jobtorob),
        ("Automate America",  scrape_automate_america),
        ("Biddingo",          scrape_biddingo),
    ]

    for name, fn in runners:
        try:
            signals = fn()
            all_signals.extend(signals)
            logger.info(f"{name}: {len(signals)} signals")
        except Exception as exc:
            logger.error(f"{name} runner failed: {exc}")

    logger.info(f"Total RFP signals: {len(all_signals)}")
    return all_signals
