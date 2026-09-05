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
from app.services.lead_name_gate import check_oem_prospect_name
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

# Large buyers / operators — semantic actor may be a deployment site, not an OEM prospect
_BUYER_ACTORS = frozenset({
    "amazon", "walmart", "target", "costco", "fedex", "ups", "dhl", "usps",
    "home depot", "lowe's", "lowes", "kroger", "albertsons", "sysco",
    "mcdonald's", "mcdonalds", "starbucks", "delta", "united airlines",
    "boeing", "lockheed martin", "general motors", "ford", "tesla",
})

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


def _extract_oem_company_name(
    title: str,
    description: str = "",
    *,
    semantic_frame=None,
) -> Optional[str]:
    """Best-effort OEM company name — semantic frame actor first, then known vendors."""
    clean_title = _strip_rss_title(title)
    blob = f"{clean_title} {description}".strip()
    if not blob:
        return None

    from app.services.robot_vendor_names import KNOWN_ROBOTICS_VENDOR_NAMES

    lower = blob.lower()
    for vendor in sorted(KNOWN_ROBOTICS_VENDOR_NAMES, key=len, reverse=True):
        if vendor in lower:
            if vendor == vendor.lower():
                return vendor.title()
            return vendor

    if semantic_frame and semantic_frame.actor:
        actor = semantic_frame.actor
        if actor.lower() not in _BUYER_ACTORS:
            return actor

    from app.services.company_name_inference import extract_company_name_from_headline

    name = extract_company_name_from_headline(clean_title)
    if name and len(name) >= 3 and name.lower() not in _BUYER_ACTORS:
        return name

    if semantic_frame and semantic_frame.actor:
        return semantic_frame.actor

    from app.services.headline_parser import extract_actor

    actor = extract_actor(clean_title)
    if actor and len(actor) >= 3 and actor.lower() not in _BUYER_ACTORS:
        return actor

    return None


def _buyer_deployment_not_oem(semantic_frame, blob: str) -> bool:
    """True when verb-anchor actor is a large operator deploying automation, not making robots."""
    if not semantic_frame or not semantic_frame.actor:
        return False
    actor = semantic_frame.actor.lower()
    if actor not in _BUYER_ACTORS:
        return False
    blob_lower = blob.lower()
    oem_markers = (
        "humanoid", "robotics", "robot company", "startup", "oem", " unveils ",
        " launches ", " announces new robot", " biped", " cobot", " amr ",
    )
    if any(m in blob_lower for m in oem_markers):
        return False
    concepts = set(semantic_frame.ontology_concepts or [])
    if concepts & {"humanoid_robotics", "robot_oem", "mobile_robot", "collaborative_robot"}:
        return False
    return True


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
    semantic_frame=None,
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
    if semantic_frame:
        intel["semantic_frame"] = semantic_frame.to_dict()
        intel["semantic_summary"] = semantic_frame.summary_line()

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
        if semantic_frame:
            meta["semantic_frame"] = semantic_frame.to_dict()
            meta["semantic_summary"] = semantic_frame.summary_line()
        existing.market_intelligence = meta
        existing.data_source = existing.data_source or "stagegate_oem_xbot"
        existing.notes = (existing.notes or "")[:2000]
        if article_url and article_url not in (existing.notes or ""):
            existing.notes = f"{existing.notes}\nDiscovered: {article_url}".strip()[:4000]
        db.add(existing)
        _sync_stagegate_crm(db, existing)
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
        market_intelligence={
            "stagegate_oem": intel,
            **(
                {
                    "semantic_frame": semantic_frame.to_dict(),
                    "semantic_summary": semantic_frame.summary_line(),
                }
                if semantic_frame
                else {}
            ),
        },
        notes=f"Auto-discovered via OEM/XBOT news scrape.\n{article_url}"[:4000],
    )
    db.add(rc)
    db.flush()
    _sync_stagegate_crm(db, rc)
    return rc, True


