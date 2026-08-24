"""Trained-task registry + Hardware / Intelligence Fit."""
from __future__ import annotations

from app.services.robot_intelligence_fit import (
    hardware_fit,
    intelligence_fit_for_job,
    job_work_profile,
)
from app.services.robot_ontology import trained_task_registry
from app.services.robot_requirement_match import match_job_spec
from app.services.robot_task_registry_catalog import build_registry


def test_registry_has_100_to_300_trained_tasks():
    catalog = build_registry()
    dumped = trained_task_registry()
    assert 100 <= catalog["task_count"] <= 300
    assert dumped.get("task_count") == catalog["task_count"]
    assert catalog["tasks"][0]["task_id"]
    assert catalog["tasks"][0]["task_family"]
    names = {m["name"] for m in catalog["models"]}
    assert "OpenVLA 7B" in names
    assert any("Octo" in n for n in names)
    assert any("π" in n or "pi" in n.lower() for n in names)


def test_mixed_case_depalletize_has_high_pick_place_and_low_mixed_coverage():
    profile = job_work_profile(
        title="Remove mixed cartons from a pallet and place each onto a conveyor",
        industry="warehouse",
        text="mixed SKU depalletizing onto conveyor",
        tape_family="pallet",
    )
    assert "mixed_case_depalletize" in profile["task_families"]
    fit = intelligence_fit_for_job(
        title="Remove mixed cartons from a pallet and place each onto a conveyor",
        industry="warehouse",
        text="mixed SKU depalletizing onto conveyor",
        tape_family="pallet",
        requirements=[
            {"necessity": "required", "state": "MATCHED"},
            {"necessity": "required", "state": "MATCHED"},
            {"necessity": "required", "state": "UNKNOWN"},
        ],
        robot_classes=["manipulator"],
    )
    by_fam = {row["task_family"]: row["coverage"] for row in fit["task_coverage"]}
    assert by_fam["pick_place"] == "HIGH"
    assert by_fam["mixed_case_depalletize"] == "LOW"
    kitchen = intelligence_fit_for_job(
        title="Pick the mug and place it on the plate",
        industry="restaurant kitchen",
        text="pick and place mug onto plate",
        tape_family="gripper",
        requirements=[{"necessity": "required", "state": "MATCHED"}],
        robot_classes=["manipulator"],
    )
    assert fit["intelligence_fit"] < kitchen["intelligence_fit"]
    assert "score" not in fit
    assert "OpenVLA" in " ".join(m["model_name"] or "" for m in fit["model_matches"])


def test_hardware_fit_drops_on_unmet_and_does_not_invent_presence():
    matched = hardware_fit(
        [
            {"necessity": "required", "state": "MATCHED"},
            {"necessity": "required", "state": "MATCHED"},
        ]
    )
    unmet = hardware_fit(
        [
            {"necessity": "required", "state": "MATCHED"},
            {"necessity": "required", "state": "UNMET"},
        ]
    )
    assert matched > unmet
    assert unmet <= 0.5


def test_match_payload_includes_fit_without_generic_score(tmp_path):
    import json
    from pathlib import Path

    fixtures = Path(__file__).resolve().parent / "fixtures" / "m2_profiles"
    profile = json.loads((fixtures / "vega.json").read_text(encoding="utf-8"))
    card = match_job_spec(profile, "manip_novolex_kinston_nc")
    payload = card.to_api_job()
    assert "score" not in payload
    assert payload.get("fit")
    assert payload["fit"]["hardware_fit"] > 0
    assert payload["fit"]["intelligence_fit"] > 0
    assert payload["fit"]["deployment_readiness"] == round(
        payload["fit"]["hardware_fit"]
        * payload["fit"]["intelligence_fit"]
        * payload["fit"]["environment_fit"],
        4,
    )
    assert all(m["presence"] == "unknown" for m in payload["required_task_models"])
