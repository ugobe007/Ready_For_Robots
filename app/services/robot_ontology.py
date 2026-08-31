"""
Machine-readable ontology loader — makes the ontology library *usable* by the
scraping/parsing → derive → match workflow (not just Markdown docs).

Loads the JSON ontologies under ``ontology/`` (capability, workflow, hardware,
inference rules) and exposes typed accessors. Fails **open**: if a file is
missing or malformed, the baked-in defaults (which mirror the current code) are
returned so production behaviour never breaks. ``tests/test_robot_ontology.py``
enforces that these ontologies stay in sync with the live pipeline, so updating
the ontology JSON is meaningful and safe.
"""
from __future__ import annotations

import json
import re as _re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[2]
_ONT_DIR = _ROOT / "ontology"

ONTOLOGY_VERSION = "1.0.0"

# ── Baked-in fallbacks (mirror the code so a missing file never breaks prod) ──
_DEFAULT_CONFIDENCE_STATES = ("EXPLICIT", "DERIVED", "LIKELY", "UNKNOWN", "CONFLICTED")
_DEFAULT_DISTINCTIVE = frozenset(
    {
        "manipulate", "dual_arm", "tote_transport", "transport", "food_prep",
        "beverage_prep", "surface_clean", "hard_floor_scrub", "inspect_route",
        "load_unload", "reach",
    }
)
_DEFAULT_GENERIC = frozenset({"mobile"})
_DEFAULT_FAMILIES: dict[str, list[str]] = {
    "pallet": ["manipulate"],
    "gripper": ["manipulate"],
    "transport": ["tote_transport", "transport"],
    "cart": ["tote_transport", "transport"],
    "scrub": ["hard_floor_scrub"],
    "inspect": ["inspect_route"],
    "serve": ["transport"],
    "food_prep": ["food_prep"],
    "beverage": ["beverage_prep"],
    "restroom": ["surface_clean"],
}


def _load(name: str) -> dict[str, Any]:
    try:
        return json.loads((_ONT_DIR / name).read_text(encoding="utf-8"))
    except Exception:
        return {}


@lru_cache(maxsize=1)
def capability_ontology() -> dict[str, Any]:
    return _load("capability_ontology.v1.json")


@lru_cache(maxsize=1)
def workflow_ontology() -> dict[str, Any]:
    return _load("workflow_ontology.v1.json")


@lru_cache(maxsize=1)
def hardware_ontology() -> dict[str, Any]:
    return _load("hardware_ontology.v1.json")


@lru_cache(maxsize=1)
def inference_rules() -> dict[str, Any]:
    return _load("inference_rules.v1.json")


@lru_cache(maxsize=1)
def vertical_ontology() -> dict[str, Any]:
    return _load("vertical_ontology.v1.json")


@lru_cache(maxsize=1)
def task_model_ontology() -> dict[str, Any]:
    return _load("task_model_ontology.v1.json")


@lru_cache(maxsize=1)
def oem_sku_catalog() -> dict[str, Any]:
    """Operator OEM → named SKU identity catalog. Fail-open to {}."""
    return _load("oem_sku_catalog.v1.json")


# ── Accessors used by the pipeline (each fails open to the baked-in default) ──

def confidence_states() -> tuple[str, ...]:
    states = capability_ontology().get("confidence_states")
    return tuple(states) if states else _DEFAULT_CONFIDENCE_STATES


def _capabilities() -> list[dict[str, Any]]:
    return capability_ontology().get("capabilities") or []


def capability_keys() -> frozenset[str]:
    caps = {c["key"] for c in _capabilities() if c.get("key")}
    return frozenset(caps) if caps else (_DEFAULT_DISTINCTIVE | _DEFAULT_GENERIC | {"payload"})


def distinctive_capabilities() -> frozenset[str]:
    caps = {c["key"] for c in _capabilities() if c.get("distinctive")}
    return frozenset(caps) if caps else _DEFAULT_DISTINCTIVE


def generic_capabilities() -> frozenset[str]:
    caps = {c["key"] for c in _capabilities() if c.get("generic")}
    return frozenset(caps) if caps else _DEFAULT_GENERIC


def grounding_predicates(capability: str) -> list[str]:
    for c in _capabilities():
        if c.get("key") == capability:
            return list(c.get("grounded_by") or [])
    return []


def workflow_families() -> frozenset[str]:
    fams = (workflow_ontology().get("families") or {}).keys()
    return frozenset(fams) if fams else frozenset(_DEFAULT_FAMILIES)


