"""
Deployment Intelligence Engine — public Deployment Evidence (not live telemetry).

Discover OEM/customer claims → classify stage → extract metrics → score evidence
→ connect to Work Graph primitives. Live customer telemetry is optional later.
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

_ROOT = Path(__file__).resolve().parents[2]
_ONT_PATH = _ROOT / "docs" / "ontology" / "deployment_stages.v1.json"

# Phrase → deployment_stage
_STAGE_PATTERNS: Tuple[Tuple[str, re.Pattern[str]], ...] = (
    ("CANCELLED", re.compile(r"\b(cancel(?:led)?|terminated\s+deployment|ended\s+the\s+pilot)\b", re.I)),
    ("EXPANSION", re.compile(r"\b(expand(?:ing|ed)?|multi[- ]site|additional\s+sites?|rollout)\b", re.I)),
    ("MULTI_SITE", re.compile(r"\b(nine\s+customer\s+facilities|\d+\s+facilities|\d+\s+sites)\b", re.I)),
    ("COMMERCIAL_DEPLOYMENT", re.compile(
        r"\b(commercial\s+deployment|production\s+deployment|live\s+at|in\s+production)\b", re.I
    )),
    ("LIVE_DEPLOYMENT", re.compile(
        r"\b(live\s+deployment|operating\s+hours|robots?\s+deployed|\d+-month\s+deployment)\b",
        re.I,
    )),
    ("PILOT", re.compile(r"\b(pilot(?:ing)?|trial\s+deployment)\b", re.I)),
    ("PROOF_OF_CONCEPT", re.compile(r"\b(proof[- ]of[- ]concept|\bpoc\b)\b", re.I)),
    ("EVALUATION", re.compile(r"\b(evaluat(?:e|ing|ion)|testing)\b", re.I)),
    ("AGREEMENT", re.compile(r"\b(commercial\s+agreement|signed\s+an?\s+agreement|memorandum|loi)\b", re.I)),
    ("ANNOUNCED", re.compile(r"\b(announce[sd]?|plans?\s+to\s+deploy|will\s+deploy)\b", re.I)),
)

_METRIC_PATTERNS: Tuple[Tuple[str, re.Pattern[str], Optional[str]], ...] = (
    ("totes_moved", re.compile(r"([\d,]+)\+?\s*totes?\b", re.I), "count"),
    ("parts_processed", re.compile(r"([\d,]+)\+?\s*parts?\b", re.I), "count"),
    ("pallets_moved", re.compile(r"([\d,]+)\+?\s*pallets?\b", re.I), "count"),
    ("operating_hours", re.compile(r"([\d,]+)\+?\s*(?:operating\s+)?hours\b", re.I), "hours"),
    ("robots_live", re.compile(r"([\d,]+)\+?\s*robots?\s+(?:deployed|live|in\s+production)\b", re.I), "count"),
    ("deployment_sites", re.compile(r"([\d,]+)\+?\s*(?:customer\s+)?(?:facilities|sites)\b", re.I), "count"),
    ("hours_per_shift", re.compile(r"(\d+(?:\.\d+)?)\s*-?\s*hour\s+(?:weekday\s+)?shifts?\b", re.I), "hours"),
)

# Work phrase → primitives.v1 for PERFORMED edges
_WORK_TO_PRIMITIVES: Tuple[Tuple[re.Pattern[str], Tuple[str, ...]], ...] = (
    (
        re.compile(r"\b(tote|unload(?:ing)?\s+totes?|amr.{0,40}conveyor|conveyor.{0,40}pack[- ]?out)\b", re.I),
        (
            "eng.acquire_cart_or_tote",
            "man.case_pick",
            "mob.navigate_indoor",
            "tr.point_to_point",
            "plc.staging_place",
            "int.human_handoff",
        ),
    ),
    (
        re.compile(r"\b(parts?\s+handl|assembly[- ]line|line[- ]side|load(?:ed)?\s+parts?)\b", re.I),
        (
            "man.case_pick",
            "man.dexterous_adjust",
            "mob.navigate_mixed_traffic",
            "tr.line_replenishment",
            "plc.staging_place",
            "int.human_handoff",
        ),
    ),
    (
        re.compile(r"\b(pallet|forklift|material\s+handl)\b", re.I),
        (
            "eng.acquire_pallet_floor",
            "man.lift_vertical",
            "tr.point_to_point",
            "plc.floor_place",
            "mob.navigate_indoor",
        ),
    ),
)

_SOURCE_TYPE_TIER = {
    "customer_site": "A",
    "customer_press": "A",
    "joint_announcement": "A",
    "sec_filing": "A",
    "earnings": "A",
    "oem_case_study": "B",
    "oem_press_release": "B",
    "integrator_case_study": "C",
    "reputable_news": "C",
    "conference": "C",
    "public_news": "E",
    "social": "F",
}


@lru_cache(maxsize=1)
def load_deployment_ontology() -> dict:
    if _ONT_PATH.exists():
        return json.loads(_ONT_PATH.read_text(encoding="utf-8"))
    return {}


def classify_deployment_stage(text: str) -> str:
    blob = text or ""
    for stage, pattern in _STAGE_PATTERNS:
        if pattern.search(blob):
            return stage
    return "UNKNOWN"


def evidence_level_for(
    *,
    source_type: str,
    deployment_stage: str,
    has_named_customer: bool,
    has_metrics: bool,
    is_customer_source: bool = False,
) -> str:
    """A (strongest) … F (weakest)."""
    stage = (deployment_stage or "").upper()
    if stage in {"ANNOUNCED", "AGREEMENT"} and not has_metrics:
        return "E"
    if stage in {"PILOT", "PROOF_OF_CONCEPT", "EVALUATION"}:
        base = "D"
    elif stage in {"LIVE_DEPLOYMENT", "COMMERCIAL_DEPLOYMENT", "MULTI_SITE", "EXPANSION", "COMPLETED"}:
        base = "C"
    else:
        base = _SOURCE_TYPE_TIER.get((source_type or "").lower(), "F")

    if is_customer_source and has_metrics and has_named_customer:
        return "A"
    if has_metrics and has_named_customer:
        if (source_type or "").lower().startswith("oem"):
            return "B"
        return "A"
    if has_named_customer and not has_metrics:
        if stage in {"COMMERCIAL_DEPLOYMENT", "LIVE_DEPLOYMENT", "MULTI_SITE", "EXPANSION"}:
            return "C"
        if stage in {"PILOT", "PROOF_OF_CONCEPT", "EVALUATION"}:
            return "D"
        return "E"
    if not has_named_customer:
        return "F"
    return base


def extract_metrics(text: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for key, pattern, unit in _METRIC_PATTERNS:
        m = pattern.search(text or "")
        if not m:
            continue
        raw = (m.group(1) or "").replace(",", "")
        try:
            val = float(raw)
        except ValueError:
            continue
        if key in seen:
            continue
        seen.add(key)
        out.append(
            {
                "metric_key": key,
                "metric_value_numeric": val,
                "metric_value_text": m.group(0)[:80],
                "unit": unit,
                "confidence": 0.75,
            }
        )
    return out


def primitives_performed_from_text(text: str) -> List[str]:
    codes: List[str] = []
    for pattern, prims in _WORK_TO_PRIMITIVES:
        if pattern.search(text or ""):
            for c in prims:
                if c not in codes:
                    codes.append(c)
    return codes


def deployment_search_queries(vendor: str, robot_model: Optional[str] = None) -> List[str]:
    """Query templates for the recurring crawler (vendor seed × deployment language)."""
    v = (vendor or "").strip()
    r = (robot_model or "").strip()
    q = [
        f'"{v}" deployment',
        f'"{v}" customer',
        f'"{v}" case study',
        f'"{v}" commercial deployment',
    ]
    if r:
        q.extend(
            [
                f'"{r}" deployed',
                f'"{r}" pilot',
                f'"{r}" warehouse',
                f'"{r}" factory',
                f'"{r}" logistics',
                f'"{r}" production',
                f'"{r}" robots deployed',
                f'"{r}" throughput',
                f'"{r}" operating hours',
                f'"{r}" units moved',
            ]
        )
    return q


def parse_deployment_claim(
    text: str,
    *,
    source_url: Optional[str] = None,
    source_type: str = "oem_press_release",
    vendor_name: Optional[str] = None,
    robot_model: Optional[str] = None,
    customer_name: Optional[str] = None,
    facility_name: Optional[str] = None,
    industry: Optional[str] = None,
    work_type: Optional[str] = None,
    workflow: Optional[Dict[str, Any]] = None,
    source_date: Optional[str] = None,
) -> Dict[str, Any]:
    """Structure a public claim into a Deployment Evidence record (Knowledge layer)."""
    stage = classify_deployment_stage(text)
    metrics = extract_metrics(text)
    prims = primitives_performed_from_text(text)
    named = bool(customer_name) or bool(
        re.search(r"\b(at|with)\s+[A-Z][A-Za-z0-9&.\- ]{2,40}\b", text or "")
    )
    is_customer = (source_type or "").lower().startswith("customer")
    level = evidence_level_for(
        source_type=source_type,
        deployment_stage=stage,
        has_named_customer=named or bool(customer_name),
        has_metrics=bool(metrics),
        is_customer_source=is_customer,
    )
    # Quantity hygiene: announced ≠ live
    robots_announced = None
    robots_live = None
    if re.search(r"\b(plans?\s+to\s+deploy|will\s+deploy|intends?\s+to)\b", text or "", re.I):
        m = re.search(r"([\d,]+)\s*robots?", text or "", re.I)
        if m:
            robots_announced = int(m.group(1).replace(",", ""))
    for met in metrics:
        if met["metric_key"] == "robots_live":
            robots_live = int(met["metric_value_numeric"])

    conf = {"A": 0.92, "B": 0.85, "C": 0.7, "D": 0.55, "E": 0.4, "F": 0.25}.get(level, 0.2)
    digest = hashlib.sha1(f"{vendor_name}|{robot_model}|{customer_name}|{text[:200]}".encode()).hexdigest()[:8]
    domain = urlparse(source_url).netloc if source_url else None

    return {
        "deployment_id": f"DEP-{digest}",
        "vendor": vendor_name,
        "robot": robot_model,
        "customer": customer_name,
        "facility": facility_name,
        "industry": industry,
        "work_type": work_type,
        "workflow": workflow or {},
        "deployment_stage": stage,
        "metrics": {m["metric_key"]: m["metric_value_numeric"] for m in metrics},
        "metrics_detail": metrics,
        "performed_primitives": prims,
        "source_type": source_type.upper() if source_type else "PUBLIC_NEWS",
        "source_url": source_url,
        "source_domain": domain,
        "source_date": source_date,
        "evidence_level": level,
        "confidence": conf,
        "robots_announced": robots_announced,
        "robots_live": robots_live,
        "layer": "deployment_evidence",
    }


def commercial_evidence_score(events: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """Summarize a robot's public Deployment Evidence profile."""
    stages = [str(e.get("deployment_stage") or "") for e in events]
    levels = [str(e.get("evidence_level") or "F") for e in events]
    pilots = sum(1 for s in stages if s in {"PILOT", "PROOF_OF_CONCEPT", "EVALUATION"})
    commercial = sum(
        1 for s in stages if s in {"COMMERCIAL_DEPLOYMENT", "LIVE_DEPLOYMENT", "MULTI_SITE", "EXPANSION"}
    )
    expansions = sum(1 for s in stages if s == "EXPANSION")
    named = len({e.get("customer") for e in events if e.get("customer")})
    hours = 0.0
    for e in events:
        mets = e.get("metrics") or {}
        if isinstance(mets, dict) and mets.get("operating_hours"):
            hours += float(mets["operating_hours"])
    strong = sum(1 for lv in levels if lv in {"A", "B"})
    score = min(
        100.0,
        commercial * 12 + expansions * 8 + strong * 6 + min(20.0, hours / 5000.0) + named * 3,
    )
    return {
        "commercial_evidence_score": round(score, 1),
        "commercial_sites": commercial,
        "named_customers": named,
        "pilots": pilots,
        "production_deployments": commercial,
        "expansions": expansions,
        "reported_operating_hours": hours or None,
        "metrics_coverage": "high" if strong >= 2 else "medium" if strong else "low",
        "evidence_confidence": round(min(0.95, 0.35 + strong * 0.1 + commercial * 0.05), 2),
        "event_count": len(events),
    }


