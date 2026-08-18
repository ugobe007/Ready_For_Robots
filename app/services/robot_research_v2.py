"""
Robot Research Agent v2 — evidence-backed capability extraction (M1 narrow reopen).

Reason for reopen (Understanding v1.0):
    manufacturer capability narrative + structured product data present →
    material robot capabilities absent.

v1 fact extraction is pure regex/table matching. It can visit a manufacturer
site full of explicit capability evidence (e.g. 1X NEO: humanoid, bipedal,
autonomous navigation, dexterous 22–25 DoF hands, 7-DoF arms, 55 lb carry) and
still return capabilities=[] because none of those phrasings matched a regex.

This module behaves like a robotics analyst first, a parser second:

    AI discovers meaning  →  code enforces truth

It reads the ALREADY-FETCHED evidence pack (same pages v1 fetched), asks an LLM
to produce a typed, provenance-carrying product model, then DETERMINISTICALLY
validates every claim against the source text before converting it into the
EXISTING RobotFact predicate schema. Nothing reaches the profile unless its
evidence is present in the fetched pages. The frozen matcher and
derive_capabilities are unchanged — v2 only feeds them facts v1's regex missed.

Enabled with ROBOT_RESEARCH_V2=1. Always fails open to v1 (never worse).
No per-vendor branches (no `if 1x`, no `if humanoid`).
"""
from __future__ import annotations

import json
import os
import re
from typing import Any, Optional

from app.services.robot_understanding_v1.models import RobotFact

# ── Config ──────────────────────────────────────────────────────────────────

_MAX_CHARS_PER_SOURCE = 5000
_MAX_SOURCES = 8
_AI_TIMEOUT_SEC = 30.0


def research_v2_enabled() -> bool:
    return (os.getenv("ROBOT_RESEARCH_V2") or "").strip().lower() in ("1", "true", "yes")


# ── Controlled vocabularies (map rich analyst output → frozen predicates) ─────

# Morphology → product_class values that derive_capabilities already understands.
_MORPHOLOGY_TO_CLASS = {
    "humanoid": "humanoid",
    "mobile_manipulator": "mobile_manipulator",
    "mobile manipulator": "mobile_manipulator",
    "amr": "amr",
    "autonomous_mobile_robot": "amr",
    "quadruped": "quadruped",
    "legged": "quadruped",
    "autonomous_scrubber": "autonomous_scrubber",
    "scrubber": "autonomous_scrubber",
    "cleaning_robot": "autonomous_scrubber",
    "cobot": "cobot",
    "collaborative_arm": "cobot",
    "robot_arm": "manipulator",
    "manipulator": "manipulator",
    "arm": "arm",
}

# Rich capability keys the analyst may emit (for display + provenance).
_KNOWN_CAP_KEYS = frozenset(
    {
        "mobile",
        "navigate",
        "walk",
        "whole_body_locomotion",
        "carry",
        "lift",
        "grasp",
        "pick",
        "place",
        "push",
        "pull",
        "open",
        "tool_use",
        "two_arm_manipulation",
        "dexterous_manipulation",
        "whole_body_manipulation",
        "in_hand_manipulation",
        "object_handling",
        "human_interaction",
        "hard_floor_scrub",
        "tote_transport",
        "load_unload",
        "inspect",
    }
)

_MANIP_CAP_KEYS = frozenset(
    {
        "grasp",
        "pick",
        "place",
        "push",
        "pull",
        "open",
        "tool_use",
        "dexterous_manipulation",
        "whole_body_manipulation",
        "in_hand_manipulation",
        "object_handling",
    }
)


# ── Evidence pack + provenance ────────────────────────────────────────────────

def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).strip()


def _build_pack(collected: list, home_text: str = "") -> tuple[str, list[dict[str, Any]]]:
    """Return (prompt_pack_text, source_index_map). Index maps to source ids."""
    pack_lines: list[str] = []
    index_map: list[dict[str, Any]] = []
    seen = 0
    for c in collected[:_MAX_SOURCES]:
        page = getattr(c, "page", None)
        src = getattr(c, "source", None)
        text = (getattr(page, "text", "") or "")[:_MAX_CHARS_PER_SOURCE]
        if not text.strip():
            continue
        idx = seen
        index_map.append(
            {
                "index": idx,
                "source_id": getattr(src, "id", f"src_{idx}"),
                "url": getattr(src, "url", "") or getattr(page, "final_url", ""),
                "type": getattr(src, "source_type", "other"),
            }
        )
        pack_lines.append(f"[SOURCE {idx}] ({index_map[-1]['type']}) {index_map[-1]['url']}\n{text}")
        seen += 1
    return "\n\n".join(pack_lines), index_map


