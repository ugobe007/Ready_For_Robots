"""Canonical trained-task catalog (source of truth).

Catalogs *tasks* public models were trained or fine-tuned on. This is not a
claim that any candidate SKU carries those weights. Trajectory counts and
licenses are filled only when the source states them; otherwise null/unknown.
"""
from __future__ import annotations

from typing import Any

PERCEPTION = frozenset(
    {
        "detect_object",
        "detect_carton",
        "estimate_pose",
        "estimate_grasp",
        "segment_instance",
        "read_label",
    }
)
MANIPULATION = frozenset(
    {
        "reach",
        "grasp",
        "lift",
        "orient",
        "place",
        "release",
        "insert",
        "open_drawer",
        "close_drawer",
        "open_door",
        "close_door",
        "press_button",
        "pour",
        "fold",
        "wipe",
        "handover",
    }
)
MOBILITY = frozenset({"stationary", "base_nav", "humanoid_walk"})

PNP = (
    "detect_object",
    "estimate_pose",
    "estimate_grasp",
    "reach",
    "grasp",
    "lift",
    "orient",
    "place",
    "release",
)
KITCHEN = PNP + ("open_drawer", "close_drawer", "open_door", "press_button")
BIMANUAL = PNP + ("handover",)


def _split_skills(skills: tuple[str, ...]) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    perc = tuple(s for s in skills if s in PERCEPTION)
    manip = tuple(s for s in skills if s in MANIPULATION)
    mob = tuple(s for s in skills if s in MOBILITY)
    return perc, manip, mob or ("stationary",)


def _model(
    mid: str,
    *,
    name: str,
    family: str,
    source: str,
    url: str,
    base_model: str | None = None,
    fine_tuned_model: str | None = None,
    training_dataset: str | None = None,
    trajectory_count: int | None = None,
    embodiments: tuple[str, ...] = (),
    arm_count: int | None = 1,
    dof: str | None = None,
    gripper_type: str | None = None,
    camera_configuration: str | None = None,
    action_space: str | None = None,
    observation_space: str | None = None,
    zero_shot_capable: bool | None = None,
    fine_tuning_required: bool | None = None,
    simulation_verified: bool | None = None,
    real_world_verified: bool | None = None,
    license: str | None = None,
    commercial_use: str = "unknown",
    confidence: str = "medium",
    note: str = "",
) -> dict[str, Any]:
    return {
        "id": mid,
        "name": name,
        "family": family,
        "source": source,
        "url": url,
        "base_model": base_model,
        "fine_tuned_model": fine_tuned_model,
        "training_dataset": training_dataset,
        "trajectory_count": trajectory_count,
        "robot_embodiments": list(embodiments),
        "arm_count": arm_count,
        "dof": dof,
        "gripper_type": gripper_type,
        "camera_configuration": camera_configuration,
        "action_space": action_space,
        "observation_space": observation_space,
        "zero_shot_capable": zero_shot_capable,
        "fine_tuning_required": fine_tuning_required,
        "simulation_verified": simulation_verified,
        "real_world_verified": real_world_verified,
        "license": license,
        "commercial_use": commercial_use,
        "confidence": confidence,
        "note": note,
    }


