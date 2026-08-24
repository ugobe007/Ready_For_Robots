"""Hardware Fit vs Intelligence Fit for Robot Jobs.

Hardware Fit — can this embodiment physically do the work (requirement states).
Intelligence Fit — do public trained tasks/policies cover the job's skills.
Environment Fit — overlap between the workplace and trained-task environments.

Deployment readiness = hardware × intelligence × environment.

Does not assert that a candidate SKU has OpenVLA / π₀ / GR00T weights.
Task-model presence stays unknown until evidence names a checkpoint on the robot.
No generic match `score` — the categorical verdict remains the gate.
"""
from __future__ import annotations

import math
from functools import lru_cache
from typing import Any, Iterable

from app.services.robot_task_registry_catalog import (
    MANIPULATION,
    MOBILITY,
    MODELS,
    PERCEPTION,
    PNP,
    build_registry,
)

_STATE_WEIGHT = {
    "MATCHED": 1.0,
    "LIKELY": 0.72,
    "UNKNOWN": 0.38,
    "UNMET": 0.0,
}

_ENV_RELATED: dict[str, frozenset[str]] = {
    "warehouse": frozenset({"warehouse", "factory", "lab"}),
    "factory": frozenset({"factory", "warehouse", "lab"}),
    "kitchen": frozenset({"kitchen", "home", "dining", "lab"}),
    "home": frozenset({"home", "kitchen", "bedroom", "dining", "bathroom", "lab"}),
    "hospital": frozenset({"hospital", "home"}),
    "lab": frozenset({"lab", "factory", "home"}),
    "office": frozenset({"office", "home", "lab"}),
}

_SPARSE_FAMILIES = frozenset(
    {
        "mixed_case_depalletize",
        "machine_tend_cnc",
        "trailer_unload_floor",
        "hospital_linen_cart",
        "parcel_sort_induct",
    }
)

_WAREHOUSE_TOKS = (
    "warehouse", "pallet", "carton", "case", "sku", "conveyor", "depal",
    "palletiz", "dock", "trailer", "tote", "fulfillment",
)
_HOSPITAL_TOKS = ("hospital", "clinic", "linen", "patient", "nursing", "or suite")
_KITCHEN_TOKS = ("kitchen", "food", "dish", "mug", "stove", "coffee")
_FACTORY_TOKS = ("cnc", "machine tend", "fixture", "workpiece", "kitting")
_FOLD_TOKS = ("fold", "laundry", "linen", "towel")


@lru_cache(maxsize=1)
def trained_task_registry() -> dict[str, Any]:
    return build_registry()


def _hay(*parts: str) -> str:
    return " ".join(p for p in parts if p).lower()


def _band(n: int) -> str:
    if n >= 12:
        return "HIGH"
    if n >= 4:
        return "MEDIUM"
    if n >= 1:
        return "LOW"
    return "NONE"


def _band_score(band: str) -> float:
    return {"HIGH": 1.0, "MEDIUM": 0.55, "LOW": 0.22, "NONE": 0.05}.get(band, 0.05)


