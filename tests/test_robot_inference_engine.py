"""Robot Inference Engine — deterministic phased-inference tests (no network/LLM).

Contract: evidence → inference → capability. Explicit signals are detected from
the evidence pack; structural/capability inference forward-chains with provenance.
Conclusions require capability-appropriate evidence — "2X productivity" is never
arm_count=2, "handles" is never a hand.
"""
from types import SimpleNamespace

from app.services.robot_inference_engine import (
    _detect_arm_count,
    _detect_hand_dof,
    _phase1_detect,
    _phase23_infer,
    infer_facts,
    Observation,
)
from app.services.robot_understanding_v1.models import RobotFact


def _pack(*texts: str):
    """Build a fake collected pack: list of objects with .page.text and .source.id."""
    out = []
    for i, t in enumerate(texts):
        out.append(
            SimpleNamespace(
                page=SimpleNamespace(text=t),
                source=SimpleNamespace(id=f"s{i}"),
            )
        )
    return out


def _grounded(obs_list):
    g = {}
    for o in obs_list:
        g.setdefault(o.predicate, o)
    return g


# ── Signal detection ─────────────────────────────────────────────────────────

def test_arm_count_detects_real_arms_not_2x():
    assert _detect_arm_count("Degrees of Freedom Hands 22x2 Arms 7x2")[0] == 2
    assert _detect_arm_count("NEO has two arms")[0] == 2
    # Marketing "2X" must NOT be read as arm_count.
    assert _detect_arm_count("enhances productivity by more than 2X") is None
    assert _detect_arm_count("keeps the room warm") is None


def test_hand_dof_detection():
    assert _detect_hand_dof("Degrees of Freedom Hands 22x2")[0] == 22
    assert _detect_hand_dof("25 DoF hands")[0] == 25
    assert _detect_hand_dof("handles dynamic tasks") is None  # "handles" is not a hand


def test_phase1_detectors_ground_neo_like_signals():
    pack = _pack(
        "NEO is a humanoid robot. Degrees of Freedom Hands 22x2 Arms 7x2. "
        "Fully mobile. Uses AI for autonomous navigation. Payload 18 lb."
    )
    obs = _phase1_detect(pack, "NEO")
    preds = {o.predicate: o.value for o in obs}
    assert preds.get("product_class") == "humanoid"
    assert preds.get("has_dexterous_hands") is True
    assert preds.get("arm_count") == 2
    assert preds.get("has_mobile_base") is True
    assert preds.get("autonomous_navigation") is True
    # Every observation carries evidence + a source id.
    assert all(o.evidence and o.source_id for o in obs)


def test_phase1_does_not_over_attribute_amr():
    pack = _pack(
        "Locus Origin is a collaborative mobile robot that enhances productivity by more than 2X. "
        "Person-to-Goods. Incorporating LiDAR and navigation. Handles totes and containers."
    )
    obs = _phase1_detect(pack, "Origin")
    preds = {o.predicate for o in obs}
    assert "arm_count" not in preds  # "2X" is not arms
    assert "has_dexterous_hands" not in preds  # "handles" is not a hand
    assert "autonomous_navigation" in preds  # LiDAR / navigation
    assert "supports_tote_handling" in preds  # totes / person-to-goods


def test_phase1_subject_scoping_blocks_sibling_sku_manipulation():
    # Capabilities belong to the SELECTED product/config — a sibling SKU's arm on
    # the same page must not be attributed to the AMR being researched.
    pack = _pack(
        "Origin is an autonomous mobile robot that moves totes. "
        "The RoboArm-500 module has two arms and dexterous hands for pick and place."
    )
    obs = _phase1_detect(pack, "Origin")
    preds = {o.predicate for o in obs}
    # The arm/hand evidence names RoboArm-500 (a different SKU) → not Origin's.
    assert "arm_count" not in preds
    assert "has_dexterous_hands" not in preds
    # Origin's own mobility/transport still grounds.
    assert "supports_tote_handling" in preds