def _evidence_supported(evidence: str, pack_norm: str) -> bool:
    """The quote (or a strong shingle of it) must actually appear in the fetched pages."""
    ev = _norm(evidence)
    if len(ev) < 4:
        return False
    if ev in pack_norm:
        return True
    # Fall back to a 5-word shingle match to tolerate light paraphrase/truncation.
    words = ev.split()
    if len(words) >= 5:
        for i in range(0, len(words) - 4):
            shingle = " ".join(words[i : i + 5])
            if shingle in pack_norm:
                return True
    return False


# The evidence quote must pertain to the specific claim — not just exist on the page.
# This is what stops "enhances productivity by more than 2X" → arm_count=2, or
# "dynamic task interleaving" → gripper. General rule; no per-vendor logic.
_CLAIM_KEYWORDS: dict[str, tuple[str, ...]] = {
    "arm_count": ("arm", "arms", "manipulator", "limb"),
    "has_dexterous_hands": ("hand", "hands", "finger", "dexter", "dof", "degrees of freedom", "grip"),
    "end_effector": ("gripper", "hand", "end effector", "suction", "vacuum", "finger", "claw", "grasp", "arm", "manipulat", "dexter"),
    "carrying_capacity": ("lb", "lbs", "pound", "kg", "kilogram", "payload", "capacity", "carry", "carrying", "lift"),
    "reach_or_workspace": ("reach", "workspace", "span", "arm length"),
    "battery_runtime": ("hour", "hours", "hr", "runtime", "battery", "operation", "operating"),
    "has_mobile_base": ("mobile", "navigat", "autonomous", "lidar", "wheel", "drive", "biped", "leg", "locomot", "walk"),
    "autonomous_navigation": ("navigat", "autonomous", "lidar", "slam", "self driving", "self-driving"),
    "mobility_architecture": ("biped", "leg", "wheel", "omnidirection", "track", "quadruped", "drive"),
    "supports_hard_floor_scrubbing": ("scrub", "clean", "floor", "wash", "mop"),
    "supports_tote_handling": ("tote", "bin", "cart", "container", "goods", "payload", "carry", "transport"),
    "claims_warehouse_transport": ("warehouse", "transport", "goods", "tote", "bin", "cart", "fulfil"),
    "claims_load_unload": ("load", "unload"),
}

_CLASS_KEYWORDS: dict[str, tuple[str, ...]] = {
    "humanoid": ("humanoid", "bipedal", "human like", "human-like"),
    "mobile_manipulator": ("mobile manipulator", "manipulat"),
    "amr": ("amr", "autonomous mobile", "mobile robot", "lidar", "navigat", "goods", "warehouse"),
    "quadruped": ("quadruped", "legged", "four legged", "four-legged"),
    "autonomous_scrubber": ("scrub", "clean", "floor", "wash"),
    "cobot": ("cobot arm", "robot arm", "manipulator", "collaborative arm", "axis"),
    "manipulator": ("manipulator", "robot arm", "axis"),
    "arm": ("robot arm", "manipulator"),
}

# Manipulation-implying capability keys are only credible when the quote mentions
# manipulation hardware — not warehouse/pick process language.
_MANIP_HW_KEYWORDS = ("arm", "hand", "gripper", "manipulat", "grasp", "finger", "dexter", "end effector")

# Words whose bare stem produces false positives (arm↔warm, hand↔handles/handling).
# These require an exact whole-word token; everything else matches by word-start stem.
_AMBIGUOUS_WORDS = frozenset({"arm", "arms", "hand", "hands", "leg", "legs"})


def _num(value: Any) -> Optional[float]:
    try:
        return float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def _kw_hit(ev_norm: str, ev_tokens: list[str], kw: str) -> bool:
    """Word-boundary keyword match. Phrases → substring; ambiguous words → exact
    token; stems (manipulat, navigat, gripper…) → word-start prefix."""
    if " " in kw:
        return kw in ev_norm
    if kw in _AMBIGUOUS_WORDS:
        return kw in ev_tokens
    return any(t.startswith(kw) for t in ev_tokens)


