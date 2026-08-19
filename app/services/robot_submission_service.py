"""Fail-open persistence for submitted robots (durable, deduped entity ledger).

Every robot URL pasted into the front door becomes a durable ``robot_submissions``
row (one per normalized domain) with an integer ID + timestamps + a submission
count. Enrichment (capabilities, matched real buyers) updates the same row.

All writes are best-effort: a persistence failure must never break the user's
research / match request, so every public function swallows errors and rolls back.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.robot_submission import RobotSubmission
from app.services.company_domain import normalize_website_domain

logger = logging.getLogger(__name__)


def _domain_key(url: str | None) -> str | None:
    """Stable dedupe key from a URL. Falls back to a bare-string normalization."""
    if not url or not str(url).strip():
        return None
    dom = normalize_website_domain(url)
    if dom:
        return dom[:240]
    # No parseable host (e.g. a bare token) — still dedupe on a normalized form.
    raw = str(url).strip().lower().split("://")[-1].strip("/")
    return raw[:240] or None


def _get_or_create(db: Session, domain: str, url: str) -> RobotSubmission:
    row = (
        db.query(RobotSubmission)
        .filter(RobotSubmission.website_domain == domain)
        .one_or_none()
    )
    if row is None:
        row = RobotSubmission(
            website_domain=domain,
            submitted_url=url[:2000],
            submission_count=0,
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
) -> Optional[RobotSubmission]:
    """Upsert the durable robot record for ``url``; increment submission count.

    Returns the row (with its ``id``) or None on any failure. Fail-open.
    """
    domain = _domain_key(url)
    if not domain:
        return None
    try:
        row = _get_or_create(db, domain, url)
        row.submitted_url = (url or row.submitted_url)[:2000]
        row.submission_count = int(row.submission_count or 0) + 1
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
        # Likely a race on the unique domain — roll back, re-read, retry the bump once.
        db.rollback()
        try:
            row = (
                db.query(RobotSubmission)
                .filter(RobotSubmission.website_domain == domain)
                .one_or_none()
            )
            if row is not None:
                row.submission_count = int(row.submission_count or 0) + 1
                db.commit()
                db.refresh(row)
                return row
        except Exception:
            db.rollback()
        logger.exception("record_robot_submission_failed domain=%s", domain)
        return None
    except Exception:
        db.rollback()
        logger.exception("record_robot_submission_failed domain=%s", domain)
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

    Creates the row if it does not exist yet (a match can be the first touch, e.g.
    the /pipeline buyers surface). Does NOT bump submission_count.
    """
    domain = _domain_key(url)
    if not domain:
        return None
    from datetime import datetime, timezone

    try:
        row = _get_or_create(db, domain, url)
        if capabilities is not None:
            # Store a compact, stable list of capability keys/labels.
            row.capabilities = _compact_caps(capabilities)
        if matched_company_ids is not None:
            ids = [int(x) for x in matched_company_ids if _is_int(x)][:100]
            row.matched_company_ids = ids
            row.last_match_count = len(ids) if match_count is None else int(match_count)
            row.last_matched_at = datetime.now(timezone.utc)
        elif match_count is not None:
            row.last_match_count = int(match_count)
            row.last_matched_at = datetime.now(timezone.utc)
        if job_count is not None:
            row.last_job_count = int(job_count)
        if source and not row.source:
            row.source = str(source)[:120]
        db.commit()
        db.refresh(row)
        return row
    except Exception:
        db.rollback()
        logger.exception("record_submission_match_failed domain=%s", domain)
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
