"""Humanoid pilot language tagging and ranking."""
import pytest

from app.services.humanoid_pilot_ranking import (
    assess_humanoid_pilot_language,
    humanoid_pilot_sort_key,
)


def _sig(text: str, signal_type: str = "news"):
    return {"raw_text": text, "signal_type": signal_type}


def test_active_pilot_assembly_line():
    ass = assess_humanoid_pilot_language(
        [
            _sig(
                "Automotive supplier pilots humanoid workforce deployment on assembly line "
                "to address skilled labor shortages",
                "robot_installation",
            )
        ],
        industry="Automotive & Manufacturing",
    )
    assert ass.tier == "ACTIVE_PILOT"
    assert ass.score >= 85
    assert "workcell" in ass.action.lower() or "pilot" in ass.action.lower()


def test_pilot_intent_rfp_language():
    ass = assess_humanoid_pilot_language(
        [_sig("Facility team evaluating humanoid robots for warehouse RFP next quarter")],
        industry="Logistics",
    )
    assert ass.tier == "PILOT_INTENT"
    assert ass.score >= 70


def test_oem_unveil_downgraded():
    ass = assess_humanoid_pilot_language(
        [_sig("Neura Robotics unveils NEURA 4NE1 humanoid robot platform at Hannover Messe")],
    )
    assert ass.tier == "HUMANOID_MENTION"
    assert "vendor" in ass.action.lower() or "oem" in ass.action.lower()


def test_no_humanoid_returns_none():
    ass = assess_humanoid_pilot_language([_sig("Warehouse adds AMR fleet for outbound flow")])
    assert ass.tier == "NONE"
    assert ass.score == 0


def test_humanoid_pilot_sort_key_ranks_active_first():
    active = {"humanoid_pilot_tier": "ACTIVE_PILOT", "humanoid_pilot_score": 90, "priority_score": 60}
    warm = {"humanoid_pilot_tier": "NONE", "priority_score": 95}
    ranked = sorted([warm, active], key=humanoid_pilot_sort_key)
    assert ranked[0]["humanoid_pilot_tier"] == "ACTIVE_PILOT"


def test_as_dict_omits_none_tier():
    ass = assess_humanoid_pilot_language([_sig("No robots here")])
    payload = ass.as_dict()
    assert payload["humanoid_pilot_tier"] is None
    assert payload["humanoid_pilot_score"] is None
