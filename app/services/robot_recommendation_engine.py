"""
Robot Recommendation Engine Service.

Translates physical work task descriptions and payload constraints into optimal
robot hardware categories, vendor models, key capabilities, and task models.

Taxonomy supported:
- pallet_transport (heavy AMRs / autonomous forklifts)
- palletizing (articulated palletizing arms / cobots)
- machine_tending (CNC / press loading cobots & arms)
- welding (MIG/TIG robotic arc welding cells)
- pick_and_place (high-speed SCARA / Delta / piece picking)
- assembly (precision 7-DoF / bimanual assembly cobots)
- inspection (quadrupeds / mobile inspection AMRs)
- floor_scrubbing (commercial floor scrubbing AMRs)
- humanoid_multitask (general purpose bipedal humanoids)
"""
from typing import Any, Optional


RECOMMENDATION_TAXONOMY: dict[str, dict[str, Any]] = {
    "pallet_transport": {
        "category": "Autonomous Mobile Robot (AMR) / Heavy Pallet Transport & Tugger",
        "suggested_models": ["MiR 1350", "OTTO 1500", "Fetch Heavy Pallet", "Linde Autonomous Forklift"],
        "key_capabilities": ["autonomous SLAM navigation", "1000kg+ payload capacity", "automated hitching / lift deck", "ANSI/RIA R15.08 safety compliance"],
        "typical_task_model": "pallet_transport_v1",
        "description": "Heavy payload mobile platforms engineered for horizontal transport of 500lb+ pallets, carts, and containers across warehouses and factories."
    },
    "palletizing": {
        "category": "High-Payload Palletizing Robot Arm / Palletizing Cobot",
        "suggested_models": ["Universal Robots UR20 / UR30", "FANUC M-20iD/35", "Yaskawa Motoman GP25", "ABB IRB 460"],
        "key_capabilities": ["extended reach (1700mm+)", "high payload (20kg–50kg+)", "pallet pattern software", "vacuum & mechanical end-effectors"],
        "typical_task_model": "case_palletizing_v1",
        "description": "End-of-line articulated robot arms and high-payload cobots built to stack cases, boxes, or bags onto pallets with pattern precision."
    },
    "machine_tending": {
        "category": "Precision Machine Tending Cobot / Industrial Arm",
        "suggested_models": ["Universal Robots UR10e", "FANUC CRX-10iA/L", "Doosan H2017", "Techman TM12"],
        "key_capabilities": ["IP67 coolant resistance", "dual-chucker pneumatic gripper", "force-torque sensing", "CNC door interface (IO-Link / Euromap)"],
        "typical_task_model": "machine_tending_v1",
        "description": "Collaborative arms and industrial manipulators for loading/unloading CNC lathes, mills, injection molding machines, and stamping presses."
    },
    "welding": {
        "category": "Robotic Arc & MIG/TIG Welding Cell / Welding Cobot",
        "suggested_models": ["Universal Robots UR10e Welding Cell (Hirebotics / Miller)", "FANUC ARC Mate 100iD", "Yaskawa AR1440"],
        "key_capabilities": ["torch weave patterns", "seam tracking", "high IP protection against spatter", "intuitive teach pendant weld recipes"],
        "typical_task_model": "robotic_welding_v1",
        "description": "Specialized welding cobots and robotic arc welding manipulators designed for repetitive MIG, TIG, and seam welding operations."
    },
    "pick_and_place": {
        "category": "High-Speed Pick-and-Place Robot (Delta / SCARA / Piece-Picking Cobot)",
        "suggested_models": ["ABB FlexPicker IRB 360", "Epson SCARA GX Series", "Universal Robots UR5e", "RightHand Robotics RightPick"],
        "key_capabilities": ["high cycle speed (100+ picks/min)", "2D/3D vision guidance", "suction/finger gripper", "conveyor belt tracking"],
        "typical_task_model": "high_speed_piece_picking_v1",
        "description": "Fast Delta, SCARA, or lightweight articulated arms optimized for rapid sorting, kitting, conveyor picking, and packaging."
    },
    "assembly": {
        "category": "Precision Assembly Cobot / Bimanual Robot Arm",
        "suggested_models": ["Franka Emika Panda / Production", "ABB YuMi (IRB 14000)", "Universal Robots UR3e", "KUKA LBR iiwa"],
        "key_capabilities": ["joint torque sensors (7-DoF)", "sub-millimeter insertion accuracy", "force-guided screwdriving", "ESD safe"],
        "typical_task_model": "precision_assembly_v1",
        "description": "High-precision 7-DoF or bimanual cobots for screwdriving, electronic component insertion, fastening, and micro-assembly."
    },
    "inspection": {
        "category": "Autonomous Mobile Inspection Robot / Quadruped",
        "suggested_models": ["Boston Dynamics Spot", "ANYbotics ANYmal", "Energy Robotics Inspection AMR"],
        "key_capabilities": ["stair & obstacle climbing", "thermal imaging & acoustic leak detection", "gas sensing", "IP67 ruggedized chassis"],
        "typical_task_model": "facility_inspection_patrol_v1",
        "description": "Mobile quadrupedal or tracked inspection robots for autonomous thermal scanning, gauge reading, and facility safety monitoring."
    },
    "floor_scrubbing": {
        "category": "Autonomous Commercial Floor Scrubber & Cleaning AMR",
        "suggested_models": ["Tennant T7AMR", "Avidbots Neo 2", "Brain Corp Powered Scrubber", "Nilfisk Liberty SC50"],
        "key_capabilities": ["autonomous water recycling", "LiDAR & 3D camera obstacle avoidance", "coverage reporting", "docking & auto-fill"],
        "typical_task_model": "commercial_floor_clean_v1",
        "description": "Industrial autonomous scrubbers designed for continuous hard floor cleaning in commercial, retail, and manufacturing facilities."
    },
    "humanoid_multitask": {
        "category": "General Purpose Bipedal Humanoid / Mobile Manipulator",
        "suggested_models": ["Figure 02", "Unitree G1", "Apptronik Apollo", "Agility Robotics Digit", "Boston Dynamics Atlas"],
        "key_capabilities": ["whole-body VLA policy", "5-finger dexterous hands", "bipedal threshold navigation", "20kg+ dual-arm payload"],
        "typical_task_model": "humanoid_unstructured_work_v1",
        "description": "Humanoid platforms equipped with dexterous hands and bipedal mobility for unstructured warehouse, tote handling, and multi-task work."
    }
}