def persist_deployment_event(db, claim: Dict[str, Any]) -> Optional[Any]:
    from app.models.deployment_evidence import (
        DeploymentEvent,
        DeploymentEvidence,
        DeploymentMetric,
        DeploymentSource,
    )

    url = claim.get("source_url") or f"urn:rfr:deployment:{claim.get('deployment_id')}"
    src = db.query(DeploymentSource).filter(DeploymentSource.url == url).one_or_none()
    if src is None:
        src = DeploymentSource(
            url=url,
            source_type=str(claim.get("source_type") or "public_news").lower(),
            source_tier=str(claim.get("evidence_level") or "F"),
            title=None,
            domain=claim.get("source_domain"),
            raw_excerpt=str(claim.get("notes") or "")[:2000] or None,
        )
        db.add(src)
        db.flush()

    dep_id = claim.get("deployment_id")
    ev = db.query(DeploymentEvent).filter(DeploymentEvent.deployment_id == dep_id).one_or_none()
    if ev is None:
        ev = DeploymentEvent(deployment_id=dep_id)
        db.add(ev)
    ev.vendor_name = claim.get("vendor")
    ev.robot_model = claim.get("robot")
    ev.customer_name = claim.get("customer")
    ev.facility_name = claim.get("facility")
    ev.industry = claim.get("industry")
    ev.work_type = claim.get("work_type")
    ev.workflow = claim.get("workflow") or {}
    ev.deployment_stage = claim.get("deployment_stage") or "UNKNOWN"
    ev.evidence_level = claim.get("evidence_level") or "F"
    ev.confidence = float(claim.get("confidence") or 0)
    ev.performed_primitives = list(claim.get("performed_primitives") or [])
    ev.robots_announced = claim.get("robots_announced")
    ev.robots_live = claim.get("robots_live")
    ev.primary_source_id = src.id
    db.flush()

    claim_text = json.dumps(
        {"metrics": claim.get("metrics"), "stage": claim.get("deployment_stage")},
        sort_keys=True,
    )[:500]
    existing = (
        db.query(DeploymentEvidence)
        .filter(
            DeploymentEvidence.deployment_event_id == ev.id,
            DeploymentEvidence.source_id == src.id,
        )
        .first()
    )
    if existing is None:
        db.add(
            DeploymentEvidence(
                deployment_event_id=ev.id,
                source_id=src.id,
                claim_text=claim_text,
                evidence_level=ev.evidence_level,
                confidence=ev.confidence,
                supports_stage=ev.deployment_stage,
            )
        )

    for met in claim.get("metrics_detail") or []:
        db.add(
            DeploymentMetric(
                deployment_event_id=ev.id,
                source_id=src.id,
                metric_key=met["metric_key"],
                metric_value_numeric=met.get("metric_value_numeric"),
                metric_value_text=met.get("metric_value_text"),
                unit=met.get("unit"),
                confidence=float(met.get("confidence") or 0.5),
            )
        )
    return ev


