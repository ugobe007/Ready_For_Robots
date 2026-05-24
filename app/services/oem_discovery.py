"""
OEM / XBOT discovery for StageGate sales pipeline (Supply Pipeline UI).

Discovers robot OEM companies from news RSS, scores StageGate need probability,
and persists HOT/WARM prospects to ``robot_companies`` — the table that powers
``/supply-pipeline`` and ``GET /api/robot-companies/agent/supply-side``.
"""
from __future__ import annotations

import logging
import re
import ssl
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.robot_company import RobotCompany
from app.scrapers.scrape_targets import get_oem_discovery_queries
from app.services.lead_filter import is_junk
from app.services.oem_need_scorer import score as oem_need_score
from app.services.website_inference import sleep_between_lookups, try_duckduckgo_company_website

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

_PUBLISHER_SUFFIX = re.compile(r"\s+[-–—|]\s+[^-–—|]{2,80}$")
_SHOW_RE = re.compile(r"\b(CES|MODEX|Automate|ProMat|NAB|AUVSI|XPONENTIAL|Hannover)\b", re.I)

_ICP_TO_ROBOT_TYPE = {
    "Foreign Humanoid / Exoskeleton": "humanoid",
    "Medical Robot": "service",
    "Security / Patrol Robot": "service",
    "Hospitality Robot": "service",
    "Warehouse AMR": "AMR",
    "Drone / UAV": "service",
    "Eureka Park Startup": "humanoid",
    "General Robotics": "industrial",
}


def _ssl_context():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def _strip_rss_title(title: str) -> str:
    """Remove Google News publisher suffix: 'Headline - Forbes'."""
    return _PUBLISHER_SUFFIX.sub("", (title or "").strip()).strip()


def _extract_oem_company_name(title: str, description: str = "") -> Optional[str]:
    """Best-effort OEM company name from headline + description."""
    clean_title = _strip_rss_title(title)
    blob = f"{clean_title} {description}".strip()
    if not blob:
        return None

    from app.services.robot_vendor_names import KNOWN_ROBOTICS_VENDOR_NAMES

    lower = blob.lower()
    for vendor in sorted(KNOWN_ROBOTICS_VENDOR_NAMES, key=len, reverse=True):
        if vendor in lower:
            # Preserve canonical casing where possible
            if vendor == vendor.lower():
                return vendor.title()
            return vendor

    from app.services.company_name_inference import extract_company_name_from_headline

    name = extract_company_name_from_headline(clean_title)
    if name and len(name) >= 3:
        return name

    from app.services.headline_parser import extract_actor

    actor = extract_actor(clean_title)
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


def _resolve_website(name: str) -> Optional[str]:
    try:
        from app.services.company_url_openai import (
            batch_resolve_company_homepage_urls,
            openai_url_resolve_enabled,
        )

        if openai_url_resolve_enabled():
            hit = batch_resolve_company_homepage_urls([name]).get(name.lower())
            if hit:
                return hit
    except Exception:
        pass
    found = try_duckduckgo_company_website(name)
    if found:
        sleep_between_lookups(0.5)
    return found