def _models() -> dict[str, dict[str, Any]]:
    rows = (
        _model(
            "openvla-7b",
            name="OpenVLA 7B",
            family="OpenVLA",
            source="openvla",
            url="https://github.com/openvla/openvla",
            training_dataset="Open X-Embodiment",
            trajectory_count=970_000,
            embodiments=("widowx", "franka", "google_robot", "single_arm"),
            dof="7-DoF EE",
            gripper_type="parallel",
            camera_configuration="third_person_rgb",
            action_space="end_effector_delta",
            observation_space="rgb + language",
            zero_shot_capable=True,
            fine_tuning_required=True,
            simulation_verified=True,
            real_world_verified=True,
            license="MIT",
            commercial_use="permissive",
            confidence="high",
            note="Language-conditioned VLA pretrained on ~970k OXE trajectories. New embodiments typically need fine-tuning.",
        ),
        _model(
            "openvla-7b-libero-spatial",
            name="OpenVLA 7B LIBERO-Spatial",
            family="OpenVLA",
            source="openvla",
            url="https://huggingface.co/openvla/openvla-7b-finetuned-libero-spatial",
            base_model="openvla-7b",
            fine_tuned_model="openvla-7b-libero-spatial",
            training_dataset="LIBERO-Spatial",
            embodiments=("libero_sim_arm", "single_arm"),
            simulation_verified=True,
            real_world_verified=False,
            license="MIT",
            commercial_use="permissive",
            confidence="high",
            fine_tuning_required=False,
            zero_shot_capable=False,
        ),
        _model(
            "openvla-7b-libero-object",
            name="OpenVLA 7B LIBERO-Object",
            family="OpenVLA",
            source="openvla",
            url="https://huggingface.co/openvla/openvla-7b-finetuned-libero-object",
            base_model="openvla-7b",
            fine_tuned_model="openvla-7b-libero-object",
            training_dataset="LIBERO-Object",
            embodiments=("libero_sim_arm", "single_arm"),
            simulation_verified=True,
            real_world_verified=False,
            license="MIT",
            commercial_use="permissive",
            confidence="high",
        ),
        _model(
            "openvla-7b-libero-goal",
            name="OpenVLA 7B LIBERO-Goal",
            family="OpenVLA",
            source="openvla",
            url="https://huggingface.co/openvla/openvla-7b-finetuned-libero-goal",
            base_model="openvla-7b",
            fine_tuned_model="openvla-7b-libero-goal",
            training_dataset="LIBERO-Goal",
            embodiments=("libero_sim_arm", "single_arm"),
            simulation_verified=True,
            real_world_verified=False,
            license="MIT",
            commercial_use="permissive",
            confidence="high",
        ),
        _model(
            "openvla-7b-libero-long",
            name="OpenVLA 7B LIBERO-Long",
            family="OpenVLA",
            source="openvla",
            url="https://huggingface.co/openvla/openvla-7b-finetuned-libero-10",
            base_model="openvla-7b",
            fine_tuned_model="openvla-7b-libero-long",
            training_dataset="LIBERO-Long (LIBERO-10)",
            embodiments=("libero_sim_arm", "single_arm"),
            simulation_verified=True,
            real_world_verified=False,
            license="MIT",
            commercial_use="permissive",
            confidence="high",
        ),
        _model(
            "octo-base-1.5",
            name="Octo Base 1.5",
            family="Octo",
            source="octo",
            url="https://github.com/octo-models/octo",
            training_dataset="Open X-Embodiment (oxe_magic_soup)",
            trajectory_count=800_000,
            embodiments=("widowx", "franka", "google_robot", "single_arm"),
            camera_configuration="multi_rgb",
            action_space="diffusion_chunk",
            observation_space="rgb + language_or_goal_image",
            zero_shot_capable=True,
            fine_tuning_required=True,
            simulation_verified=True,
            real_world_verified=True,
            license="MIT",
            commercial_use="permissive",
            confidence="high",
            note="Generalist policy on ~800k trajectories; adapters for new observation/action spaces.",
        ),
        _model(
            "octo-small-1.5",
            name="Octo Small 1.5",
            family="Octo",
            source="octo",
            url="https://huggingface.co/rail-berkeley/octo-small-1.5",
            training_dataset="Open X-Embodiment",
            trajectory_count=800_000,
            embodiments=("widowx", "franka", "single_arm"),
            zero_shot_capable=True,
            fine_tuning_required=True,
            license="MIT",
            commercial_use="permissive",
            confidence="high",
        ),
        _model(
            "pi0",
            name="π₀",
            family="Physical Intelligence",
            source="physical_intelligence",
            url="https://www.physicalintelligence.company/blog/pi0",
            training_dataset="π cross-embodiment corpus (not fully public)",
            embodiments=("single_arm", "mobile_manipulator", "bimanual"),
            zero_shot_capable=True,
            fine_tuning_required=True,
            simulation_verified=True,
            real_world_verified=True,
            license="unknown",
            commercial_use="unknown",
            confidence="medium",
            note="Generalist VLA. Weights and license must be checked before commercial placement.",
        ),
        _model(
            "pi0.5",
            name="π₀.₅",
            family="Physical Intelligence",
            source="physical_intelligence",
            url="https://www.physicalintelligence.company/",
            embodiments=("single_arm", "mobile_manipulator", "humanoid"),
            zero_shot_capable=True,
            fine_tuning_required=True,
            real_world_verified=True,
            license="unknown",
            commercial_use="unknown",
            confidence="medium",
        ),
        _model(
            "gr00t-n1",
            name="NVIDIA GR00T N1",
            family="GR00T",
            source="nvidia",
            url="https://developer.nvidia.com/isaac/gr00t",
            training_dataset="GR00T embodiment mix (Isaac / humanoid)",
            embodiments=("humanoid", "bimanual", "single_arm"),
            arm_count=2,
            camera_configuration="multi_rgb",
            action_space="humanoid_control",
            observation_space="vision + language + proprioception",
            zero_shot_capable=True,
            fine_tuning_required=True,
            simulation_verified=True,
            real_world_verified=True,
            license="NVIDIA research",
            commercial_use="unknown",
            confidence="medium",
        ),
        _model(
            "smolvla",
            name="SmolVLA",
            family="LeRobot",
            source="lerobot",
            url="https://huggingface.co/lerobot",
            training_dataset="LeRobot community datasets",
            embodiments=("aloha", "so100", "single_arm"),
            arm_count=2,
            zero_shot_capable=False,
            fine_tuning_required=True,
            simulation_verified=True,
            real_world_verified=True,
            license="Apache-2.0",
            commercial_use="permissive",
            confidence="medium",
        ),
        _model(
            "act",
            name="ACT (Action Chunking Transformer)",
            family="ACT",
            source="lerobot",
            url="https://huggingface.co/docs/lerobot",
            embodiments=("aloha", "bimanual"),
            arm_count=2,
            fine_tuning_required=True,
            simulation_verified=True,
            real_world_verified=True,
            license="Apache-2.0",
            commercial_use="permissive",
            confidence="high",
        ),
        _model(
            "diffusion-policy",
            name="Diffusion Policy",
            family="Diffusion Policy",
            source="lerobot",
            url="https://huggingface.co/docs/lerobot",
            embodiments=("franka", "single_arm"),
            fine_tuning_required=True,
            simulation_verified=True,
            real_world_verified=True,
            license="MIT",
            commercial_use="permissive",
            confidence="high",
        ),
    )
    return {m["id"]: m for m in rows}


