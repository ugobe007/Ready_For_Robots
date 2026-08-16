"""
Generic capability signals from product-page text → RDD-aligned families.

No OEM allowlists. Only evidence backed by page/description text.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class CapabilitySignal:
    key: str
    label: str
    confidence: float
    excerpt: str | None = None


@dataclass
class CapabilityProfile:
    robot_name: str
    capabilities: list[CapabilitySignal] = field(default_factory=list)
    families: list[dict[str, Any]] = field(default_factory=list)  # {id, confidence}
    evidence_count: int = 0
    understood: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "robot_name": self.robot_name,
            "capabilities": [
                {
                    "key": c.key,
                    "label": c.label,
                    "confidence": c.confidence,
                    "excerpt": c.excerpt,
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
        r"\b(omnidirectional|mobile\s+base|autonomous\s+mobile|wheeled\s+base|"
        r"\bamr\b|navigat(?:e|ion)|self[- ]driving|mobile\s+manipulation|"
        r"mobile\s+robot|factory\s+floor)\b",
        re.I,
    )),
    ("dual_arm", "Dual-arm manipulation", re.compile(
        r"\b(dual[- ]arm|two\s+arms|both\s+arms|bimanual)\b",
        re.I,
    )),
    ("single_arm", "Arm manipulation", re.compile(
        r"\b((?:robot(?:ic)?\s+)?arm|manipulator\s+arm|6[- ]?axis|7[- ]?axis)\b",
        re.I,
    )),
    ("dexterous", "Dexterous hands / end effectors", re.compile(
        r"\b(dexterous|multi[- ]finger|robot(?:ic)?\s+hand|gripper|end[- ]effector|eoat)\b",
        re.I,
    )),
    ("load_unload", "Load / unload objects", re.compile(
        r"\b(load(?:s|ing)?\s+(?:and\s+)?unload|machine\s+tend(?:ing)?|"
        r"pick\s+and\s+place|pick[- ]and[- ]place)\b",
        re.I,
    )),
    ("material_transport", "Material transport", re.compile(
        r"\b(material\s+(?:handling|transport|movement)|tote|cart\s+transport|"
        r"point[- ]of[- ]use|replenish(?:ment)?|kitting|goods[- ]to[- ]person)\b",
        re.I,
    )),
    ("machine_interaction", "Machine interaction", re.compile(
        r"\b(cnc|machine\s+tend(?:ing)?|spindle|fixture|machine\s+shop|"
        r"manufacturing\s+cell)\b",
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
        r"\b(\d+\+?\s*(?:hr|hrs|hour|hours)\s+(?:runtime|run\s*time|battery)|"
        r"long[- ]duration|multi[- ]shift|24\s*/\s*7)\b",
        re.I,
    )),
    ("payload", "Industrial payload", re.compile(
        r"\b(payload|load\s+capacity|\d+\s*(?:lb|lbs|kg)\s*(?:per\s+arm|/arm)?)\b",
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


def build_capability_profile(
    *,
    text: str,
    robot_name: str | None = None,
    page_title: str | None = None,
    manufacturer: str | None = None,
    model: str | None = None,
    chip: str | None = None,
) -> CapabilityProfile:
    """Extract capabilities from evidence text and/or a visitor chip prior."""
    name = (robot_name or model or manufacturer or page_title or "your robot").strip()
    if page_title and not robot_name and not model:
        # Prefer left side of title separators
        name = re.split(r"\s+[|\-—]\s+", page_title)[0].strip() or name

    profile = CapabilityProfile(robot_name=name[:120])
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
            )
        )
        profile.evidence_count = 1
        profile.understood = True
        return profile

    if not blob:
        return profile

    for key, label, pattern in CAPABILITY_PATTERNS:
        match = pattern.search(blob)
        if not match:
            continue
        profile.capabilities.append(
            CapabilitySignal(
                key=key,
                label=label,
                confidence=0.8,
                excerpt=match.group(0)[:160],
            )
        )

    profile.evidence_count = len(profile.capabilities)
    profile.families = _families_from_capabilities(profile.capabilities)
    # Minimum understanding: at least one strong capability signal
    profile.understood = profile.evidence_count >= 2 or any(
        c.key in {"mobile", "dual_arm", "scrub", "inspect", "load_unload", "dexterous"}
        for c in profile.capabilities
    )
    return profile


def _families_from_capabilities(caps: list[CapabilitySignal]) -> list[dict[str, Any]]:
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
    if "mobile" in keys and (
        "dual_arm" in keys
        or "single_arm" in keys
        or "dexterous" in keys
        or "load_unload" in keys
    ):
        bump("mobile_manipulation", 3.5)
    if "mobile" in keys or "material_transport" in keys:
        bump("transport_amr", 2.0 if "dual_arm" not in keys else 1.2)
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
