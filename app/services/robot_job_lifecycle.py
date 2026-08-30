"""Close or keep a Robot Job from *new public evidence* — never from invention.

Statuses (employment, not CRM):
  open              posting still describes human work
  filled_by_robot   evidence a robot now performs this work at this employer
  withdrawn         posting gone / expired without robot evidence
  incumbent_robot   workplace already automated (same close-out for discovery)
  unknown           text does not decide
"""
from __future__ import annotations

import re
from typing import Any, Optional

WITHDRAWN_RE = re.compile(
    r"(no longer accepting|job has expired|this position has been filled|"
    r"posting (is )?closed|no longer available)",
    re.I,
)

ROBOT_DOING_WORK_RE = re.compile(
    r"("
    r"(deployed|deploys|deploying|went live|now (live|operating)|installed)\s+"
    r".{0,80}(amr|autonomous mobile robot|humanoid|cobot|collaborative robot|"
    r"delivery robot|scrubber robot|palletiz(?:er|ing) robot|digit|stretch|tug)"
    r"|"
    r"robots?\s+(are |is |now )?(picking|pack(?:ing)?|scrubbing|delivering|"
    r"transporting|hauling totes|moving pallets|making (beds|rooms))"
    r"|"
    r"replaced\s+.{0,60}(associates|pickers|housekeepers|evs)\s+with\s+robots?"
    r")",
    re.I,
)


def _norm(value: Optional[str]) -> str:
    return re.sub(r"\s+", " ", (value or "").lower()).strip()


def employer_mentioned(employer: str, text: str) -> bool:
    name = _norm(employer)
    blob = _norm(text)
    if len(name) < 3 or not blob:
        return False
    if name in blob:
        return True
    token = name.split()[0]
    return len(token) >= 4 and token in blob


def work_family_mentioned(job_function: Optional[str], job_title: Optional[str], text: str) -> bool:
    blob = _norm(text)
    needles = [n for n in (_norm(job_function), _norm(job_title)) if n]
    extras = {
        "picking": ("pick", "tote", "order select"),
        "packing": ("pack", "pack-out"),
        "material_handling": ("warehouse", "material handl", "fulfillment", "amr"),
        "housekeeping": ("housekeep", "room attendant", "guest room"),
        "environmental_services": ("evs", "floor scrub", "corridor"),
        "patient_transport": ("patient transport", "pharmacy delivery"),
    }
    family = _norm(job_function)
    needles.extend(extras.get(family, ()))
    return any(n and n in blob for n in needles)


def status_from_evidence(
    *,
    employer: str,
    job_title: str = "",
    job_function: Optional[str] = None,
    evidence_text: str,
) -> dict[str, Any]:
    """Classify one evidence blob against one existing Robot Job."""
    blob = evidence_text or ""
    if WITHDRAWN_RE.search(blob) and not ROBOT_DOING_WORK_RE.search(blob):
        m = WITHDRAWN_RE.search(blob)
        return {
            "status": "withdrawn",
            "reason": "posting_closed",
            "excerpt": m.group(0) if m else None,
        }
    robot_hit = ROBOT_DOING_WORK_RE.search(blob)
    if robot_hit and employer_mentioned(employer, blob) and work_family_mentioned(
        job_function, job_title, blob
    ):
        return {
            "status": "filled_by_robot",
            "reason": "public_deployment_evidence",
            "excerpt": robot_hit.group(0).strip()[:240],
        }
    if robot_hit and employer_mentioned(employer, blob):
        return {
            "status": "incumbent_robot",
            "reason": "employer_has_robot_unclear_task",
            "excerpt": robot_hit.group(0).strip()[:240],
        }
    return {"status": "open", "reason": "no_closeout_evidence", "excerpt": None}


def status_from_posting_text(description: str) -> dict[str, Any]:
    """Fresh posting body — usually still open unless the board marked it dead."""
    blob = description or ""
    if WITHDRAWN_RE.search(blob):
        return status_from_evidence(
            employer="",
            evidence_text=blob,
        )
    return {"status": "open", "reason": "active_posting", "excerpt": None}


def should_close(status: str) -> bool:
    return status in {"filled_by_robot", "withdrawn", "incumbent_robot"}


