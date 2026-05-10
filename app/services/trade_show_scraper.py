"""
Trade show discovery for partner GTM (The Robot Guild, etc.).

Strategy (reliable, low-maintenance):
  1. Fetch curated public event / calendar pages (``TRADE_SHOW_SEED_URLS`` env: comma URLs,
     else built-in robotics-heavy show sites).
  2. Parse ``application/ld+json`` blocks for ``@type`` Event / BusinessEvent.
  3. Keep events whose name/description matches robot / automation relevance heuristics.
  4. ``exhibitor_hints``: substring hits from ``robot_companies.company_name`` plus a small
     static OEM list against page text (best-effort — not an official exhibitor API).

Official exhibitor APIs often require keys; this module is intentionally RSS/HTML-first.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Sequence, Tuple
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from app.models.partner_trade_show import PartnerTradeShow
from app.models.robot_company import RobotCompany

logger = logging.getLogger(__name__)

_DEFAULT_SEED_URLS: Tuple[str, ...] = (
    "https://www.automate.org/",
    "https://www.automate.org/exhibits",
    "https://www.promatsupplychain.com/",
    "https://www.modexshow.com/",
)

_ROBOT_FOCUS = re.compile(
    r"(robot|robotics|cobot|cobots|amr\b|agv|humanoid|machine\s+tending|"
    r"machine\s+vision|industrial\s+automation|motion\s+control|plc\b|"
    r"industry\s*4\.0|warehouse\s+automation|fulfillment\s+automation|"
    r"autonomous\s+mobile|pick\s+and\s+place|welding\s+automation)",
    re.I,
)

_STATIC_OEM_HINTS: Tuple[str, ...] = (
    "ABB",
    "FANUC",
    "KUKA",
    "Yaskawa",
    "Omron",
    "Universal Robots",
    "Boston Dynamics",
    "Agility Robotics",
    "Figure AI",
    "MiR",
    "Mobile Industrial Robots",
    "Locus Robotics",
    "GreyOrange",
    "Symbotic",
    "Exotec",
    "Geek+",
    "Schneider Electric",
    "Siemens",
    "Rockwell Automation",
    "ifm",
    "Keyence",
    "Cognex",
    "Telexistence",
)


def _seed_urls() -> List[str]:
    raw = (os.getenv("TRADE_SHOW_SEED_URLS") or "").strip()
    if raw:
        parts = [p.strip() for p in raw.split(",") if p.strip().startswith("http")]
        if parts:
            return parts
    return list(_DEFAULT_SEED_URLS)


def _flatten_json_ld(data: Any) -> List[dict]:
    out: List[dict] = []
    if isinstance(data, dict):
        t = data.get("@type")
        if isinstance(t, list):
            types = t
        elif isinstance(t, str):
            types = [t]
        else:
            types = []
        if any(x in ("Event", "BusinessEvent", "EducationEvent", "ExhibitionEvent") for x in types):
            out.append(data)
        g = data.get("@graph")
        if isinstance(g, list):
            for item in g:
                out.extend(_flatten_json_ld(item))
    elif isinstance(data, list):
        for item in data:
            out.extend(_flatten_json_ld(item))
    return out


def extract_events_from_html(html: str) -> List[dict]:
    """Return Event-shaped dicts from JSON-LD scripts."""
    soup = BeautifulSoup(html, "html.parser")
    found: List[dict] = []
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = (script.string or "").strip()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        found.extend(_flatten_json_ld(data))
    return found


def _parse_date(val: Any) -> Optional[date]:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, date):
        return val
    s = str(val).strip()
    if not s:
        return None
    s_iso = s.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(s_iso).date()
    except ValueError:
        pass
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    return None


def _event_blob(ev: dict) -> str:
    parts = [
        str(ev.get("name") or ""),
        str(ev.get("description") or ""),
        str(ev.get("location") or ""),
    ]
    loc = ev.get("location")
    if isinstance(loc, dict):
        parts.append(str(loc.get("name") or ""))
        parts.append(str(loc.get("address") or ""))
    return " ".join(parts)


def is_robot_focused_event(ev: dict) -> bool:
    return bool(_ROBOT_FOCUS.search(_event_blob(ev)))


def _source_key(partner_slug: str, name: str, start: Optional[date], url: str) -> str:
    key = f"{partner_slug}|{(name or '').strip().lower()}|{start or ''}|{(url or '').strip()}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:48]


def _collect_brand_hints(db: Session, text_blob: str, limit: int = 35) -> List[str]:
    low = text_blob.lower()
    hits: List[str] = []
    for brand in _STATIC_OEM_HINTS:
        if len(hits) >= limit:
            break
        if brand.lower() in low:
            hits.append(brand)
    try:
        q = (
            db.query(RobotCompany.company_name)
            .filter(RobotCompany.company_name.isnot(None))
            .limit(600)
            .all()
        )
        for (n,) in q:
            if len(hits) >= limit:
                break
            if not n or len(n) < 4:
                continue
            nl = n.strip().lower()
            if nl in low and n.strip() not in hits:
                hits.append(n.strip())
    except Exception as exc:
        logger.debug("robot_companies hint scan skipped: %s", exc)
    return sorted(set(hits), key=len, reverse=True)[:limit]


def _fetch_html(url: str, timeout: int = 22) -> Optional[str]:
    try:
        r = requests.get(
            url,
            timeout=timeout,
            headers={
                "User-Agent": "ReadyForRobots-TradeShowBot/1.0 (+https://readyforrobots.com)",
                "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
            },
        )
        if r.status_code != 200 or not r.text:
            logger.warning("trade_show fetch %s -> HTTP %s", url, r.status_code)
            return None
        return r.text
    except Exception as exc:
        logger.warning("trade_show fetch %s failed: %s", url, exc)
        return None


def scrape_and_upsert_trade_shows(
    db: Session,
    *,
    partner_slug: str = "the_robot_guild",
    seed_urls: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    """
    Fetch seeds, parse JSON-LD events, upsert ``partner_trade_shows`` rows.
    Returns summary counts for the admin API.
    """
    urls = list(seed_urls) if seed_urls is not None else _seed_urls()
    inserted = 0
    updated = 0
    skipped = 0
    errors: List[str] = []

    for url in urls:
        host = urlparse(url).netloc or url
        html = _fetch_html(url)
        if not html:
            errors.append(f"fetch_failed:{host}")
            continue
        events = extract_events_from_html(html)
        if not events:
            skipped += 1
            logger.info("No JSON-LD events on %s — page may use a different format.", host)
            continue
        text_for_hints = html[:400_000]
        for ev in events:
            if not is_robot_focused_event(ev):
                continue
            name = str(ev.get("name") or "").strip()
            if len(name) < 4 or len(name) > 500:
                continue
            start = _parse_date(ev.get("startDate") or ev.get("startdate"))
            end = _parse_date(ev.get("endDate") or ev.get("enddate"))
            loc = ev.get("location")
            location: Optional[str] = None
            if isinstance(loc, str):
                location = loc[:500]
            elif isinstance(loc, dict):
                location = (loc.get("name") or str(loc.get("address") or ""))[:500]
            desc = str(ev.get("description") or "")[:4000]
            event_url = str(ev.get("url") or ev.get("sameAs") or "")[:1024] or None
            blob = _event_blob(ev) + " " + text_for_hints
            hints = _collect_brand_hints(db, blob)
            sk = _source_key(partner_slug, name, start, event_url or url)

            row = db.query(PartnerTradeShow).filter(PartnerTradeShow.source_key == sk).first()
            if row:
                row.name = name[:512]
                row.summary = desc or None
                row.location = location
                row.start_date = start
                row.end_date = end
                row.event_url = event_url
                row.source_page_url = url[:1024]
                row.exhibitor_hints = hints or None
                updated += 1
            else:
                db.add(
                    PartnerTradeShow(
                        partner_slug=partner_slug,
                        source_key=sk,
                        name=name[:512],
                        summary=desc or None,
                        location=location,
                        start_date=start,
                        end_date=end,
                        event_url=event_url,
                        source_page_url=url[:1024],
                        exhibitor_hints=hints or None,
                    )
                )
                inserted += 1
        try:
            db.commit()
        except Exception as exc:
            db.rollback()
            logger.exception("trade_show upsert commit failed for %s: %s", host, exc)
            errors.append(f"db:{host}:{exc}")

    return {
        "partner_slug": partner_slug,
        "seed_urls": urls,
        "inserted": inserted,
        "updated": updated,
        "pages_without_events": skipped,
        "errors": errors,
    }
