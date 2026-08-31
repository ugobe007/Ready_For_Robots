"""Ontology parameters for Robot Job scrapers and OEM page extract.

COMPANY → PRODUCT → CONFIGURATION → HARDWARE → CAPABILITIES → TASK MODELS
→ JOB REQUIREMENTS → MATCH. Never company → category → jobs.

Job-board extract classifies the *work*, not the OEM. Mixed hubs (Pudu serving
+ cleaning + humanoid) must not dump one company class onto every posting.
Named products are evidence SKUs only. Task-model kind/source use the same
field names as CRM (``work_task_model_kind`` / ``work_task_model_source``)
so Apply can fill them later. Do not invent model names from listings.
"""
from __future__ import annotations

import re
from typing import Any, Optional

WORK_TASK_MODEL_KINDS = ("unknown", "source", "self_train")

# Nav / marketing labels that are not employers and not SKUs.
CHROME_NAMES = frozenset(
    {
        "impact",
        "farmers",
        "farmer",
        "product",
        "products",
        "about",
        "news",
        "blog",
        "imprint",
        "impressum",
        "privacy",
        "terms",
        "en",
        "home",
        "shop",
        "contact",
        "careers",
        "career",
        "investors",
        "vehicles",
        "vehicle",
        "powered by ai",
    }
)

# Category / company+class dumps and SKUs that are not on the page.
INVENTED_SKU_NAMES = frozenset(
    {
        "seer humanoid",
        "amr scrubbers",
        "scrubber",
        "scrubbers",
        "twa reach",
        "galbot g2",
        "qiyuan t1",
    }
)

_COMPANY_CLASS_DUMP = re.compile(
    r"^[A-Z][A-Za-z0-9]*(?:\s+[A-Z][A-Za-z0-9]+)*\s+"
    r"(?:Humanoid|Scrubber|AMR|Cleaner|Serving)s?$",
    re.I,
)
_CATEGORY_BLOB = re.compile(
    r"^(?:the\s+)?(?:apple|strawberry|grape|cotton|berry|warehouse|delivery|"
    r"floor|pallet|amr|agv)?\s*(?:harvest(?:er|ing)?|weeding|tractors?|robots?|"
    r"systems?|platform|automation|equipment|scrubbers?|cleaners?)\s*$",
    re.I,
)

# Human job-function → FIND product class (work physics, not an OEM dump).
JOB_FUNCTION_PRODUCT_CLASS = {
    "serving": "serving",
    "food_prep": "food_prep",
    "warewash": "food_prep",
    "environmental_services": "cleaning",
    "facade_cleaning": "cleaning_drone",
    "housekeeping": "hospitality",
    "front_desk": "hospitality",
    "laundry": "hospitality",
    "patient_transport": "healthcare",
    "pharmacy": "healthcare",
    "picking": "warehouse",
    "packing": "warehouse",
    "material_handling": "warehouse",
    "receiving": "warehouse",
    "replenishment": "warehouse",
    "shipping": "logistics",
    "palletizing": "factory",
    "machine_tending": "factory",
    "harvest": "agriculture",
    "field_work": "agriculture",
    "tractor": "agriculture",
    "weeding": "agriculture",
    "haulage": "mining",
    "drywall": "construction",
    "framing": "construction",
    "construction_labor": "construction",
}

# Product class → grounded capabilities. Serving is not floor-scrub.
CLASS_REQUIRED_CAPABILITIES = {
    "serving": ("serving_task",),
    "food_prep": ("food_prep",),
    "cleaning": ("surface_clean", "hard_floor_scrub"),
    "cleaning_drone": ("surface_clean", "drone_task"),
    "hospitality": ("hospitality_task",),
    "healthcare": ("healthcare_task",),
    "warehouse": ("tote_transport", "pick_pack"),
    "logistics": ("transport",),
    "factory": ("load_unload",),
    "agriculture": ("agriculture_task",),
    "mining": ("mining_task",),
    "construction": ("construction_task",),
}

FLOOR_SCRUB_CAPS = frozenset({"hard_floor_scrub"})
CLEANER_SKU_CLASSES = frozenset({"cleaning", "autonomous_scrubber", "scrubber", "cleaning_robot"})

_SELF_TRAIN_RE = re.compile(
    r"\b("
    r"self[- ]train(?:ed|ing)?"
    r"|we(?:'| wi)ll train"
    r"|train(?:ed|ing)? (?:on[- ]site|on this (?:job|task|work)|the robot for this)"
    r"|bring your own (?:policy|model)"
    r")\b",
    re.I,
)

# Long names only. Bare "ACT" / "Octo" collide with English.
_NAMED_SOURCE_NEEDLES = (
    "openvla",
    "lerobot",
    "gr00t",
    "nvidia isaac",
    "π0.5",
    "pi0.5",
    "octo policy",
    "act policy",
)

_TASK_PACK_RE = re.compile(
    r"\b((?:oem|vendor)\s+(?:skill|task|policy)\s+pack"
    r"|named\s+(?:skill|task|policy)\s+pack)\b",
    re.I,
)


def _norm_name(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip()).lower()


def is_chrome_name(value: str) -> bool:
    """True for nav/legal/marketing labels (Impact, Farmers, Product)."""
    low = _norm_name(value)
    if not low:
        return True
    return low in CHROME_NAMES


def is_invented_sku_name(value: str) -> bool:
    """True for empty names, class dumps, and SKUs that are not on the page."""
    raw = re.sub(r"\s+", " ", (value or "").strip(" .-"))
    if not raw:
        return True
    low = raw.lower()
    if low in INVENTED_SKU_NAMES or low in CHROME_NAMES:
        return True
    if _COMPANY_CLASS_DUMP.fullmatch(raw) or _CATEGORY_BLOB.fullmatch(raw):
        return True
    return False