MODELS = _models()


def _task(
    tid: str,
    *,
    name: str,
    family: str,
    object_type: str,
    environment: str,
    skills: tuple[str, ...] = PNP,
    models: tuple[str, ...] = (),
    training_dataset: str | None = None,
    trajectory_count: int | None = None,
    embodiment: str | None = None,
    arm_count: int | None = None,
    source: str = "",
    url: str | None = None,
    simulation_verified: bool | None = None,
    real_world_verified: bool | None = None,
    confidence: str = "medium",
    commercial_use: str | None = None,
) -> dict[str, Any]:
    perc, manip, mob = _split_skills(skills)
    primary = MODELS.get(models[0]) if models else None
    return {
        "task_id": tid,
        "task_name": name,
        "task_family": family,
        "object_type": object_type,
        "environment": environment,
        "required_perception": list(perc),
        "required_manipulation": list(manip),
        "required_mobility": list(mob),
        "model_ids": list(models),
        "model_name": (primary or {}).get("name"),
        "model_family": (primary or {}).get("family"),
        "model_source": source or (primary or {}).get("source"),
        "model_url": url or (primary or {}).get("url"),
        "base_model": (primary or {}).get("base_model"),
        "fine_tuned_model": (primary or {}).get("fine_tuned_model"),
        "training_dataset": training_dataset or (primary or {}).get("training_dataset"),
        "trajectory_count": trajectory_count
        if trajectory_count is not None
        else (primary or {}).get("trajectory_count"),
        "robot_embodiment": embodiment
        or (((primary or {}).get("robot_embodiments") or [None])[0]),
        "arm_count": arm_count if arm_count is not None else (primary or {}).get("arm_count"),
        "dof": (primary or {}).get("dof"),
        "gripper_type": (primary or {}).get("gripper_type"),
        "camera_configuration": (primary or {}).get("camera_configuration"),
        "action_space": (primary or {}).get("action_space"),
        "observation_space": (primary or {}).get("observation_space"),
        "zero_shot_capable": (primary or {}).get("zero_shot_capable"),
        "fine_tuning_required": (primary or {}).get("fine_tuning_required"),
        "simulation_verified": simulation_verified
        if simulation_verified is not None
        else (primary or {}).get("simulation_verified"),
        "real_world_verified": real_world_verified
        if real_world_verified is not None
        else (primary or {}).get("real_world_verified"),
        "license": (primary or {}).get("license"),
        "commercial_use": commercial_use or (primary or {}).get("commercial_use") or "unknown",
        "confidence": confidence,
    }


LIBERO_SPATIAL = (
    ("between_plate_and_ramekin", "black bowl between the plate and the ramekin"),
    ("next_to_ramekin", "black bowl next to the ramekin"),
    ("table_center", "black bowl from table center"),
    ("on_cookie_box", "black bowl on the cookie box"),
    ("in_top_drawer", "black bowl in the top drawer of the wooden cabinet"),
    ("on_stove", "black bowl on the stove"),
    ("next_to_plate", "black bowl next to the plate"),
    ("on_wooden_cabinet", "black bowl on the wooden cabinet"),
    ("next_to_cookie_box", "black bowl next to the cookie box"),
    ("on_ramekin", "black bowl on the ramekin"),
)

LIBERO_OBJECT = (
    "alphabet_soup",
    "cream_cheese",
    "ketchup",
    "tomato_sauce",
    "butter",
    "milk",
    "orange_juice",
    "bbq_sauce",
    "salad_dressing",
    "chocolate_pudding",
)

LIBERO_GOAL = (
    ("open_middle_drawer", "Open the middle drawer of the cabinet", "drawer", ("detect_object", "estimate_pose", "reach", "open_drawer")),
    ("bowl_on_stove", "Put the bowl on the stove", "bowl", PNP),
    ("wine_on_cabinet", "Put the wine bottle on top of the cabinet", "bottle", PNP),
    ("bowl_in_top_drawer", "Open the top drawer and put the bowl inside", "bowl", PNP + ("open_drawer",)),
    ("bowl_on_cabinet", "Put the bowl on top of the cabinet", "bowl", PNP),
    ("push_plate_stove", "Push the plate to the front of the stove", "plate", ("detect_object", "estimate_pose", "reach", "orient")),
    ("cream_cheese_in_bowl", "Put the cream cheese in the bowl", "food", PNP),
    ("turn_on_stove", "Turn on the stove", "stove", ("detect_object", "reach", "press_button")),
    ("bowl_on_plate", "Put the bowl on the plate", "bowl", PNP),
    ("wine_on_rack", "Put the wine bottle on the rack", "bottle", PNP),
)

LIBERO_LONG = (
    ("soup_and_tomato_in_basket", "Put alphabet soup and tomato sauce in the basket", "grocery"),
    ("cream_cheese_and_butter", "Put cream cheese box and butter in the basket", "grocery"),
    ("stove_and_moka", "Turn on the stove and put the moka pot on it", "pot"),
    ("bowl_in_bottom_drawer", "Put the black bowl in the bottom drawer and close it", "bowl"),
    ("two_mugs_on_plates", "Put the white mug on the left plate and the yellow-and-white mug on the right plate", "mug"),
    ("book_in_caddy", "Pick up the book and place it in the back compartment of the caddy", "book"),
    ("mug_and_pudding", "Put the white mug on the plate and the chocolate pudding to the right of the plate", "mug"),
    ("soup_and_cream_cheese", "Put alphabet soup and cream cheese box in the basket", "grocery"),
    ("both_moka_pots", "Put both moka pots on the stove", "pot"),
    ("mug_in_microwave", "Put the yellow-and-white mug in the microwave and close it", "mug"),
)

