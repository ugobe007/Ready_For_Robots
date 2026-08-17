"""
Reconstruct WORK units from job / labor signal text onto primitives.v1.

Spine: docs/ontology/primitives.v1.json
Architecture: docs/rfr_intelligence_architecture.md

Job text → tasks / objects / origin–destination → ordered primitive codes.
Same codes are used for robot capability cards so Robot→Job and Job→Robot share one spine.

Rule-based v1 (no LLM). Evidence excerpts attached to every inferred primitive.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

from app.domain.enums import load_primitives_ontology

# Phrase → primitives. Patterns are applied against lowercased text.
# Order matters for template selection (first high-confidence family wins for primary WORK).
_FAMILY_PATTERNS: Tuple[Tuple[str, re.Pattern[str]], ...] = (
    (
        "tugger_line_replenishment",
        re.compile(
            r"\b(tugger|milk[- ]?run|tow\s+tractor|cart\s+train|line[- ]side\s+replenish|"
            r"line\s+replenishment|kanban\s+cart|pull\s+cart)\b",
            re.I,
        ),
    ),
    (
        "strong_transport",
        re.compile(
            r"\b(pallet(?:ized)?\s+loads?|powered\s+industrial\s+truck|\bpit\b|"
            r"forklift|reach\s+truck|pallet\s+jack|internal\s+transport|"
            r"move\s+pallet|transport\s+pallet|production\s+to\s+warehouse|"
            r"receiving.{0,40}(staging|outbound|warehouse)|dock\s+to\s+(storage|reserve))\b",
            re.I,
        ),
    ),
    (
        "mixed_material_handler",
        re.compile(
            r"\b(water\s+spider|mixed\s+cases?|case\s+handling|hand\s+stack|"
            r"pick.{0,20}stage.{0,20}deliver|irregular\s+skus?|dunnage)\b",
            re.I,
        ),
    ),
    (
        "trailer_yard",
        re.compile(r"\b(trailer\s+(entry|loading|unloading)|yard\s+jockey|dock\s+plate)\b", re.I),
    ),
    (
        "inventory_cycle_count",
        re.compile(r"\b(cycle\s+count|inventory\s+(count|audit)|rf\s+scan)\b", re.I),
    ),
)

# Evidence phrase → primitive codes + optional object/topology hints
_PHRASE_RULES: Tuple[Tuple[re.Pattern[str], Tuple[str, ...], Dict[str, Any]], ...] = (
    (
        re.compile(r"\b(pallet(?:ized)?\s+loads?|wooden\s+pallets?|acquire\s+(?:a\s+)?pallet|pallet\s+pickup)\b", re.I),
        ("eng.acquire_pallet_floor", "per.detect_pallet"),
        {"object": "pallet"},
    ),
    (
        re.compile(r"\b(high[- ]?rack|racked\s+pallet|putaway\s+to\s+rack|selectivity\s+rack)\b", re.I),
        ("eng.acquire_pallet_rack", "plc.rack_place", "man.lift_vertical"),
        {"object": "pallet"},
    ),
    (
        re.compile(r"\b(forklift|reach\s+truck|powered\s+industrial\s+truck|\bpit\b|pallet\s+jack)\b", re.I),
        ("eng.acquire_pallet_floor", "man.lift_vertical", "mob.navigate_indoor"),
        {"object": "pallet", "equipment": "pit"},
    ),
    (
        re.compile(r"\b(tugger|tow\s+tractor|cart\s+train|pin\s+hitch|hitch)\b", re.I),
        ("eng.tow_hitch", "eng.acquire_cart_or_tote", "tr.line_replenishment"),
        {"object": "cart", "equipment": "tugger"},
    ),
    (
        re.compile(r"\b(milk[- ]?run|line[- ]side|line\s+replenish|supermarket)\b", re.I),
        ("tr.line_replenishment", "plc.staging_place"),
        {"destination": "production"},
    ),
    (
        re.compile(r"\b(receiving|inbound\s+dock|dock\s+to)\b", re.I),
        ("tr.dock_to_storage", "mob.navigate_indoor"),
        {"origin": "receiving"},
    ),
    (
        re.compile(r"\b(staging|stage\s+inbound|staging\s+lanes?)\b", re.I),
        ("plc.staging_place",),
        {"destination": "staging"},
    ),
    (
        re.compile(r"\b(outbound|shipping|reserve\s+storage|warehouse)\b", re.I),
        ("tr.point_to_point",),
        {"destination": "warehouse"},
    ),
    (
        re.compile(r"\b(production\s+to\s+warehouse|finished\s+pallets?|finished\s+goods)\b", re.I),
        ("tr.point_to_point", "eng.acquire_pallet_floor", "plc.floor_place"),
        {"origin": "production", "destination": "warehouse", "object": "pallet"},
    ),
    (
        re.compile(r"\b(narrow\s+aisle|marked\s+aisles?)\b", re.I),
        ("mob.narrow_aisle", "mob.navigate_indoor"),
        {},
    ),
    (
        re.compile(r"\b(trailer|dock\s+plate|truck\s+loading)\b", re.I),
        ("mob.trailer_entry",),
        {"origin": "trailer"},
    ),
    (
        re.compile(r"\b(outdoor|yard\s+jockey|yard\s+move)\b", re.I),
        ("mob.outdoor_yard",),
        {},
    ),
    (
        re.compile(r"\b(mixed\s+traffic|pedestrian|safety\s+vest|human[- ]shared)\b", re.I),
        ("mob.navigate_mixed_traffic", "per.detect_human"),
        {},
    ),
    (
        re.compile(r"\b(case(?:s)?|carton(?:s)?|tote(?:s)?|hand\s+stack|piece\s+pick)\b", re.I),
        ("man.case_pick", "eng.acquire_cart_or_tote"),
        {"object": "case"},
    ),
    (
        re.compile(r"\b(wms|mes|rf\s+scan|scan\s+barcode|inventory\s+transaction)\b", re.I),
        ("int.wms_handshake", "per.localize"),
        {},
    ),
    (
        re.compile(r"\b(cycle\s+count|inventory\s+count)\b", re.I),
        ("per.localize", "int.wms_handshake"),
        {"task": "cycle_count"},
    ),
    (
        re.compile(r"\b(blocked\s+path|exception|damaged\s+(?:load|pallet)|call\s+for\s+help|andon)\b", re.I),
        ("exc.handle_blocked_path", "exc.call_for_help"),
        {},
    ),
    (
        re.compile(r"\b(floor\s+place|place\s+on\s+(?:the\s+)?floor|ground[- ]level)\b", re.I),
        ("plc.floor_place",),
        {},
    ),
    (
        re.compile(r"\b(point[- ]to[- ]point|fixed\s+routes?|travel\s+fixed)\b", re.I),
        ("tr.point_to_point", "mob.navigate_indoor"),
        {},
    ),
)

_FAMILY_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "strong_transport": {
        "task": "Move palletized loads between facility zones",
        "object": "pallet",
        "origin": "receiving",
        "destination": "staging",
        "action_chain": [
            "per.detect_pallet",
            "eng.acquire_pallet_floor",
            "man.lift_vertical",
            "mob.navigate_indoor",
            "mob.navigate_mixed_traffic",
            "tr.point_to_point",
            "plc.floor_place",
            "per.detect_human",
        ],
    },
    "tugger_line_replenishment": {
        "task": "Pull cart trains on timed line-replenishment routes",
        "object": "cart",
        "origin": "supermarket",
        "destination": "production",
        "action_chain": [
            "eng.tow_hitch",
            "eng.acquire_cart_or_tote",
            "mob.navigate_indoor",
            "mob.navigate_mixed_traffic",
            "tr.line_replenishment",
            "plc.staging_place",
            "per.detect_human",
            "int.human_handoff",
        ],
    },
    "mixed_material_handler": {
        "task": "Pick, stage, and deliver mixed cases with partial cart transport",
        "object": "case",
        "origin": "storage",
        "destination": "production",
        "action_chain": [
            "eng.acquire_cart_or_tote",
            "man.case_pick",
            "man.dexterous_adjust",
            "mob.navigate_indoor",
            "tr.line_replenishment",
            "plc.staging_place",
            "exc.call_for_help",
            "int.human_handoff",
        ],
    },
    "trailer_yard": {
        "task": "Load/unload trailers and yard moves",
        "object": "pallet",
        "origin": "trailer",
        "destination": "receiving",
        "action_chain": [
            "mob.trailer_entry",
            "eng.acquire_pallet_floor",
            "man.lift_vertical",
            "tr.dock_to_storage",
            "plc.floor_place",
        ],
    },
    "inventory_cycle_count": {
        "task": "Cycle count inventory",
        "object": "inventory",
        "origin": "storage",
        "destination": "storage",
        "action_chain": [
            "mob.navigate_indoor",
            "per.localize",
            "int.wms_handshake",
        ],
    },
    "unknown": {
        "task": "Unclassified material / labor work",
        "object": None,
        "origin": None,
        "destination": None,
        "action_chain": [],
    },
}

_PAYLOAD_LB = re.compile(
    r"(?:(\d{1,2}(?:,\d{3})+|\d{3,5})\s*-?\s*(?:lb|lbs|pounds)\b|"
    r"(?:capacity|forklift|pit|payload)[^\d]{0,24}(\d{1,2}(?:,\d{3})+|\d{3,5})\s*-?\s*(?:lb|lbs|pounds)\b)",
    re.I,
)
_PAYLOAD_KG = re.compile(
    r"(?:(\d{3,5})\s*kg\s*(?:payload|capacity)?|(?:payload|capacity)[^\d]{0,24}(\d{3,5})\s*kg)",
    re.I,
)
_SHIFT = re.compile(r"\b(third[- ]shift|2nd\s+shift|second\s+shift|night\s+shift|three\s+shifts?|2\s+shifts?|two\s+shifts?)\b", re.I)


@dataclass
class PrimitiveEvidence:
    code: str
    confidence: float
    truth_state: str
    excerpt: str
    source: str = "job_text_rules_v1"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class WorkUnit:
    """One reconstructed WORK node (Knowledge layer)."""

    work_unit_id: str
    workflow_family: str
    task: str
    object: Optional[str]
    origin: Optional[str]
    destination: Optional[str]
    action_chain: List[str]
    primitives: List[PrimitiveEvidence] = field(default_factory=list)
    payload_kg_hint: Optional[float] = None
    shift_hint: Optional[str] = None
    confidence: float = 0.0
    truth_state: str = "SIGNAL_INFERRED"
    source: str = "work_unit_reconstruct_v1"
    job_title: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d

    @property
    def required_primitives(self) -> List[str]:
        return list(self.action_chain)


def _valid_primitive_codes() -> frozenset[str]:
    ont = load_primitives_ontology()
    return frozenset(p["code"] for p in ont["primitives"])


def _excerpt(text: str, match: re.Match[str], *, pad: int = 40) -> str:
    start = max(0, match.start() - pad)
    end = min(len(text), match.end() + pad)
    snippet = text[start:end].strip()
    return re.sub(r"\s+", " ", snippet)[:160]


def _parse_payload_kg(text: str) -> Optional[float]:
    m = _PAYLOAD_KG.search(text)
    if m:
        raw = m.group(1) or m.group(2)
        try:
            return float(raw.replace(",", ""))
        except ValueError:
            pass
    m = _PAYLOAD_LB.search(text)
    if m:
        raw = m.group(1) or m.group(2)
        try:
            pounds = float(raw.replace(",", ""))
            return round(pounds * 0.453592, 1)
        except ValueError:
            pass
    return None


def detect_workflow_family(text: str, job_title: Optional[str] = None) -> Tuple[str, float, Optional[str]]:
    blob = f"{job_title or ''}\n{text or ''}"
    for family, pattern in _FAMILY_PATTERNS:
        m = pattern.search(blob)
        if m:
            return family, 0.78, _excerpt(blob, m)
    return "unknown", 0.2, None


def _merge_chain(template: Sequence[str], extras: Sequence[str]) -> List[str]:
    valid = _valid_primitive_codes()
    out: List[str] = []
    for code in [*template, *extras]:
        if code in valid and code not in out:
            out.append(code)
    return out


def reconstruct_work_from_text(
    text: str,
    *,
    job_title: Optional[str] = None,
    source_id: Optional[str] = None,
) -> WorkUnit:
    """
    Reconstruct a single primary WORK unit from posting / signal text.

    Returns Knowledge-layer inference (truth_state=SIGNAL_INFERRED).
    """
    raw = (text or "").strip()
    title = (job_title or "").strip() or None
    blob = f"{title or ''}\n{raw}".strip()
    family, family_conf, family_excerpt = detect_workflow_family(raw, title)
    template = _FAMILY_TEMPLATES[family]

    evidence_by_code: Dict[str, PrimitiveEvidence] = {}
    extras: List[str] = []
    object_hint = template.get("object")
    origin = template.get("origin")
    destination = template.get("destination")
    task = str(template.get("task") or "Unclassified work")

    if not blob:
        wu_id = _work_id(source_id, "empty", family)
        return WorkUnit(
            work_unit_id=wu_id,
            workflow_family="unknown",
            task=task,
            object=None,
            origin=None,
            destination=None,
            action_chain=[],
            confidence=0.0,
            job_title=title,
        )

    for pattern, codes, hints in _PHRASE_RULES:
        m = pattern.search(blob)
        if not m:
            continue
        excerpt = _excerpt(blob, m)
        for code in codes:
            extras.append(code)
            prev = evidence_by_code.get(code)
            conf = 0.72
            if prev is None or conf > prev.confidence:
                evidence_by_code[code] = PrimitiveEvidence(
                    code=code,
                    confidence=conf,
                    truth_state="SIGNAL_INFERRED",
                    excerpt=excerpt,
                )
        if hints.get("object"):
            object_hint = hints["object"]
        if hints.get("origin"):
            origin = hints["origin"]
        if hints.get("destination"):
            destination = hints["destination"]
        if hints.get("task"):
            task = str(hints["task"])

    chain = _merge_chain(template.get("action_chain") or [], extras)

    # Always attach family-level evidence for template primitives if missing
    if family_excerpt:
        for code in chain:
            if code not in evidence_by_code:
                evidence_by_code[code] = PrimitiveEvidence(
                    code=code,
                    confidence=max(0.45, family_conf - 0.15),
                    truth_state="SIGNAL_INFERRED",
                    excerpt=family_excerpt,
                )

    primitives = [evidence_by_code[c] for c in chain if c in evidence_by_code]
    # Coverage confidence: family + fraction of chain with phrase hits
    phrase_hits = sum(1 for p in primitives if p.confidence >= 0.7)
    coverage = phrase_hits / max(len(chain), 1) if chain else 0.0
    confidence = round(min(0.95, 0.35 * family_conf + 0.65 * coverage + (0.1 if chain else 0.0)), 3)
    if family == "unknown" and not chain:
        confidence = 0.05

    shift_m = _SHIFT.search(blob)
    shift_hint = shift_m.group(1).lower() if shift_m else None

    return WorkUnit(
        work_unit_id=_work_id(source_id, blob, family),
        workflow_family=family,
        task=task,
        object=object_hint,
        origin=origin,
        destination=destination,
        action_chain=chain,
        primitives=primitives,
        payload_kg_hint=_parse_payload_kg(blob),
        shift_hint=shift_hint,
        confidence=confidence,
        job_title=title,
    )


def reconstruct_work_units_from_texts(
    texts: Sequence[str],
    *,
    job_title: Optional[str] = None,
    source_id: Optional[str] = None,
) -> WorkUnit:
    """Merge multiple signal excerpts for one company into one WORK unit."""
    blob = "\n".join(t for t in texts if t and str(t).strip())
    return reconstruct_work_from_text(blob, job_title=job_title, source_id=source_id)


def _work_id(source_id: Optional[str], blob: str, family: str) -> str:
    digest = hashlib.sha1(f"{source_id or ''}|{family}|{blob[:400]}".encode("utf-8")).hexdigest()[:12]
    return f"work:{family}:{digest}"


def work_unit_summary(wu: WorkUnit) -> Dict[str, Any]:
    """Compact dict for market-graph / API surfaces."""
    return {
        "work_unit_id": wu.work_unit_id,
        "workflow_family": wu.workflow_family,
        "task": wu.task,
        "object": wu.object,
        "origin": wu.origin,
        "destination": wu.destination,
        "required_primitives": wu.required_primitives,
        "payload_kg_hint": wu.payload_kg_hint,
        "shift_hint": wu.shift_hint,
        "confidence": wu.confidence,
        "truth_state": wu.truth_state,
        "source": wu.source,
        "job_title": wu.job_title,
        "primitive_evidence": [p.to_dict() for p in wu.primitives[:12]],
    }
