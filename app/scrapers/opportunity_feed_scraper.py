"""API-first Robot Job feeds: structured postings, no browser, no anti-bot.

Every fetcher returns normalized *cards* ({title, company, location, desc, url,
html}) and hands them to ``EnhancedJobBoardScraper.process_cards`` — the same
classify → extract → upsert path as the HTML boards, so one ontology governs all.

Lanes (see robot_opportunity_sources):
    amazon_jobs                                   no key
    greenhouse / lever / ashby / smartrecruiters  no key (public board APIs)
    workday                                       no key (public CXS endpoint)
    adzuna / jooble / usajobs / sam_gov           free API keys via env

ATS boards are also *discovered*: any page we scrape that links to
boards.greenhouse.io/<token>, jobs.lever.co/<token>, jobs.ashbyhq.com/<token>,
jobs.smartrecruiters.com/<company> or <tenant>.wdN.myworkdayjobs.com/<site>
is registered in the ``sources`` table (source_type='ats_board') and polled on
the next cycle. Boards that 404 three times in a row are disabled.
"""
from __future__ import annotations

import hashlib
import html as html_lib
import logging
import os
import re
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Iterable, Optional

import requests
from bs4 import BeautifulSoup

from app.scrapers.robot_opportunity_sources import OpportunitySource, api_sources

logger = logging.getLogger(__name__)

UA = "ReadyForRobots/1.0 (+https://readyforrobots.com; jobs@readyforrobots.com)"
TIMEOUT = 25
Card = dict[str, Any]


def _text(raw: str) -> str:
    if not raw:
        return ""
    return BeautifulSoup(html_lib.unescape(str(raw)), "html.parser").get_text(" ", strip=True)


def _get(url: str, **kw) -> requests.Response:
    headers = {"User-Agent": UA, "Accept": "application/json", **kw.pop("headers", {})}
    return requests.get(url, headers=headers, timeout=TIMEOUT, **kw)


def _post(url: str, **kw) -> requests.Response:
    headers = {"User-Agent": UA, "Accept": "application/json", **kw.pop("headers", {})}
    return requests.post(url, headers=headers, timeout=TIMEOUT, **kw)


class SourceGone(Exception):
    """404/410 — board removed or token wrong."""


def _check(r: requests.Response) -> requests.Response:
    if r.status_code in (404, 410):
        raise SourceGone(f"{r.status_code} {r.url}")
    r.raise_for_status()
    return r


# ─── Fetchers ────────────────────────────────────────────────────────────────