def test_phase1_off_subject_page_contributes_nothing():
    pack = _pack("The Atlas humanoid has two arms and dexterous 22x2 hands.")
    # Researching "Origin", but the page is entirely about Atlas → no facts leak in.
    assert _phase1_detect(pack, "Origin") == []


# ── Manipulation is a capability, not a category (Bob's domain correction) ────

def test_amr_with_grab_off_shelf_grounds_manipulation():
    # An AMR that itself grabs items off shelves DOES manipulate — not excluded by label.
    pack = _pack(
        "Origin is an autonomous mobile robot. Its telescoping mast retrieves items "
        "off shelves and places products into the onboard tote."
    )
    obs = {o.predicate for o in _phase1_detect(pack, "Origin")}
    assert "end_effector" in obs  # manipulation grounded from the robot's own action
    assert "supports_tote_handling" in obs


def test_food_prep_is_manipulation():
    for text in [
        "The kitchen robot chops celery and dices onions for each order.",
        "This robot prepares fresh salads and assembles bowls to order.",
        "A foodservice robot with dexterous hands for food preparation.",
    ]:
        obs = {o.predicate for o in _phase1_detect(_pack(text), "")}
        assert "has_dexterous_hands" in obs, text


def test_human_in_the_loop_pick_is_not_robot_manipulation():
    # Person-to-goods: the WORKER picks. The robot transports; it does not manipulate.
    pack = _pack(
        "Locus Origin is a person-to-goods AMR. Workers pick items from the tote; "
        "it supports picking and putaway tasks."
    )
    obs = {o.predicate for o in _phase1_detect(pack, "Origin")}
    assert "end_effector" not in obs
    assert "has_dexterous_hands" not in obs
    assert "supports_tote_handling" in obs


def test_mobile_manipulator_class_detected():
    obs = {o.predicate: o.value for o in _phase1_detect(_pack("Reflex is a mobile manipulator platform."), "Reflex")}
    assert obs.get("product_class") == "mobile_manipulator"


def test_mobile_manipulator_plural_and_grounds_manipulation():
    # "Mobile manipulators" (plural) must still detect the class, and a mobile
    # manipulator — by definition — is mobile AND manipulates.
    grounded = _grounded(_phase1_detect(_pack("Our mobile manipulators pick directly inside the storage area."), ""))
    assert grounded.get("product_class") and grounded["product_class"].value == "mobile_manipulator"
    inferred = {o.predicate for o in _phase23_infer(grounded)}
    assert "has_mobile_base" in inferred


def test_brightpick_like_amr_grounds_robotic_picking(monkeypatch):
    # Brightpick: an AMR whose OWN robots pick (mobile manipulators pick, robotic
    # picking) — this is robot manipulation, unlike person-to-goods where a worker picks.
    monkeypatch.setenv("ROBOT_INFERENCE_ENGINE", "1")
    pack = _pack(
        "Our AI robots automate every step of warehouse order fulfillment with mobile robotic picking. "
        "Mobile manipulators pick directly inside the storage area. "
        "Flexible Goods-to-Person workflows support batch picking. Standard shelving and totes."
    )
    _, summary = infer_facts(pack, subject="", existing_facts=[])
    caps = {c["capability"] for c in summary["capabilities"]}
    assert "manipulate" in caps  # the robot itself picks → manipulation grounded
    assert "mobile" in caps
    assert "tote_transport" in caps


def test_bimanual_dexterity_grounds_manipulation(monkeypatch):
    # Nimo: entire pitch is "highly dexterous bimanual manipulation" / "two-handed
    # tasks" — no noun "hands", but this is explicit dexterity → grounded.
    monkeypatch.setenv("ROBOT_INFERENCE_ENGINE", "1")
    pack = _pack(
        "General-purpose robotic systems. Our architecture centers on highly dexterous bimanual "
        "manipulation, allowing our systems to perform complex, two-handed tasks."
    )
    _, summary = infer_facts(pack, subject="", existing_facts=[])
    caps = {c["capability"] for c in summary["capabilities"]}
    assert {"manipulate", "dexterous_manipulation", "dual_arm"} <= caps
    # "handles the complex tasks" must NOT be the trigger — dexterity is.
    obs = {o.predicate for o in _phase1_detect(_pack("The system handles complex tasks."), "")}
    assert "has_dexterous_hands" not in obs


