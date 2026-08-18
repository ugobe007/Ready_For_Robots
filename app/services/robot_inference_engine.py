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
    (_rx(r"\bautonomous\s+mobile\s+robot\b|\bamr\b"), "product_class", "amr", None, CONF["MEDIUM"]),
    (_rx(r"\bdexterous\b(?:\s+\w+){0,3}?\s+hands?\b|\bhands?\b(?:\s+\w+){0,3}?\s+dexter"),
     "has_dexterous_hands", True, None, CONF["HIGH"]),
    (_rx(r"\b(?:mobile\s+base|fully\s+mobile|omnidirectional|mecanum|holonomic|wheeled\s+base)\b"),
     "has_mobile_base", True, None, CONF["HIGH"]),
    (_rx(r"\b(?:bipedal|biped|two\s+legs|legged\s+locomotion)\b"),
     "mobility_architecture", "bipedal", None, CONF["HIGH"]),
    (_rx(r"\b(?:autonomous\s+navigation|autonomously\s+navigat\w*|self[-\s]navigat\w*|\blidar\b|\bslam\b)\b"),
     "autonomous_navigation", True, None, CONF["HIGH"]),
    (_rx(r"\b(?:gripper|end[-\s]effector|vacuum\s+gripper|suction\s+cup|parallel[-\s]jaw|two[-\s]finger)\b"),
     "end_effector", "gripper", None, CONF["MEDIUM"]),
    (_rx(r"\b(?:tote|goods[-\s]to[-\s]person|person[-\s]to[-\s]goods|order\s+picking|"
         r"move\s+(?:totes|carts|bins)|(?:tote|cart|bin)\s+(?:transport|movement|handling))\b"),
     "supports_tote_handling", True, None, CONF["MEDIUM"]),
    (_rx(r"\b(?:load\s+and\s+unload|loading\s+and\s+unloading|machine\s+tending|load/unload)\b"),
     "claims_load_unload", True, None, CONF["MEDIUM"]),
    (_rx(r"\b(?:hard[-\s]floor\s+scrub\w*|scrub\w*\s+floors?|cleans?\s+floors?)\b"),
     "supports_hard_floor_scrubbing", True, None, CONF["HIGH"]),
]


def _window(text: str, start: int, end: int, pad: int = 50) -> str:
    a = max(0, start - pad)
    b = min(len(text), end + pad)
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


def _phase1_detect(collected: list) -> list[Observation]:
    obs: list[Observation] = []
    for c in collected:
        page = getattr(c, "page", None)
        src = getattr(c, "source", None)
        sid = getattr(src, "id", None) or "inference"
        text = getattr(page, "text", "") or ""
        if not text.strip():
            continue
        for rx, predicate, value, units, conf in _BOOL_DETECTORS:
            m = rx.search(text)
            if m:
                obs.append(Observation(predicate, value, units, _window(text, m.start(), m.end()),
                                       sid, conf, "explicit"))
        arm = _detect_arm_count(text)
        if arm:
            obs.append(Observation("arm_count", arm[0], None, arm[1], sid, CONF["HIGH"], "explicit"))
        hd = _detect_hand_dof(text)
        if hd:
            obs.append(Observation("hand_dof", hd[0], None, hd[1], sid, CONF["HIGH"], "explicit"))
            obs.append(Observation("has_dexterous_hands", True, None, hd[1], sid, CONF["HIGH"], "explicit"))
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

    # Navigation or a mobility architecture implies a mobile base.
    if _has(grounded, "autonomous_navigation") and "has_mobile_base" not in grounded:
        add("has_mobile_base", True, None, ["autonomous_navigation"], CONF["HIGH"], "autonomous_navigation")
    if grounded.get("mobility_architecture") and "has_mobile_base" not in grounded:
        add("has_mobile_base", True, None, ["mobility_architecture"], CONF["HIGH"], "mobility_architecture")

    # Scrubber class implies hard-floor scrubbing.
    if _has(grounded, "product_class", "autonomous_scrubber") and "supports_hard_floor_scrubbing" not in grounded:
        add("supports_hard_floor_scrubbing", True, None, ["product_class=autonomous_scrubber"], CONF["HIGH"], "product_class")

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

        # PHASE 1 — detect additional explicit facts from the evidence pack.
        detected = _phase1_detect(collected)
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