def is_class_dump_title(title: str) -> bool:
    """True when the posting title is a company+class dump, not operational work."""
    raw = re.sub(r"\s+", " ", (title or "").strip())
    if not raw:
        return False
    low = raw.lower()
    if low in INVENTED_SKU_NAMES:
        return True
    return bool(_COMPANY_CLASS_DUMP.fullmatch(raw) or _CATEGORY_BLOB.fullmatch(raw))


def product_class_for_job_function(job_function: Optional[str]) -> Optional[str]:
    key = (job_function or "").strip().lower()
    if not key:
        return None
    return JOB_FUNCTION_PRODUCT_CLASS.get(key)


def infer_product_class(
    *,
    title: str,
    description: str = "",
    job_function: Optional[str] = None,
) -> Optional[str]:
    """Work-language class for this posting. Never an OEM company dump."""
    blob = f"{title or ''}\n{description or ''}"
    try:
        from app.services.robot_ontology import match_work_language

        hit = match_work_language(blob)
    except Exception:
        hit = None
    if hit and hit.find_class:
        return hit.find_class
    return product_class_for_job_function(job_function)


def infer_required_capabilities(
    product_class: Optional[str],
    *,
    title: str = "",
    description: str = "",
) -> list[str]:
    """Capabilities grounded in this posting's work. Serving ≠ floor scrub."""
    cls = (product_class or "").strip().lower()
    caps = list(CLASS_REQUIRED_CAPABILITIES.get(cls) or ())
    blob = f"{title or ''} {description or ''}".lower()
    if cls == "cleaning_drone" or "cleaning drone" in blob or "facade" in blob:
        caps = [c for c in caps if c not in FLOOR_SCRUB_CAPS]
        if "drone_task" not in caps:
            caps.append("drone_task")
        if "surface_clean" not in caps:
            caps.append("surface_clean")
        return caps
    if cls == "serving":
        return [c for c in caps if c not in FLOOR_SCRUB_CAPS]
    return caps


def infer_task_model_requirement(
    *,
    title: str,
    description: str = "",
    product_class: Optional[str] = None,
) -> dict[str, Any]:
    """Named source vs self-train vs unknown. Never invent a model name.

    ``task_model_ids`` are ontology slots the work would need, not a SKU.
    ``work_task_model_kind`` / ``work_task_model_source`` match CRM columns.
    """
    blob = f"{title or ''}\n{description or ''}"
    kind = "unknown"
    source: Optional[str] = None
    if _SELF_TRAIN_RE.search(blob):
        kind = "self_train"
        source = None
    else:
        low = blob.lower()
        for needle in _NAMED_SOURCE_NEEDLES:
            if needle in low:
                kind = "source"
                source = needle.upper() if needle == "gr00t" else needle
                if needle == "openvla":
                    source = "OpenVLA"
                elif needle == "lerobot":
                    source = "LeRobot"
                elif needle == "nvidia isaac":
                    source = "NVIDIA Isaac"
                elif needle in {"π0.5", "pi0.5"}:
                    source = "π0.5"
                elif needle == "gr00t":
                    source = "GR00T"
                break
        if kind == "unknown" and _TASK_PACK_RE.search(blob):
            # Posting says a pack exists but does not name it. Unknown, not invented.
            kind = "unknown"
            source = None

    task_ids: list[str] = []
    industry_id: Optional[str] = None
    terms: list[str] = []
    try:
        from app.services.robot_ontology import match_work_language

        hit = match_work_language(blob)
    except Exception:
        hit = None
    if hit:
        task_ids = list(hit.task_model_ids or ())
        industry_id = hit.industry_id or None
        terms = list(hit.matched_terms or ())
    if not task_ids and (product_class or "").strip().lower() == "serving":
        task_ids = ["dining_floor_service_policy"]
    if not task_ids and (product_class or "").strip().lower() == "cleaning":
        task_ids = ["commercial_cleaning_policy"]
    if not task_ids and (product_class or "").strip().lower() == "food_prep":
        task_ids = ["food_prep_station_policy"]
    return {
        "work_task_model_kind": kind if kind in WORK_TASK_MODEL_KINDS else "unknown",
        "work_task_model_source": source if kind == "source" else None,
        "task_model_ids": task_ids,
        "industry_id": industry_id,
        "work_language_terms": terms,
    }


def serving_caps_exclude_cleaner_sku(caps: list[str], product_class: Optional[str]) -> bool:
    """Serving work must not attach to a cleaner SKU class / floor-scrub-only cap."""
    cls = (product_class or "").strip().lower()
    if cls == "serving":
        return cls not in CLEANER_SKU_CLASSES and not (set(caps) & FLOOR_SCRUB_CAPS)
    return True


def drone_cleaning_not_floor_scrub_only(caps: list[str], product_class: Optional[str]) -> bool:
    cls = (product_class or "").strip().lower()
    if cls == "cleaning_drone":
        return "hard_floor_scrub" not in caps
    return True


def should_persist_robot_job(
    *,
    title: str,
    employer: str,
    job_function: Optional[str] = None,
) -> bool:
    """Drop class-dump titles, chrome employers, and empty/invented SKU names."""
    from app.services.robot_job_extract import is_job_employer_name, job_function_from_title

    if not (title or "").strip() or not (employer or "").strip():
        return False
    if is_chrome_name(employer) or is_invented_sku_name(employer):
        return False
    if not is_job_employer_name(employer, title=title):
        return False
    if is_class_dump_title(title) or is_invented_sku_name(title):
        return False
    function = job_function or job_function_from_title(title)
    if not function and is_chrome_name(title):
        return False
    return True
