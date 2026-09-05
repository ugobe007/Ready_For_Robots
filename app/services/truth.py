"""Provenance / truth utilities — never confuse inference with observation."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.enums import assert_truth_state
from app.models.robot_intelligence import EvidenceClaim
from app.models.source import Source


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def provenanced(
    value: Any,
    *,
    truth_state: str,
    confidence: float,
    evidence_refs: list[str] | None = None,
) -> dict[str, Any]:
    """UI/API envelope for a material field."""
    state = assert_truth_state(truth_state)
    if state == "unknown":
        return {
            "value": None if value is None else value,
            "truth_state": "unknown",
            "confidence": 0.0,
            "evidence_refs": evidence_refs or [],
        }
    conf = max(0.0, min(1.0, float(confidence)))
    return {
        "value": value,
        "truth_state": state,
        "confidence": conf,
        "evidence_refs": evidence_refs or [],
    }


def ensure_observed_has_excerpt(*, truth_state: str, excerpt: str | None) -> None:
    if assert_truth_state(truth_state) == "observed" and not (excerpt or "").strip():
        raise ValueError("observed claims require a non-empty source excerpt")


def upsert_source(
    db: Session,
    *,
    source_type: str,
    url: str | None = None,
    title: str | None = None,
    publisher: str | None = None,
    raw_text: str | None = None,
    content_hash: str | None = None,
    metadata: dict | None = None,
    captured_at: datetime | None = None,
) -> Source:
    """Create a Source row (append-oriented; dedupe by content_hash+url when present)."""
    import uuid as uuid_mod

    if content_hash and url:
        existing = (
            db.query(Source)
            .filter(Source.content_hash == content_hash, Source.url == url)
            .first()
        )
        if existing:
            return existing
    dialect = db.bind.dialect.name if db.bind else "postgresql"
    new_id = str(uuid_mod.uuid4()) if dialect == "sqlite" else uuid_mod.uuid4()
    source = Source(
        id=new_id,
        source_type=source_type,
        url=url,
        title=title,
        publisher=publisher,
        captured_at=captured_at or utcnow(),
        content_hash=content_hash,
        raw_text=raw_text,
        metadata_json=metadata or {},
    )
    db.add(source)
    db.flush()
    return source


def append_claim(
    db: Session,
    *,
    entity_type: str,
    entity_id: str,
    field_path: str,
    value: Any,
    truth_state: str,
    confidence: float,
    source_id: str | UUID | None = None,
    source_type: str | None = None,
    source_url: str | None = None,
    excerpt: str | None = None,
    observed_at: datetime | None = None,
    recorded_by_user_id=None,
    supersedes_claim_id=None,
) -> EvidenceClaim:
    import uuid as uuid_mod

    state = assert_truth_state(truth_state)
    ensure_observed_has_excerpt(truth_state=state, excerpt=excerpt)
    if state == "unknown":
        value = None
        confidence = 0.0
    dialect = db.bind.dialect.name if db.bind else "postgresql"
    new_id = str(uuid_mod.uuid4()) if dialect == "sqlite" else uuid_mod.uuid4()
    claim = EvidenceClaim(
        id=new_id,
        entity_type=entity_type,
        entity_id=str(entity_id),
        field_path=field_path,
        value=value,
        truth_state=state,
        source_type=source_type,
        source_url=source_url,
        source_id=str(source_id) if source_id else None,
        excerpt=excerpt,
        observed_at=observed_at or utcnow(),
        confidence=max(0.0, min(1.0, float(confidence))),
        supersedes_claim_id=supersedes_claim_id,
        recorded_by_user_id=recorded_by_user_id,
    )
    db.add(claim)
    db.flush()
    return claim