def job_work_profile(
    *,
    title: str = "",
    industry: str = "",
    path: str = "",
    text: str = "",
    tape_family: str = "",
) -> dict[str, Any]:
    hay = _hay(title, industry, path, text, tape_family)
    tape = (tape_family or "").lower()
    skills: set[str] = set(PNP)
    mobility = {"stationary"}
    families = ["pick_place"]
    environment = "lab"
    objects = ["object"]

    if any(tok in hay for tok in _WAREHOUSE_TOKS) or tape in {"pallet", "gripper"}:
        environment = "warehouse"
        objects = ["carton"]
        skills.update({"detect_carton", "estimate_pose", "estimate_grasp"})
    if any(tok in hay for tok in _HOSPITAL_TOKS):
        environment = "hospital"
        mobility = {"base_nav"}
        families = ["hospital_linen_cart"]
        skills = {"base_nav"}
        objects = ["cart"]
    if any(tok in hay for tok in _KITCHEN_TOKS) and environment != "warehouse":
        environment = "kitchen"
        families = ["kitchen_manipulation", "pick_place"]
        skills.update({"open_drawer", "open_door", "press_button"})
    if any(tok in hay for tok in _FACTORY_TOKS):
        environment = "factory"
        families = ["machine_tend_cnc", "pick_place"]
        skills.update({"insert"})
        objects = ["workpiece"]
    if any(tok in hay for tok in _FOLD_TOKS) and environment != "hospital":
        families = list(dict.fromkeys(["folding", *families]))
        skills.add("fold")
        objects = ["cloth"]

    if "mixed" in hay or "depal" in hay or "depallet" in hay:
        families = list(
            dict.fromkeys(
                ["mixed_case_depalletize", "pick_place", "homogeneous_palletize", *families]
            )
        )
        skills.update({"detect_carton", "segment_instance", "orient"})
        objects = ["mixed_carton"]
    elif "pallet" in hay or tape == "pallet":
        families = list(dict.fromkeys(["homogeneous_palletize", "pick_place", *families]))
    if "bin" in hay and "pick" in hay:
        families = list(dict.fromkeys(["bin_pick_mixed", "pick_place", *families]))
    if "bimanual" in hay or "dual-arm" in hay or "two arm" in hay:
        families = list(dict.fromkeys(["bimanual_manipulation", *families]))
        skills.add("handover")

    perception = tuple(s for s in skills if s in PERCEPTION)
    manipulation = tuple(s for s in skills if s in MANIPULATION)
    mobility_t = tuple(s for s in (skills | mobility) if s in MOBILITY) or ("stationary",)
    return {
        "environment": environment,
        "object_types": objects,
        "task_families": families,
        "required_perception": list(perception),
        "required_manipulation": list(manipulation),
        "required_mobility": list(mobility_t),
        "required_skills": list(perception) + list(manipulation) + list(mobility_t),
    }


def _state(row: Any) -> str:
    if isinstance(row, dict):
        return str(row.get("state") or "")
    return str(getattr(row, "state", "") or "")


def _necessity(row: Any) -> str:
    if isinstance(row, dict):
        return str(row.get("necessity") or "")
    return str(getattr(row, "necessity", "") or "")


def hardware_fit(requirements: Iterable[Any]) -> float:
    reqs = [r for r in requirements if _necessity(r) == "required"]
    if not reqs:
        return 0.5
    total = sum(_STATE_WEIGHT.get(_state(r), 0.38) for r in reqs)
    return round(total / len(reqs), 4)


def _task_skills(task: dict[str, Any]) -> set[str]:
    return (
        set(task.get("required_perception") or [])
        | set(task.get("required_manipulation") or [])
        | set(task.get("required_mobility") or [])
    )


def _env_score(job_env: str, task_envs: list[str]) -> float:
    if not task_envs:
        return 0.35
    related = _ENV_RELATED.get(job_env, frozenset({job_env}))
    exact = sum(1 for env in task_envs if env == job_env)
    near = sum(1 for env in task_envs if env in related)
    n = len(task_envs)
    return round(min(1.0, (exact + 0.45 * max(near - exact, 0)) / n + 0.12), 4)


def _embodiment_compatible(model: dict[str, Any], robot_classes: set[str]) -> str:
    if not robot_classes:
        return "unknown"
    classes = {c.lower() for c in robot_classes}
    embs = {str(e).lower() for e in (model.get("robot_embodiments") or [])}
    arms = model.get("arm_count") or 1
    manip = bool(
        classes
        & {"manipulator", "cobot", "arm", "humanoid", "mobile_manipulator", "dual_arm"}
    )
    humanoid = "humanoid" in classes
    amr_only = bool(classes & {"amr", "mobile", "tugger", "forklift"}) and not manip
    if amr_only and arms and not (embs & {"amr", "stretch"}):
        return "mismatch"
    if humanoid and ("humanoid" in embs or "humanoid" in " ".join(embs)):
        return "plausible"
    if manip:
        return "plausible"
    return "unknown"


