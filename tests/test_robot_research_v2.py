"""Robot Research Agent v2 — deterministic truth-guard tests (no network / no LLM).

These lock the "code enforces truth" layer: an AI quote that exists on the page
but does not pertain to the claim must be rejected (e.g. "enhances productivity
by more than 2X" must NOT become arm_count=2; "handles dynamic task interleaving"
must NOT imply a gripper). Real capability evidence (e.g. "Arms 7x2") must pass.
"""
from app.services.robot_research_v2 import (
    _claim_supported,
    _cap_display_supported,
    _facts_from_extraction,
    _kw_hit,
    _norm,
)


def test_kw_hit_word_boundaries():
    toks = _norm("Locus Origin handles dynamic task interleaving").split()
    assert not _kw_hit("locus origin handles dynamic task interleaving", toks, "hand")  # not "handles"
    toks2 = _norm("Degrees of Freedom Hands 22x2 Arms 7x2").split()
    assert _kw_hit(_norm("Hands 22x2 Arms 7x2"), toks2, "hands")  # exact "hands" token
    assert _kw_hit(_norm("Arms 7x2"), _norm("Arms 7x2").split(), "arms")
    assert not _kw_hit(_norm("keeps the room warm"), _norm("keeps the room warm").split(), "arm")
    assert _kw_hit(_norm("autonomous navigation via LiDAR"), _norm("autonomous navigation via lidar").split(), "navigat")


def test_claim_supported_rejects_mismatched_evidence():
    # The Locus failure: number present but no arm context, or fabricated specs.
    assert not _claim_supported("arm_count", 2, "enhances productivity by more than 2X")
    assert not _claim_supported("has_dexterous_hands", True, "enhances productivity by more than 2X")
    assert not _claim_supported("end_effector", "gripper", "handles dynamic task interleaving")
    assert not _claim_supported("carrying_capacity", 55, "collaborative mobile robot 2X")
    # Real evidence passes.
    assert _claim_supported("arm_count", 2, "Degrees of Freedom Hands 22x2 Arms 7x2")
    assert _claim_supported("has_dexterous_hands", True, "Degrees of Freedom Hands 22x2")
    assert _claim_supported("carrying_capacity", 18, "Payload 18 lb")
    assert _claim_supported("product_class", "humanoid", "NEO is a humanoid robot")
    assert not _claim_supported("product_class", "humanoid", "collaborative mobile robot")


def test_cap_display_manipulation_needs_hardware_evidence():
    pack = _norm("locus origin handles dynamic task interleaving picking and putaway")
    assert not _cap_display_supported("pick", "handles dynamic task interleaving picking", pack)
    pack2 = _norm("neo has two arms and dexterous hands that grasp objects")
    assert _cap_display_supported("grasp", "two arms and dexterous hands that grasp", pack2)


def _extract(pack_text, extraction):
    pack_norm = _norm(pack_text)
    index_map = [{"index": 0, "source_id": "s0", "url": "u", "type": "product"}]
    facts, summary = _facts_from_extraction(
        extraction,
        subject="Robot",
        index_map=index_map,
        pack_norm=pack_norm,
        existing_predicates=set(),
    )
    return {f.predicate: f.value for f in facts}, summary


def test_neo_like_extraction_grounds_manipulation():
    pack = "NEO humanoid robot. Degrees of Freedom Hands 22x2 Arms 7x2. Payload 18 lb. Uses AI for navigating."
    extraction = {
        "product": {
            "morphology": "humanoid",
            "capabilities": [
                {"key": "two_arm_manipulation", "evidence": "Arms 7x2", "source_index": 0},
                {"key": "navigate", "evidence": "Uses AI for navigating", "source_index": 0},
            ],
            "specs": {
                "arm_count": {"value": 2, "evidence": "Arms 7x2", "source_index": 0},
                "has_dexterous_hands": {"value": True, "evidence": "Hands 22x2", "source_index": 0},
                "carrying_capacity": {"value": 18, "units": "lb", "evidence": "Payload 18 lb", "source_index": 0},
            },
        }
    }
    facts, _ = _extract(pack, extraction)
    assert facts.get("arm_count") == 2
    assert facts.get("has_dexterous_hands") is True
    assert facts.get("carrying_capacity") == 18
    assert facts.get("product_class") == "humanoid"


def test_locus_like_extraction_rejects_false_manipulation():
    pack = (
        "Locus Origin is a collaborative mobile robot that enhances productivity by more than 2X. "
        "Person-to-Goods. Incorporating LiDAR and navigation. Handles totes and containers."
    )
    extraction = {
        "product": {
            "morphology": "amr",
            "capabilities": [
                {"key": "pick", "evidence": "handles dynamic task interleaving", "source_index": 0},
                {"key": "navigate", "evidence": "Incorporating LiDAR and navigation", "source_index": 0},
                {"key": "tote_transport", "evidence": "Handles totes and containers", "source_index": 0},
            ],
            "specs": {
                "arm_count": {"value": 2, "evidence": "enhances productivity by more than 2X", "source_index": 0},
                "has_dexterous_hands": {"value": True, "evidence": "collaborative mobile robot", "source_index": 0},
            },
        }
    }
    facts, _ = _extract(pack, extraction)
    # The false manipulation claims must all be rejected.
    assert "arm_count" not in facts
    assert "has_dexterous_hands" not in facts
    assert "end_effector" not in facts
    # Legitimate transport/mobility survives.
    assert facts.get("supports_tote_handling") is True
    assert facts.get("autonomous_navigation") is True or facts.get("has_mobile_base") is True
