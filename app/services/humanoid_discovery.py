"""
Humanoid company & product discovery — seeds ``humanoid_benchmarks`` at scale.

Sources:
1. Curated vendor catalog (~180 products)
2. ``robot_companies`` rows with robot_type humanoid
3. Google News RSS humanoid startup queries
4. AI agent HEIF scoring (HEIR 2026 protocol)
"""
from __future__ import annotations

import logging
import re
import ssl
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Set

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.humanoid_scraper import (
    agent_assess_humanoid,
    compute_scores,
    upsert_humanoid_robot,
    _search_robot_specs,
)
from app.services.humanoid_spec_gaps import SEED_SPECS_BY_SLUG
from app.services.humanoid_catalog_cleanup import is_excluded_humanoid_slug, is_junk_humanoid_row
from app.services.humanoid_vendor_catalog import catalog_entries, normalize_catalog_entry, slugify

logger = logging.getLogger(__name__)

GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
    )
}

HUMANOID_DISCOVERY_QUERIES = [
    "humanoid robot startup 2025 2026",
    "humanoid robot company funding",
    "bipedal robot manufacturer",
    "humanoid robot CES 2025 2026",
    "Chinese humanoid robot startup",
    "humanoid robot pilot deployment factory",
    "general purpose humanoid robot",
    "humanoid robotics Series A",
    "humanoid robot warehouse pilot",
    "android robot company",
    "humanoid robot OEM",
    "humanoid robot benchmark",
    "AgiBot humanoid",
    "Unitree humanoid G1",
    "Figure AI humanoid",
    "EngineAI humanoid robot",
    "Astribot humanoid",
    "Galbot humanoid robot",
    "LimX Dynamics humanoid",
    "Kepler humanoid robot",
]

_PUBLISHER_SUFFIX = re.compile(r"\s+[-–—|]\s+[^-–—|]{2,80}$")
_HUMANOID_RE = re.compile(
    r"\b(humanoid|biped(?:al)?|android robot|general.?purpose robot|"
    r"human.?shaped robot|anthropomorphic robot)\b",
    re.I,
)


def _ssl_context():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def _strip_title(title: str) -> str:
    return _PUBLISHER_SUFFIX.sub("", (title or "").strip()).strip()


def _fetch_rss(query: str, max_items: int = 8) -> List[dict]:
    url = GOOGLE_NEWS_RSS.format(query=urllib.parse.quote(query))
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=12, context=_ssl_context()) as resp:
            root = ET.fromstring(resp.read())
    except Exception as exc:
        logger.warning("RSS fetch failed for %r: %s", query, exc)
        return []

    items = []
    for item in root.findall(".//item")[:max_items]:
        title = _strip_title(item.findtext("title") or "")
        link = item.findtext("link") or ""
        desc = item.findtext("description") or ""
        if title and _HUMANOID_RE.search(f"{title} {desc}"):
            items.append({"title": title, "url": link, "description": desc})
    return items


def _extract_vendor_from_headline(title: str) -> Optional[str]:
    from app.services.robot_vendor_names import KNOWN_ROBOTICS_VENDOR_NAMES

    lower = title.lower()
    for vendor in sorted(KNOWN_ROBOTICS_VENDOR_NAMES, key=len, reverse=True):
        if vendor in lower:
            return vendor.title() if vendor == vendor.lower() else vendor

    from app.services.company_name_inference import extract_company_name_from_headline
    name = extract_company_name_from_headline(title)
    if name and len(name) >= 3:
        return name
    return None


def _catalog_candidates() -> List[dict]:
    return catalog_entries()


def _robot_company_candidates(db: Session) -> List[dict]:
    rows = db.execute(
        text("""
            SELECT company_name, website, robot_type, country, lead_score
            FROM robot_companies
            WHERE lower(coalesce(robot_type, '')) = 'humanoid'
            ORDER BY lead_score DESC NULLS LAST
        """)
    ).mappings().all()

    out = []
    for row in rows:
        vendor = row["company_name"]
        slug = slugify(vendor)
        out.append(normalize_catalog_entry({
            "name": f"{vendor} Humanoid",
            "vendor": vendor,
            "model_slug": slug,
            "product_url": row.get("website"),
            "status": "pilot" if (row.get("lead_score") or 0) >= 80 else "research",
            "country": row.get("country"),
            "specs": {},
        }))
    return [c for c in out if not is_junk_humanoid_row(c["name"], c["vendor"], c["model_slug"])]


def _news_candidates(max_queries: int = 10) -> List[dict]:
    seen_titles: Set[str] = set()
    candidates: List[dict] = []

    for query in HUMANOID_DISCOVERY_QUERIES[:max_queries]:
        for art in _fetch_rss(query):
            title = art["title"]
            if title in seen_titles:
                continue
            seen_titles.add(title)
            vendor = _extract_vendor_from_headline(title)
            if not vendor:
                continue
            slug = slugify(f"{vendor}-{title[:40]}")
            candidates.append({
                "name": title[:120],
                "vendor": vendor,
                "model_slug": slug,
                "product_url": art.get("url"),
                "status": "research",
                "specs": {},
                "sources": [art],
            })
        time.sleep(1.2)

    return [c for c in candidates if not is_junk_humanoid_row(c["name"], c["vendor"], c["model_slug"])]


