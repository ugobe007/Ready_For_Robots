"""Sprint 0 — frozen ontology & enum contracts."""
from __future__ import annotations

from app.domain.enums import (
    assert_call_priority,
    assert_loss_reason,
    assert_truth_state,
    call_priorities,
    load_primitives_ontology,
    loss_reason_codes,
    opportunity_states,
    prediction_wrong_code,
    truth_states,
)


def test_truth_states_frozen():
    assert "observed" in truth_states()
    assert "unknown" in truth_states()
    assert "OBSERVED".lower() not in {"OBSERVED"}  # API is lowercase set
    assert assert_truth_state("OEM_VERIFIED") == "oem_verified"


def test_opportunity_states_exclude_expanding():
    assert "deployed" in opportunity_states()
    assert "expanding" not in opportunity_states()


def test_call_priorities_include_do_not_surface():
    assert "do_not_surface" in call_priorities()
    assert assert_call_priority("CALL_NOW") == "call_now"


def test_loss_ontology_requires_prediction_wrong():
    assert prediction_wrong_code() in loss_reason_codes()
    assert assert_loss_reason("RFR_PREDICTION_WRONG") == "rfr_prediction_wrong"


def test_primitives_ids_stable_and_categorized():
    data = load_primitives_ontology()
    codes = [p["code"] for p in data["primitives"]]
    assert len(codes) == len(set(codes))
    assert "eng.acquire_pallet_floor" in codes
    assert "mob.trailer_entry" in codes
    cats = {p["category"] for p in data["primitives"]}
    assert "MOBILITY" in cats
    assert "EXCEPTION_HANDLING" in cats