def _upsert_robot_company(
    db: Session,
    name: str,
    *,
    need,
    article_url: str,
    article_blob: str,
) -> Tuple[RobotCompany, bool]:
    existing = (
        db.query(RobotCompany)
        .filter(RobotCompany.company_name.ilike(name))
        .first()
    )
    tier = (need.tier or "COLD").lower()
    robot_type = _ICP_TO_ROBOT_TYPE.get(need.icp or "", "industrial")
    show_match = _SHOW_RE.search(article_blob)
    next_show = show_match.group(1).upper() if show_match else None

    intel = {
        "oem_need_score": round(need.total, 1),
        "oem_need_tier": need.tier,
        "icp": need.icp,
        "reasons": need.reasons[:8],
        "source_article": article_url,
        "source_headline": article_blob[:240],
    }

    if existing:
        existing.lead_score = max(existing.lead_score or 0, int(round(need.total)))
        if tier in ("hot", "warm"):
            existing.priority_tier = tier
        existing.robot_type = existing.robot_type or robot_type
        if next_show:
            existing.next_trade_show = next_show
            shows = list(existing.trade_shows or [])
            if next_show not in shows:
                shows.append(next_show)
                existing.trade_shows = shows
        meta = dict(existing.market_intelligence or {})
        meta["stagegate_oem"] = intel
        existing.market_intelligence = meta
        existing.data_source = existing.data_source or "stagegate_oem_xbot"
        existing.notes = (existing.notes or "")[:2000]
        if article_url and article_url not in (existing.notes or ""):
            existing.notes = f"{existing.notes}\nDiscovered: {article_url}".strip()[:4000]
        db.add(existing)
        return existing, False

    website = _resolve_website(name)
    rc = RobotCompany(
        company_name=name,
        robot_type=robot_type,
        target_market="trade_show_ops",
        lead_score=int(round(need.total)),
        priority_tier=tier if tier in ("hot", "warm") else "warm",
        website=website,
        data_source="stagegate_oem_xbot",
        outreach_status="not_contacted",
        workflow_stage="research",
        next_action="Review StageGate show-ops outreach angle",
        next_trade_show=next_show,
        trade_shows=[next_show] if next_show else None,
        partnership_opportunity="; ".join(need.reasons[:3]),
        market_intelligence={"stagegate_oem": intel},
        notes=f"Auto-discovered via OEM/XBOT news scrape.\n{article_url}"[:4000],
    )
    db.add(rc)
    db.flush()
    return rc, True


def run_oem_discovery(db: Session, *, max_queries: int = 30) -> Dict[str, Any]:
    """
    StageGate prospect discovery: RSS → oem_need_scorer → ``robot_companies`` table.

    Article headlines are NOT run through ``is_junk`` (they are always long).
    Only extracted company names are validated.
    """
    queries = get_oem_discovery_queries()[:max_queries]
    stats = {
        "queries_run": len(queries),
        "articles_seen": 0,
        "articles_scored_hot_warm": 0,
        "oem_hot": 0,
        "oem_warm": 0,
        "robot_companies_created": 0,
        "robot_companies_updated": 0,
        "skipped_no_company_name": 0,
        "skipped_junk_name": 0,
    }
    seen_urls: set[str] = set()

    logger.info("StageGate OEM/XBOT discovery starting — %d queries", len(queries))

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

            blob = f"{_strip_rss_title(title)}. {desc}"
            need = oem_need_score(text=blob)
            if need.tier not in ("HOT", "WARM"):
                continue

            stats["articles_scored_hot_warm"] += 1
            if need.tier == "HOT":
                stats["oem_hot"] += 1
            else:
                stats["oem_warm"] += 1

            company_name = _extract_oem_company_name(title, desc)
            if not company_name:
                stats["skipped_no_company_name"] += 1
                logger.debug("OEM: no company extracted from %r", title[:70])
                continue

            junk, junk_reason = is_junk(company_name, mode="oem_prospect")
            if junk:
                stats["skipped_junk_name"] += 1
                logger.debug("OEM name rejected %r: %s", company_name, junk_reason)
                continue

            from app.services.company_validator import is_valid_lead
            from app.services.text_classifier import classify

            tc = classify(company_name)
            valid, vreason = is_valid_lead(company_name, entity_hint=tc)
            if not valid:
                stats["skipped_junk_name"] += 1
                logger.debug("OEM logic engine rejected %r: %s", company_name, vreason)
                continue

            rc, created = _upsert_robot_company(
                db,
                company_name,
                need=need,
                article_url=link,
                article_blob=blob,
            )
            if created:
                stats["robot_companies_created"] += 1
                logger.info(
                    "StageGate NEW prospect [%s] %s (score=%.0f) — %s",
                    need.tier,
                    rc.company_name,
                    need.total,
                    title[:60],
                )
            else:
                stats["robot_companies_updated"] += 1

        db.commit()
        time.sleep(0.8)

    logger.info(
        "StageGate OEM/XBOT complete: %d HOT/WARM articles | %d new | %d updated robot_companies",
        stats["articles_scored_hot_warm"],
        stats["robot_companies_created"],
        stats["robot_companies_updated"],
    )
    return stats