def _sync_stagegate_crm(db: Session, rc: RobotCompany) -> None:
    try:
        from app.services.stagegate_crm_bridge import sync_robot_company_to_crm

        sync_robot_company_to_crm(db, rc, refresh_draft=False)
    except Exception as exc:
        logger.warning("StageGate CRM bridge failed for %r: %s", rc.company_name, exc)


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
        "skipped_buyer_deployment": 0,
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

            from app.services.semantic_frame import parse_news_semantic_frame

            frame = parse_news_semantic_frame(blob)

            if _buyer_deployment_not_oem(frame, blob):
                stats["skipped_buyer_deployment"] += 1
                logger.debug(
                    "OEM: buyer deployment (not OEM) actor=%r — %s",
                    frame.actor,
                    title[:70],
                )
                continue

            need = oem_need_score(text=blob)
            if need.tier not in ("HOT", "WARM"):
                continue

            stats["articles_scored_hot_warm"] += 1
            if need.tier == "HOT":
                stats["oem_hot"] += 1
            else:
                stats["oem_warm"] += 1

            company_name = _extract_oem_company_name(title, desc, semantic_frame=frame)
            if not company_name:
                stats["skipped_no_company_name"] += 1
                logger.debug("OEM: no company extracted from %r", title[:70])
                continue

            ok, reject_reason = check_oem_prospect_name(company_name)
            if not ok:
                stats["skipped_junk_name"] += 1
                logger.debug("OEM gate rejected %r: %s", company_name, reject_reason)
                continue

            rc, created = _upsert_robot_company(
                db,
                company_name,
                need=need,
                article_url=link,
                article_blob=blob,
                semantic_frame=frame,
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


_DEPLOYMENT_MENTION_RE = re.compile(
    r"(?i)\b(deploy(?:ed|s|ing|ment)?|partner(?:ed|s|ing|ship)?|selected|"
    r"install(?:ed|s|ing)?|fleet|pilot(?:ing|ed)?|integrat(?:ed|es|ing)|"
    r"roll(?:ed|ing)?\s+out|chose|chosen|contract(?:ed|s|ing)?)\b",
)


def _vendor_display_name(vendor_key: str) -> str:
    if vendor_key == vendor_key.lower():
        return vendor_key.title()
    return vendor_key


def _mention_need_score(article_blob: str):
    """Score OEM need for a co-mention; bump WARM when text looks like a deployment story."""
    from app.services.oem_need_scorer import OEMNeedScore

    need = oem_need_score(text=article_blob)
    if need.tier in ("HOT", "WARM"):
        return need
    if _DEPLOYMENT_MENTION_RE.search(article_blob or ""):
        return OEMNeedScore(
            total=max(need.total, 48.0),
            tier="WARM",
            icp=need.icp or "General Robotics",
            reasons=(need.reasons or []) + ["mentioned in buyer deployment article"],
        )
    return OEMNeedScore(
        total=max(need.total, 35.0),
        tier="COLD",
        icp=need.icp or "General Robotics",
        reasons=(need.reasons or []) + ["mentioned in industry news article"],
    )


def enrich_vendors_mentioned_in_article(
    db: Session,
    text: str,
    article_url: str = "",
) -> int:
    """
    Scan article text for known robotics OEMs and upsert ``robot_companies`` rows.

    Called from the buyer news scraper so vendor names co-mentioned in deployment
    stories (e.g. "Sysco deploys Fetch AMRs") land in the supply pipeline even
    when the vendor is not the headline subject.
    """
    blob = (text or "").strip()
    if len(blob) < 20:
        return 0

    from app.services.robot_vendor_names import KNOWN_ROBOTICS_VENDOR_NAMES

    lower = blob.lower()
    touched = 0
    seen: set[str] = set()

    for vendor_key in sorted(KNOWN_ROBOTICS_VENDOR_NAMES, key=len, reverse=True):
        if vendor_key not in lower:
            continue
        display = _vendor_display_name(vendor_key)
        norm = display.lower()
        if norm in seen:
            continue
        seen.add(norm)

        if not check_oem_prospect_name(display)[0]:
            continue

        need = _mention_need_score(blob)
        _upsert_robot_company(
            db,
            display,
            need=need,
            article_url=article_url,
            article_blob=blob[:600],
            semantic_frame=None,
        )
        touched += 1

    if touched:
        db.commit()
    return touched