ROBOCASA_ATOMIC = (
    ("pick_place_counter", "Pick and place an object on the kitchen counter", "kitchen_object", PNP),
    ("open_drawer", "Open a kitchen drawer", "drawer", ("detect_object", "estimate_pose", "reach", "grasp", "open_drawer")),
    ("close_drawer", "Close a kitchen drawer", "drawer", ("detect_object", "reach", "close_drawer")),
    ("open_door", "Open a cabinet or appliance door", "door", ("detect_object", "estimate_pose", "reach", "grasp", "open_door")),
    ("close_door", "Close a cabinet or appliance door", "door", ("detect_object", "reach", "close_door")),
    ("turn_on_sink", "Turn on the sink faucet", "faucet", ("detect_object", "reach", "press_button")),
    ("turn_off_sink", "Turn off the sink faucet", "faucet", ("detect_object", "reach", "press_button")),
    ("turn_sink_spout", "Turn the sink spout", "faucet", ("detect_object", "reach", "orient")),
    ("turn_on_stove", "Turn on the stove", "stove", ("detect_object", "reach", "press_button")),
    ("turn_off_stove", "Turn off the stove", "stove", ("detect_object", "reach", "press_button")),
    ("coffee_press_button", "Press the coffee-machine button", "coffee_machine", ("detect_object", "reach", "press_button")),
    ("coffee_serve_mug", "Serve a mug from the coffee machine", "mug", PNP),
    ("coffee_setup_mug", "Place a mug under the coffee machine", "mug", PNP),
    ("turn_on_microwave", "Turn on the microwave", "microwave", ("detect_object", "reach", "press_button")),
    ("turn_off_microwave", "Turn off the microwave", "microwave", ("detect_object", "reach", "press_button")),
    ("pnp_counter_to_cab", "Pick from counter and place in cabinet", "kitchen_object", PNP + ("open_door",)),
    ("pnp_cab_to_counter", "Pick from cabinet and place on counter", "kitchen_object", PNP + ("open_door",)),
    ("pnp_counter_to_sink", "Pick from counter and place in sink", "kitchen_object", PNP),
    ("pnp_sink_to_counter", "Pick from sink and place on counter", "kitchen_object", PNP),
    ("pnp_counter_to_stove", "Pick from counter and place on stove", "cookware", PNP),
    ("pnp_stove_to_counter", "Pick from stove and place on counter", "cookware", PNP),
    ("pnp_counter_to_microwave", "Pick from counter and place in microwave", "food", PNP + ("open_door", "close_door")),
    ("pnp_microwave_to_counter", "Pick from microwave and place on counter", "food", PNP + ("open_door",)),
    ("open_single_door", "Open a single kitchen door", "door", ("detect_object", "reach", "open_door")),
    ("close_single_door", "Close a single kitchen door", "door", ("detect_object", "reach", "close_door")),
)

ROBOCASA_COMPOSITE = (
    "prepare_coffee",
    "heat_food_in_microwave",
    "store_leftovers_in_cabinet",
    "wash_mug_in_sink",
    "set_mug_on_dining_counter",
    "restock_condiments_from_cabinet",
    "move_cookware_stove_to_sink",
    "clear_counter_to_cabinet",
    "place_ingredients_on_cutting_board",
    "load_dishwasher_rack",
    "unload_dishwasher_to_cabinet",
    "fill_kettle_at_sink",
    "set_table_with_bowl_and_cup",
    "put_groceries_away",
    "wipe_and_clear_prep_counter",
)