# ── Structural / capability inference (forward chaining) ──────────────────────

def test_humanoid_infers_mobility_and_dual_arm():
    grounded = _grounded([
        Observation("product_class", "humanoid", None, "humanoid robot", "s0", 0.9, "explicit"),
        Observation("has_dexterous_hands", True, None, "22 DoF hands", "s0", 0.9, "explicit"),
    ])
    inferred = _phase23_infer(grounded)
    ip = {o.predicate: o for o in inferred}
    assert "has_mobile_base" in ip and ip["has_mobile_base"].mode == "strongly_inferred"
    assert ip["has_mobile_base"].basis  # cites its basis
    assert ip.get("arm_count") and int(ip["arm_count"].value) == 2


def test_navigation_infers_mobile_base():
    grounded = _grounded([
        Observation("autonomous_navigation", True, None, "autonomous navigation", "s0", 0.9, "explicit"),
    ])
    inferred = {o.predicate for o in _phase23_infer(grounded)}
    assert "has_mobile_base" in inferred


# ── End-to-end (flagged) via infer_facts, monkeypatching the enable flag ──────

def test_infer_facts_neo_end_to_end(monkeypatch):
    monkeypatch.setenv("ROBOT_INFERENCE_ENGINE", "1")
    pack = _pack(
        "NEO humanoid robot. Degrees of Freedom Hands 22x2 Arms 7x2. "
        "Fully mobile, autonomous navigation. Payload 18 lb."
    )
    existing = [RobotFact.create("NEO", "carrying_capacity", 18, source_id="s0", units="lb", evidence_span="Payload 18 lb")]
    extra, summary = infer_facts(pack, subject="NEO", existing_facts=existing)
    preds = {f.predicate: f for f in extra}
    assert "product_class" in preds and preds["product_class"].value == "humanoid"
    assert "has_dexterous_hands" in preds
    assert "arm_count" in preds
    assert "has_mobile_base" in preds
    # Inferred facts are GROUNDED (explicit or strongly_inferred) → matcher-visible.
    assert all(f.epistemic in ("explicit", "strongly_inferred") for f in extra)
    assert summary and summary["capabilities"]
    caps = {c["capability"] for c in summary["capabilities"]}
    assert {"manipulate", "dual_arm", "mobile"} <= caps


def test_infer_facts_disabled_is_noop():
    # Flag off → no work, no change (frozen v1 path).
    extra, summary = infer_facts(_pack("humanoid robot with 22 DoF hands"), subject="X", existing_facts=[])
    assert extra == [] and summary is None


def test_works_autonomously_grounds_navigation():
    pack = _pack("NEO works autonomously by default. Expert mode is optional.")
    obs = {o.predicate: o.value for o in _phase1_detect(pack, "NEO")}
    assert obs.get("autonomous_navigation") is True


def test_infer_facts_1x_style_marketing_grounds_humanoid(monkeypatch):
    monkeypatch.setenv("ROBOT_INFERENCE_ENGINE", "1")
    pack = _pack(
        "NEO is a fully electronic humanoid robot, with a .75 kWh battery pack. "
        "NEO works autonomously by default. Payload 18 lb."
    )
    extra, summary = infer_facts(pack, subject="NEO", existing_facts=[])
    preds = {f.predicate: f for f in extra}
    assert preds.get("product_class") and preds["product_class"].value == "humanoid"
    assert "has_mobile_base" in preds
    assert "autonomous_navigation" in preds
    caps = {c["capability"] for c in (summary or {}).get("capabilities") or []}
    assert "manipulate" in caps
    assert "mobile" in caps
