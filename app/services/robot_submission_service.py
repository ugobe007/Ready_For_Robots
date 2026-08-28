"""Fail-open persistence for submitted robots (durable, URL-keyed entity ledger).

Every robot URL pasted into FIND becomes a durable ``robot_submissions`` row
(one per canonical URL) with an integer ID + first/last seen + a submission
count. Incomplete identity (Agtonomy qualify_robot) still writes the URL.
Enrichment (capabilities, matched buyers, research snippets) updates the same
row.

All writes are best-effort: a persistence failure must never break the user's
research / match request, so every public function swallows errors and rolls back.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.robot_submission import RobotSubmission
from app.services.company_domain import normalize_website_domain
from app.services.robot_url_safety import canonical_robot_url, robot_url_host

logger = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _canonical_key(url: str | None) -> str | None:
    key = canonical_robot_url(url)
    if key:
        return key[:2000]
    return None


def _host_key(url: str | None, canonical: str | None = None) -> str:
    host = robot_url_host(canonical or url)
    if host:
        return host[:240]
    dom = normalize_website_domain(url or "")
    if dom:
        return str(dom)[:240]
    raw = str(url or "").strip().lower().split("://")[-1].strip("/")
    return (raw.split("/")[0] if raw else "unknown")[:240]


def _get_or_create(db: Session, canonical: str, url: str) -> RobotSubmission:
    row = (
        db.query(RobotSubmission)
        .filter(RobotSubmission.canonical_url == canonical)
        .one_or_none()
    )
    if row is None:
        host = _host_key(url, canonical)
        row = RobotSubmission(
            canonical_url=canonical,
            website_domain=host,
            host=host,
            submitted_url=(url or canonical)[:2000],
            submission_count=0,
            research_snippets=[],
        )
        db.add(row)
    return row


def record_robot_submission(
    db: Session,
    *,
    url: str,
    company_name: Optional[str] = None,
    product_name: Optional[str] = None,
    robot_class: Optional[str] = None,
    profile_tier: Optional[str] = None,
    source: Optional[str] = None,
    bump_count: bool = True,
) -> Optional[RobotSubmission]:
    """Upsert the durable robot record for ``url``.

    Incomplete identity is fine — the canonical URL is the row. Returns the
    row (with its ``id``) or None on any failure. Fail-open.
    """
    canonical = _canonical_key(url)
    if not canonical:
        return None
    now = _now()
    try:
        row = _get_or_create(db, canonical, url)
        row.submitted_url = (url or row.submitted_url)[:2000]
        row.host = _host_key(url, canonical)
        if not row.website_domain:
            row.website_domain = row.host
        if bump_count:
            row.submission_count = int(row.submission_count or 0) + 1
        if row.first_seen_at is None:
            row.first_seen_at = now
        row.last_seen_at = now
        if company_name:
            row.company_name = str(company_name)[:240]
        if product_name:
            row.product_name = str(product_name)[:240]
        if robot_class:
            row.robot_class = str(robot_class)[:64]
        if profile_tier:
            row.profile_tier = str(profile_tier)[:8]
        if source and not row.source:
            row.source = str(source)[:120]
        db.commit()
        db.refresh(row)
        return row
    except SQLAlchemyError:
        db.rollback()
        try:
            row = (
                db.query(RobotSubmission)
                .filter(RobotSubmission.canonical_url == canonical)
                .one_or_none()
            )
            if row is not None:
                if bump_count:
                    row.submission_count = int(row.submission_count or 0) + 1
                row.last_seen_at = now
                db.commit()
                db.refresh(row)
                return row
        except Exception:
            db.rollback()
        logger.exception("record_robot_submission_failed url=%s", canonical)
        return None
    except Exception:
        db.rollback()
        logger.exception("record_robot_submission_failed url=%s", canonical)
        return None


def record_submission_match(
    db: Session,
    *,
    url: str,
    capabilities: Optional[list[Any]] = None,
    matched_company_ids: Optional[list[int]] = None,
    match_count: Optional[int] = None,
    job_count: Optional[int] = None,
    source: Optional[str] = None,
) -> Optional[RobotSubmission]:
    """Enrich the robot record with capabilities + matched real buyers. Fail-open.

    Creates the row if it does not exist yet. Does NOT bump submission_count.
    """
    canonical = _canonical_key(url)
    if not canonical:
        return None
    now = _now()

    try:
        row = _get_or_create(db, canonical, url)
        if capabilities is not None:
            row.capabilities = _compact_caps(capabilities)
        if matched_company_ids is not None:
            ids = [int(x) for x in matched_company_ids if _is_int(x)][:100]
            row.matched_company_ids = ids
            row.last_match_count = len(ids) if match_count is None else int(match_count)
            row.last_matched_at = now
        elif match_count is not None:
            row.last_match_count = int(match_count)
            row.last_matched_at = now
        if job_count is not None:
            row.last_job_count = int(job_count)
        if source and not row.source:
            row.source = str(source)[:120]
        if row.first_seen_at is None:
            row.first_seen_at = now
        row.last_seen_at = row.last_seen_at or now
        db.commit()
        db.refresh(row)
        return row
    except Exception:
        db.rollback()
        logger.exception("record_submission_match_failed url=%s", canonical)
        return None


def _is_int(x: Any) -> bool:
    try:
        int(x)
        return True
    except (TypeError, ValueError):
        return False


def _compact_caps(capabilities: list[Any]) -> list[str]:
    out: list[str] = []
    for c in capabilities or []:
        if isinstance(c, str):
            key = c
        elif isinstance(c, dict):
            key = c.get("key") or c.get("label") or c.get("name") or ""
        else:
            key = str(c)
        key = str(key).strip()
        if key and key not in out:
            out.append(key)
    return out[:50]
