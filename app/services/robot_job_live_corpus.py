"""Named live Robot Jobs → FIND match corpus rows.

Scrapers persist onto ``robot_jobs``. FIND used a frozen JSON file, so new
employer+work never reached Job Cards. Overlay recent named jobs that map to
a FIND tape family. Fail-open if the table is missing. Do not invent employers.
"""
from __future__ import annotations

import logging
import os
import time
from typing import Any, Optional

from app.services.robot_job_extract import (
    is_job_employer_name,
    job_function_from_title,
    tape_family_for_job_function,
)

logger = logging.getLogger(__name__)

LIVE_CAP = 48
LIVE_TTL_SEC = 600
_CACHE: dict[str, Any] = {"at": 0.0, "rows": ()}

TAPE_INDUSTRY = {
    "pick_pack": "Warehouse",
    "warehouse": "Warehouse",
    "logistics": "Logistics",
    "hospitality": "Hospitality",
    "food_prep": "Restaurant",
    "serve": "Restaurant",
    "disinfection": "Healthcare",
    "clinical_delivery": "Healthcare",
    "pallet": "Factory",
    "factory": "Factory",
    "agriculture": "Agriculture",
    "construction": "Construction",
    "mining": "Mining",
}

TAPE_FAMILIES = {
    "pick_pack": ["manipulator", "mobile_manipulation"],
    "warehouse": ["transport_amr", "mobile_manipulation"],
    "logistics": ["transport_amr"],
    "hospitality": ["transport_amr", "mobile_manipulation"],
    "food_prep": ["manipulator"],
    "serve": ["transport_amr"],
    "disinfection": ["floor_scrub"],
    "clinical_delivery": ["transport_amr", "mobile_manipulation"],
    "pallet": ["manipulator"],
    "factory": ["manipulator"],
    "agriculture": [],
    "construction": [],
    "mining": [],
}


def live_corpus_enabled() -> bool:
    return os.getenv("ROBOT_JOB_LIVE_CORPUS", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def clear_live_job_cache() -> None:
    _CACHE["at"] = 0.0
    _CACHE["rows"] = ()


def tape_family_for_live_job(
    *,
    job_function: Optional[str],
    title: str = "",
    extra_text: str = "",
) -> Optional[str]:
    tape = tape_family_for_job_function(job_function)
    if tape:
        return tape
    tape = tape_family_for_job_function(job_function_from_title(title))
    if tape:
        return tape
    blob = f"{title} {extra_text}".strip()
    if len(blob) < 12:
        return None
    try:
        from app.services.robot_ontology import find_class_from_work_language

        cls = find_class_from_work_language(blob)
    except Exception:
        return None
    if not cls:
        return None
    return {
        "healthcare": "clinical_delivery",
        "hospitality": "hospitality",
        "agriculture": "agriculture",
        "construction": "construction",
        "mining": "mining",
        "warehouse": "warehouse",
        "logistics": "logistics",
        "factory": "factory",
        "food_prep": "food_prep",
    }.get(cls)


def corpus_row_from_robot_job(row: Any) -> Optional[dict[str, Any]]:
    employer = str(getattr(row, "company_name", "") or "").strip()
    locality = str(getattr(row, "locality", "") or "").strip()
    title = str(getattr(row, "robot_compatible_task", "") or "").strip()
    req = getattr(row, "requirements", None) or {}
    if not isinstance(req, dict):
        req = {}
    function = str(req.get("job_function") or getattr(row, "action", "") or "").strip()
    from app.services.robot_requirement_match import is_named_robot_job

    if not is_named_robot_job(employer, locality):
        return None
    if not is_job_employer_name(employer, title=title):
        return None
    tape = tape_family_for_live_job(
        job_function=function,
        title=title,
        extra_text=f"{employer} {locality}",
    )
    if not tape:
        return None
    key = str(getattr(row, "job_key", "") or "").strip()
    if not key:
        return None
    email = str(getattr(row, "employer_email", "") or "").strip() or None
    if not email:
        raw_email = req.get("employer_email")
        email = str(raw_email).strip() if isinstance(raw_email, str) else None
    contact_url = str(getattr(row, "contact_url", "") or "").strip() or None
    if not contact_url:
        raw_c = req.get("contact_url")
        contact_url = str(raw_c).strip() if isinstance(raw_c, str) else None
    apply_url = str(getattr(row, "apply_url", "") or "").strip() or None
    if not apply_url:
        raw_a = req.get("apply_url")
        apply_url = str(raw_a).strip() if isinstance(raw_a, str) else None
    mapped = {
        "job_key": f"live_{key}",
        "title": title or function or "Operational work",
        "industry": TAPE_INDUSTRY.get(tape, "Operations"),
        "path": (function or tape).replace("_", " "),
        "company_name": employer,
        "locality": locality,
        "families": list(TAPE_FAMILIES.get(tape) or []),
        "actions": [function] if function and function not in {"work", "unknown"} else [],
        "text": f"{title} {function} {employer} {locality} {tape}",
        "source": "live_scrape",
        "tape_family": tape,
        "unknowns": list(req.get("unknowns") or getattr(row, "unknowns", None) or []),
        "employer_email": email,
        "contact_url": contact_url,
        "apply_url": apply_url,
    }
    return mapped


def _fetch_live_named_jobs(limit: int = LIVE_CAP) -> tuple[dict[str, Any], ...]:
    from app.database import SessionLocal
    from app.models.robot_directed_discovery import RobotJob

    db = SessionLocal()
    try:
        q = (
            db.query(RobotJob)
            .filter(RobotJob.company_name.isnot(None))
            .filter(RobotJob.locality.isnot(None))
            .order_by(RobotJob.created_at.desc())
            .limit(max(limit * 4, 80))
        )
        out: list[dict[str, Any]] = []
        seen: set[str] = set()
        for row in q:
            mapped = corpus_row_from_robot_job(row)
            if not mapped:
                continue
            key = mapped["job_key"]
            if key in seen:
                continue
            seen.add(key)
            out.append(mapped)
            if len(out) >= limit:
                break
        return tuple(out)
    finally:
        db.close()


def load_live_named_jobs(limit: int = LIVE_CAP) -> tuple[dict[str, Any], ...]:
    """Recent named Robot Jobs mapped to FIND corpus shape. Empty on any failure."""
    if not live_corpus_enabled():
        return ()
    now = time.time()
    cached = _CACHE.get("rows") or ()
    if cached and now - float(_CACHE.get("at") or 0) < LIVE_TTL_SEC:
        return cached
    try:
        rows = _fetch_live_named_jobs(limit=limit)
    except Exception:
        logger.debug("live robot_jobs overlay skipped", exc_info=True)
        rows = ()
    _CACHE["at"] = now
    _CACHE["rows"] = rows
    return rows


def merge_live_jobs(bundled: tuple[dict[str, Any], ...] | list[dict[str, Any]]) -> tuple[dict[str, Any], ...]:
    seen = {(row.get("job_key") or "") for row in bundled}
    extra = [
        row
        for row in load_live_named_jobs()
        if row.get("job_key") and row["job_key"] not in seen
    ]
    if not extra:
        return tuple(bundled)
    return tuple(list(bundled) + extra)
