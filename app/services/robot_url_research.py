"""Grounded research pass over stored robot URLs.

Walks ``robot_submissions``, fetches the company page with a hard crawl budget
(Agtonomy-class JS shells fail fast), and stores spec/news snippets only when
the text is on the company host or a cited public source URL. Incomplete
identity stays incomplete. SKUs are never invented.
"""
from __future__ import annotations

import logging
import re
import time
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.parse import urljoin, urlparse

from sqlalchemy.orm import Session

from app.models.robot_submission import RobotSubmission
from app.services.robot_url_safety import robot_url_host

logger = logging.getLogger(__name__)

RESEARCH_BUDGET_SEC = 8.0
MAX_SNIPPETS = 6
_NEWS_HREF = re.compile(
    r"/(news|blog|press|updates?|changelog|release|specs?|products?)(/|$|\?)",
    re.I,
)
_SKU_INVENT = re.compile(
    r"\b(model|sku|product)\s+(called|named)\s+[A-Z0-9][\w-]{1,20}\b",
    re.I,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _same_host(url: str, host: str) -> bool:
    try:
        parsed = urlparse(url)
    except Exception:
        return False
    other = (parsed.hostname or "").lower().removeprefix("www.")
    return bool(other and other == host)


def _clean_text(raw: str, *, limit: int = 400) -> str:
    text = re.sub(r"\s+", " ", (raw or "")).strip()
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0]
    return (cut or text[:limit]).rstrip(" ,;:") + "…"


def _snippet(kind: str, text: str, source_url: str) -> dict[str, Any]:
    return {
        "kind": kind,
        "text": _clean_text(text),
        "source_url": source_url,
        "captured_at": _now().isoformat(),
    }


def extract_grounded_snippets(
    page: Any,
    *,
    host: str,
    extra_pages: list[Any] | None = None,
) -> list[dict[str, Any]]:
    """Snippets only from the company page or a cited same-host/public URL."""
    out: list[dict[str, Any]] = []
    pages = [page, *(extra_pages or [])]
    seen: set[str] = set()
    for item in pages:
        source = getattr(item, "final_url", None) or getattr(item, "url", "") or ""
        if not source:
            continue
        if not _same_host(source, host):
            continue
        title = (getattr(item, "title", None) or "").strip()
        body = (getattr(item, "text", None) or "").strip()
        if title and title.lower() not in seen:
            seen.add(title.lower())
            kind = "news" if _NEWS_HREF.search(source) else "spec"
            out.append(_snippet(kind, title, source))
        if body:
            key = body[:80].lower()
            if key not in seen:
                seen.add(key)
                kind = "news" if _NEWS_HREF.search(source) else "spec"
                out.append(_snippet(kind, body, source))
        if len(out) >= MAX_SNIPPETS:
            break
    return out[:MAX_SNIPPETS]


def research_robot_row(
    db: Session,
    row: RobotSubmission,
    *,
    budget_sec: float = RESEARCH_BUDGET_SEC,
    fetch_page=None,
    homepage_is_chrome_only=None,
) -> dict[str, Any]:
    """Research one stored robot. Always stamps last_researched_at. Fail-open."""
    from app.services.robot_understanding_v1.fetch import (
        DEFAULT_PAGE_TIMEOUT,
        fetch_page as _fetch_page,
        timeout_for_deadline,
    )
    from app.services.robot_understanding_v1.sources import homepage_is_chrome_only as _chrome

    fetch_fn = fetch_page or _fetch_page
    chrome_fn = homepage_is_chrome_only or _chrome
    url = (row.canonical_url or row.submitted_url or "").strip()
    host = (row.host or robot_url_host(url) or "")[:240]
    now = _now()
    result: dict[str, Any] = {
        "id": row.id,
        "canonical_url": url,
        "status": "incomplete",
        "snippets": [],
    }
    if not url:
        row.last_researched_at = now
        row.research_status = "incomplete"
        try:
            db.commit()
        except Exception:
            db.rollback()
        return result

    deadline = time.monotonic() + max(1.0, float(budget_sec))
    try:
        timeout = timeout_for_deadline(deadline, default=DEFAULT_PAGE_TIMEOUT) or (1.0, 2.0)
        page = fetch_fn(url, timeout=timeout, allow_archive=False)
    except Exception as exc:
        logger.info("robot_research_fetch_failed url=%s err=%s", url, type(exc).__name__)
        row.last_researched_at = now
        row.research_status = "incomplete"
        try:
            db.commit()
        except Exception:
            db.rollback()
        result["error"] = type(exc).__name__
        return result

    extra: list[Any] = []
    chrome_only = False
    try:
        chrome_only = bool(chrome_fn(page))
    except Exception:
        chrome_only = False

    if chrome_only:
        # Agtonomy-class JS shell: do not invent SKUs or follow a hub crawl.
        row.last_researched_at = now
        row.research_status = "incomplete"
        row.research_snippets = []
        try:
            db.commit()
        except Exception:
            db.rollback()
        result["status"] = "incomplete"
        result["chrome_only"] = True
        return result

    if time.monotonic() < deadline:
        for href, anchor in list(getattr(page, "links", None) or [])[:12]:
            if time.monotonic() >= deadline:
                break
            target = urljoin(getattr(page, "final_url", url) or url, href or "")
            if not _NEWS_HREF.search(target) and not _NEWS_HREF.search(anchor or ""):
                continue
            if not _same_host(target, host):
                continue
            try:
                extra_timeout = timeout_for_deadline(deadline, default=(1.5, 3.0))
                if extra_timeout is None:
                    break
                extra.append(fetch_fn(target, timeout=extra_timeout, allow_archive=False))
            except Exception:
                continue
            if len(extra) >= 2:
                break

    snippets = extract_grounded_snippets(page, host=host, extra_pages=extra)
    # Never keep SKU-invention language; grounded title/body from the site is fine.
    snippets = [s for s in snippets if s.get("text") and not _SKU_INVENT.search(s["text"])]
    row.last_researched_at = now
    row.research_snippets = snippets
    row.research_status = "complete" if snippets else "incomplete"
    if not row.host and host:
        row.host = host
    try:
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("robot_research_commit_failed id=%s", row.id)
    result["status"] = row.research_status
    result["snippets"] = snippets
    return result


def due_robot_rows(
    db: Session,
    *,
    limit: int = 25,
    stale_hours: float = 24.0,
) -> list[RobotSubmission]:
    from datetime import timedelta

    from sqlalchemy import or_

    cutoff = _now() - timedelta(hours=max(0.1, stale_hours))
    q = (
        db.query(RobotSubmission)
        .filter(
            or_(
                RobotSubmission.last_researched_at.is_(None),
                RobotSubmission.last_researched_at < cutoff,
            )
        )
        .order_by(RobotSubmission.last_seen_at.desc())
        .limit(max(1, int(limit)))
    )
    return list(q.all())


def research_due_robots(
    db: Session,
    *,
    limit: int = 25,
    budget_sec: float = RESEARCH_BUDGET_SEC,
    stale_hours: float = 24.0,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in due_robot_rows(db, limit=limit, stale_hours=stale_hours):
        out.append(research_robot_row(db, row, budget_sec=budget_sec))
    return out