OXE_DATASETS = (
    ("bridge_v2_pick_place", "BridgeData V2 pick-and-place", "household_object", "home", PNP, "bridge_v2"),
    ("bridge_v2_drawer", "BridgeData V2 drawer manipulation", "drawer", "home", PNP + ("open_drawer", "close_drawer"), "bridge_v2"),
    ("fractal_rt1_kitchen", "RT-1 / Fractal kitchen manipulation", "kitchen_object", "kitchen", KITCHEN, "fractal"),
    ("kuka_bin_pick", "KUKA OXE bin picking", "part", "factory", PNP, "kuka"),
    ("taco_play_table", "TACO Play tabletop manipulation", "tabletop_object", "lab", PNP, "taco_play"),
    ("jaco_play_kitchen", "Jaco Play kitchen pick-and-place", "kitchen_object", "kitchen", PNP, "jaco_play"),
    ("berkeley_cable_routing", "Berkeley cable routing", "cable", "lab", ("detect_object", "estimate_pose", "reach", "grasp", "insert"), "berkeley_cable_routing"),
    ("roboturk_pick", "RoboTurk pick-and-place", "object", "lab", PNP, "roboturk"),
    ("nyu_door_open", "NYU door opening", "door", "home", ("detect_object", "estimate_pose", "reach", "grasp", "open_door"), "nyu_door"),
    ("viola_tabletop", "VIOLA tabletop skills", "object", "lab", PNP, "viola"),
    ("berkeley_autolab_ur5", "Berkeley AUTOLAB UR5 manipulation", "object", "lab", PNP, "berkeley_autolab_ur5"),
    ("toto_pick", "TOTO pick tasks", "object", "lab", PNP, "toto"),
    ("language_table", "Language-Table rearrangement", "block", "lab", ("detect_object", "reach", "orient", "place"), "language_table"),
    ("columbia_pusht", "Push-T planar pushing", "t_block", "lab", ("detect_object", "estimate_pose", "reach"), "pusht"),
    ("stanford_hydra", "Stanford HYDRA manipulation", "object", "lab", PNP, "stanford_hydra"),
    ("austin_buds", "Austin BUDS household skills", "household_object", "home", PNP, "austin_buds"),
    ("nyu_franka_play", "NYU Franka Play", "toy", "lab", PNP, "nyu_franka_play"),
    ("furniture_bench", "FurnitureBench assembly", "furniture_part", "lab", PNP + ("insert",), "furniture_bench"),
    ("ucsd_kitchen", "UCSD kitchen manipulation", "kitchen_object", "kitchen", KITCHEN, "ucsd_kitchen"),
    ("austin_sailor", "Austin SAILOR mobile manipulation", "object", "home", PNP + ("base_nav",), "austin_sailor"),
    ("bc_z_google", "BC-Z Google robot skills", "household_object", "home", PNP, "bc_z"),
    ("droid_diverse", "DROID diverse real-world manipulation", "object", "lab", PNP, "droid"),
    ("cmu_playing", "CMU play manipulation", "object", "lab", PNP, "cmu_playing"),
    ("utaustin_mutex", "UT Austin MUTEX multi-task", "object", "lab", PNP, "utaustin_mutex"),
)

LEROBOT = (
    ("aloha_static_coffee", "ALOHA static coffee making", "mug", "kitchen", KITCHEN, "aloha", 2),
    ("aloha_static_candy", "ALOHA candy wrapping / transfer", "small_object", "tabletop", BIMANUAL, "aloha", 2),
    ("aloha_static_towel", "ALOHA towel folding", "cloth", "tabletop", ("detect_object", "grasp", "fold", "place"), "aloha", 2),
    ("aloha_mobile_cabinet", "ALOHA mobile cabinet pick", "object", "home", PNP + ("base_nav",), "aloha_mobile", 2),
    ("aloha_mobile_chair", "ALOHA mobile chair interaction", "chair", "home", PNP + ("base_nav",), "aloha_mobile", 2),
    ("so100_pick_place", "SO-100 LeRobot pick-and-place", "object", "tabletop", PNP, "so100", 1),
    ("so100_folding", "SO-100 cloth folding", "cloth", "tabletop", ("detect_object", "grasp", "fold"), "so100", 1),
    ("pusht_lerobot", "LeRobot Push-T", "t_block", "lab", ("detect_object", "estimate_pose", "reach"), "pusht_env", 1),
    ("unitree_g1_pick", "Unitree G1 pick demonstration (LeRobot)", "object", "lab", PNP + ("humanoid_walk",), "humanoid", 2),
    ("stretch_pick", "Hello Robot Stretch pick-and-place", "object", "home", PNP + ("base_nav",), "stretch", 1),
    ("koch_pick", "Koch v1.1 pick-and-place", "object", "tabletop", PNP, "koch", 1),
    ("omx_pick", "OMX LeRobot pick", "object", "tabletop", PNP, "omx", 1),
)

ROBOTWIN = (
    ("handover_block", "Bimanual block handover", "block", BIMANUAL),
    ("stack_blocks", "Bimanual block stacking", "block", PNP),
    ("insert_peg", "Peg-in-hole insertion", "peg", PNP + ("insert",)),
    ("open_pot", "Open a pot with two arms", "pot", BIMANUAL),
    ("beat_block_hammer", "Hammer a block", "hammer", ("detect_object", "grasp", "orient", "reach")),
    ("place_container_plate", "Place container on plate", "container", PNP),
    ("scan_object", "Scan and reorient an object", "object", PNP),
    ("lift_pot", "Lift a pot bimanually", "pot", BIMANUAL),
    ("handover_mic", "Handover a microphone", "microphone", BIMANUAL),
    ("stack_bowls", "Stack bowls", "bowl", PNP),
    ("pick_dual_bottles", "Pick two bottles (dual arm)", "bottle", BIMANUAL),
    ("put_object_cabinet", "Put object into cabinet", "object", PNP + ("open_door",)),
    ("move_can_pot", "Move can into pot", "can", PNP),
    ("hang_object", "Hang an object", "object", PNP),
    ("press_stapler", "Press a stapler", "stapler", ("detect_object", "reach", "press_button")),
)

