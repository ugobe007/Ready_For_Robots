"""
Observe-only Understanding v1.0 shadow persistence + review metrics.

Never mutates user-facing Robot Profile or job-match results.
Shadow write failures must not fail the product request (fail-open).
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import func, inspect
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.understanding_shadow import (
    SHADOW_FAILURE_THEMES,
    SHADOW_REVIEW_LABELS,
    UnderstandingShadowObservation,
)
from app.services.robot_understanding_v1.models import RobotProfile

logger = logging.getLogger(__name__)

REVIEW_LABELS = SHADOW_REVIEW_LABELS
FAILURE_THEMES = SHADOW_FAILURE_THEMES


def validate_review_label(label: str) -> str:
    normalized = (label or "").strip().upper()
    if normalized not in REVIEW_LABELS:
        raise ValueError(
            f"Invalid review_label {label!r}; expected one of {', '.join(REVIEW_LABELS)}"
        )
    return normalized


def validate_failure_themes(themes: list[str] | None) -> list[str]:
    if not themes:
        return []
    allowed = set(FAILURE_THEMES)
    out: list[str] = []
    for raw in themes:
        t = (raw or "").strip().lower()
        if not t:
            continue
        if t not in allowed:
            raise ValueError(
                f"Invalid failure_theme {raw!r}; expected one of {', '.join(FAILURE_THEMES)}"
            )
        if t not in out:
            out.append(t)
    return out


def _table_ready(db: Session) -> bool:
    try:
        return inspect(db.bind).has_table(UnderstandingShadowObservation.__tablename__)
    except SQLAlchemyError:
        return False


def _compact_source(s: dict[str, Any]) -> dict[str, Any]:
    return {
        "url": s.get("url"),
        "source_type": s.get("source_type"),
        "title": s.get("title"),
        "publisher_role": s.get("publisher_role"),
        "confidence": s.get("confidence"),
    }


def _compact_fact(f: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": f.get("id"),
        "predicate": f.get("predicate"),
        "value": f.get("value"),
        "units": f.get("units"),
        "epistemic": f.get("epistemic"),
        "confidence": f.get("confidence"),
        "evidence_span": f.get("evidence_span"),
        "source_id": f.get("source_id"),
    }


def observation_payload_from_profile(
    profile: RobotProfile,
    *,
    research_duration_ms: int | None = None,
    correlation_id: str | None = None,
) -> dict[str, Any]:
    """Project RobotProfile into shadow columns (additive snapshot; no mutation)."""
    data = profile.to_dict()
    facts = list(data.get("facts") or [])
    grounded = [
        _compact_fact(f)
        for f in facts
        if f.get("epistemic") not in ("unknown", None) and f.get("epistemic") != "contradicted"
    ]
    unknowns = [_compact_fact(f) for f in facts if f.get("epistemic") == "unknown"]
    contradictions = [_compact_fact(f) for f in facts if f.get("epistemic") == "contradicted"]
    company = data.get("company") or {}
    selected = data.get("selected_product")
    products = data.get("products") or []
    return {
        "correlation_id": (correlation_id or "")[:64] or None,
        "submitted_url": data.get("submitted_url") or profile.submitted_url,
        "research_duration_ms": research_duration_ms,
        "company_name": company.get("name"),
        "company_domain": company.get("primary_domain"),
        "selected_product": (selected or {}).get("name") if isinstance(selected, dict) else None,
        "products_found": [
            {"name": p.get("name"), "generation": p.get("generation"), "display_class": p.get("display_class")}
            for p in products
            if isinstance(p, dict)
        ],
        "profile_tier": data.get("profile_confidence"),
        "coverage_rate": data.get("coverage_rate"),
        "coverage_level": data.get("coverage_level"),
        "source_quality_rate": data.get("source_quality_rate"),
        "source_quality_level": data.get("source_quality_level"),
        "source_grounding_rate": data.get("source_grounding_rate"),
        "research_morphology": data.get("research_morphology"),
        "source_pack": [_compact_source(s) for s in (data.get("sources") or []) if isinstance(s, dict)],
        "grounded_facts": grounded,
        "unknowns": unknowns,
        "contradictions": contradictions,
        "notes": list(data.get("notes") or []),
        "research_stages": list(data.get("research_stages") or []),
        "profile_snapshot": data,
    }


def record_shadow_observation(
    db: Session,
    profile: RobotProfile,
    *,
    research_duration_ms: int | None = None,
    correlation_id: str | None = None,
) -> Optional[str]:
    """
    Persist one shadow observation. Fail-open: returns None on any error;
    never raises into the product path.
    """
    if not _table_ready(db):
        return None
    try:
        payload = observation_payload_from_profile(
            profile,
            research_duration_ms=research_duration_ms,
            correlation_id=correlation_id,
        )
        row_id = str(uuid.uuid4())
        db.add(
            UnderstandingShadowObservation(
                id=row_id,
                **payload,
            )
        )
        db.commit()
        return row_id
    except Exception:
        logger.exception("understanding_shadow_write_failed")
        try:
            db.rollback()
        except Exception:
            pass
        return None


def list_shadow_observations(
    db: Session,
    *,
    limit: int = 50,
    offset: int = 0,
    review_label: str | None = None,
    unreviewed_only: bool = False,
) -> list[UnderstandingShadowObservation]:
    if not _table_ready(db):
        return []
    q = db.query(UnderstandingShadowObservation).order_by(
        UnderstandingShadowObservation.submitted_at.desc()
    )
    if review_label:
        q = q.filter(UnderstandingShadowObservation.review_label == validate_review_label(review_label))
    if unreviewed_only:
        q = q.filter(UnderstandingShadowObservation.review_label.is_(None))
    return q.offset(max(0, offset)).limit(min(max(limit, 1), 200)).all()


def get_shadow_observation(db: Session, observation_id: str) -> Optional[UnderstandingShadowObservation]:
    if not _table_ready(db):
        return None
    return (
        db.query(UnderstandingShadowObservation)
        .filter(UnderstandingShadowObservation.id == observation_id)
        .first()
    )


def set_shadow_review(
    db: Session,
    observation_id: str,
    *,
    review_label: str,
    review_notes: str | None = None,
    failure_themes: list[str] | None = None,
    reviewed_by: str | None = None,
) -> UnderstandingShadowObservation:
    label = validate_review_label(review_label)
    themes = validate_failure_themes(failure_themes)
    row = get_shadow_observation(db, observation_id)
    if row is None:
        raise KeyError(observation_id)
    row.review_label = label
    row.review_notes = (review_notes or "").strip() or None
    row.failure_themes = themes
    row.reviewed_at = datetime.now(timezone.utc)
    row.reviewed_by = (reviewed_by or "")[:120] or None
    db.commit()
    db.refresh(row)
    return row


def observation_to_summary(row: UnderstandingShadowObservation) -> dict[str, Any]:
    return {
        "id": row.id,
        "correlation_id": row.correlation_id,
        "submitted_url": row.submitted_url,
        "submitted_at": row.submitted_at.isoformat() if row.submitted_at else None,
        "research_duration_ms": row.research_duration_ms,
        "company_name": row.company_name,
        "company_domain": row.company_domain,
        "selected_product": row.selected_product,
        "products_found": row.products_found or [],
        "profile_tier": row.profile_tier,
        "coverage_rate": row.coverage_rate,
        "coverage_level": row.coverage_level,
        "source_quality_rate": row.source_quality_rate,
        "source_quality_level": row.source_quality_level,
        "source_grounding_rate": row.source_grounding_rate,
        "research_morphology": row.research_morphology,
        "source_pack": row.source_pack or [],
        "grounded_facts": row.grounded_facts or [],
        "unknowns": row.unknowns or [],
        "contradictions": row.contradictions or [],
        "notes": row.notes or [],
        "research_stages": row.research_stages or [],
        "review_label": row.review_label,
        "review_notes": row.review_notes,
        "failure_themes": row.failure_themes or [],
        "reviewed_at": row.reviewed_at.isoformat() if row.reviewed_at else None,
        "reviewed_by": row.reviewed_by,
    }


def compute_trust_metrics(db: Session) -> dict[str, Any]:
    """
    Primary metric: % of *reviewed* real submissions we'd be comfortable showing
    a robotics professional. Comfortable ≡ GOOD.

    Also reports GOOD / (GOOD+INCOMPLETE+WRONG+UNVERIFIABLE) and INCOMPLETE share.
    """
    empty = {
        "reviewed_total": 0,
        "label_counts": {k: 0 for k in REVIEW_LABELS},
        "comfortable_pct": None,
        "good_over_all_reviewed_pct": None,
        "incomplete_pct_of_reviewed": None,
        "failure_theme_counts": {},
        "unreviewed_total": 0,
        "primary_metric": (
            "comfortable_pct = GOOD / reviewed_total "
            "(reviewed = GOOD+INCOMPLETE+WRONG+UNVERIFIABLE)"
        ),
    }
    if not _table_ready(db):
        return empty

    rows = (
        db.query(
            UnderstandingShadowObservation.review_label,
            func.count(UnderstandingShadowObservation.id),
        )
        .filter(UnderstandingShadowObservation.review_label.isnot(None))
        .group_by(UnderstandingShadowObservation.review_label)
        .all()
    )
    counts = {k: 0 for k in REVIEW_LABELS}
    for label, n in rows:
        if label in counts:
            counts[label] = int(n)
    reviewed = sum(counts.values())
    good = counts["GOOD"]
    incomplete = counts["INCOMPLETE"]

    unreviewed = (
        db.query(func.count(UnderstandingShadowObservation.id))
        .filter(UnderstandingShadowObservation.review_label.is_(None))
        .scalar()
        or 0
    )

    theme_counts: dict[str, int] = {}
    theme_rows = (
        db.query(UnderstandingShadowObservation.failure_themes)
        .filter(UnderstandingShadowObservation.review_label.isnot(None))
        .all()
    )
    for (themes,) in theme_rows:
        for t in themes or []:
            if isinstance(t, str) and t:
                theme_counts[t] = theme_counts.get(t, 0) + 1

    def _pct(num: int, den: int) -> float | None:
        if den <= 0:
            return None
        return round(100.0 * num / den, 2)

    return {
        "reviewed_total": reviewed,
        "label_counts": counts,
        "comfortable_pct": _pct(good, reviewed),
        "good_over_all_reviewed_pct": _pct(good, reviewed),
        "incomplete_pct_of_reviewed": _pct(incomplete, reviewed),
        "failure_theme_counts": theme_counts,
        "unreviewed_total": int(unreviewed),
        "primary_metric": (
            "comfortable_pct = GOOD / reviewed_total "
            "(reviewed = GOOD+INCOMPLETE+WRONG+UNVERIFIABLE); "
            "INCOMPLETE tracked separately via incomplete_pct_of_reviewed"
        ),
    }