def workflow_required_capabilities(family: str) -> list[str]:
    fam = (workflow_ontology().get("families") or {}).get(family)
    if fam and fam.get("required_any"):
        return list(fam["required_any"])
    return list(_DEFAULT_FAMILIES.get(family, []))


_DEFAULT_VERTICALS = frozenset(
    {
        "warehouse", "manufacturing", "retail", "hospitality", "restaurant",
        "healthcare", "eldercare", "airport", "commercial", "utilities",
        "indoor", "construction", "mining", "agriculture", "marine", "aviation",
        "aerospace",
    }
)


def _verticals() -> list[dict[str, Any]]:
    return vertical_ontology().get("verticals") or []


def verticals() -> frozenset[str]:
    keys = {v["key"] for v in _verticals() if v.get("key")}
    return frozenset(keys) if keys else _DEFAULT_VERTICALS


def in_scope_verticals() -> frozenset[str]:
    return frozenset(v["key"] for v in _verticals() if v.get("in_scope"))


# ── Industry work language (FIND class after hardware, R33) ──────────────────

_OR_TERMS = frozenset({"or", "o.r.", "o.r"})
_MORPHOLOGY_DEFAULT = frozenset({"humanoid", "semi-humanoid", "biped", "bipedal"})


@lru_cache(maxsize=1)
def industry_work_language() -> dict[str, Any]:
    """Fail-open to {} so a missing file never breaks production."""
    return _load("industry_work_language.v1.json")


def industry_work_rows() -> list[dict[str, Any]]:
    return list(industry_work_language().get("industries") or [])


def _term_to_pattern(term: str) -> str:
    raw = (term or "").strip()
    if not raw:
        return ""
    if raw.lower() in _OR_TERMS or raw == "OR":
        return (
            r"(?:operating\s+rooms?|operating\s+theatres?|"
            r"\bor\s+suites?\b|\bo\.r\.)"
        )
    parts = [_re.escape(p) for p in _re.split(r"[\s/_-]+", raw) if p]
    if not parts:
        return ""
    if len(parts) == 1:
        return rf"\b{parts[0]}\b"
    return rf"\b{r'[\s/_-]+'.join(parts)}\b"


@lru_cache(maxsize=1)
def _industry_compiled() -> tuple[tuple[dict[str, Any], _re.Pattern[str], _re.Pattern[str]], ...]:
    compiled: list[tuple[dict[str, Any], _re.Pattern[str], _re.Pattern[str]]] = []
    for row in industry_work_rows():
        signals = [t for t in (row.get("class_signals") or []) if t]
        words = [t for t in (row.get("work_words") or signals) if t]
        sig_pats = [_term_to_pattern(t) for t in signals]
        word_pats = [_term_to_pattern(t) for t in words]
        sig_pats = [p for p in sig_pats if p]
        word_pats = [p for p in word_pats if p]
        if not word_pats:
            continue
        sig_rx = _re.compile("|".join(sig_pats), _re.I) if sig_pats else _re.compile(r"(?!x)x")
        word_rx = _re.compile("|".join(f"({p})" for p in word_pats), _re.I)
        compiled.append((row, sig_rx, word_rx))
    return tuple(compiled)


@dataclass(frozen=True)
class WorkLanguageHit:
    industry_id: str
    find_class: str | None
    claim_predicate: str | None
    product_classes: tuple[str, ...]
    outranks_morphology: tuple[str, ...]
    task_model_ids: tuple[str, ...]
    matched_terms: tuple[str, ...]
    capability: str | None
    score: int


def match_work_language(text: str) -> WorkLanguageHit | None:
    """Strongest industry work-language hit in product copy, or None.

    Requires at least two class_signals OR two work_words. Does not invent
    jobs. Hardware still comes first; this names the configuration class.
    """
    blob = text or ""
    if len(blob) < 12:
        return None
    best: WorkLanguageHit | None = None
    for row, sig_rx, word_rx in _industry_compiled():
        words = list(word_rx.finditer(blob))
        if not words:
            continue
        unique = tuple(sorted({m.group(0).lower() for m in words if m.group(0)}))
        # Bug 2 fix: require at least 2 unique matched terms, even for class_signals
        if len(unique) < 2:
            continue
        signal = bool(sig_rx.search(blob))
        score = len(unique) + (2 if signal else 0)
        find_class = (row.get("find_class") or None) or None
        if isinstance(find_class, str):
            find_class = find_class.strip() or None
        hit = WorkLanguageHit(
            industry_id=str(row.get("id") or ""),
            find_class=find_class,
            claim_predicate=(row.get("claim_predicate") or None) or None,
            product_classes=tuple(str(x) for x in (row.get("product_classes") or []) if x),
            outranks_morphology=tuple(
                str(x).lower() for x in (row.get("outranks_morphology") or []) if x
            ),
            task_model_ids=tuple(str(x) for x in (row.get("task_model_ids") or []) if x),
            matched_terms=unique,
            capability=(row.get("capability") or None) or None,
            score=score,
        )
        if best is None:
            best = hit
            continue
        if _work_language_hit_better(hit, best):
            best = hit
    return best