BEHAVIOR1K: tuple[tuple[str, ...], ...] = (
    ("wash_dishes", "Wash dishes", "dish", "kitchen", PNP + ("wipe",)),
    ("load_dishwasher", "Load the dishwasher", "dish", "kitchen", PNP + ("open_door",)),
    ("unload_dishwasher", "Unload the dishwasher", "dish", "kitchen", PNP + ("open_door",)),
    ("fold_laundry", "Fold laundry", "cloth", "home", ("detect_object", "grasp", "fold", "place")),
    ("make_bed", "Make the bed", "cloth", "bedroom", ("grasp", "fold", "place")),
    ("vacuum_floor", "Vacuum the floor", "floor", "home", ("wipe", "base_nav")),
    ("mop_floor", "Mop the floor", "floor", "home", ("wipe", "base_nav")),
    ("dust_furniture", "Dust furniture", "furniture", "home", ("reach", "wipe")),
    ("set_table", "Set the table", "tableware", "dining", PNP),
    ("clear_table", "Clear the table", "tableware", "dining", PNP),
    ("store_groceries", "Store groceries", "grocery", "kitchen", PNP + ("open_door",)),
    ("take_out_trash", "Take out the trash", "bag", "home", PNP + ("base_nav",)),
    ("water_plants", "Water plants", "plant", "home", ("grasp", "pour")),
    ("wipe_counters", "Wipe kitchen counters", "counter", "kitchen", ("reach", "wipe")),
    ("sort_laundry", "Sort laundry", "cloth", "home", PNP),
    ("hang_clothes", "Hang clothes", "cloth", "home", ("grasp", "place")),
    ("pick_up_toys", "Pick up toys", "toy", "home", PNP),
    ("organize_closet", "Organize a closet", "clothing", "home", PNP + ("open_door",)),
    ("clean_bathroom", "Clean the bathroom", "bathroom", "home", ("wipe", "base_nav")),
    ("cook_simple_meal", "Cook a simple meal", "food", "kitchen", KITCHEN + ("pour",)),
    ("pour_drink", "Pour a drink", "cup", "kitchen", ("grasp", "pour", "place")),
    ("open_fridge", "Open the refrigerator", "fridge", "kitchen", ("open_door",)),
    ("put_leftovers_away", "Put leftovers away", "food", "kitchen", PNP + ("open_door",)),
    ("make_coffee", "Make coffee", "mug", "kitchen", KITCHEN + ("pour",)),
    ("wipe_table", "Wipe the dining table", "table", "dining", ("wipe",)),
    ("sweep_floor", "Sweep the floor", "floor", "home", ("wipe", "base_nav")),
    ("bring_object", "Bring an object to a person", "object", "home", PNP + ("handover", "base_nav")),
    ("throw_away_object", "Throw an object in the trash", "object", "home", PNP),
    ("slice_food", "Slice food (sim)", "food", "kitchen", ("grasp", "orient")),
    ("serve_food", "Serve food to the table", "plate", "dining", PNP),
    ("collect_mail", "Collect mail", "mail", "home", PNP + ("base_nav",)),
    ("turn_off_lights", "Turn off lights", "switch", "home", ("press_button",)),
    ("put_books_on_shelf", "Put books on a shelf", "book", "home", PNP),
    ("fold_towel", "Fold a towel", "cloth", "home", ("grasp", "fold", "place")),
    ("wash_hands_setup", "Set up soap and towel at a sink", "soap", "bathroom", PNP),
    ("relocate_chair", "Relocate a chair", "chair", "home", ("grasp", "base_nav")),
    ("close_window", "Close a window", "window", "home", ("reach", "close_door")),
    ("wipe_mirror", "Wipe a mirror", "mirror", "bathroom", ("wipe",)),
    ("sort_recycling", "Sort recycling", "bottle", "home", PNP),
    ("pack_bag", "Pack a bag", "object", "home", PNP),
    ("unpack_bag", "Unpack a bag", "object", "home", PNP),
    ("load_washer", "Load a washing machine", "cloth", "home", PNP + ("open_door",)),
    ("unload_dryer", "Unload a dryer", "cloth", "home", PNP + ("open_door",)),
    ("set_alarm_clock", "Interact with a bedside object", "clock", "bedroom", ("reach", "press_button")),
    ("clean_stove", "Wipe the stove", "stove", "kitchen", ("wipe",)),
    ("put_shoes_away", "Put shoes away", "shoes", "home", PNP),
    ("carry_box", "Carry a box between rooms", "box", "home", PNP + ("base_nav",)),
    ("plug_in_device", "Plug in a device", "plug", "home", ("grasp", "insert")),
    ("tidy_desk", "Tidy a desk", "object", "office", PNP),
    ("water_indoor_plants", "Water indoor plants from a pitcher", "pitcher", "home", ("grasp", "pour")),
)

INDUSTRIAL_SPARSE = (
    (
        "mixed_case_depalletize",
        "Mixed-SKU depalletization onto conveyor",
        "mixed_carton",
        "warehouse",
        ("detect_carton", "estimate_pose", "estimate_grasp", "segment_instance", "reach", "grasp", "lift", "orient", "place", "release"),
        "low",
    ),
    (
        "homogeneous_palletize",
        "Stack uniform cases onto a pallet",
        "carton",
        "warehouse",
        ("detect_carton", "estimate_pose", "estimate_grasp", "reach", "grasp", "lift", "orient", "place", "release"),
        "medium",
    ),
    (
        "bin_pick_mixed",
        "Mixed bin picking",
        "part",
        "factory",
        ("detect_object", "estimate_pose", "estimate_grasp", "segment_instance", "reach", "grasp", "lift", "orient", "place"),
        "medium",
    ),
    (
        "machine_tend_cnc",
        "Load/unload a CNC fixture",
        "workpiece",
        "factory",
        ("detect_object", "estimate_pose", "estimate_grasp", "reach", "grasp", "insert", "release"),
        "low",
    ),
    (
        "trailer_unload_floor",
        "Unload floor-loaded cartons from a trailer",
        "carton",
        "warehouse",
        ("detect_carton", "estimate_pose", "reach", "grasp", "lift", "place"),
        "low",
    ),
    (
        "parcel_sort_induct",
        "Induct parcels onto a sorter",
        "parcel",
        "warehouse",
        ("detect_object", "estimate_pose", "read_label", "reach", "grasp", "place"),
        "low",
    ),
    (
        "kitting_from_bins",
        "Kit parts from bins into a tote",
        "part",
        "factory",
        ("detect_object", "estimate_grasp", "reach", "grasp", "place"),
        "medium",
    ),
    (
        "hospital_linen_cart",
        "Move linen carts in a hospital",
        "cart",
        "hospital",
        ("base_nav",),
        "low",
    ),
)