def recommend_robots_for_task(
    task_description: str,
    payload_capacity_kg: Optional[float] = None,
    environment: Optional[str] = "indoor"
) -> list[dict[str, Any]]:
    """
    Analyze task description and return semantically accurate robot recommendations.
    Differentiates between pallet transport vs palletizing, machine tending vs welding,
    assembly vs high-speed picking, inspection vs cleaning, and humanoids.
    """
    desc = task_description.lower().strip()
    matched_keys: list[str] = []

    # 1. Palletizing (Check BEFORE horizontal transport if 'palletizing' or 'stack' is mentioned)
    if "palletiz" in desc or "stack" in desc or "case stack" in desc or "end of line" in desc:
        matched_keys.append("palletizing")

    # 2. Pallet Transport / Moving heavy pallets
    if ("pallet" in desc and "palletiz" not in desc) or ("move" in desc and "pallet" in desc) or "tug" in desc or "amr" in desc or "forklift" in desc:
        if "pallet_transport" not in matched_keys:
            matched_keys.append("pallet_transport")

    # 3. Welding
    if "weld" in desc or "mig" in desc or "tig" in desc or "seam" in desc or "torch" in desc:
        matched_keys.append("welding")

    # 4. Machine Tending
    if "tend" in desc or "cnc" in desc or "lathe" in desc or "press" in desc or "injection mold" in desc or "loading machine" in desc:
        if "welding" not in matched_keys:
            matched_keys.append("machine_tending")

    # 5. Inspection
    if "inspect" in desc or "audit" in desc or "gauge" in desc or "thermal" in desc or "patrol" in desc or "leak" in desc:
        matched_keys.append("inspection")

    # 6. Commercial Cleaning / Floor Scrubbing
    if "clean" in desc or "scrub" in desc or "janitor" in desc or "floor clean" in desc:
        if "inspection" not in matched_keys:
            matched_keys.append("floor_scrubbing")

    # 7. Assembly
    if "assembl" in desc or "screw" in desc or "fasten" in desc or "pcb" in desc or "insertion" in desc:
        matched_keys.append("assembly")

    # 8. High-speed Pick & Place / Kitting / Sorting
    if ("pick and place" in desc or "sort" in desc or "conveyor" in desc or "kitting" in desc) and "assembl" not in desc and "tend" not in desc:
        matched_keys.append("pick_and_place")

    # 9. Humanoid / Unstructured
    if "humanoid" in desc or "tote" in desc or "unstructured" in desc or "biped" in desc or "general purpose" in desc:
        matched_keys.append("humanoid_multitask")

    # 10. Payload adjustments
    if payload_capacity_kg is not None and payload_capacity_kg > 200.0:
        if "pallet_transport" not in matched_keys and "palletizing" not in matched_keys:
            matched_keys.append("pallet_transport")

    # Fallback if no specific keyword matched
    if not matched_keys:
        if "pick" in desc or "move" in desc or "handle" in desc:
            matched_keys.append("pick_and_place")
        else:
            matched_keys.append("machine_tending")
            matched_keys.append("humanoid_multitask")

    results: list[dict[str, Any]] = []
    for key in matched_keys:
        if key in RECOMMENDATION_TAXONOMY:
            item = RECOMMENDATION_TAXONOMY[key].copy()
            results.append(item)

    return results