def comparable_evidence_for_work(
    db,
    *,
    workflow_family: Optional[str],
    required_primitives: Sequence[str] | None,
) -> Optional[Dict[str, Any]]:
    """Find a public deployment with overlapping performed primitives / work type."""
    from app.models.deployment_evidence import DeploymentEvent

    req = set(required_primitives or [])
    try:
        rows = (
            db.query(DeploymentEvent)
            .filter(DeploymentEvent.evidence_level.in_(["A", "B", "C"]))
            .order_by(DeploymentEvent.confidence.desc())
            .limit(40)
            .all()
        )
    except Exception:
        return None
    best = None
    best_overlap = 0
    for row in rows:
        prims = set(row.performed_primitives or [])
        overlap = len(req & prims) if req else 0
        family_hit = False
        wt = (row.work_type or "").lower()
        if workflow_family == "tugger_line_replenishment" and "replenish" in wt:
            family_hit = True
        if workflow_family == "strong_transport" and ("pallet" in wt or "material" in wt):
            family_hit = True
        if "tote" in wt and req & {"eng.acquire_cart_or_tote", "man.case_pick"}:
            family_hit = True
            overlap = max(overlap, 2)
        score = overlap + (2 if family_hit else 0)
        if score > best_overlap:
            best_overlap = score
            best = row
    if best is None or best_overlap <= 0:
        return None
    return {
        "deployment_id": best.deployment_id,
        "robot": best.robot_model,
        "customer": best.customer_name,
        "facility": best.facility_name,
        "work_type": best.work_type,
        "deployment_stage": best.deployment_stage,
        "evidence_level": best.evidence_level,
        "confidence": best.confidence,
        "workflow": best.workflow,
    }