def intelligence_fit_for_job(
    *,
    title: str = "",
    industry: str = "",
    path: str = "",
    text: str = "",
    tape_family: str = "",
    requirements: Iterable[Any] = (),
    robot_classes: Iterable[str] = (),
) -> dict[str, Any]:
    registry = trained_task_registry()
    tasks: list[dict[str, Any]] = list(registry.get("tasks") or [])
    models_by_id = {m["id"]: m for m in (registry.get("models") or [])} or dict(MODELS)
    profile = job_work_profile(
        title=title,
        industry=industry,
        path=path,
        text=text,
        tape_family=tape_family,
    )
    required_skills: list[str] = profile["required_skills"]
    job_env = profile["environment"]
    classes = {str(c).lower() for c in robot_classes}

    skill_bands: dict[str, str] = {}
    skill_scores: list[float] = []
    for skill in required_skills:
        n = sum(1 for task in tasks if skill in _task_skills(task))
        band = _band(n)
        skill_bands[skill] = band
        skill_scores.append(_band_score(band))
    intelligence = sum(skill_scores) / len(skill_scores) if skill_scores else 0.2

    family_coverage: list[dict[str, Any]] = []
    family_scores: list[float] = []
    for fam in profile["task_families"]:
        n = sum(1 for task in tasks if (task.get("task_family") or "") == fam)
        if fam == "pick_place":
            n = max(
                n,
                sum(1 for task in tasks if "place" in (task.get("required_manipulation") or [])),
            )
        band = _band(n)
        if fam in _SPARSE_FAMILIES:
            band = "LOW" if n >= 1 else "NONE"
        family_coverage.append(
            {"task_family": fam, "coverage": band, "trained_task_count": n}
        )
        family_scores.append(_band_score(band))
    if family_scores:
        family_mean = sum(family_scores) / len(family_scores)
        # Sparse industrial jobs (mixed-case depalletize, CNC tend, …) should not
        # inherit a kitchen pick-place HIGH as if the policy already existed.
        weight = 0.5 if any(f in _SPARSE_FAMILIES for f in profile["task_families"]) else 0.38
        intelligence = round((1.0 - weight) * intelligence + weight * family_mean, 4)
    else:
        intelligence = round(intelligence, 4)

    covering = [
        task
        for task in tasks
        if len(_task_skills(task) & set(required_skills))
        >= max(2, len(required_skills) // 4)
    ]
    environment = _env_score(
        job_env,
        [str(task.get("environment") or "") for task in covering or tasks[:40]],
    )

    hw = hardware_fit(requirements)
    readiness = round(hw * intelligence * environment, 4)

    model_scores: list[dict[str, Any]] = []
    for mid, model in models_by_id.items():
        owned = [task for task in tasks if mid in (task.get("model_ids") or [])]
        if not owned:
            continue
        covered = {skill for task in owned for skill in _task_skills(task)}
        skill_frac = (
            len(covered & set(required_skills)) / len(required_skills)
            if required_skills
            else 0.0
        )
        env_s = _env_score(
            job_env, [str(task.get("environment") or "") for task in owned]
        )
        traj = model.get("trajectory_count") or 0
        traj_boost = min(1.0, math.log10(1 + traj) / 6.0) if traj else 0.2
        coverage = round(0.62 * skill_frac + 0.25 * env_s + 0.13 * traj_boost, 4)
        if coverage < 0.12:
            continue
        model_scores.append(
            {
                "model_id": mid,
                "model_name": model.get("name"),
                "model_family": model.get("family"),
                "url": model.get("url"),
                "coverage": coverage,
                "trajectory_count": traj or None,
                "embodiment_compatible": _embodiment_compatible(model, classes),
                "zero_shot_capable": model.get("zero_shot_capable"),
                "fine_tuning_required": model.get("fine_tuning_required"),
                "license": model.get("license"),
                "commercial_use": model.get("commercial_use"),
                "note": (
                    "Coverage of this job's skills by public trained tasks — "
                    "not evidence this SKU loads these weights."
                ),
            }
        )
    model_scores.sort(key=lambda row: (-row["coverage"], row["model_name"] or ""))
    model_scores = model_scores[:8]

    return {
        "hardware_fit": hw,
        "intelligence_fit": intelligence,
        "environment_fit": environment,
        "deployment_readiness": readiness,
        "formula": "hardware_fit × intelligence_fit × environment_fit",
        "honesty": (
            "Intelligence Fit is trained-task coverage, not a claim this robot has "
            "OpenVLA, π₀, Octo, or GR00T installed. Task-model presence stays unknown."
        ),
        "work_units": {
            "environment": job_env,
            "object_types": profile["object_types"],
            "task_families": profile["task_families"],
            "required_perception": profile["required_perception"],
            "required_manipulation": profile["required_manipulation"],
            "required_mobility": profile["required_mobility"],
        },
        "skill_coverage": skill_bands,
        "task_coverage": family_coverage,
        "model_matches": model_scores,
        "registry_task_count": registry.get("task_count") or len(tasks),
        "chain": registry.get("chain") or [],
    }
