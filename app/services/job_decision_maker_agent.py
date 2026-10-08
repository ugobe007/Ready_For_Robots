"""Job-aware decision-maker agent for operator sales cards.

Maps a Robot Job (work + workplace) to the titles that actually own that work,
then scores real Hunter.io people against those titles.

FIND does not call this. Names are never invented. A miss is valid.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Optional

from app.services.robot_job_extract import job_function_from_title

DEFAULT_TITLES = [
    "Director of Operations",
    "VP Operations",
    "Site Operations Manager",
    "Head of Automation",
]

TITLES_BY_FUNCTION: dict[str, list[str]] = {
    "pharmacy": [
        "Director of Pharmacy",
        "Pharmacy Operations Manager",
        "Director of Pharmacy Operations",
        "Director of Materials Management",
        "Director of Support Services",
    ],
    "patient_transport": [
        "Director of Patient Transport",
        "Director of Support Services",
        "Director of Patient Experience",
        "Nurse Manager",
    ],
    "environmental_services": [
        "Director of Environmental Services",
        "Director of EVS",
        "EVS Manager",
        "Director of Facilities",
        "Director of Facilities Operations",
    ],
    "housekeeping": [
        "Director of Housekeeping",
        "Director of Rooms Operations",
        "Director of Facilities",
        "General Manager",
    ],
    "material_handling": [
        "Director of Warehouse Operations",
        "Warehouse Operations Manager",
        "Distribution Center Manager",
        "Site Operations Manager",
        "VP Supply Chain",
    ],
    "picking": [
        "Director of Warehouse Operations",
        "Fulfillment Operations Manager",
        "VP Fulfillment",
        "Site Operations Manager",
    ],
    "packing": [
        "Packaging Manager",
        "Director of Warehouse Operations",
        "Plant Manager",
        "Site Operations Manager",
    ],
    "palletizing": [
        "Plant Manager",
        "Packaging Manager",
        "Warehouse Operations Manager",
        "Director of Operations",
    ],
    "receiving": [
        "Receiving Manager",
        "Warehouse Operations Manager",
        "Director of Warehouse Operations",
        "Dock Supervisor",
    ],
    "shipping": [
        "Shipping Manager",
        "Warehouse Operations Manager",
        "Director of Warehouse Operations",
        "Dock Supervisor",
    ],
    "food_prep": [
        "Director of Culinary Operations",
        "Kitchen Operations Manager",
        "Director of Restaurant Operations",
        "VP Restaurant Operations",
    ],
    "serving": [
        "Director of Food and Beverage",
        "Restaurant General Manager",
        "VP Restaurant Operations",
        "Director of Operations",
    ],
    "machine_tending": [
        "Plant Manager",
        "Director of Manufacturing",
        "Director of Automation",
        "Manufacturing Operations Manager",
    ],
    "facade_cleaning": [
        "Director of Facilities",
        "Property Operations Manager",
        "Director of Building Operations",
    ],
    "laundry": [
        "Director of Laundry",
        "Director of Support Services",
        "Director of Environmental Services",
    ],
}

ACTION_TO_FUNCTION = {
    "pallet_move": "material_handling",
    "pallet": "palletizing",
    "delivery": "material_handling",
    "assembly": "food_prep",
    "scrub": "environmental_services",
    "clean": "environmental_services",
    "inspect": "machine_tending",
    "transport": "material_handling",
    "unload": "material_handling",
    "replenishment": "material_handling",
    "warewash": "food_prep",
}

KEYWORD_FUNCTION = (
    ("pharmac", "pharmacy"),
    ("medication", "pharmacy"),
    ("evs", "environmental_services"),
    ("environmental service", "environmental_services"),
    ("floor scrub", "environmental_services"),
    ("auto-scrub", "environmental_services"),
    ("autoscrub", "environmental_services"),
    ("concourse", "environmental_services"),
    ("terminal floor", "environmental_services"),
    ("cnc", "machine_tending"),
    ("laser", "machine_tending"),
    ("plasma", "machine_tending"),
    ("machine tend", "machine_tending"),
    ("bowl assembl", "food_prep"),
    ("kitchen", "food_prep"),
    ("culinary", "food_prep"),
    ("trailer", "material_handling"),
    ("dock", "material_handling"),
    ("tote", "material_handling"),
    ("warehouse", "material_handling"),
    ("patient transport", "patient_transport"),
)

DISTINCTIVE_TOKENS: dict[str, tuple[str, ...]] = {
    "pharmacy": ("pharmacy", "medication", "pharma", "materials management"),
    "patient_transport": ("patient transport", "support services", "patient experience"),
    "environmental_services": (
        "evs",
        "environmental",
        "facilit",
        "custodial",
        "janitor",
        "housekeep",
        "property operations",
        "building operations",
    ),
    "housekeeping": ("housekeep", "rooms", "facilit"),
    "material_handling": (
        "warehouse",
        "distribution",
        "fulfillment",
        "dock",
        "logistics",
        "supply chain",
        "site operations",
    ),
    "picking": ("warehouse", "fulfillment", "distribution"),
    "packing": ("packaging", "warehouse", "plant"),
    "palletizing": ("plant", "packaging", "warehouse", "pallet"),
    "receiving": ("receiving", "warehouse", "dock"),
    "shipping": ("shipping", "warehouse", "dock"),
    "food_prep": ("culinary", "kitchen", "restaurant", "food and beverage", "food & beverage"),
    "serving": ("food and beverage", "food & beverage", "restaurant", "hospitality"),
    "machine_tending": ("plant", "manufactur", "cnc", "automation", "production", "maintenance"),
    "facade_cleaning": ("facilit", "property", "building operations"),
    "laundry": ("laundry", "support services", "evs"),
}

PENALTY_TOKENS = (
    "chief development",
    "fundraising",
    "philanthrop",
    "marketing",
    "communications",
    "public relations",
    "recruiter",
    "talent acquisition",
    "human resources",
    "counsel",
    "attorney",
    "general counsel",
    "investor",
    "board member",
    "security",
)
JUNIOR_TOKENS = (
    "technician",
    "assistant",
    "intern",
    "clerk",
    "aide",
    "trainee",
    "student",
    "associate",
    "coordinator",
    "specialist",
)
SENIORITY_TOKENS = (
    "director",
    "vp",
    "vice president",
    "manager",
    "head",
    "chief",
    "supervisor",
    "lead",
)

MIN_ACCEPT_SCORE = 24
STRONG_TITLE_SCORE = 36


@dataclass
class DecisionMakerPlan:
    function: str
    titles: list[str]
    departments: str
    tokens: tuple[str, ...] = field(default_factory=tuple)


def _get(row: Any, *names: str) -> str:
    if isinstance(row, dict):
        for name in names:
            val = row.get(name)
            if val:
                return str(val).strip()
        return ""
    for name in names:
        val = getattr(row, name, None)
        if val:
            return str(val).strip()
    return ""


def job_text(row: Any) -> str:
    return " ".join(
        part
        for part in (
            _get(row, "action"),
            _get(row, "robot_compatible_task", "title"),
            _get(row, "observed_workflow", "description"),
            _get(row, "why_job"),
            _get(row, "target"),
            _get(row, "operating_context"),
            _get(row, "worksite_label"),
            _get(row, "industry"),
        )
        if part
    )


def function_for_job(row: Any) -> str:
    blob = job_text(row).lower()
    for needle, function in KEYWORD_FUNCTION:
        if needle in blob:
            return function
    action = _get(row, "action").lower().replace(" ", "_")
    if action in TITLES_BY_FUNCTION:
        return action
    from_title = job_function_from_title(blob)
    if from_title and from_title in TITLES_BY_FUNCTION:
        return from_title
    if from_title and from_title in ACTION_TO_FUNCTION:
        return ACTION_TO_FUNCTION[from_title]
    if action in ACTION_TO_FUNCTION:
        return ACTION_TO_FUNCTION[action]
    return "operations"


def hunter_departments_for_function(function: str) -> str:
    if function in {"pharmacy", "patient_transport"}:
        return "health,operations"
    return "operations,management"


def plan_for_job(row: Any) -> DecisionMakerPlan:
    function = function_for_job(row)
    titles = list(TITLES_BY_FUNCTION.get(function) or DEFAULT_TITLES)
    blob = job_text(row).lower()
    if "airport" in blob and function == "environmental_services":
        titles = [
            "Director of Airport Operations",
            "Director of Facilities",
            *titles,
        ]
    if "mall" in blob and function == "environmental_services":
        titles = ["Property Operations Manager", "Director of Facilities", *titles]
    # Dedupe, keep order.
    seen: set[str] = set()
    ordered: list[str] = []
    for title in titles:
        key = title.lower()
        if key in seen:
            continue
        seen.add(key)
        ordered.append(title)
    return DecisionMakerPlan(
        function=function,
        titles=ordered[:8],
        departments=hunter_departments_for_function(function),
        tokens=DISTINCTIVE_TOKENS.get(function, ()),
    )


def _norm(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").lower()).strip()


def score_candidate(
    plan: DecisionMakerPlan,
    person: dict[str, Any],
    *,
    locality: str = "",
) -> Optional[tuple[int, str]]:
    """Return (score, why) or None when the title does not belong on this job."""
    title = _norm(str(person.get("title") or person.get("position") or ""))
    if not title:
        return None
    if any(tok in title for tok in PENALTY_TOKENS):
        return None
    senior = any(tok in title for tok in SENIORITY_TOKENS)
    if not senior and any(tok in title for tok in JUNIOR_TOKENS):
        return None
    score = 0
    why_bits: list[str] = []
    for target in plan.titles:
        target_l = _norm(target)
        if target_l and target_l in title:
            score += 48
            why_bits.append(f"title is {target}")
            break
        words = [
            w
            for w in re.findall(r"[a-z]{4,}", target_l)
            if w not in {"director", "manager", "head", "chief", "vice"}
        ]
        hits = [w for w in words if w in title]
        if len(hits) >= 2:
            score += 36
            why_bits.append(f"title matches {target}")
            break
        if len(hits) == 1 and hits[0] not in {"operations"}:
            score += 18
            why_bits.append(f"title has {hits[0]}")
            break
    token_hits = [tok for tok in plan.tokens if tok in title]
    if token_hits:
        score += 16 * min(2, len(token_hits))
        if not why_bits:
            why_bits.append(f"title has {token_hits[0]}")
    person_place = _norm(
        " ".join(
            str(person.get(k) or "")
            for k in ("city", "state", "location", "locality")
        )
    )
    loc = _norm(locality)
    if loc and person_place:
        city = loc.split(",")[0].strip()
        if city and city in person_place:
            score += 12
            why_bits.append(f"same city as {city.title()}")
    if plan.function in {
        "operations",
        "material_handling",
        "picking",
        "packing",
        "shipping",
        "receiving",
        "palletizing",
    } and ("chief operating" in title or re.search(r"\bcoo\b", title)):
        score += 40
        why_bits.append("title is COO")
    if not senior and score < STRONG_TITLE_SCORE:
        return None
    if score < MIN_ACCEPT_SCORE:
        return None
    work = plan.function.replace("_", " ")
    why = why_bits[0] if why_bits else f"matched {work} titles"
    return score, f"{why} for this {work} job"


def pick_candidate(
    plan: DecisionMakerPlan,
    people: list[dict[str, Any]],
    *,
    locality: str = "",
) -> Optional[dict[str, Any]]:
    best: Optional[dict[str, Any]] = None
    best_score = -1
    best_why = ""
    for person in people:
        if not isinstance(person, dict):
            continue
        ranked = score_candidate(plan, person, locality=locality)
        if not ranked:
            continue
        score, why = ranked
        confidence = int(person.get("confidence") or 0)
        score += min(10, confidence // 20)
        if score > best_score:
            best_score = score
            best = dict(person)
            best_why = why
    if not best:
        return None
    best["match_score"] = best_score
    best["match_why"] = best_why
    best["target_titles"] = list(plan.titles)
    best["job_function"] = plan.function
    return best