def _merge_candidates(*groups: List[dict]) -> List[dict]:
    by_slug: Dict[str, dict] = {}
    for group in groups:
        for entry in group:
            slug = entry.get("model_slug") or slugify(f"{entry.get('vendor')}-{entry.get('name')}")
            entry = normalize_catalog_entry({**entry, "model_slug": slug})
            if slug in by_slug:
                prev = by_slug[slug]
                prev_specs = prev.get("specs") or {}
                prev_specs.update(entry.get("specs") or {})
                prev["specs"] = prev_specs
                prev_sources = list(prev.get("sources") or [])
                prev_sources.extend(entry.get("sources") or [])
                prev["sources"] = prev_sources
                if not prev.get("product_url") and entry.get("product_url"):
                    prev["product_url"] = entry["product_url"]
            else:
                by_slug[slug] = entry
    return list(by_slug.values())


def _existing_slugs(db: Session) -> Set[str]:
    rows = db.execute(text("SELECT model_slug FROM humanoid_benchmarks")).all()
    return {r[0] for r in rows if r[0]}


def run_humanoid_discovery(
    db: Session,
    *,
    use_catalog: bool = True,
    use_robot_companies: bool = True,
    news_queries: int = 8,
    agent_limit: int = 30,
    rescore_existing: bool = False,
) -> dict:
    """
    Discover humanoid products, score with HEIF agent, upsert to humanoid_benchmarks.

    ``agent_limit``: max LLM assessments per run (catalog-only rows use rule-based scores).
    """
    groups: List[List[dict]] = []
    if use_catalog:
        groups.append(_catalog_candidates())
    if use_robot_companies:
        groups.append(_robot_company_candidates(db))
    if news_queries > 0:
        groups.append(_news_candidates(max_queries=news_queries))

    candidates = _merge_candidates(*groups) if groups else []
    existing = _existing_slugs(db)

    stats = {
        "catalog_candidates": len(groups[0]) if use_catalog and groups else 0,
        "total_candidates": len(candidates),
        "inserted": 0,
        "updated": 0,
        "agent_scored": 0,
        "skipped": 0,
        "errors": 0,
    }

    agent_budget = agent_limit
    for entry in candidates:
        slug = entry["model_slug"]
        if is_excluded_humanoid_slug(slug) or is_junk_humanoid_row(
            entry.get("name") or "", entry.get("vendor") or "", slug
        ):
            stats["skipped"] += 1
            continue
        is_new = slug not in existing
        if not is_new and not rescore_existing:
            stats["skipped"] += 1
            continue
        # Rescore mode: only AI-assess up to agent_limit — skip mass rule-based rewrites.
        if not is_new and rescore_existing and agent_budget <= 0:
            stats["skipped"] += 1
            continue

        try:
            entry = {
                **entry,
                "specs": {**(SEED_SPECS_BY_SLUG.get(slug) or {}), **(entry.get("specs") or {})},
            }
            use_agent = agent_budget > 0 and (is_new or rescore_existing)
            articles = list(entry.get("sources") or [])
            if use_agent and not articles:
                articles = _search_robot_specs(entry["name"], entry["vendor"])

            if use_agent:
                assessment = agent_assess_humanoid(
                    entry["name"],
                    entry["vendor"],
                    country=entry.get("country") or "",
                    status=entry.get("status") or "research",
                    product_url=entry.get("product_url") or "",
                    articles=articles,
                    existing_specs=entry.get("specs") or {},
                )
                agent_budget -= 1
                if assessment.get("agent_scored"):
                    stats["agent_scored"] += 1
            else:
                specs = entry.get("specs") or {}
                scores = compute_scores(
                    specs,
                    status=entry.get("status") or "research",
                    vendor=entry["vendor"],
                )
                assessment = {
                    "status": entry.get("status") or "research",
                    "specs": specs,
                    "scores": scores,
                    "evidence_summary": "Catalog rule-based score",
                }

            robot = {
                **entry,
                "status": assessment["status"],
                "specs": assessment["specs"],
                "scores": assessment["scores"],
                "evidence_summary": assessment.get("evidence_summary", ""),
                "sources": articles,
            }
            result = upsert_humanoid_robot(db, robot, source="discovery", commit=False)
            stats[result] = stats.get(result, 0) + 1
            existing.add(slug)
        except Exception as exc:
            logger.warning("Discovery failed for %s: %s", slug, exc)
            stats["errors"] += 1

    db.commit()
    stats["total_in_db"] = db.execute(
        text("SELECT COUNT(*) FROM humanoid_benchmarks")
    ).scalar() or 0
    return stats