def _claim_supported(predicate: str, value: Any, evidence: str) -> bool:
    """Evidence must pertain to THIS claim (keywords), and quote specific numbers."""
    ev = _norm(evidence)
    if not ev:
        return False
    tokens = ev.split()
    # Specific numeric specs must actually be quoted (prevents fabricated values).
    if predicate in ("arm_count", "carrying_capacity", "reach_or_workspace", "battery_runtime"):
        num = _num(value)
        if num is None:
            return False
        cands = set()
        if num == int(num):
            cands.add(str(int(num)))
        cands.add(str(num))
        # Use word-boundary matching to prevent substring false positives (5 in 55).
        if not any(c and (f" {c} " in f" {ev} " or ev.startswith(f"{c} ") or ev.endswith(f" {c}")) for c in cands):
            return False
    if predicate == "product_class":
        kws = _CLASS_KEYWORDS.get(str(value).lower(), ())
        return any(_kw_hit(ev, tokens, k) for k in kws)
    kws = _CLAIM_KEYWORDS.get(predicate, ())
    if kws:
        return any(_kw_hit(ev, tokens, k) for k in kws)
    return True


def _cap_display_supported(key: str, evidence: str, pack_norm: str) -> bool:
    """Guard the display-capability list: manipulation claims need hardware evidence."""
    if not _evidence_supported(evidence, pack_norm):
        return False
    ev = _norm(evidence)
    tokens = ev.split()
    if key in _MANIP_CAP_KEYS or key == "two_arm_manipulation":
        return any(_kw_hit(ev, tokens, k) for k in _MANIP_HW_KEYWORDS)
    return True


# ── LLM extraction ────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = (
    "You are a professional robotics analyst. You are given manufacturer evidence "
    "pages for a robot. Determine what the robot actually is and what it can "
    "physically do, using ONLY the provided pages. For every material claim you "
    "MUST quote the exact supporting text verbatim from the pages and cite the "
    "SOURCE index it came from. If something is not established in the pages, mark "
    "it unknown — never guess or use outside knowledge. Output strict JSON only."
)


def _user_prompt(company: str, product: str, pack: str) -> str:
    schema = {
        "company_name": "string (the manufacturer/organization name, from evidence)",
        "product": {
            "name": "string",
            "categories": ["e.g. Humanoid, Mobile Manipulator, Indoor Service Robot"],
            "morphology": "one of: humanoid, mobile_manipulator, amr, quadruped, autonomous_scrubber, cobot, manipulator, arm, other",
            "capabilities": [
                {
                    "key": "one of: mobile, navigate, walk, carry, lift, grasp, pick, place, push, pull, open, tool_use, two_arm_manipulation, dexterous_manipulation, whole_body_manipulation, in_hand_manipulation, object_handling, human_interaction, hard_floor_scrub, tote_transport, load_unload, inspect",
                    "evidence": "verbatim quote from a SOURCE page",
                    "source_index": 0,
                    "confidence": "high|medium|low",
                }
            ],
            "specs": {
                "arm_count": {"value": 2, "evidence": "verbatim", "source_index": 0},
                "carrying_capacity": {"value": 55, "units": "lb", "evidence": "verbatim", "source_index": 0},
                "reach": {"value": 1.0, "units": "m", "evidence": "verbatim", "source_index": 0},
                "runtime_hours": {"value": 4, "evidence": "verbatim", "source_index": 0},
                "has_dexterous_hands": {"value": True, "evidence": "verbatim", "source_index": 0},
                "autonomous_navigation": {"value": True, "evidence": "verbatim", "source_index": 0},
                "bipedal": {"value": True, "evidence": "verbatim", "source_index": 0},
            },
            "workflows": ["demonstrated or explicitly claimed physical tasks, short phrases"],
            "operating_environment": ["e.g. indoor, home, warehouse"],
            "unknowns": ["important attributes not established in the evidence"],
        },
    }
    return (
        f"Target company: {company}\nTarget product: {product or '(unknown — pick the primary robot)'}\n\n"
        f"Return JSON with EXACTLY this shape (omit spec/capability entries you cannot ground):\n"
        f"{json.dumps(schema, indent=2)}\n\n"
        f"Every 'evidence' value must be copied verbatim from a [SOURCE n] block below, and "
        f"'source_index' must be that n. Do not include any claim you cannot quote.\n\n"
        f"=== EVIDENCE PAGES ===\n{pack}"
    )


def _ai_extract(company: str, product: str, pack: str) -> Optional[dict[str, Any]]:
    from app.services.llm_client import llm_json_completion

    raw = llm_json_completion(
        _SYSTEM_PROMPT,
        _user_prompt(company, product, pack),
        max_tokens=2000,
        temperature=0.1,
        timeout=_AI_TIMEOUT_SEC,
    )
    if not raw:
        return None
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        # Tolerate stray prose around the JSON object.
        m = re.search(r"\{.*\}", raw, re.S)
        if not m:
            return None
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            return None


