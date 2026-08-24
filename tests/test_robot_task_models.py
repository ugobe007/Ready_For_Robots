"""Task models required by a Robot Job — slots and lookups, not fake presence."""
from __future__ import annotations

import json

from app.services.robot_task_models import (
    required_task_models_for_job,
    task_model_open_questions,
)
from app.services import robot_ontology as ont
from app.services.robot_requirement_match import match_job_spec


def _ids(models: list[dict]) -> set[str]:
    return {m["id"] for m in models}


def test_ontology_loads_task_model_slots():
    data = ont.task_model_ontology()
    slots = data.get("slots") or data.get("slots") or []
    assert slots
    assert data.get("ui_term") == "task model"
    assert data.get("internal_nickname") == "certificate"
    dumped = json.dumps(slots).lower()
    assert "certificate" not in dumped
    assert data.get("shared_lookups")
    assert data.get("qualify_filters")
    assert data.get("pricing_lookups")
    blob = json.dumps(data).lower()
    # Chat LLMs may be named as a counterexample, never as the job policy.
    assert "not warehouse pick" in blob or "not a chat llm" in blob or "not warehouse" in blob


def test_warehouse_palletize_needs_pick_policy_unknown():
    models = required_task_models_for_job(
        tape_family="pallet",
        industry="Kinston, NC",
        title="Pick packed cases from conveyor and stack onto pallets",
        path="PALLETIZING",
        text="unload cases from conveyors and stack onto pallets",
    )
    assert "warehouse_pick_place_policy" in _ids(models)
    assert all(m["presence"] == "unknown" for m in models)
    assert all(m["where_to_look"] for m in models)
    questions = task_model_open_questions(models)
    assert any("pick-and-place" in q.lower() or "pick-and-place" in q.lower() for q in questions)
    names = {d["name"] for m in models for d in m["where_to_look"]}
    assert any("Hugging Face" in n for n in names)
    assert any("Argo-Robot" in n or "OpenVLA" in n for n in names)
    assert any("Robotic Data" in n for n in names)
    assert any("World Labs" in n for n in names)
    assert any("Mercor" in n for n in names)
    kinds = {d.get("kind") for m in models for d in m["where_to_look"]}
    assert "training_data" in kinds
    assert "sim_to_real" in kinds
    assert "talent" in kinds
    assert models[0]["qualify_filters"]
    assert any(f["id"] == "commercial_license" for f in models[0]["qualify_filters"])
    assert any(f["id"] == "compute_footprint" for f in models[0]["qualify_filters"])
    price_names = {d["name"] for d in models[0]["pricing_lookups"]}
    assert any("BenchLM" in n for n in price_names)
    assert any("Axe Compute" in n for n in price_names)
    assert "OpenVLA" in models[0]["candidate_families"]
    assert any("chat LLM" in q.lower() or "vla" in q.lower() for q in questions)
    assert any("license" in q.lower() for q in questions)
    assert any("cost" in q.lower() or "price" in q.lower() or "token" in q.lower() for q in questions)


def test_warehouse_tote_move_is_amr_nav_not_hospital():
    models = required_task_models_for_job(
        tape_family="transport",
        industry="specialty pharma dc",
        title="Return empty totes and carts to pack stations",
        path="pack→return",
        text="warehouse associates restock pack stations and return totes",
    )
    ids = _ids(models)
    assert "warehouse_amr_fleet_nav" in ids
    assert "hospital_logistics_transport" not in ids
    assert all(m["presence"] == "unknown" for m in models)


def test_hospital_linen_run_is_clinical_not_warehouse_pick():
    models = required_task_models_for_job(
        tape_family="transport",
        industry="hospital",
        title="Move soiled linens from nursing units to laundry",
        path="unit→laundry",
        text="clinical corridors patient rooms linen carts",
    )
    ids = _ids(models)
    assert "hospital_logistics_transport" in ids
    assert "warehouse_pick_place_policy" not in ids
    assert all(m["presence"] == "unknown" for m in models)


def test_cnc_tending_needs_machine_tending_policy():
    models = required_task_models_for_job(
        tape_family="gripper",
        industry="precision machining",
        title="Tend CNC mills/lathes — workpiece load/unload around cycle",
        path="machine-tend",
        text="load workpieces into CNC fixtures",
    )
    assert "machine_tending_load_unload" in _ids(models)


def test_opaque_job_still_asks_for_a_site_task_policy():
    models = required_task_models_for_job(
        tape_family="unknown",
        title="Unspecified facility work",
    )
    assert _ids(models) == {"site_task_policy"}
    assert models[0]["presence"] == "unknown"


def test_novolex_match_card_exposes_unknown_task_models():
    from pathlib import Path

    fixtures = Path(__file__).resolve().parent / "fixtures" / "m2_profiles"
    if not (fixtures / "vega.json").exists():
        return
    import json as _json

    profile = _json.loads((fixtures / "vega.json").read_text(encoding="utf-8"))
    card = match_job_spec(profile, "manip_novolex_kinston_nc")
    payload = card.to_api_job()
    assert payload.get("required_task_models")
    assert all(m["presence"] == "unknown" for m in payload["required_task_models"])
    blob = _json.dumps(payload).lower()
    assert "certificate" not in blob
    assert any("task model" in u.lower() or "policy" in u.lower() for u in card.still_unknown)
