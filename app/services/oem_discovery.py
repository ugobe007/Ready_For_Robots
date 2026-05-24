"""
OEM / XBOT discovery for StageGate sales pipeline.

Discovers robot OEM companies (the buyers of StageGate operational infrastructure),
scores need probability, persists HOT/WARM prospects with signals and metadata.
"""
from __future__ import annotations

import logging
import ssl
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.signal import Signal
from app.scrapers.scrape_targets import get_oem_discovery_queries
from app.services.lead_filter import is_junk
from app.services.oem_need_scorer import score as oem_need_score
from app.services.scraper_intelligence import (
    classify_article_signals,
    enrich_new_company_website,
    primary_signal_type,
)

logger = logging.getLogger(__name__)

GOOGLE_NEWS_RSS = (
    "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
)
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
    )
}


def _ssl_context():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def _extract_oem_company_name(title: str, description: str = "") -> Optional[str]:
    """Best-effort OEM company name from headline."""
    blob = f"{title} {description}".strip()
    if not blob:
        return None

    from app.services.robot_vendor_names import KNOWN_ROBOTICS_VENDOR_NAMES

    lower = blob.lower()
    for vendor in sorted(KNOWN_ROBOTICS_VENDOR_NAMES, key=len, reverse=True):
        if vendor in lower:
            return vendor.title() if vendor.islower() else vendor

    from app.services.company_name_inference import extract_company_name_from_headline

    name = extract_company_name_from_headline(title)
    if name and len(name) >= 3:
        return name

    from app.services.headline_parser import extract_actor

    actor = extract_actor(title)
    if actor and len(actor) >= 3:
        return actor

    return None


def _fetch_rss(query: str, *, max_items: int = 8) -> List[dict]:
    url = GOOGLE_NEWS_RSS.format(query=urllib.parse.quote(query))
    items: List[dict] = []
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=12, context=_ssl_context()) as resp:
            root = ET.fromstring(resp.read())
        for item in root.findall(".//item")[:max_items]:
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            desc = (item.findtext("description") or "").strip()
            if title:
                items.append({"title": title, "link": link, "description": desc})
    except Exception as exc:
        logger.debug("OEM RSS fetch failed for %r: %s", query[:50], exc)
    return items


def _get_or_create_oem_company(
    db: Session,
    name: str,
    *,
    icp: str,
    need_score: float,
    tier: str,
    reasons: List[str],
) -> Tuple[Company, bool]:
    existing = db.query(Company).filter(Company.name == name).first()
    if existing:
        meta = dict(existing.crm_metadata or {})
        meta["oem_need"] = {
            "score": need_score,
            "tier": tier,
            "icp": icp,
            "reasons": reasons[:6],
            "source": "oem_xbot",
        }
        existing.crm_metadata = meta
        if not existing.source or existing.source == "news_scraper":
            existing.source = "oem_xbot"
        db.add(existing)
        return existing, False

    company = Company(
        name=name,
        industry="Robotics OEM",
        source="oem_xbot",
        crm_metadata={
            "oem_need": {
                "score": need_score,
                "tier": tier,
                "icp": icp,
                "reasons": reasons[:6],
                "source": "oem_xbot",
            }
        },
    )
    db.add(company)
    db.flush()
    enrich_new_company_website(company)
    return company, True


def run_oem_discovery(db: Session, *, max_queries: int = 30) -> Dict[str, Any]:
    """
    Run XBOT OEM pipeline: RSS queries → oem_prospect junk filter → need scorer → DB.
    """
    queries = get_oem_discovery_queries()[:max_queries]
    stats = {
        "queries_run": len(queries),
        "articles_seen": 0,
        "oem_prospects_found": 0,
        "oem_hot": 0,
        "oem_warm": 0,
        "companies_created": 0,
        "signals_created": 0,
    }
    seen_urls: set[str] = set()

    logger.info("OEM/XBOT discovery starting — %d queries", len(queries))

    for query in queries:
        for article in _fetch_rss(query):
            stats["articles_seen"] += 1
            title = article["title"]
            link = article.get("link") or ""
            desc = article.get("description") or ""
            if link and link in seen_urls:
                continue
            if link:
                seen_urls.add(link)

            blob = f"{title}. {desc}"
            junk, junk_reason = is_junk(title, mode="oem_prospect")
            if junk:
                logger.debug("OEM junk: %r — %s", title[:60], junk_reason)
                continue

            need = oem_need_score(text=blob)
            stats["oem_prospects_found"] += 1
            if need.tier == "HOT":
                stats["oem_hot"] += 1
            elif need.tier == "WARM":
                stats["oem_warm"] += 1
            else:
                continue

            company_name = _extract_oem_company_name(title, desc)
            if not company_name:
                logger.debug("OEM: no company extracted from %r", title[:60])
                continue

            company, created = _get_or_create_oem_company(
                db,
                company_name,
                icp=need.icp or "general",
                need_score=need.total,
                tier=need.tier,
                reasons=need.reasons,
            )
            if created:
                stats["companies_created"] += 1

            signal_types = classify_article_signals(blob, article_url=link)
            sig_type = signal_types[0] if signal_types else primary_signal_type(blob, article_url=link)
            signal_text = blob[:600]

            dup = (
                db.query(Signal)
                .filter(
                    Signal.company_id == company.id,
                    Signal.signal_text == signal_text,
                )
                .first()
            )
            if not dup:
                strength = round(min(need.total / 100.0, 1.0), 4)
                db.add(
                    Signal(
                        company_id=company.id,
                        signal_type=sig_type,
                        signal_text=signal_text,
                        signal_strength=max(strength, 0.5),
                        source_url=link,
                    )
                )
                stats["signals_created"] += 1

        db.commit()
        time.sleep(0.8)

    logger.info(
        "OEM/XBOT complete: %d prospects | %d HOT | %d WARM | %d new companies | %d signals",
        stats["oem_prospects_found"],
        stats["oem_hot"],
        stats["oem_warm"],
        stats["companies_created"],
        stats["signals_created"],
    )
    return stats