def build_tasks() -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    libero_models_spatial = ("openvla-7b-libero-spatial", "openvla-7b", "octo-base-1.5", "pi0")
    libero_models_object = ("openvla-7b-libero-object", "openvla-7b", "octo-base-1.5", "pi0")
    libero_models_goal = ("openvla-7b-libero-goal", "openvla-7b", "octo-base-1.5", "pi0.5")
    libero_models_long = ("openvla-7b-libero-long", "openvla-7b", "pi0.5", "gr00t-n1")

    for slug, phrase in LIBERO_SPATIAL:
        tasks.append(
            _task(
                f"libero_spatial_{slug}",
                name=f"Pick up the {phrase} and place it on the plate",
                family="pick_place",
                object_type="bowl",
                environment="kitchen",
                skills=PNP + (("open_drawer",) if "drawer" in slug else ()),
                models=libero_models_spatial,
                training_dataset="LIBERO-Spatial",
                embodiment="libero_sim_arm",
                simulation_verified=True,
                real_world_verified=False,
                source="libero",
                url="https://github.com/Lifelong-Robot-Learning/LIBERO",
                confidence="high",
                commercial_use="permissive",
            )
        )

    for item in LIBERO_OBJECT:
        tasks.append(
            _task(
                f"libero_object_{item}",
                name=f"Pick up the {item.replace('_', ' ')} and place it in the basket",
                family="pick_place",
                object_type=item,
                environment="kitchen",
                skills=PNP,
                models=libero_models_object,
                training_dataset="LIBERO-Object",
                embodiment="libero_sim_arm",
                simulation_verified=True,
                real_world_verified=False,
                source="libero",
                url="https://github.com/Lifelong-Robot-Learning/LIBERO",
                confidence="high",
                commercial_use="permissive",
            )
        )

    for slug, name, obj, skills in LIBERO_GOAL:
        tasks.append(
            _task(
                f"libero_goal_{slug}",
                name=name,
                family="kitchen_manipulation",
                object_type=obj,
                environment="kitchen",
                skills=skills,
                models=libero_models_goal,
                training_dataset="LIBERO-Goal",
                embodiment="libero_sim_arm",
                simulation_verified=True,
                real_world_verified=False,
                source="libero",
                url="https://github.com/Lifelong-Robot-Learning/LIBERO",
                confidence="high",
                commercial_use="permissive",
            )
        )

    for slug, name, obj in LIBERO_LONG:
        tasks.append(
            _task(
                f"libero_long_{slug}",
                name=name,
                family="long_horizon_manipulation",
                object_type=obj,
                environment="kitchen",
                skills=KITCHEN,
                models=libero_models_long,
                training_dataset="LIBERO-Long",
                embodiment="libero_sim_arm",
                simulation_verified=True,
                real_world_verified=False,
                source="libero",
                url="https://github.com/Lifelong-Robot-Learning/LIBERO",
                confidence="high",
                commercial_use="permissive",
            )
        )

    for slug, name, obj, skills in ROBOCASA_ATOMIC:
        tasks.append(
            _task(
                f"robocasa_{slug}",
                name=name,
                family="kitchen_manipulation",
                object_type=obj,
                environment="kitchen",
                skills=skills,
                models=("octo-base-1.5", "openvla-7b", "pi0", "smolvla"),
                training_dataset="RoboCasa",
                embodiment="robocasa_arm",
                simulation_verified=True,
                real_world_verified=False,
                source="robocasa",
                url="https://github.com/robocasa/robocasa",
                confidence="high",
            )
        )

    for slug in ROBOCASA_COMPOSITE:
        tasks.append(
            _task(
                f"robocasa_composite_{slug}",
                name=slug.replace("_", " ").capitalize(),
                family="household_activity",
                object_type="kitchen_object",
                environment="kitchen",
                skills=KITCHEN,
                models=("pi0.5", "openvla-7b", "gr00t-n1", "octo-base-1.5"),
                training_dataset="RoboCasa composite",
                embodiment="robocasa_arm",
                simulation_verified=True,
                real_world_verified=False,
                source="robocasa",
                url="https://github.com/robocasa/robocasa",
                confidence="medium",
            )
        )

    oxe_models = ("openvla-7b", "octo-base-1.5", "pi0", "octo-small-1.5")
    for slug, name, obj, env, skills, dataset in OXE_DATASETS:
        tasks.append(
            _task(
                f"oxe_{slug}",
                name=name,
                family="pick_place" if "place" in skills else "manipulation",
                object_type=obj,
                environment=env,
                skills=skills,
                models=oxe_models,
                training_dataset=f"Open X-Embodiment / {dataset}",
                source="open_x_embodiment",
                url="https://robotics-transformer-x.github.io/",
                real_world_verified=True,
                simulation_verified=False,
                confidence="high",
                commercial_use="unknown",
            )
        )

    for slug, name, obj, env, skills, emb, arms in LEROBOT:
        family = "folding" if "fold" in skills else ("bimanual_manipulation" if arms == 2 else "pick_place")
        tasks.append(
            _task(
                f"lerobot_{slug}",
                name=name,
                family=family,
                object_type=obj,
                environment=env,
                skills=skills,
                models=("smolvla", "act", "diffusion-policy"),
                training_dataset="LeRobot",
                embodiment=emb,
                arm_count=arms,
                source="lerobot",
                url="https://huggingface.co/lerobot",
                real_world_verified=True,
                simulation_verified=True,
                confidence="medium",
                commercial_use="permissive",
            )
        )

    for slug, name, obj, skills in ROBOTWIN:
        tasks.append(
            _task(
                f"robotwin_{slug}",
                name=name,
                family="bimanual_manipulation",
                object_type=obj,
                environment="lab",
                skills=skills,
                models=("act", "pi0.5", "gr00t-n1", "smolvla"),
                training_dataset="RoboTwin",
                embodiment="bimanual_arm",
                arm_count=2,
                source="robotwin",
                url="https://robotwin-platform.github.io/",
                simulation_verified=True,
                real_world_verified=False,
                confidence="medium",
            )
        )

    for slug, name, obj, env, skills in BEHAVIOR1K:
        family = "folding" if "fold" in skills else (
            "household_nav" if "base_nav" in skills and not any(s in MANIPULATION for s in skills) else "household_activity"
        )
        tasks.append(
            _task(
                f"behavior1k_{slug}",
                name=name,
                family=family,
                object_type=obj,
                environment=env,
                skills=skills,
                models=("pi0.5", "gr00t-n1", "openvla-7b", "smolvla"),
                training_dataset="BEHAVIOR-1K (activity ontology; not a claim of full-dataset training)",
                embodiment="humanoid_or_mobile_manipulator",
                arm_count=2,
                source="behavior1k",
                url="https://behavior.stanford.edu/",
                simulation_verified=True,
                real_world_verified=False,
                confidence="medium",
            )
        )

    for slug, name, obj, env, skills, conf in INDUSTRIAL_SPARSE:
        tasks.append(
            _task(
                f"industrial_{slug}",
                name=name,
                family=slug,
                object_type=obj,
                environment=env,
                skills=skills,
                models=("pi0.5", "openvla-7b", "gr00t-n1", "octo-base-1.5"),
                training_dataset=None,
                trajectory_count=None,
                embodiment="industrial_arm" if env != "hospital" else "amr",
                source="sparse_industrial",
                simulation_verified=False,
                real_world_verified=False,
                confidence=conf,
                commercial_use="unknown",
            )
        )

    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for task in tasks:
        tid = task["task_id"]
        if tid in seen:
            continue
        seen.add(tid)
        out.append(task)
    return out