# Serving / cleaning / food_prep are more specific than hospitality on a tie
# (BellaBot: "tray"+"restaurants" vs "guest"+"hotels" — waiter, not hotel ops).
_WORK_LANGUAGE_TIEBREAK = {
    "serving": 4,
    "cleaning": 4,
    "food_prep": 4,
    "agriculture": 2,
    "healthcare": 2,
    "hospitality": 1,
}


def _work_language_hit_better(hit: WorkLanguageHit, best: WorkLanguageHit) -> bool:
    if hit.score > best.score:
        return True
    if hit.score < best.score:
        return False
    hit_has_class = bool(hit.find_class)
    best_has_class = bool(best.find_class)
    if hit_has_class and not best_has_class:
        return True
    if best_has_class and not hit_has_class:
        return False
    if hit.outranks_morphology and not best.outranks_morphology:
        return True
    if best.outranks_morphology and not hit.outranks_morphology:
        return False
    hit_tb = _WORK_LANGUAGE_TIEBREAK.get((hit.find_class or "").lower(), 0)
    best_tb = _WORK_LANGUAGE_TIEBREAK.get((best.find_class or "").lower(), 0)
    return hit_tb > best_tb


def find_class_from_work_language(text: str) -> str | None:
    """FIND / product_class implied by ontology work language, or None."""
    hit = match_work_language(text)
    if hit and hit.find_class:
        return hit.find_class
    return None


def work_language_outranks_morphology(text: str, morphology: str | None = "humanoid") -> bool:
    """R33: work/task evidence beats generic humanoid morphology when both fire."""
    want = (morphology or "humanoid").strip().lower()
    hit = match_work_language(text)
    if not hit:
        return False
    # Only outrank when we have a FIND class to replace it with (Bug 1 fix)
    if not hit.find_class:
        return False
    ranked = hit.outranks_morphology or tuple(_MORPHOLOGY_DEFAULT if hit.find_class else ())
    return want in {r.lower() for r in ranked}


def industry_class_aliases() -> dict[str, str]:
    """alias → FIND class. Ontology is the source; morphology aliases stay in qualify."""
    out: dict[str, str] = {}
    for row in industry_work_rows():
        find_class = (row.get("find_class") or "").strip()
        if not find_class:
            continue
        for alias in row.get("aliases") or []:
            key = str(alias).strip().lower().replace(" ", "_").replace("-", "_")
            if key:
                out[key] = find_class
        for cls in row.get("product_classes") or []:
            key = str(cls).strip().lower().replace(" ", "_").replace("-", "_")
            if key:
                out[key] = find_class
        out[find_class] = find_class
    return out


def domain_priority_classes() -> frozenset[str]:
    """product_class values that outrank torso morphology (R33).

    Only industries with ``outranks_morphology`` belong here. Warehouse /
    factory / logistics FIND classes must not steal Figure-style humanoids.
    """
    out: set[str] = set()
    for row in industry_work_rows():
        if not (row.get("outranks_morphology") or []):
            continue
        if row.get("find_class"):
            out.add(str(row["find_class"]).lower())
        for cls in row.get("product_classes") or []:
            out.add(str(cls).lower())
        for alias in row.get("aliases") or []:
            out.add(str(alias).lower().replace(" ", "_").replace("-", "_"))
    return frozenset(x for x in out if x)


def healthcare_ontology_work_words() -> frozenset[str]:
    """Closed set the pstack ontology critic requires in healthcare rows."""
    for row in industry_work_rows():
        if row.get("id") == "healthcare":
            words = set(str(w).lower() for w in (row.get("work_words") or []) if w)
            words.update(str(w).lower() for w in (row.get("class_signals") or []) if w)
            return frozenset(words)
    return frozenset()