def seed_canonical_public_deployments(db) -> int:
    """Seed Digit/GXO + Figure/BMW style public evidence (idempotent)."""
    seeds = [
        parse_deployment_claim(
            "Digit moved more than 100,000 totes at GXO. Digit unloading totes from AMRs "
            "and placing them onto a conveyor feeding pack-out. Digit accumulated more than "
            "65,000 operating hours across deployment commitments at nine customer facilities.",
            source_url="https://example.readyforrobots.local/evidence/agility-gxo-totes",
            source_type="oem_press_release",
            vendor_name="Agility Robotics",
            robot_model="Digit",
            customer_name="GXO",
            facility_name="Flowery Branch, GA",
            industry="Logistics",
            work_type="Tote handling",
            workflow={"origin": "AMR", "action": "Unload tote", "destination": "Conveyor"},
            source_date="2025-11-20",
        ),
        parse_deployment_claim(
            "Figure 02 completed an 11-month BMW deployment involving 90,000+ parts and "
            "10-hour weekday shifts on an active assembly line at Spartanburg.",
            source_url="https://example.readyforrobots.local/evidence/figure-bmw-parts",
            source_type="oem_press_release",
            vendor_name="Figure",
            robot_model="Figure 02",
            customer_name="BMW",
            facility_name="Spartanburg",
            industry="Automotive",
            work_type="Parts handling / assembly-line logistics",
            workflow={"origin": "buffer", "action": "Load part", "destination": "assembly line"},
            source_date="2025-06-01",
        ),
        parse_deployment_claim(
            "Figure and Catalyst signed a commercial agreement beginning at Catalyst's "
            "Reno distribution center.",
            source_url="https://example.readyforrobots.local/evidence/figure-catalyst-agreement",
            source_type="oem_press_release",
            vendor_name="Figure",
            robot_model="Figure 02",
            customer_name="Catalyst",
            facility_name="Reno distribution center",
            industry="Logistics",
            work_type="Distribution",
            source_date="2026-05-01",
        ),
    ]
    n = 0
    for claim in seeds:
        try:
            persist_deployment_event(db, claim)
            n += 1
        except Exception as exc:
            logger.warning("seed deployment failed: %s", exc)
            try:
                db.rollback()
            except Exception:
                pass
    try:
        db.commit()
    except Exception:
        db.rollback()
    return n