# ── Convert validated extraction → RobotFacts (existing predicate schema) ─────

def _source_id_for(index: Any, index_map: list[dict[str, Any]]) -> Optional[str]:
    try:
        i = int(index)
    except (TypeError, ValueError):
        return None
    for entry in index_map:
        if entry["index"] == i:
            return entry["source_id"]
    return None


def _facts_from_extraction(
    extraction: dict[str, Any],
    *,
    subject: str,
    index_map: list[dict[str, Any]],
    pack_norm: str,
    existing_predicates: set[str],
) -> tuple[list[RobotFact], dict[str, Any]]:
    product = extraction.get("product") or {}
    caps = product.get("capabilities") or []
    specs = product.get("specs") or {}
    facts: list[RobotFact] = []
    accepted_caps: list[dict[str, Any]] = []

    default_src = index_map[0]["source_id"] if index_map else "research_v2"

    def emit(predicate: str, value: Any, *, evidence: str, source_index: Any, units: str | None = None):
        if predicate in existing_predicates:
            return  # do not clobber a regex-extracted explicit fact
        if not _evidence_supported(evidence, pack_norm):
            return  # quote must be from the fetched pages
        if not _claim_supported(predicate, value, evidence):
            return  # quote must actually pertain to this claim (no "2X" → arm_count=2)
        sid = _source_id_for(source_index, index_map) or default_src
        facts.append(
            RobotFact.create(
                subject,
                predicate,
                value,
                source_id=sid,
                epistemic="explicit",
                units=units,
                confidence=0.8,
                evidence_span=evidence,
            )
        )
        existing_predicates.add(predicate)

    # 1) Morphology → product_class (drives manipulate/mobile inference). Emit only
    # when class-appropriate evidence exists (emit() enforces _claim_supported).
    morph = str(product.get("morphology") or "").strip().lower()
    cls = _MORPHOLOGY_TO_CLASS.get(morph)
    if cls:
        morph_word = morph.replace("_", " ")
        morph_ev = ""
        morph_src: Any = 0
        # Prefer the morphology word itself when it appears verbatim in the pages
        # AND passes the length check (>= 4 chars normalized).
        if morph_word in pack_norm and len(_norm(morph_word)) >= 4 and _claim_supported("product_class", cls, morph_word):
            morph_ev = morph_word
        else:
            for c in caps:
                cev = c.get("evidence") or ""
                if _evidence_supported(cev, pack_norm) and _claim_supported("product_class", cls, cev):
                    morph_ev = cev
                    morph_src = c.get("source_index", 0)
                    break
        if morph_ev:
            emit("product_class", cls, evidence=morph_ev, source_index=morph_src)

    # 2) Rich capabilities → validated → predicate facts.
    manip_seen = False
    for c in caps:
        key = str(c.get("key") or "").strip().lower()
        ev = c.get("evidence") or ""
        if key not in _KNOWN_CAP_KEYS:
            continue
        if not _cap_display_supported(key, ev, pack_norm):
            continue
        accepted_caps.append({"key": key, "evidence": ev[:240], "confidence": c.get("confidence")})
        si = c.get("source_index", 0)
        if key in ("mobile", "navigate", "walk", "whole_body_locomotion"):
            emit("has_mobile_base", True, evidence=ev, source_index=si)
            if key == "navigate":
                emit("autonomous_navigation", True, evidence=ev, source_index=si)
        if key == "two_arm_manipulation":
            emit("arm_count", 2, evidence=ev, source_index=si)
            manip_seen = True
        if key in ("dexterous_manipulation", "in_hand_manipulation"):
            emit("has_dexterous_hands", True, evidence=ev, source_index=si)
            emit("end_effector", "dexterous_hand", evidence=ev, source_index=si)
            manip_seen = True
        if key in _MANIP_CAP_KEYS:
            manip_seen = True
        if key == "hard_floor_scrub":
            emit("supports_hard_floor_scrubbing", True, evidence=ev, source_index=si)
        if key == "tote_transport":
            emit("supports_tote_handling", True, evidence=ev, source_index=si)
        if key == "load_unload":
            emit("claims_load_unload", True, evidence=ev, source_index=si)

    # If the analyst grounded manipulation actions but no arm/hand fact emitted,
    # record an end-effector so derive_capabilities can see manipulation.
    if manip_seen and "end_effector" not in existing_predicates and "arm_count" not in existing_predicates:
        # Only when we have a supporting manipulation quote.
        m = next(
            (c for c in accepted_caps if c["key"] in _MANIP_CAP_KEYS or c["key"] == "two_arm_manipulation"),
            None,
        )
        if m:
            emit("end_effector", "gripper", evidence=m["evidence"], source_index=0)

    # 3) Numeric / boolean specs → predicate facts.
    def spec(name: str):
        s = specs.get(name)
        return s if isinstance(s, dict) else None

    sp = spec("arm_count")
    if sp and _num(sp.get("value")) and _evidence_supported(sp.get("evidence") or "", pack_norm):
        emit("arm_count", int(_num(sp.get("value"))), evidence=sp.get("evidence") or "", source_index=sp.get("source_index", 0))

    sp = spec("carrying_capacity")
    if sp and _num(sp.get("value")) and _evidence_supported(sp.get("evidence") or "", pack_norm):
        emit("carrying_capacity", _num(sp.get("value")), units=(sp.get("units") or None), evidence=sp.get("evidence") or "", source_index=sp.get("source_index", 0))

    sp = spec("reach")
    if sp and _num(sp.get("value")) and _evidence_supported(sp.get("evidence") or "", pack_norm):
        emit("reach_or_workspace", _num(sp.get("value")), units=(sp.get("units") or "m"), evidence=sp.get("evidence") or "", source_index=sp.get("source_index", 0))

    sp = spec("runtime_hours")
    if sp and _num(sp.get("value")) and _evidence_supported(sp.get("evidence") or "", pack_norm):
        emit("battery_runtime", _num(sp.get("value")), units="hr", evidence=sp.get("evidence") or "", source_index=sp.get("source_index", 0))

    sp = spec("has_dexterous_hands")
    if sp and bool(sp.get("value")) and _evidence_supported(sp.get("evidence") or "", pack_norm):
        emit("has_dexterous_hands", True, evidence=sp.get("evidence") or "", source_index=sp.get("source_index", 0))
        emit("end_effector", "dexterous_hand", evidence=sp.get("evidence") or "", source_index=sp.get("source_index", 0))

    sp = spec("autonomous_navigation")
    if sp and bool(sp.get("value")) and _evidence_supported(sp.get("evidence") or "", pack_norm):
        emit("autonomous_navigation", True, evidence=sp.get("evidence") or "", source_index=sp.get("source_index", 0))
        emit("has_mobile_base", True, evidence=sp.get("evidence") or "", source_index=sp.get("source_index", 0))

    sp = spec("bipedal")
    if sp and bool(sp.get("value")) and _evidence_supported(sp.get("evidence") or "", pack_norm):
        emit("mobility_architecture", "bipedal", evidence=sp.get("evidence") or "", source_index=sp.get("source_index", 0))
        emit("has_mobile_base", True, evidence=sp.get("evidence") or "", source_index=sp.get("source_index", 0))

    summary = {
        "categories": [str(x) for x in (product.get("categories") or [])][:8],
        "capabilities": accepted_caps,
        "workflows": [str(x) for x in (product.get("workflows") or [])][:12],
        "operating_environment": [str(x) for x in (product.get("operating_environment") or [])][:6],
        "unknowns": [str(x) for x in (product.get("unknowns") or [])][:12],
        "fact_count": len(facts),
    }
    return facts, summary


# ── Public entry ──────────────────────────────────────────────────────────────

def enrich_facts(
    collected: list,
    *,
    subject: str,
    company: str,
    product: str,
    existing_facts: list[RobotFact],
) -> tuple[list[RobotFact], Optional[dict[str, Any]]]:
    """
    Run the AI research pass and return (extra_facts, research_v2_summary).

    Fails open: any error or missing provider returns ([], None) so the caller
    keeps the deterministic v1 profile unchanged.
    """
    if not research_v2_enabled():
        return [], None
    try:
        pack, index_map = _build_pack(collected)
        if not pack.strip() or not index_map:
            return [], None
        extraction = _ai_extract(company, product or subject, pack)
        if not isinstance(extraction, dict):
            return [], None
        pack_norm = _norm(pack)
        existing_predicates = {
            f.predicate
            for f in existing_facts
            if (f.epistemic or "") not in ("unknown", "contradicted")
        }
        facts, summary = _facts_from_extraction(
            extraction,
            subject=subject,
            index_map=index_map,
            pack_norm=pack_norm,
            existing_predicates=existing_predicates,
        )
        return facts, summary
    except Exception:
        return [], None
