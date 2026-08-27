"""The machine-readable ontology must stay in sync with the live pipeline.

This is what makes the ontology *usable* (loaded by app/services/robot_ontology.py)
and *updated* (drift between ontology JSON and code fails here). It loads the
JSON ontologies and asserts they match the actual derive capabilities, matcher
families/distinctive sets, and fact predicates.
"""
from __future__ import annotations

import json
from pathlib import Path

from app.services import robot_ontology as ont
from app.services.robot_capability_derive import derive_capabilities
from app.services import robot_requirement_match as matcher

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "app" / "data" / "robot_job_match_corpus.json"


def _all_capabilities_profile() -> dict:
    """A synthetic robot whose facts trigger every derived capability."""
    def f(pred, val, units=None):
        return {"predicate": pred, "value": val, "units": units, "epistemic": "explicit",
                "confidence": 0.9, "evidence_span": pred, "source_id": "s0"}
    return {
        "selected_product": {"name": "Everything", "display_class": "mobile_manipulator"},
        "company": {"name": "Everything Robotics"},
        "facts": [
            f("product_class", "quadruped"),          # inspect_route
            f("arm_count", 2),                          # manipulate + dual_arm
            f("has_dexterous_hands", True),
            f("has_mobile_base", True),                 # mobile
            f("autonomous_navigation", True),
            f("claims_item_delivery", True),            # transport
            f("supports_tote_handling", True),          # tote_transport
            f("claims_food_prep", True),                # food_prep
            f("claims_beverage_prep", True),            # beverage_prep
            f("claims_surface_cleaning", True),         # surface_clean
            f("claims_shelf_scan", True),               # shelf_scan
            f("claims_pallet_handling", True),          # pallet_move
            f("claims_trailer_unload", True),           # trailer_unload
            f("claims_piece_pick", True),               # pick_pack
            f("claims_sortation", True),                # sortation
            f("claims_disinfection", True),             # disinfect
            f("claims_goods_to_person", True),          # goods_to_person
            f("claims_agriculture", True),              # agriculture_task
            f("claims_construction", True),             # construction_task
            f("claims_mining", True),                   # mining_task
            f("claims_marine", True),                   # marine_task
            f("claims_avionics", True),                 # avionics_task
            f("supports_hard_floor_scrubbing", True),   # hard_floor_scrub
            f("reach_or_workspace", 2.0, "m"),          # reach
            f("carrying_capacity", 50, "kg"),           # payload
            f("claims_load_unload", True),              # load_unload
        ],
    }


def test_ontology_files_load():
    assert ont.capability_ontology().get("capabilities")
    assert ont.workflow_ontology().get("families")
    assert ont.hardware_ontology().get("predicates")
    assert ont.inference_rules().get("rules")
    task_models = ont.task_model_ontology()
    assert task_models.get("slots") or task_models.get("slots")
    assert ont.ONTOLOGY_VERSION == "1.0.0"


def test_confidence_states_match_code():
    # The confidence vocabulary must map onto the code epistemic states.
    code_states = {"explicit", "strongly_inferred", "likely", "unknown", "contradicted"}
    cmap = ont.capability_ontology()["confidence_code_map"]
    assert set(cmap) == set(ont.confidence_states())
    assert set(cmap.values()) == code_states


def test_capability_keys_match_derive():
    present = {k for k, c in derive_capabilities(_all_capabilities_profile()).items()
               if c.present and k != "classes"}
    assert present == set(ont.capability_keys()), (
        "capability_ontology.v1.json is out of sync with derive_capabilities()"
    )


def test_distinctive_and_generic_match_matcher():
    assert set(matcher.DISTINCTIVE_CAPABILITIES) == set(ont.distinctive_capabilities())
    assert set(matcher.GENERIC_CAPABILITIES) == set(ont.generic_capabilities())


def test_workflow_families_match_corpus_and_matcher():
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    corpus_families = {j.get("tape_family") for j in corpus["jobs"] if j.get("tape_family")}
    assert set(ont.workflow_families()) == corpus_families, (
        "workflow_ontology.v1.json families must equal the corpus tape_families"
    )
    # Each family's required capabilities must be real capability keys, and the
    # matcher must exercise that capability for the family.
    for fam in ont.workflow_families():
        reqs = ont.workflow_required_capabilities(fam)
        assert reqs, f"family {fam} has no required capability"
        for cap in reqs:
            assert cap in ont.capability_keys(), f"{fam} requires unknown capability {cap}"


def test_grounding_predicates_exist_in_hardware_ontology():
    hw = {p["predicate"] for p in ont.hardware_ontology()["predicates"]}
    for c in ont.capability_ontology()["capabilities"]:
        for pred in c.get("grounded_by") or []:
            assert pred in hw, f"capability {c['key']} grounded_by unknown predicate {pred}"


def test_vertical_ontology_loads():
    assert ont.vertical_ontology().get("verticals")
    assert ont.verticals()  # non-empty
    assert ont.in_scope_verticals() <= ont.verticals()
    # Healthcare + eldercare are first-class (Aethon/Relay/hospital robots).
    assert {"healthcare", "eldercare", "hospitality"} <= ont.verticals()


def test_extractor_environment_values_are_known_verticals():
    """Every operating_environment value the parser can emit must be a known
    vertical, so the front door labels any robot URL instead of flattening it."""
    import re
    from pathlib import Path

    facts_src = (Path(__file__).resolve().parents[1]
                 / "app" / "services" / "robot_understanding_v1" / "facts.py").read_text()
    # The environment block assigns `val = "<vertical>"`; collect those literals.
    block = facts_src[facts_src.index("Vertical/environment ontology"):]
    block = block[: block.index("add(\"operating_environment\"")]
    emitted = set(re.findall(r'val\s*=\s*"([a-z_]+)"', block))
    assert emitted, "no operating_environment literals found"
    unknown = emitted - set(ont.verticals())
    assert not unknown, f"extractor emits verticals not in vertical_ontology: {unknown}"