def build_registry() -> dict[str, Any]:
    tasks = build_tasks()
    return {
        "registry_id": "rfr_robot_task_registry_v1",
        "version": "1.0.0",
        "product_term": "trained_task",
        "honesty": (
            "Catalog of public trained robot tasks and associated models. "
            "Does not assert that a candidate robot SKU has these weights. "
            "Chat LLMs are not warehouse, hospital, or CNC policies."
        ),
        "chain": [
            "JOB",
            "work_units",
            "required_physical_skills",
            "learned_policies",
            "compatible_embodiments",
            "compatible_robots",
            "vendors",
        ],
        "scores": {
            "hardware_fit": "Can this embodiment physically perform the job?",
            "intelligence_fit": "Do existing trained tasks/policies cover the job's skills?",
            "environment_fit": "Do trained-task environments overlap the workplace?",
            "deployment_readiness": "hardware_fit × intelligence_fit × environment_fit",
        },
        "models": list(MODELS.values()),
        "tasks": tasks,
        "task_count": len(tasks),
        "sources": [
            {"id": "lerobot", "name": "Hugging Face LeRobot", "url": "https://huggingface.co/lerobot"},
            {"id": "openvla", "name": "OpenVLA", "url": "https://github.com/openvla/openvla"},
            {"id": "octo", "name": "Octo", "url": "https://github.com/octo-models/octo"},
            {"id": "open_x_embodiment", "name": "Open X-Embodiment", "url": "https://robotics-transformer-x.github.io/"},
            {"id": "physical_intelligence", "name": "Physical Intelligence π₀ / π₀.₅", "url": "https://www.physicalintelligence.company/"},
            {"id": "nvidia", "name": "NVIDIA GR00T", "url": "https://developer.nvidia.com/isaac/gr00t"},
            {"id": "libero", "name": "LIBERO", "url": "https://github.com/Lifelong-Robot-Learning/LIBERO"},
            {"id": "robocasa", "name": "RoboCasa", "url": "https://github.com/robocasa/robocasa"},
            {"id": "robotwin", "name": "RoboTwin", "url": "https://robotwin-platform.github.io/"},
            {"id": "behavior1k", "name": "BEHAVIOR-1K", "url": "https://behavior.stanford.edu/"},
        ],
    }
