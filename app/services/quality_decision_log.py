"""
Quality decision records for offline ML and audit exports.

Combines the same signals used at ingest time:
  lead_filter.is_junk → text_classifier.classify → company_validator.is_valid_lead
  (logic engine with and without classifier hint).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from app.services.company_validator import is_valid_lead
from app.services.lead_filter import is_junk
from app.services.text_classifier import classify


# Stable schema for JSONL consumers (notebooks, training jobs, dashboards).
DECISION_RECORD_KEYS: tuple[str, ...] = (
    "export_ts",
    "id",
    "name",
    "source",
    "created_at",
    "is_junk",
    "junk_reason",
    "classifier_entity_type",
    "classifier_confidence",
    "classifier_is_valid_company",
    "classifier_evidence",
    "is_valid_lead_no_hint",
    "valid_lead_reason_no_hint",
    "is_valid_lead_with_classifier_hint",
    "valid_lead_reason_with_hint",
)


def export_timestamp_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_decision_record(
    *,
    company_id: int,
    name: str,
    source: Optional[str],
    created_at: Optional[datetime],
    export_ts: str,
) -> dict[str, Any]:
    """
    Build one JSON-serializable row from company fields (no ORM required).

    ``name`` should match persisted ``companies.name`` (strip before calling).
    """
    name = (name or "").strip()
    j_bad, j_reason = is_junk(name)
    tc = classify(name)
    ok_lead, lead_reason = is_valid_lead(name)
    ok_hint, hint_reason = is_valid_lead(name, entity_hint=tc)
    created_iso = created_at.isoformat() if created_at else None
    return {
        "export_ts": export_ts,
        "id": company_id,
        "name": name,
        "source": source,
        "created_at": created_iso,
        "is_junk": j_bad,
        "junk_reason": j_reason or None,
        "classifier_entity_type": tc.entity_type.value,
        "classifier_confidence": tc.confidence,
        "classifier_is_valid_company": tc.is_valid_company,
        "classifier_evidence": tc.evidence[:8],
        "is_valid_lead_no_hint": ok_lead,
        "valid_lead_reason_no_hint": lead_reason or None,
        "is_valid_lead_with_classifier_hint": ok_hint,
        "valid_lead_reason_with_hint": hint_reason or None,
    }


def assert_decision_record_schema(rec: dict[str, Any]) -> None:
    """Raise AssertionError if a record is missing keys or has wrong evidence shape."""
    missing = [k for k in DECISION_RECORD_KEYS if k not in rec]
    if missing:
        raise AssertionError(f"missing keys: {missing}")
    ev = rec["classifier_evidence"]
    if not isinstance(ev, list) or len(ev) > 8:
        raise AssertionError(f"classifier_evidence must be list, len<=8, got {ev!r}")