def fetch_greenhouse(token: str, company: str = "") -> list[Card]:
    data = _check(_get(f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs", params={"content": "true"})).json()
    out = []
    for j in data.get("jobs") or []:
        content = html_lib.unescape(j.get("content") or "")
        out.append({
            "title": j.get("title") or "",
            "company": company or (j.get("company_name") or token),
            "location": ((j.get("location") or {}).get("name") or ""),
            "desc": _text(content),
            "url": j.get("absolute_url") or "",
            "html": content,
        })
    return out


def fetch_lever(token: str, company: str = "") -> list[Card]:
    data = _check(_get(f"https://api.lever.co/v0/postings/{token}", params={"mode": "json"})).json()
    return [{
        "title": j.get("text") or "",
        "company": company or token,
        "location": ((j.get("categories") or {}).get("location") or ""),
        "desc": j.get("descriptionPlain") or _text(j.get("description") or ""),
        "url": j.get("hostedUrl") or j.get("applyUrl") or "",
        "html": j.get("description") or "",
    } for j in (data if isinstance(data, list) else [])]


def fetch_ashby(token: str, company: str = "") -> list[Card]:
    data = _check(_get(f"https://api.ashbyhq.com/posting-api/job-board/{token}",
                       params={"includeCompensation": "true"})).json()
    out = []
    for j in data.get("jobs") or []:
        comp = ((j.get("compensation") or {}).get("compensationTierSummary") or "")
        out.append({
            "title": j.get("title") or "",
            "company": company or token,
            "location": j.get("location") or "",
            "desc": f"{j.get('descriptionPlain') or _text(j.get('descriptionHtml') or '')} {comp}".strip(),
            "url": j.get("jobUrl") or j.get("applyUrl") or "",
            "html": j.get("descriptionHtml") or "",
        })
    return out


def fetch_smartrecruiters(token: str, company: str = "") -> list[Card]:
    data = _check(_get(f"https://api.smartrecruiters.com/v1/companies/{token}/postings",
                       params={"limit": 100, "country": "us"})).json()
    out = []
    for j in data.get("content") or []:
        loc = j.get("location") or {}
        out.append({
            "title": j.get("name") or "",
            "company": company or ((j.get("company") or {}).get("name") or token),
            "location": ", ".join(p for p in (loc.get("city"), loc.get("region")) if p),
            "desc": " ".join(filter(None, [(j.get("function") or {}).get("label"), (j.get("industry") or {}).get("label"),
                                           (j.get("typeOfEmployment") or {}).get("label")])),
            "url": f"https://jobs.smartrecruiters.com/{token}/{j.get('id')}",
            "html": "",
        })
    return out


def fetch_workday(host: str, tenant: str, site: str, company: str = "", search: str = "") -> list[Card]:
    out: list[Card] = []
    for offset in range(0, 200, 20):
        r = _check(_post(f"https://{host}/wday/cxs/{tenant}/{site}/jobs",
                         json={"appliedFacets": {}, "limit": 20, "offset": offset, "searchText": search}))
        posts = r.json().get("jobPostings") or []
        for j in posts:
            out.append({
                "title": j.get("title") or "",
                "company": company or tenant,
                "location": j.get("locationsText") or "",
                "desc": " ".join(j.get("bulletFields") or []),
                "url": f"https://{host}/{site}{j.get('externalPath') or ''}",
                "html": "",
            })
        if len(posts) < 20:
            break
    return out


def fetch_amazon(query: str) -> list[Card]:
    data = _check(_get("https://www.amazon.jobs/en/search.json", params={
        "base_query": query, "result_limit": 100, "sort": "recent", "country": "USA",
    })).json()
    out = []
    for j in data.get("jobs") or []:
        loc = ", ".join(p for p in (j.get("city"), j.get("state")) if p) or (j.get("location") or "")
        desc = " ".join(filter(None, [j.get("description_short"), _text(j.get("description") or ""),
                                      _text(j.get("basic_qualifications") or "")]))
        out.append({
            "title": j.get("title") or "",
            "company": "Amazon",
            "location": loc,
            "desc": desc,
            "url": "https://www.amazon.jobs" + (j.get("job_path") or ""),
            "html": "",
        })
    return out


def fetch_adzuna(what: str, where: str = "") -> list[Card]:
    app_id, key = os.environ["ADZUNA_APP_ID"], os.environ["ADZUNA_APP_KEY"]
    params = {"app_id": app_id, "app_key": key, "what": what, "results_per_page": 50, "max_days_old": 14,
              "content-type": "application/json", "sort_by": "date"}
    if where:
        params["where"] = where
    data = _check(_get("https://api.adzuna.com/v1/api/jobs/us/search/1", params=params)).json()
    return [{
        "title": _text(j.get("title") or ""),
        "company": ((j.get("company") or {}).get("display_name") or ""),
        "location": ((j.get("location") or {}).get("display_name") or ""),
        "desc": _text(j.get("description") or "")
                + (f" ${j['salary_min']:.0f}-${j['salary_max']:.0f} per year" if j.get("salary_min") and j.get("salary_max") and j["salary_min"] > 1000 else ""),
        "url": j.get("redirect_url") or "",
        "html": "",
    } for j in data.get("results") or []]


def fetch_jooble(keywords: str, location: str = "") -> list[Card]:
    key = os.environ["JOOBLE_API_KEY"]
    data = _check(_post(f"https://jooble.org/api/{key}", json={"keywords": keywords, "location": location or "USA"})).json()
    return [{
        "title": _text(j.get("title") or ""),
        "company": j.get("company") or "",
        "location": j.get("location") or "",
        "desc": _text(j.get("snippet") or "") + (f" {j['salary']}" if j.get("salary") else ""),
        "url": j.get("link") or "",
        "html": "",
    } for j in data.get("jobs") or []]


def fetch_usajobs(keyword: str) -> list[Card]:
    headers = {"Host": "data.usajobs.gov", "User-Agent": os.environ["USAJOBS_EMAIL"],
               "Authorization-Key": os.environ["USAJOBS_API_KEY"]}
    data = _check(_get("https://data.usajobs.gov/api/search",
                       params={"Keyword": keyword, "ResultsPerPage": 250, "DatePosted": 14}, headers=headers)).json()
    out = []
    for item in ((data.get("SearchResult") or {}).get("SearchResultItems") or []):
        d = item.get("MatchedObjectDescriptor") or {}
        pay = (d.get("PositionRemuneration") or [{}])[0]
        summary = ((d.get("UserArea") or {}).get("Details") or {}).get("JobSummary") or ""
        if pay.get("RateIntervalCode") == "PH":
            summary += f" ${pay.get('MinimumRange')}-${pay.get('MaximumRange')} per hour"
        out.append({
            "title": d.get("PositionTitle") or "",
            "company": d.get("OrganizationName") or d.get("DepartmentName") or "",
            "location": d.get("PositionLocationDisplay") or "",
            "desc": summary,
            "url": d.get("PositionURI") or "",
            "html": "",
        })
    return out


def fetch_sam_gov(keyword: str, days: int = 30) -> list[Card]:
    today = datetime.now(timezone.utc).date()
    params = {
        "api_key": os.environ["SAM_GOV_API_KEY"],
        "postedFrom": (today - timedelta(days=days)).strftime("%m/%d/%Y"),
        "postedTo": today.strftime("%m/%d/%Y"),
        "title": keyword,
        "limit": 100,
        "ptype": "o,k,p,r,s",   # solicitation, combined, presolicitation, sources sought, special notice
    }
    data = _check(_get("https://api.sam.gov/opportunities/v2/search", params=params)).json()
    out = []
    for o in data.get("opportunitiesData") or []:
        pop = o.get("placeOfPerformance") or {}
        city = (pop.get("city") or {}).get("name") or ""
        state = (pop.get("state") or {}).get("code") or ""
        agency = (o.get("fullParentPathName") or o.get("department") or "").split(".")[-1].strip()
        notice = o.get("type") or "solicitation"
        out.append({
            "title": o.get("title") or "",
            "company": agency.title() if agency.isupper() else agency,
            "location": ", ".join(p for p in (city, state) if p),
            # The tender itself IS the automation intent; say so for the classifier.
            "desc": f"Request for proposals ({notice}) issued by {agency}: {o.get('title') or ''}. "
                    f"NAICS {o.get('naicsCode') or ''}. Response due {o.get('responseDeadLine') or 'n/a'}.",
            "url": o.get("uiLink") or "",
            "html": "",
            "lane": "tender",
        })
    return out


def _dispatch(src: OpportunitySource) -> list[Card]:
    k, p = src.kind, src.param
    if k == "amazon_jobs":
        return fetch_amazon(p("query"))
    if k == "greenhouse":
        return fetch_greenhouse(p("token"), p("company", ""))
    if k == "lever":
        return fetch_lever(p("token"), p("company", ""))
    if k == "ashby":
        return fetch_ashby(p("token"), p("company", ""))
    if k == "smartrecruiters":
        return fetch_smartrecruiters(p("token"), p("company", ""))
    if k == "workday":
        return fetch_workday(p("host"), p("tenant"), p("site"), p("company", ""), p("search", ""))
    if k == "adzuna":
        return fetch_adzuna(p("what"), p("where", ""))
    if k == "jooble":
        return fetch_jooble(p("keywords"), p("location", ""))
    if k == "usajobs":
        return fetch_usajobs(p("keyword"))
    if k == "sam_gov":
        return fetch_sam_gov(p("keyword"))
    raise ValueError(f"unknown source kind {k}")


# ─── ATS discovery (self-growing employer list) ──────────────────────────────

ATS_PATTERNS: tuple[tuple[str, re.Pattern], ...] = (
    ("greenhouse", re.compile(r"(?:boards|job-boards)(?:\.eu)?\.greenhouse\.io/(?:embed/job_board\?for=)?([A-Za-z0-9_-]{2,60})", re.I)),
    ("lever", re.compile(r"jobs\.lever\.co/([A-Za-z0-9_.-]{2,60})", re.I)),
    ("ashby", re.compile(r"jobs\.ashbyhq\.com/([A-Za-z0-9_.%-]{2,60})", re.I)),
    ("smartrecruiters", re.compile(r"(?:jobs|careers)\.smartrecruiters\.com/([A-Za-z0-9_-]{2,60})", re.I)),
    ("workday", re.compile(r"([a-z0-9-]+)\.(wd\d{1,2})\.myworkdayjobs\.com/(?:[a-z]{2}-[A-Z]{2}/)?([A-Za-z0-9_-]{2,80})", re.I)),
)
_ATS_STOP = {"embed", "jobs", "job", "v1", "boards", "api", "search", "en-us", "login", "careers", "share", "static"}


def find_ats_boards(text: str) -> set[tuple]:
    found: set[tuple] = set()
    for ats, rx in ATS_PATTERNS:
        for m in rx.finditer(text or ""):
            if ats == "workday":
                tenant, wd, site = m.group(1).lower(), m.group(2).lower(), m.group(3)
                if site.lower() in _ATS_STOP:
                    continue
                found.add(("workday", f"{tenant}.{wd}.myworkdayjobs.com", tenant, site))
            else:
                token = m.group(1).strip(".")
                if token.lower() in _ATS_STOP:
                    continue
                found.add((ats, token))
    return found


def _board_key(board: tuple) -> str:
    return "ats:" + ":".join(board)


def register_ats_boards_from_text(db, text: str, found_on: str = "") -> int:
    """Remember ATS boards seen on any page. Returns number newly registered."""
    boards = find_ats_boards(text)
    if not boards or db is None:
        return 0
    from app.models.source import Source

    new = 0
    for board in boards:
        key = _board_key(board)
        if db.query(Source.id).filter(Source.source_type == "ats_board", Source.url == key).first():
            continue
        meta = {"ats": board[0], "found_on": found_on[:500], "status": "new", "fails": 0}
        if board[0] == "workday":
            meta.update(host=board[1], tenant=board[2], site=board[3])
        else:
            meta.update(token=board[1])
        db.add(Source(source_type="ats_board", url=key, title=board[1] if board[0] != "workday" else board[2],
                      metadata_json=meta, captured_at=datetime.now(timezone.utc)))
        new += 1
    if new:
        try:
            db.commit()
        except Exception:
            db.rollback()
            return 0
    return new


def discovered_board_sources(db, limit: int = 200) -> list[tuple[Any, OpportunitySource]]:
    from app.models.source import Source

    rows = (db.query(Source).filter(Source.source_type == "ats_board").order_by(Source.created_at.asc()).limit(limit * 3).all())
    out = []
    for row in rows:
        meta = dict(row.metadata_json or {})
        if meta.get("status") == "disabled":
            continue
        ats = meta.get("ats")
        if ats == "workday":
            params = (("host", meta.get("host")), ("tenant", meta.get("tenant")), ("site", meta.get("site")),
                      ("company", meta.get("company", "")))
        else:
            params = (("token", meta.get("token")), ("company", meta.get("company", "")))
        out.append((row, OpportunitySource(ats, f"{row.title} ({ats}, discovered)", params=params)))
        if len(out) >= limit:
            break
    return out


# ─── Runner ──────────────────────────────────────────────────────────────────


def _missing_env(src: OpportunitySource) -> list[str]:
    return [k for k in src.needs_env if not (os.getenv(k) or "").strip()]


def _scraper(db):
    from app.scrapers.job_board_scraper_enhanced import EnhancedJobBoardScraper

    s = EnhancedJobBoardScraper()
    if db is not None and s.db is not db:
        try:
            s.db.close()
        except Exception:
            pass
        s.db = db
    s._rate_limit = lambda: None  # APIs: we pace per request below, not per card
    return s


def run_sources(
    db,
    sources: Iterable[OpportunitySource],
    *,
    fetch: Callable[[OpportunitySource], list[Card]] = _dispatch,
    pause_s: float = 1.0,
    on_result: Optional[Callable[[OpportunitySource, Optional[dict], Optional[Exception]], None]] = None,
) -> dict[str, Any]:
    from app.services.job_posting_ingest_pause import source_kind_paused

    scraper = _scraper(db)
    totals: dict[str, int] = {"sources": 0, "skipped_no_key": 0, "failed": 0, "found": 0, "robot_jobs": 0}
    missing_keys: set[str] = set()
    for src in sources:
        miss = _missing_env(src)
        if miss:
            totals["skipped_no_key"] += 1
            missing_keys.update(miss)
            continue
        totals["sources"] += 1
        try:
            cards = fetch(src)
            if not source_kind_paused(src.kind):
                for c in cards:
                    register_ats_boards_from_text(db, f"{c.get('url', '')} {c.get('html', '')}", found_on=src.label)
            stats = scraper.process_cards(cards, src.label, source_kind=src.kind)
            totals["found"] += stats.get("found", 0)
            totals["robot_jobs"] += stats.get("robot_jobs", 0)
            logger.info("[OpportunityFeeds] %s found=%s robot_jobs=%s", src.label, stats.get("found"), stats.get("robot_jobs"))
            if on_result:
                on_result(src, stats, None)
        except Exception as exc:  # one bad source never stops the sweep
            totals["failed"] += 1
            logger.warning("[OpportunityFeeds] %s failed: %s", src.label, exc)
            try:
                db.rollback()
            except Exception:
                pass
            if on_result:
                on_result(src, None, exc)
        if pause_s:
            time.sleep(pause_s)
    if missing_keys:
        logger.info("[OpportunityFeeds] skipped sources needing env: %s", ", ".join(sorted(missing_keys)))
    totals["missing_env"] = sorted(missing_keys)  # type: ignore[assignment]
    return totals


def run_opportunity_feeds(kinds: Optional[Iterable[str]] = None, max_sources: Optional[int] = None) -> dict[str, Any]:
    """Scheduled entry point: catalog API sources + discovered ATS boards."""
    from app.database import SessionLocal
    from app.services.job_posting_ingest_pause import source_kind_paused

    cap = max_sources or int(os.getenv("OPPORTUNITY_FEEDS_MAX_SOURCES", "60"))
    db = SessionLocal()
    try:
        static = api_sources(kinds)
        paused_kinds = sorted({s.kind for s in static if source_kind_paused(s.kind)})
        static = [s for s in static if s.kind not in paused_kinds]
        if paused_kinds:
            logger.warning("Opportunity feeds: people-posting kinds paused (PAUSE_JOB_POSTING_INGEST): %s",
                           ", ".join(paused_kinds))
        # Rotate so every API query runs over a day, not just the first `cap`.
        if len(static) > cap:
            cycle = int(time.time() // 3600)
            start = (cycle * cap) % len(static)
            static = (static[start:] + static[:start])[:cap]
        discovered = [(row, src) for row, src in discovered_board_sources(db, limit=max(10, cap // 2))
                      if not source_kind_paused(src.kind)]
        by_src = {id(src): row for row, src in discovered}

        def on_result(src, stats, exc):
            row = by_src.get(id(src))
            if row is None:
                return
            meta = dict(row.metadata_json or {})
            if isinstance(exc, SourceGone):
                meta["fails"] = int(meta.get("fails", 0)) + 1
                if meta["fails"] >= 3:
                    meta["status"] = "disabled"
            elif exc is None:
                meta.update(status="ok", fails=0, last_found=(stats or {}).get("found", 0),
                            last_ok=datetime.now(timezone.utc).isoformat())
            row.metadata_json = meta
            try:
                db.commit()
            except Exception:
                db.rollback()

        result = run_sources(db, static + [src for _, src in discovered], on_result=on_result)
        result["status"] = "ok"
        result["discovered_boards"] = len(discovered)
        result["paused_kinds"] = paused_kinds
        return result
    finally:
        db.close()


def card_fingerprint(card: Card) -> str:
    raw = f"{card.get('company', '')}|{card.get('title', '')}|{card.get('location', '')}".lower()
    return hashlib.sha1(raw.encode()).hexdigest()[:16]