def robot_job_key(employer: str, title: str, locality: str = "") -> str:
    import hashlib

    raw = f"{_norm(employer)}|{_norm(title)}|{_norm(locality)}"
    return hashlib.sha1(raw.encode()).hexdigest()[:24]


_CONTACT_COLUMNS_READY: Optional[bool] = None


def reset_contact_column_cache() -> None:
    global _CONTACT_COLUMNS_READY
    _CONTACT_COLUMNS_READY = None


def robot_jobs_contact_columns_ready(db) -> bool:
    """False until Fly runs ``alembic upgrade head`` (jcnt0a1b2c3d4)."""
    global _CONTACT_COLUMNS_READY
    if _CONTACT_COLUMNS_READY is not None:
        return _CONTACT_COLUMNS_READY
    try:
        from sqlalchemy import inspect as sa_inspect

        bind = db.get_bind()
        names = {c["name"] for c in sa_inspect(bind).get_columns("robot_jobs")}
        _CONTACT_COLUMNS_READY = "employer_email" in names
    except Exception:
        _CONTACT_COLUMNS_READY = False
    return _CONTACT_COLUMNS_READY


def _copy_contact_fields(req: dict[str, Any], extract: dict[str, Any]) -> dict[str, Any]:
    """Keep a found mailbox. Never invent. Never wipe an existing one with None."""
    for key in ("employer_email", "contact_url", "apply_url"):
        value = extract.get(key)
        if isinstance(value, str) and value.strip():
            req[key] = value.strip()[:1024] if key != "employer_email" else value.strip()[:320]
    return req


def upsert_robot_job_from_extract(
    db,
    *,
    company_id: Optional[int],
    extract: dict[str, Any],
    source_url: Optional[str] = None,
) -> Any:
    """Best-effort persist onto robot_jobs.requirements. No-op if the table is missing."""
    from app.models.robot_directed_discovery import JobEvidence, RobotJob

    employer = extract.get("employer") or ""
    title = extract.get("job_title") or ""
    if not employer or not title:
        return None
    key = robot_job_key(employer, title, extract.get("workplace") or "")
    row = db.query(RobotJob).filter(RobotJob.job_key == key).one_or_none()
    if row is None:
        row = RobotJob(
            job_key=key,
            company_name=employer[:240],
            action=(extract.get("job_function") or "work")[:120],
            robot_compatible_task=title[:2000],
        )
        db.add(row)
    row.company_id = int(company_id) if company_id is not None else row.company_id
    row.locality = (extract.get("workplace") or None)
    row.action = (extract.get("job_function") or row.action or "work")[:120]
    row.robot_compatible_task = title
    row.automation_state = extract.get("status") or row.automation_state or "open"
    req = dict(row.requirements or {})
    req["compensation"] = extract.get("compensation")
    req["performance_specs"] = extract.get("performance_specs")
    req["job_function"] = extract.get("job_function")
    req["unknowns"] = extract.get("unknowns") or []
    _copy_contact_fields(req, extract)
    row.requirements = req
    row.unknowns = list(extract.get("unknowns") or [])
    if robot_jobs_contact_columns_ready(db):
        email = req.get("employer_email")
        if email:
            row.employer_email = str(email)[:320]
        if req.get("contact_url"):
            row.contact_url = str(req["contact_url"])[:1024]
        if req.get("apply_url"):
            row.apply_url = str(req["apply_url"])[:1024]
    db.flush()
    if source_url and row.id:
        ev = JobEvidence(
            robot_job_id=row.id,
            evidence_grade="E2",
            source_url=source_url[:1024],
            source_title=title[:480],
            excerpt=format_excerpt(extract),
        )
        db.add(ev)
    return row


def format_excerpt(extract: dict[str, Any]) -> str:
    from app.services.robot_job_extract import format_robot_job_signal

    return format_robot_job_signal(extract)[:2000]


def apply_closeout_to_job(row: Any, evidence: dict[str, Any]) -> Any:
    if not row or not evidence:
        return row
    status = evidence.get("status")
    if should_close(status):
        row.automation_state = status
        extras = dict(row.provenance or {})
        extras["closeout"] = evidence
        row.provenance = extras
    return row
