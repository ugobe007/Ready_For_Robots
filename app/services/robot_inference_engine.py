"""
Robot Inference Engine — evidence → inference → capability.

Architecture correction (2026-08-18): the source of truth is
``evidence → inference → capability``, NOT ``prompt → profile``. This is a
deterministic, forward-chaining inference engine (the Pythh pattern) — not an
LLM profile generator. It reasons over the SAME fetched evidence pack v1
collects and produces evidence-backed, provenance-carrying facts.

Phases (each conclusion retains its evidence chain + confidence):

  PHASE 1  Explicit facts     deterministic signal detection over the pack
  PHASE 2  Structural         humanoid / scrubber / AMR / mobility morphology
  PHASE 3  Capability         mobile, dual_arm, dexterous_manipulation, carry…
  PHASE 4  Workflow           tote handling, machine load/unload, scrubbing…

Facts are emitted in the EXISTING RobotFact predicate schema (epistemic
``explicit`` for detected, ``strongly_inferred`` for rule-chained — both are
GROUNDED for derive_capabilities), so the matcher and derive_capabilities are
unchanged. Every emitted fact carries evidence, a source id, and confidence.

Guardrails: no per-vendor branches; word-boundary matching (so "handles" is not
"hand", "2X" is not arm_count=2); conclusions require capability-appropriate
evidence; fails conservatively. Gated by ROBOT_INFERENCE_ENGINE=1; the engine
never lowers the bar below v1 (it only adds grounded facts v1's narrow regex
missed).
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Any, Optional

from app.services.robot_understanding_v1.models import RobotFact

CONF = {"HIGH": 0.9, "MEDIUM": 0.75, "LOW": 0.6}


def inference_engine_enabled() -> bool:
    return (os.getenv("ROBOT_INFERENCE_ENGINE") or "").strip().lower() in ("1", "true", "yes")


# ── Grounded observation carrying full provenance ─────────────────────────────

@dataclass
class Observation:
    predicate: str
    value: Any
    units: Optional[str]
    evidence: str
    source_id: str
    confidence: float
    mode: str  # "explicit" (detected) | "strongly_inferred" (rule-chained)
    basis: list[str] = field(default_factory=list)  # supporting predicates for inferences


# ── PHASE 1: deterministic signal detectors over the evidence pack ────────────
# Each detector is (regex, predicate, value, units, confidence). The regex is
# applied to page text; the matched window becomes the evidence span. Word
# boundaries prevent false positives ("2X" ≠ arm_count, "handles" ≠ "hand").

def _rx(pattern: str) -> re.Pattern:
    return re.compile(pattern, re.I)


_BOOL_DETECTORS: list[tuple[re.Pattern, str, Any, Optional[str], float]] = [
    (_rx(r"\bhumanoid\b"), "product_class", "humanoid", None, CONF["HIGH"]),
    (_rx(r"\bquadruped\b|\bfour[-\s]legged\b"), "product_class", "quadruped", None, CONF["HIGH"]),
    (_rx(r"\b(?:auto[-\s]?scrubber|floor\s+scrubb?er|scrubber\b|floor\s+scrubbing)\b"),
     "product_class", "autonomous_scrubber", None, CONF["HIGH"]),
    (_rx(r"\bmobile\s+manipulators?\b"), "product_class", "mobile_manipulator", None, CONF["HIGH"]),
    (_rx(r"\bautonomous\s+mobile\s+robot\b|\bamr\b"), "product_class", "amr", None, CONF["MEDIUM"]),
    (_rx(r"\blaserweeder\b|\blaser\s+weeder\b|\bagricultural\s+robots?\b|\bweeding\s+robots?\b|"
         r"\bautonomous\s+(?:tractor|combine|harvester)\b|\bcombine\s+harvest"),
     "product_class", "agricultural_robot", None, CONF["HIGH"]),
    (_rx(r"\bmarine\s+robots?\b|\bhull\s+inspect\w*\b|\bunderwater\s+robots?\b"),
     "product_class", "marine_robot", None, CONF["HIGH"]),
    (_rx(r"\b(?:inspection\s+)?drones?\b|\buav\b|\bevtol\b|\bflying\s+cars?\b|"
         r"\bautonomous\s+(?:aircraft|planes?)\b|\bavionics\s+robots?\b"),
     "product_class", "aviation_robot", None, CONF["HIGH"]),
    (_rx(r"\baerospace\s+robots?\b|\bspace\s+robots?\b|\bsatellite\s+servic\w*\b|"
         r"\borbital\s+debris\b|\bdebris\s+(?:captur\w*|removal)\b"),
     "product_class", "aerospace_robot", None, CONF["HIGH"]),
    (_rx(r"\bconstruction\s+robots?\b|\bjobsite\s+robots?\b|"
         r"\b(?:home|house|residential)\s+(?:construction|build|framing)\s+robots?\b|"
         r"\b3d\s+(?:print(?:ed|ing)?)\s+(?:homes?|houses?|buildings?)\b"),
     "product_class", "construction_robot", None, CONF["HIGH"]),
    (_rx(r"\bdexterous\b(?:\s+\w+){0,3}?\s+hands?\b|\bhands?\b(?:\s+\w+){0,3}?\s+dexter"),
     "has_dexterous_hands", True, None, CONF["HIGH"]),
    # Bimanual / two-handed / dexterous manipulation are explicit dexterity claims
    # even without the noun "hands" — humanoids and general-purpose manipulators
    # (e.g. Nimo) describe capability this way. Word-bounded; "handles" ≠ "handed".
    (_rx(r"\bbimanual\b|\bdexterous\s+manipulat\w+|"
         r"\btwo[-\s]handed\s+(?:manipulat\w+|dexterity|tasks?|grasp\w*|grip\w*)\b"),
     "has_dexterous_hands", True, None, CONF["HIGH"]),
    (_rx(r"\b(?:robot(?:ic)?\s+arm|manipulator\s+arm|articulated\s+arm)\b"),
     "end_effector", "gripper", None, CONF["MEDIUM"]),
    (_rx(r"\b(?:mobile\s+base|fully\s+mobile|omnidirectional|mecanum|holonomic|wheeled\s+base)\b"),
     "has_mobile_base", True, None, CONF["HIGH"]),
    (_rx(r"\b(?:bipedal|biped|two\s+legs|legged\s+locomotion)\b"),
     "mobility_architecture", "bipedal", None, CONF["HIGH"]),
    (_rx(r"\b(?:autonomous\s+navigation|autonomously\s+navigat\w*|self[-\s]navigat\w*|\blidar\b|\bslam\b)\b"),
     "autonomous_navigation", True, None, CONF["HIGH"]),
    # Manufacturer copy often says "works autonomously" without the word "navigation".
    (_rx(r"\b(?:works?\s+autonomously|fully\s+autonomous|autonomous\s+operation)\b"),
     "autonomous_navigation", True, None, CONF["MEDIUM"]),
    (_rx(r"\b(?:gripper|end[-\s]effector|vacuum\s+gripper|suction\s+cup|parallel[-\s]jaw|two[-\s]finger)\b"),
     "end_effector", "gripper", None, CONF["MEDIUM"]),
    (_rx(r"\btotes?\b|\bgoods[-\s]to[-\s]person\b|\bperson[-\s]to[-\s]goods\b|\border\s+picking\b|"
         r"\bmove\s+(?:totes?|carts?|bins?)\b|\b(?:tote|cart|bin)\s+(?:transport|movement|handling)\b"),
     "supports_tote_handling", True, None, CONF["MEDIUM"]),
    (_rx(r"\b(?:load\s+and\s+unload|loading\s+and\s+unloading|machine\s+tending|load/unload)\b"),
     "claims_load_unload", True, None, CONF["MEDIUM"]),
    (_rx(r"\b(?:hard[-\s]floor\s+scrub\w*|scrub\w*\s+floors?|cleans?\s+floors?)\b"),
     "supports_hard_floor_scrubbing", True, None, CONF["HIGH"]),
]


def _window(text: str, start: int, end: int, max_pad: int = 200) -> str:
    """Sentence-bounded evidence window. Staying within the sentence keeps a
    signal's evidence about ITS subject — a sibling SKU mentioned in the next
    sentence must not bleed into (or falsely contaminate) this fact."""
    left = max(
        text.rfind(".", 0, start), text.rfind("\n", 0, start),
        text.rfind("!", 0, start), text.rfind("?", 0, start),
    )
    a = max(left + 1 if left != -1 else 0, start - max_pad)
    rights = [i for i in (text.find(".", end), text.find("\n", end), text.find("!", end), text.find("?", end)) if i != -1]
    b = min((min(rights) + 1) if rights else len(text), end + max_pad)
    return re.sub(r"\s+", " ", text[a:b]).strip()


def _detect_arm_count(text: str) -> Optional[tuple[int, str]]:
    """Detect number of arms. Requires an 'arm' keyword near the number — never '2X'."""
    # "Arms 7x2" (DoF x count) → count is the trailing number.
    m = re.search(r"\barms?\b[^.\n]{0,14}?(\d+)\s*[x×]\s*(\d+)", text, re.I)
    if m:
        return int(m.group(2)), _window(text, m.start(), m.end())
    m = re.search(r"\b(two|dual|double)[-\s]?arm", text, re.I)
    if m:
        return 2, _window(text, m.start(), m.end())
    # Bimanual / two-handed manipulation ⇒ two arms.
    m = re.search(r"\bbimanual\b|\btwo[-\s]handed\s+(?:manipulat\w+|dexterity|tasks?|grasp\w*|grip\w*)", text, re.I)
    if m:
        return 2, _window(text, m.start(), m.end())
    m = re.search(r"\b(\d+)\s*arms?\b", text, re.I)
    if m:
        n = int(m.group(1))
        if 1 <= n <= 4:
            return n, _window(text, m.start(), m.end())
    return None


def _detect_hand_dof(text: str) -> Optional[tuple[int, str]]:
    m = re.search(r"\bhands?\b[^.\n]{0,16}?(\d{1,2})\s*(?:dof|degrees?\s+of\s+freedom|x)", text, re.I)
    if m:
        return int(m.group(1)), _window(text, m.start(), m.end())
    m = re.search(r"(\d{1,2})\s*(?:dof|degrees?\s+of\s+freedom)[^.\n]{0,12}?\bhands?\b", text, re.I)
    if m:
        return int(m.group(1)), _window(text, m.start(), m.end())
    return None


# Manipulation is a CAPABILITY, not a category. Humanoids inherently manipulate;
# AMRs increasingly manipulate (telescoping grab-off-shelf, mounted arms); food
# prep is dexterous manipulation. Ground it from the robot's OWN manipulation
# actions/hardware — but not from human-in-the-loop pick language (person-to-goods,
# where the worker picks) or marketing metrics.
_HUMAN_IN_LOOP = re.compile(
    r"\b(?:person[-\s]to[-\s]goods|goods[-\s]to[-\s]person|workers?\s+pick|associates?\s+pick|"
    r"pickers?|picking\s+and\s+putaway|put[-\s]to[-\s]light|pick[-\s]to[-\s]light|pick[-\s]?assist)\b",
    re.I,
)
# The robot itself acquiring/handling objects.
_MANIP_ACTION = re.compile(
    r"\b(?:grasp\w*|grab\w*|pick(?:s|ing)?\s+up|pick[-\s]and[-\s]place|"
    r"telescop\w+|retriev\w+|(?:pick|grab|remove|retriev\w+)\s+\w*\s*(?:items?|products?|objects?|parts?|boxes?)\s+(?:off|from))\b",
    re.I,
)
_MANIP_OBJECT = re.compile(r"\b(?:item|items|object|objects|product|products|part|parts|package|packages|box|boxes|goods|shelf|shelves|rack|racks)\b", re.I)
# The ROBOT itself performing autonomous picking/grasping/placing — robot-attributed
# manipulation, not a human picker. Distinguishes Brightpick ("mobile manipulators
# pick", "robotic picking") from person-to-goods AMRs where a worker picks.
_ROBOTIC_MANIP = re.compile(
    r"\b(?:robotic\s+(?:pick\w*|grasp\w*|manipulat\w+)|"
    r"(?:mobile\s+manipulators?|robots?|robotic\s+arms?)\s+(?:pick\w*|grasp\w*|grab\w*|place\w*|load\w*)|"
    r"automate\w*\s+(?:picking|palletiz\w+))\b",
    re.I,
)
# Food preparation = dexterous manipulation. Chopping/slicing/dicing/etc. are
# dexterous on their own; prepare/cook/assemble need a real FOOD object. Verbs and
# nouns are chosen NOT to collide with warehouse copy ("mixed orders", "makes
# operations efficient") — no "mix", no "order", no bare "make".
_FOOD_DEXTEROUS = re.compile(r"\b(?:chop\w*|slic\w+|dic\w+|peel\w*|julienne\w*|debon\w+|fillet\w*|knead\w*|garnish\w*)\b", re.I)
_FOOD_NOUN = (
    r"food|meal|meals|salad\w*|bowl\w*|taco\w*|burrito\w*|pizza\w*|sandwich\w*|entree\w*|"
    r"ingredient\w*|recipe\w*|coffee|beverage\w*|dough|batter|produce|vegetable\w*|noodle\w*|"
    r"pasta|sushi|meat|protein\w*"
)
_FOOD_PREP = re.compile(
    r"\b(?:prepar\w+|assembl\w+|plat\w+|cook\w*|fry|fries|frying|grill\w*|saut\w+)\b"
    r"[^.\n]{0,40}?\b(?:" + _FOOD_NOUN + r")\b",
    re.I,
)
# NOTE: "foodservice" is a distribution vertical (moving totes of food), NOT food
# preparation — deliberately excluded so food-distribution AMRs aren't mislabeled
# as manipulators. Food-prep manipulation must come from prep verbs/nouns or an
# explicit prep context.
_FOOD_CONTEXT = re.compile(r"\b(?:food\s+prep\w*|food\s+preparation|culinary|kitchen\s+robot|meal\s+assembly)\b", re.I)


def _split_sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"[.!?\n]+", text) if s.strip()]


_WEEDING_SENTENCE = re.compile(
    r"\b(?:weed|weeding|laserweed|laser\s+weeder|crop\s+rows?|row\s+crops?|agricult)\b",
    re.I,
)


def _detect_manipulation(text: str) -> list[tuple[str, Any, str]]:
    """Return (predicate, value, evidence) manipulation groundings from robot actions
    or food prep. Skips human-in-the-loop pick sentences. Sentence-scoped."""
    out: list[tuple[str, Any, str]] = []
    for s in _split_sentences(text):
        if _HUMAN_IN_LOOP.search(s):
            continue  # the worker picks, not the robot
        if _WEEDING_SENTENCE.search(s):
            continue  # crop weeding lasers are not shop-floor grippers
        window = re.sub(r"\s+", " ", s)[:240]
        # Robot manipulation action on objects (grab/pick items off shelf, telescoping retrieve).
        if _MANIP_ACTION.search(s) and _MANIP_OBJECT.search(s):
            out.append(("end_effector", "gripper", window))
        # Robot-attributed picking/grasping (robotic picking; manipulators pick).
        elif _ROBOTIC_MANIP.search(s):
            out.append(("end_effector", "gripper", window))
        # Food prep is dexterous manipulation.
        if _FOOD_DEXTEROUS.search(s) or _FOOD_PREP.search(s) or _FOOD_CONTEXT.search(s):
            out.append(("has_dexterous_hands", True, window))
    return out


def _phase1_detect(collected: list, subject: str = "") -> list[Observation]:
    """Detect explicit facts — SUBJECT-SCOPED. Capabilities belong to the selected
    product/configuration, not the company or a morphology label. We only detect on
    pages that name the subject, and drop any signal whose evidence window cites a
    different SKU (a sibling product or an optional module).
    """
    import re as _re

    from app.services.robot_understanding_v1.facts import _evidence_names_sibling_sku
    from app.services.robot_understanding_v1.sources import page_supports_subject, subject_tokens

    subj_key = _re.sub(r"[^a-z0-9]", "", (subject or "").lower())
    tokens = subject_tokens(subject) if subject else set()

    def _off_subject(window: str) -> bool:
        return bool(subject) and _evidence_names_sibling_sku(window, subj_key=subj_key, tokens=tokens)

    obs: list[Observation] = []
    for c in collected:
        page = getattr(c, "page", None)
        src = getattr(c, "source", None)
        sid = getattr(src, "id", None) or "inference"
        text = getattr(page, "text", "") or ""
        if not text.strip():
            continue
        # Page-level subject gate: an off-subject page contributes no capability facts.
        if subject and not page_supports_subject(
            url=getattr(page, "final_url", "") or getattr(src, "url", "") or "",
            title=getattr(page, "title", "") or getattr(src, "title", "") or "",
            text=text,
            product_name=subject,
        ):
            continue
        for rx, predicate, value, units, conf in _BOOL_DETECTORS:
            m = rx.search(text)
            if m:
                window = _window(text, m.start(), m.end())
                if _off_subject(window):
                    continue  # evidence names another SKU/module — not this product
                if (
                    predicate == "product_class"
                    and str(value).lower() == "humanoid"
                ):
                    from app.services.robot_ontology import work_language_outranks_morphology

                    if work_language_outranks_morphology(text, "humanoid"):
                        continue
                obs.append(Observation(predicate, value, units, window, sid, conf, "explicit"))
        from app.services.robot_ontology import find_class_from_work_language, match_work_language

        # Bug 3 fix: Only check work language on page that passed page_supports_subject
        # (already gated above at line 271-277)
        work_cls = find_class_from_work_language(text)
        if work_cls:
            hit = match_work_language(text)
            span = (hit.matched_terms[0] if hit and hit.matched_terms else work_cls)
            obs.append(
                Observation("product_class", work_cls, None, span, sid, CONF["HIGH"], "explicit")
            )
            if hit and hit.claim_predicate:
                obs.append(
                    Observation(hit.claim_predicate, True, None, span, sid, CONF["HIGH"], "explicit")
                )
        arm = _detect_arm_count(text)
        if arm and not _off_subject(arm[1]):
            obs.append(Observation("arm_count", arm[0], None, arm[1], sid, CONF["HIGH"], "explicit"))
        hd = _detect_hand_dof(text)
        if hd and not _off_subject(hd[1]):
            obs.append(Observation("hand_dof", hd[0], None, hd[1], sid, CONF["HIGH"], "explicit"))
            obs.append(Observation("has_dexterous_hands", True, None, hd[1], sid, CONF["HIGH"], "explicit"))
        # Manipulation from the robot's own actions / food prep (category-agnostic:
        # AMRs and food robots manipulate too — not just humanoids/cobots).
        for predicate, value, window in _detect_manipulation(text):
            if not _off_subject(window):
                obs.append(Observation(predicate, value, None, window, sid, CONF["MEDIUM"], "explicit"))
    return obs


# ── PHASE 2/3: forward-chaining inference rules over grounded observations ─────

def _has(grounded: dict[str, Observation], predicate: str, value: Any = None) -> bool:
    o = grounded.get(predicate)
    if o is None:
        return False
    if value is None:
        return True
    return str(o.value).lower() == str(value).lower()


def _phase23_infer(grounded: dict[str, Observation]) -> list[Observation]:
    """Structural + capability inference. Each conclusion cites its basis."""
    out: list[Observation] = []

    def add(pred, val, units, basis_preds, conf, evidence_from):
        if pred in grounded:
            return
        ev_src = grounded.get(evidence_from)
        out.append(
            Observation(
                pred, val, units,
                (ev_src.evidence if ev_src else f"inferred from {', '.join(basis_preds)}"),
                (ev_src.source_id if ev_src else "inference"),
                conf, "strongly_inferred", basis=list(basis_preds),
            )
        )
        # make the new fact visible to later rules in this pass
        grounded[pred] = out[-1]

    # Humanoid morphology implies bipedal mobility + a mobile base.
    if _has(grounded, "product_class", "humanoid"):
        if "mobility_architecture" not in grounded:
            add("mobility_architecture", "bipedal", None, ["product_class=humanoid"], CONF["HIGH"], "product_class")
        add("has_mobile_base", True, None, ["product_class=humanoid"], CONF["HIGH"], "product_class")
        # Humanoids are dual-arm when any arm/hand evidence exists.
        if (_has(grounded, "has_dexterous_hands") or _has(grounded, "end_effector")) and "arm_count" not in grounded:
            add("arm_count", 2, None, ["product_class=humanoid", "has_dexterous_hands"], CONF["MEDIUM"], "has_dexterous_hands")

    # A mobile manipulator, by definition, is mobile AND manipulates.
    if _has(grounded, "product_class", "mobile_manipulator"):
        add("has_mobile_base", True, None, ["product_class=mobile_manipulator"], CONF["HIGH"], "product_class")
        if "end_effector" not in grounded and not _has(grounded, "has_dexterous_hands") and "arm_count" not in grounded:
            add("end_effector", "gripper", None, ["product_class=mobile_manipulator"], CONF["MEDIUM"], "product_class")

    # Navigation or a mobility architecture implies a mobile base.
    if _has(grounded, "autonomous_navigation") and "has_mobile_base" not in grounded:
        add("has_mobile_base", True, None, ["autonomous_navigation"], CONF["HIGH"], "autonomous_navigation")
    if grounded.get("mobility_architecture") and "has_mobile_base" not in grounded:
        add("has_mobile_base", True, None, ["mobility_architecture"], CONF["HIGH"], "mobility_architecture")

    # Scrubber class implies hard-floor scrubbing.
    if _has(grounded, "product_class", "autonomous_scrubber") and "supports_hard_floor_scrubbing" not in grounded:
        add("supports_hard_floor_scrubbing", True, None, ["product_class=autonomous_scrubber"], CONF["HIGH"], "product_class")
    if _has(grounded, "product_class", "cleaning") and "supports_hard_floor_scrubbing" not in grounded:
        add("supports_hard_floor_scrubbing", True, None, ["product_class=cleaning"], CONF["HIGH"], "product_class")

    # Work-domain classes ground their task claim (named derivation, not category→jobs).
    _class_claims = (
        (("agricultural_robot", "agriculture"), "claims_agriculture"),
        (("construction_robot", "construction"), "claims_construction"),
        (("marine_robot", "marine"), "claims_marine"),
        (("aviation_robot", "avionics", "drone", "evtol"), "claims_avionics"),
        (("aerospace_robot", "aerospace"), "claims_aerospace"),
        (("mining_robot", "mining"), "claims_mining"),
        (("warehouse_robot", "warehouse"), "claims_warehouse"),
        (("logistics_robot", "logistics"), "claims_logistics"),
        (("factory_robot", "factory"), "claims_factory"),
        (("hospitality_robot", "hospitality", "hotel_robot"), "claims_hospitality"),
        (("food_prep",), "claims_food_prep"),
        (("serving",), "claims_serving"),
        (("cleaning",), "claims_surface_cleaning"),
        (
            ("healthcare", "healthcare_robot", "medical_robot", "clinical_robot", "hospital_robot"),
            "claims_healthcare",
        ),
    )
    for class_vals, claim in _class_claims:
        if claim in grounded:
            continue
        if any(_has(grounded, "product_class", cls) for cls in class_vals):
            add(claim, True, None, [f"product_class={class_vals[0]}"], CONF["HIGH"], "product_class")

    return out


# ── PHASE 4: workflow inference (display only, from grounded capabilities) ─────

def _phase4_workflows(grounded: dict[str, Observation]) -> list[dict[str, Any]]:
    wf: list[dict[str, Any]] = []

    def cap(preds: list[str]) -> bool:
        return all(p in grounded for p in preds)

    manip = _has(grounded, "has_dexterous_hands") or _has(grounded, "arm_count") or _has(grounded, "end_effector")
    dual = False
    ac = grounded.get("arm_count")
    if ac is not None:
        try:
            dual = int(float(ac.value)) >= 2
        except (TypeError, ValueError):
            dual = False
    if manip:
        wf.append({"workflow": "machine load / unload", "basis": ["manipulation"]})
    if dual:
        wf.append({"workflow": "case handling / palletizing", "basis": ["dual_arm"]})
    if _has(grounded, "supports_tote_handling"):
        wf.append({"workflow": "tote / cart movement", "basis": ["tote_transport"]})
    if _has(grounded, "supports_hard_floor_scrubbing"):
        wf.append({"workflow": "surface cleaning", "basis": ["hard_floor_scrub"]})
    if _has(grounded, "product_class", "quadruped"):
        wf.append({"workflow": "inspection route", "basis": ["quadruped"]})
    return wf


# ── Capability summary (rich, provenance-carrying — for display / audit) ──────

def _capability_summary(grounded: dict[str, Observation]) -> list[dict[str, Any]]:
    caps: list[dict[str, Any]] = []

    def emit(key: str, basis_preds: list[str]):
        srcs = sorted({grounded[p].source_id for p in basis_preds if p in grounded})
        modes = {grounded[p].mode for p in basis_preds if p in grounded}
        confs = [grounded[p].confidence for p in basis_preds if p in grounded]
        caps.append({
            "capability": key,
            "confidence": round(min(confs), 2) if confs else None,
            "explicit_or_inferred": "explicit" if modes == {"explicit"} else "inferred",
            "basis": [f"{p}={grounded[p].value}" for p in basis_preds if p in grounded],
            "supporting_sources": srcs,
        })

    if any(p in grounded for p in ("has_mobile_base", "autonomous_navigation", "mobility_architecture")):
        emit("mobile", [p for p in ("has_mobile_base", "autonomous_navigation", "mobility_architecture") if p in grounded])
    if "autonomous_navigation" in grounded:
        emit("navigate", ["autonomous_navigation"])
    if "has_dexterous_hands" in grounded:
        emit("dexterous_manipulation", [p for p in ("has_dexterous_hands", "hand_dof") if p in grounded])
    if any(p in grounded for p in ("has_dexterous_hands", "arm_count", "end_effector")):
        emit("manipulate", [p for p in ("has_dexterous_hands", "arm_count", "end_effector") if p in grounded])
    elif _has(grounded, "product_class", "humanoid") or _has(grounded, "product_class", "mobile_manipulator"):
        # Humanoid / mobile-manipulator class is itself manipulation morphology.
        emit("manipulate", ["product_class"])
    ac = grounded.get("arm_count")
    if ac is not None:
        try:
            if int(float(ac.value)) >= 2:
                emit("dual_arm", ["arm_count"])
        except (TypeError, ValueError):
            pass
    if "carrying_capacity" in grounded:
        emit("carry", ["carrying_capacity"])
    if "supports_tote_handling" in grounded:
        emit("tote_transport", ["supports_tote_handling"])
    if "supports_hard_floor_scrubbing" in grounded:
        emit("hard_floor_scrub", ["supports_hard_floor_scrubbing"])
    return caps


# ── Public entry ──────────────────────────────────────────────────────────────

def infer_facts(
    collected: list,
    *,
    subject: str,
    existing_facts: list[RobotFact],
) -> tuple[list[RobotFact], Optional[dict[str, Any]]]:
    """
    Run phased inference over the evidence pack. Returns (extra_facts, summary).

    extra_facts are new RobotFacts (existing predicate schema) for predicates v1
    did not already ground. Fails conservatively: on any error returns ([], None).
    """
    if not inference_engine_enabled():
        return [], None
    try:
        # Grounded = v1's explicit facts (Phase-1 seeds) keyed by predicate.
        grounded: dict[str, Observation] = {}
        for f in existing_facts:
            if (f.epistemic or "") in ("explicit", "strongly_inferred") and f.value not in (None, "", "UNKNOWN"):
                grounded.setdefault(
                    f.predicate,
                    Observation(f.predicate, f.value, f.units, f.evidence_span or "", f.source_id, f.confidence, "explicit"),
                )

        # PHASE 1 — detect additional explicit facts from the evidence pack,
        # scoped to the selected product/configuration (no cross-SKU leakage).
        detected = _phase1_detect(collected, subject)
        for o in detected:
            grounded.setdefault(o.predicate, o)

        # PHASE 2/3 — forward-chain structural + capability inference.
        inferred = _phase23_infer(grounded)

        # Emit new facts (skip predicates v1 already produced).
        existing_preds = {
            f.predicate for f in existing_facts
            if (f.epistemic or "") not in ("unknown", "contradicted")
        }
        extra: list[RobotFact] = []
        emitted_summary_explicit: list[dict[str, Any]] = []
        emitted_summary_inferred: list[dict[str, Any]] = []
        for o in [*detected, *inferred]:
            if o.predicate in existing_preds:
                continue
            existing_preds.add(o.predicate)
            extra.append(
                RobotFact.create(
                    subject, o.predicate, o.value,
                    source_id=o.source_id,
                    epistemic="explicit" if o.mode == "explicit" else "strongly_inferred",
                    units=o.units,
                    confidence=o.confidence,
                    evidence_span=o.evidence,
                )
            )
            row = {
                "predicate": o.predicate, "value": o.value,
                "confidence": round(o.confidence, 2), "basis": o.basis,
                "source_id": o.source_id, "evidence": (o.evidence or "")[:160],
            }
            (emitted_summary_explicit if o.mode == "explicit" else emitted_summary_inferred).append(row)

        summary = {
            "engine": "robot_inference_v1",
            "explicit": emitted_summary_explicit,
            "inferred": emitted_summary_inferred,
            "capabilities": _capability_summary(grounded),
            "workflows": _phase4_workflows(grounded),
        }
        return extra, summary
    except Exception:
        return [], None
