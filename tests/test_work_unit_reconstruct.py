"""Tests for WORK reconstruction + primitive-spine matching (no DB)."""
from app.services.primitive_match import hard_blockers, work_robot_match_score
from app.services.robot_primitives import primitives_from_vendor_text
from app.services.work_unit_reconstruct import (
    detect_workflow_family,
    reconstruct_work_from_text,
)


STRONG_TRANSPORT = (
    "Move palletized loads between receiving, staging, and outbound using powered "
    "industrial trucks. This role focuses on repeatable internal pallet moves across "
    "marked aisles. Operators stage inbound pallets, travel fixed routes to staging lanes."
)

TUGGER = (
    "Pull cart trains on timed milk-runs to replenish assembly line-side racks every cycle. "
    "Routes are fixed milk-runs with sequenced stops. Focus is tugger/cart movement and "
    "line-side presentation. Cart interfaces use pin hitches."
)

MIXED = (
    "Pick, stage, and deliver mixed cases and cartons to assembly lines while clearing "
    "empty packaging. Work mixes cart transport with manual case handling."
)


def test_strong_transport_maps_to_pallet_primitives():
    wu = reconstruct_work_from_text(
        STRONG_TRANSPORT,
        job_title="Material Handler - Internal Transport",
    )
    assert wu.workflow_family == "strong_transport"
    assert "eng.acquire_pallet_floor" in wu.required_primitives
    assert "tr.point_to_point" in wu.required_primitives
    assert wu.object == "pallet"
    assert wu.confidence >= 0.4
    assert wu.truth_state == "SIGNAL_INFERRED"
    assert all(p.code.startswith(("mob.", "eng.", "tr.", "plc.", "man.", "per.", "int.", "exc.")) for p in wu.primitives)


def test_tugger_maps_to_tow_and_line_replenishment():
    wu = reconstruct_work_from_text(
        TUGGER,
        job_title="Line Replenishment Associate - Tugger Route",
    )
    assert wu.workflow_family == "tugger_line_replenishment"
    assert "eng.tow_hitch" in wu.required_primitives
    assert "tr.line_replenishment" in wu.required_primitives
    assert "eng.acquire_pallet_floor" not in wu.required_primitives or "eng.tow_hitch" in wu.required_primitives


def test_payload_hint_from_forklift_capacity():
    wu = reconstruct_work_from_text(
        "Operate 5,000-lb capacity forklift. Move finished pallets from production to warehouse."
    )
    assert wu.payload_kg_hint is not None
    assert 2200 < wu.payload_kg_hint < 2300  # ~2268 kg


def test_forklift_robot_matches_transport_not_tugger():
    transport = reconstruct_work_from_text(STRONG_TRANSPORT)
    tugger = reconstruct_work_from_text(TUGGER)
    forklift = primitives_from_vendor_text(
        robot_categories=["autonomous_forklift"],
        name="OTTO Lifter",
    )
    t_score, t_detail = work_robot_match_score(
        required_primitives=transport.required_primitives,
        supported_primitives=forklift["supported_primitives"],
        workflow_family=transport.workflow_family,
        industry_aligned=True,
        buyer_tier="HOT",
        buyer_score=90,
    )
    g_score, g_detail = work_robot_match_score(
        required_primitives=tugger.required_primitives,
        supported_primitives=forklift["supported_primitives"],
        workflow_family=tugger.workflow_family,
        industry_aligned=True,
        buyer_tier="HOT",
        buyer_score=90,
    )
    assert t_score > g_score
    assert "WRONG_MACHINE_TUGGER" in hard_blockers(
        tugger.required_primitives,
        forklift["supported_primitives"],
        workflow_family=tugger.workflow_family,
    )
    assert t_detail.get("work_match", 0) >= 70
    assert g_detail.get("hard_blockers")


def test_tugger_robot_matches_tugger_work():
    tugger = reconstruct_work_from_text(TUGGER)
    caps = primitives_from_vendor_text(robot_categories=["autonomous_tugger"], name="Tug Bot")
    score, detail = work_robot_match_score(
        required_primitives=tugger.required_primitives,
        supported_primitives=caps["supported_primitives"],
        workflow_family=tugger.workflow_family,
        industry_aligned=True,
        buyer_tier="HOT",
        buyer_score=85,
    )
    assert score >= 70
    assert not detail.get("hard_blockers")
    assert "eng.tow_hitch" in detail["matched"]


def test_mixed_handler_includes_case_pick():
    wu = reconstruct_work_from_text(MIXED, job_title="Material Handler / Water Spider")
    assert wu.workflow_family == "mixed_material_handler"
    assert "man.case_pick" in wu.required_primitives


def test_detect_family_unknown_for_thin_text():
    family, conf, _ = detect_workflow_family("Looking for a motivated team player.")
    assert family == "unknown"
    assert conf < 0.5
