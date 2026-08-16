"""
Generic capability signals from product-page text → RDD-aligned families.

No OEM allowlists. Only evidence backed by page/description text.
Separates confirmed (direct language) from inferred (class priors).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Literal

TruthState = Literal["confirmed", "inferred"]


@dataclass
class CapabilitySignal:
    key: str
    label: str
    confidence: float
    excerpt: str | None = None
    truth_state: TruthState = "confirmed"


@dataclass
class CapabilityProfile:
    robot_name: str
    capabilities: list[CapabilitySignal] = field(default_factory=list)
    families: list[dict[str, Any]] = field(default_factory=list)  # {id, confidence}
    evidence_count: int = 0
    understood: bool = False
    robot_class: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "robot_name": self.robot_name,
            "robot_class": self.robot_class,
            "capabilities": [
                {
                    "key": c.key,
                    "label": c.label,
                    "confidence": c.confidence,
                    "excerpt": c.excerpt,
                    "truth_state": c.truth_state,
                }
                for c in self.capabilities
            ],
            "families": self.families,
            "evidence_count": self.evidence_count,
            "understood": self.understood,
        }


# (capability_key, label, pattern) — generic product language only
CAPABILITY_PATTERNS: list[tuple[str, str, re.Pattern[str]]] = [
    ("mobile", "Mobile / autonomous movement", re.compile(
        r"\b("
        r"omnidirectional|mobile\s+base|autonomous\s+mobile|wheeled\s+base|"
        r"\bamr\b|navigat(?:e|ion)|self[- ]driving|mobile\s+manipulation|"
        r"mobile\s+robot|factory\s+floor|facility\s+floors?|"
        r"fully\s+autonomous|autonomous\s+(?:tool|operation|navigat)|"
        r"bipedal|walk(?:s|ing)?\s+(?:across|through|on)|"
        r"human[- ]centric\s+(?:form|design)|spaces?\s+where\s+people\s+already\s+work"
        r")\b",
        re.I,
    )),
    ("humanoid", "Humanoid form", re.compile(
        r"\b(humanoid|bipedal\s+robot|biped\s+robot)\b",
        re.I,
    )),
    ("dual_arm", "Dual-arm manipulation", re.compile(
        r"\b(dual[- ]arm|two\s+arms|both\s+arms|bimanual)\b",
        re.I,
    )),
    ("single_arm", "Arm manipulation", re.compile(
        r"\b((?:robot(?:ic)?\s+)?arm|manipulator\s+arm|6[- ]?axis|7[- ]?axis|"
        r"manipulat(?:e|es|ing|ion)\s+objects?)\b",
        re.I,
    )),
    ("dexterous", "Dexterous hands / end effectors", re.compile(
        r"\b(dexterous|multi[- ]finger|robot(?:ic)?\s+hand|gripper|end[- ]effector|eoat)\b",
        re.I,
    )),
    ("carry", "Carry / transport objects", re.compile(
        r"\b(carry(?:ing)?\s+capacity|carries?\s+(?:objects?|totes?|loads?)|"
        r"payload\s+capacity|load\s+capacity)\b",
        re.I,
    )),
    ("tote_handling", "Tote handling", re.compile(
        r"\b(totes?|tote\s+(?:handl|mov|pick|transport|workflow))\b",
        re.I,
    )),
    ("load_unload", "Load / unload objects", re.compile(
        r"\b(load(?:s|ing)?\s+(?:and\s+)?unload|unload(?:s|ing)?|"
        r"machine\s+tend(?:ing)?|pick\s+and\s+place|pick[- ]and[- ]place|"
        r"load(?:s|ing)?\s+(?:and\s+)?unload(?:ing)?\s+containers?|"
        r"container\s+(?:load|unload))\b",
        re.I,
    )),
    ("line_feeding", "Line feeding", re.compile(
        r"\b(line[- ]feed(?:ing)?|line[- ]side|milk[- ]run)\b",
        re.I,
    )),
    ("palletizing", "Palletize / depalletize", re.compile(
        r"\b(palletiz(?:e|es|ing|ation)|depalletiz(?:e|es|ing|ation)|"
        r"build(?:s|ing)?\s+(?:outbound\s+)?pallets?|stack(?:s|ing)?\s+(?:onto\s+)?pallets?)\b",
        re.I,
    )),
    ("material_transport", "Material transport", re.compile(
        r"\b(material\s+(?:handling|transport|movement)|cart\s+transport|"
        r"point[- ]of[- ]use|replenish(?:ment)?|kitting|goods[- ]to[- ]person|"
        r"putwall|workstation|between\s+carts)\b",
        re.I,
    )),
    ("machine_interaction", "Machine interaction", re.compile(
        r"\b(cnc|machine\s+tend(?:ing)?|spindle|fixture|machine\s+shop|"
        r"manufacturing\s+cell)\b",
        re.I,
    )),
    ("amr_interaction", "AMR / automation integration", re.compile(
        r"\b(amr\s+(?:load|unload|hand[- ]off|interaction)|"
        r"integrat(?:e|es|ion)\s+with\s+(?:existing\s+)?(?:warehouse\s+)?(?:amrs?|wms|wes)|"
        r"including\s+amrs?)\b",
        re.I,
    )),
    ("scrub", "Floor cleaning", re.compile(
        r"\b(floor\s+scrub|scrubber|autonomous\s+clean(?:ing)?|hard[- ]floor)\b",
        re.I,
    )),
    ("inspect", "Inspection", re.compile(
        r"\b(inspect(?:ion)?|thermograph|gauge\s+read|patrol\s+route|spot\s+check)\b",
        re.I,
    )),
    ("industrial_runtime", "Long-duration industrial operation", re.compile(
        r"\b("
        r"\d+\+?\s*(?:hr|hrs|hour|hours)\s+(?:runtime|run\s*time|battery(?:\s+life)?)"
        r"|"
        r"\d+\+?\s*(?:hr|hrs|hour|hours)\s+battery"
        r"|"
        r"(?:runtime|run\s*time|battery\s+life)[^\d]{0,20}\d+\+?\s*(?:hr|hrs|hour|hours)"
        r"|"
        r"long[- ]duration|multi[- ]shift|24\s*/\s*7|continuous\s+shifts?"
        r")\b",
        re.I,
    )),
    ("payload", "Industrial payload", re.compile(
        r"\b("
        r"payload|load\s+capacity|"
        r"\d+\s*(?:lb|lbs|kg|pound|pounds)\s*(?:per\s+arm|/arm|carrying\s+capacity)?"
        r"|"
        r"\d+\s*(?:pound|pounds|lb|lbs)\s+carrying"
        r")\b",
        re.I,
    )),
]

# Visitor recovery chips → family priors (no page required)
CHIP_TO_FAMILIES: dict[str, list[str]] = {
    "moves_materials": ["transport_amr", "mobile_manipulation"],
    "manipulates": ["manipulator", "mobile_manipulation"],
    "cleans": ["floor_scrub"],
    "inspects": ["inspection_mobile"],
    "other": ["transport_amr", "manipulator"],
}

# Class priors — marked inferred, never invent absent workflows
CLASS_INFERRED_CAPS: dict[str, list[tuple[str, str, float]]] = {
    "humanoid": [
        ("mobile", "Mobile / bipedal movement", 0.55),
        ("carry", "Object carry (humanoid form)", 0.5),
    ],
}


def build_capability_profile(
    *,
    text: str,
    robot_name: str | None = None,
    page_title: str | None = None,
    manufacturer: str | None = None,
    model: str | None = None,
    chip: str | None = None,
    robot_class: str | None = None,
) -> CapabilityProfile:
    """Extract capabilities from evidence text and/or a visitor chip prior."""
    name = (robot_name or model or manufacturer or page_title or "your robot").strip()
    if page_title and not robot_name and not model:
        name = re.split(r"\s+[|\-—]\s+", page_title)[0].strip() or name

    # Normalize class
    rclass = (robot_class or "").strip().lower() or None
    if rclass == "humanoid" or (text and re.search(r"\bhumanoid\b", text, re.I)):
        rclass = rclass or "humanoid"

    profile = CapabilityProfile(robot_name=name[:120], robot_class=rclass)
    blob = (text or "").strip()

    if chip and chip in CHIP_TO_FAMILIES:
        for fam in CHIP_TO_FAMILIES[chip]:
            profile.families.append({"id": fam, "confidence": 0.7})
        profile.capabilities.append(
            CapabilitySignal(
                key=f"chip_{chip}",
                label=chip.replace("_", " ").title(),
                confidence=0.7,
                excerpt="Visitor-selected capability",
                truth_state="inferred",
            )
        )
        profile.evidence_count = 1
        profile.understood = True
        return profile

    if not blob:
        return profile

    seen_keys: set[str] = set()
    for key, label, pattern in CAPABILITY_PATTERNS:
        match = pattern.search(blob)
        if not match:
            continue
        if key in seen_keys:
            continue
        seen_keys.add(key)
        profile.capabilities.append(
            CapabilitySignal(
                key=key,
                label=label,
                confidence=0.85,
                excerpt=match.group(0)[:160],
                truth_state="confirmed",
            )
        )

    # Inferred class priors only fill gaps — never fabricate CNC/machine tending
    if rclass in CLASS_INFERRED_CAPS:
        for key, label, conf in CLASS_INFERRED_CAPS[rclass]:
            if key in seen_keys:
                continue
            profile.capabilities.append(
                CapabilitySignal(
                    key=key,
                    label=label,
                    confidence=conf,
                    excerpt=f"Inferred from robot class: {rclass}",
                    truth_state="inferred",
                )
            )
            seen_keys.add(key)

    profile.evidence_count = len(
        [c for c in profile.capabilities if c.truth_state == "confirmed"]
    )
    profile.families = _families_from_capabilities(profile.capabilities, rclass)
    confirmed_keys = {c.key for c in profile.capabilities if c.truth_state == "confirmed"}
    profile.understood = (
        profile.evidence_count >= 2
        or bool(
            confirmed_keys
            & {
                "mobile",
                "humanoid",
                "dual_arm",
                "scrub",
                "inspect",
                "load_unload",
                "dexterous",
                "tote_handling",
                "carry",
                "palletizing",
                "line_feeding",
            }
        )
        or (rclass == "humanoid" and profile.evidence_count >= 1)
    )
    return profile


def _families_from_capabilities(
    caps: list[CapabilitySignal],
    robot_class: str | None = None,
) -> list[dict[str, Any]]:
    keys = {c.key for c in caps}
    scores: dict[str, float] = {}

    def bump(fam: str, amt: float) -> None:
        scores[fam] = scores.get(fam, 0.0) + amt

    if "scrub" in keys:
        bump("floor_scrub", 3.0)
    if "inspect" in keys:
        bump("inspection_mobile", 3.0)
    if "dual_arm" in keys or "dexterous" in keys:
        bump("manipulator", 2.5)
        bump("mobile_manipulation", 2.0)
    if "single_arm" in keys or "load_unload" in keys or "machine_interaction" in keys:
        bump("manipulator", 2.0)
    if "humanoid" in keys or robot_class == "humanoid":
        bump("mobile_manipulation", 3.0)
        bump("manipulator", 1.8)
    if "tote_handling" in keys or "carry" in keys or "palletizing" in keys:
        bump("mobile_manipulation", 2.2)
        bump("transport_amr", 1.2)
    if "line_feeding" in keys or "material_transport" in keys:
        bump("mobile_manipulation", 1.8)
        bump("transport_amr", 1.5)
    if "mobile" in keys and (
        "dual_arm" in keys
        or "single_arm" in keys
        or "dexterous" in keys
        or "load_unload" in keys
        or "humanoid" in keys
        or "tote_handling" in keys
        or "carry" in keys
    ):
        bump("mobile_manipulation", 3.5)
    if "mobile" in keys or "material_transport" in keys:
        bump("transport_amr", 2.0 if "dual_arm" not in keys and "humanoid" not in keys else 1.2)
    if "material_transport" in keys and "mobile" in keys:
        bump("transport_amr", 1.0)
        bump("mobile_manipulation", 1.0)

    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    out: list[dict[str, Any]] = []
    for fam, raw in ranked:
        if raw < 1.5:
            continue
        out.append({"id": fam, "confidence": min(0.95, round(raw / 4.0, 2))})
    return out[:5]
