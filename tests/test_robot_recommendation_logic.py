"""
Semantic Test Matrix for Robot Recommendation Logic & Engine.
Validates that recommend_robots returns accurate, distinct hardware categories,
vendor SKUs, key capabilities, and task models for specified physical tasks.
"""
import pytest
from app.services.robot_recommendation_engine import recommend_robots_for_task


def test_pallet_transport_semantic_matching():
    # Horizontal pallet transport should return Heavy Pallet AMRs (MiR 1350, OTTO 1500)
    recs = recommend_robots_for_task("moving 500-pound pallets across warehouse floor", payload_capacity_kg=227.0)
    assert len(recs) > 0
    categories = [r["category"] for r in recs]
    assert any("AMR" in c or "Pallet Transport" in c for c in categories)
    models = recs[0]["suggested_models"]
    assert any("MiR" in m or "OTTO" in m or "Fetch" in m for m in models)
    assert recs[0]["typical_task_model"] == "pallet_transport_v1"


def test_palletizing_semantic_matching():
    # End-of-line case stacking/palletizing should return Palletizing Arms (UR20, FANUC M-20iD)
    recs = recommend_robots_for_task("palletizing corrugated cases at end of packaging line")
    assert len(recs) > 0
    categories = [r["category"] for r in recs]
    assert any("Palletizing Robot Arm" in c or "Palletizing Cobot" in c for c in categories)
    models = recs[0]["suggested_models"]
    assert any("UR20" in m or "FANUC" in m or "Yaskawa" in m for m in models)
    assert recs[0]["typical_task_model"] == "case_palletizing_v1"


def test_machine_tending_semantic_matching():
    # CNC loading/unloading should return Machine Tending Cobots (UR10e, FANUC CRX)
    recs = recommend_robots_for_task("loading CNC lathe doors and holding metal shafts")
    assert len(recs) > 0
    categories = [r["category"] for r in recs]
    assert any("Machine Tending" in c or "Cobot" in c for c in categories)
    models = recs[0]["suggested_models"]
    assert any("UR10e" in m or "FANUC CRX" in m or "Doosan" in m for m in models)
    assert recs[0]["typical_task_model"] == "machine_tending_v1"


def test_welding_semantic_matching():
    # MIG/TIG welding should return Arc Welding Cells (UR10e Welding Cell, FANUC ARC Mate)
    recs = recommend_robots_for_task("robotic MIG seam welding on steel tubular frames")
    assert len(recs) > 0
    categories = [r["category"] for r in recs]
    assert any("Welding" in c for c in categories)
    models = recs[0]["suggested_models"]
    assert any("Hirebotics" in m or "ARC Mate" in m or "Yaskawa" in m for m in models)
    assert recs[0]["typical_task_model"] == "robotic_welding_v1"


def test_pick_and_place_semantic_matching():
    # High-speed sorting/picking should return Delta/SCARA (FlexPicker, SCARA)
    recs = recommend_robots_for_task("high speed pick and place sorting of items on conveyor belt")
    assert len(recs) > 0
    categories = [r["category"] for r in recs]
    assert any("Pick-and-Place" in c or "Delta" in c or "SCARA" in c for c in categories)
    models = recs[0]["suggested_models"]
    assert any("FlexPicker" in m or "Epson" in m or "UR5e" in m or "RightPick" in m for m in models)
    assert recs[0]["typical_task_model"] == "high_speed_piece_picking_v1"


def test_assembly_semantic_matching():
    # Precision assembly and screwdriving should return 7-DoF/Bimanual Cobots (Panda, YuMi)
    recs = recommend_robots_for_task("precision electronic assembly and screwdriving")
    assert len(recs) > 0
    categories = [r["category"] for r in recs]
    assert any("Assembly" in c or "Bimanual" in c for c in categories)
    models = recs[0]["suggested_models"]
    assert any("Panda" in m or "YuMi" in m or "UR3e" in m for m in models)
    assert recs[0]["typical_task_model"] == "precision_assembly_v1"


def test_inspection_semantic_matching():
    # Facility thermal scan / gauge reading should return Quadruped/Inspection (Spot, ANYmal)
    recs = recommend_robots_for_task("autonomous thermal scanning and gauge inspection patrol in power plant")
    assert len(recs) > 0
    categories = [r["category"] for r in recs]
    assert any("Inspection" in c or "Quadruped" in c for c in categories)
    models = recs[0]["suggested_models"]
    assert any("Spot" in m or "ANYmal" in m for m in models)
    assert recs[0]["typical_task_model"] == "facility_inspection_patrol_v1"


def test_floor_scrubbing_semantic_matching():
    # Hard floor cleaning should return Floor Scrubber AMRs (Tennant T7AMR, Avidbots)
    recs = recommend_robots_for_task("commercial hard floor scrubbing in distribution center")
    assert len(recs) > 0
    categories = [r["category"] for r in recs]
    assert any("Floor Scrubber" in c for c in categories)
    models = recs[0]["suggested_models"]
    assert any("Tennant" in m or "Avidbots" in m or "Brain" in m for m in models)
    assert recs[0]["typical_task_model"] == "commercial_floor_clean_v1"


def test_humanoid_multitask_semantic_matching():
    # Bipedal dexterous unstructured work should return Humanoids (Figure 02, Unitree G1)
    recs = recommend_robots_for_task("general purpose humanoid for unstructured tote handling and stair navigation")
    assert len(recs) > 0
    categories = [r["category"] for r in recs]
    assert any("Humanoid" in c for c in categories)
    models = recs[0]["suggested_models"]
    assert any("Figure 02" in m or "Unitree G1" in m or "Apollo" in m for m in models)
    assert recs[0]["typical_task_model"] == "humanoid_unstructured_work_v1"
