"""Tests for ML-facing quality decision records (junk + classifier + logic engine)."""
import json
from datetime import datetime, timezone

import pytest

from app.services.quality_decision_log import (
    DECISION_RECORD_KEYS,
    assert_decision_record_schema,
    build_decision_record,
    export_timestamp_iso,
)


def _rec(name: str, **kwargs):
    return build_decision_record(
        company_id=kwargs.get("company_id", 1),
        name=name,
        source=kwargs.get("source", "news_discovery"),
        created_at=kwargs.get("created_at"),
        export_ts=kwargs.get("export_ts", "2026-01-01T00:00:00+00:00"),
    )


def test_export_timestamp_iso_is_zulu_utc_format():
    ts = export_timestamp_iso()
    assert ts.endswith("+00:00") or ts.endswith("Z")


def test_decision_record_schema_complete():
    rec = _rec("Acme Robotics Inc", company_id=42)
    assert_decision_record_schema(rec)
    assert set(rec.keys()) == set(DECISION_RECORD_KEYS)


def test_decision_record_json_roundtrip():
    rec = _rec("TestCo LLC", company_id=99)
    blob = json.dumps(rec)
    back = json.loads(blob)
    assert back["name"] == "TestCo LLC"
    assert back["is_junk"] is False
    assert isinstance(back["classifier_evidence"], list)


@pytest.mark.parametrize(
    "name,expect_junk",
    [
        ("Meritor", False),
        ("Twin Cities Automation Inc", False),
        ("Unlock the ROI", True),
        ("Supply Chain", True),
    ],
)
def test_junk_filter_alignment(name, expect_junk):
    rec = _rec(name)
    assert rec["is_junk"] is expect_junk
    if expect_junk:
        assert rec["junk_reason"]
        assert rec["is_valid_lead_no_hint"] is False
        assert rec["valid_lead_reason_no_hint"]


def test_logic_engine_rejects_junk_even_when_classifier_wrong():
    """If name is junk, logic engine must not accept regardless of classifier."""
    rec = _rec("Unlock the ROI")
    assert rec["is_junk"] is True
    assert rec["is_valid_lead_no_hint"] is False
    assert rec["is_valid_lead_with_classifier_hint"] is False


def test_created_at_iso_optional():
    rec = _rec("Foo", created_at=None)
    assert rec["created_at"] is None
    dt = datetime(2026, 4, 1, 12, 0, 0, tzinfo=timezone.utc)
    rec2 = _rec("Foo", created_at=dt)
    assert rec2["created_at"] == "2026-04-01T12:00:00+00:00"


def test_classifier_evidence_capped():
    rec = _rec("Some Longish Company Name With Many Tokens")
    assert len(rec["classifier_evidence"]) <= 8


def test_assert_decision_record_schema_rejects_bad_evidence():
    bad = {k: None for k in DECISION_RECORD_KEYS}
    bad["classifier_evidence"] = ["x"] * 9
    with pytest.raises(AssertionError, match="classifier_evidence"):
        assert_decision_record_schema(bad)
