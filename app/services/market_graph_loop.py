"""
Market graph loop — WORK-centric OBSERVE→LEARN cycle (v1 implementation).

Canonical architecture: docs/rfr_intelligence_architecture.md
Ontology: ontology/rfr_graph.v1.json

Graph = intelligence structure (what connects robot ↔ job).
Loop  = learning behavior (what we learned after we acted).

Current cycle maps industry-bucket demand/supply into:
  OBSERVE → UNDERSTAND (partial) → MATCH → PRIORITIZE → LEARN (snapshot)
ACT / QUALIFY / VERIFY write Truth Graph edges later (CRM + deployments).

Does not invent scrapers — reuses classify_lead, Manufacturer catalog, and scores.
"""
from __future__ import annotations

import logging
import os
import threading
import traceback
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple

logger = logging.getLogger(__name__)

KEY_MARKET_GRAPH_LOOP = "public:market_graph:loop:v1"

CORE_LOOP_STAGES = (
    "OBSERVE",
    "UNDERSTAND",
    "MATCH",
    "PRIORITIZE",
    "ACT",
    "QUALIFY",
    "VERIFY",
    "LEARN",
)

_LOCK = threading.Lock()
_STATE_LOCK = threading.Lock()
_STATE: Dict[str, Any] = {
    "running": False,
    "running_since": None,
    "last_run": None,
}

# Industry keywords → demand/supply alignment buckets
_INDUSTRY_BUCKETS: Tuple[Tuple[str, Tuple[str, ...]], ...] = (
    ("logistics", ("logistics", "warehouse", "3pl", "fulfillment", "supply chain")),
    ("hospitality", ("hospitality", "hotel", "casino", "cruise")),
    ("healthcare", ("healthcare", "hospital", "medical", "senior living", "nursing")),
    ("food", ("food", "restaurant", "beverage", "cpg")),
    ("manufacturing", ("manufacturing", "automotive", "factory", "industrial")),
    ("aviation", ("airport", "aviation", "airline")),
    ("retail", ("retail", "apparel")),
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_market_graph_loop_status() -> Dict[str, Any]:
    with _STATE_LOCK:
        return {
            "running": _STATE["running"],
            "running_since": _STATE["running_since"],
            "last_run": _STATE["last_run"],
        }


def loop_health_from_snapshot(snap: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Public heartbeat from the cached snapshot, not web-process RAM.

    The 12h loop runs on the Fly worker. ``GET /status`` is served by web
    processes whose in-memory ``last_run`` is always empty. Trust
    ``last_completed_at`` (snapshot ``generated_at``).
    """
    snap = snap if isinstance(snap, dict) else {}
    generated = snap.get("generated_at")
    status = snap.get("status")
    age_hours: Optional[float] = None
    if generated:
        try:
            raw = str(generated).replace("Z", "+00:00")
            dt = datetime.fromisoformat(raw)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            age_hours = round(
                (datetime.now(timezone.utc) - dt).total_seconds() / 3600.0, 2
            )
        except ValueError:
            age_hours = None
    try:
        interval_hours = float(os.getenv("MARKET_GRAPH_EVERY_HOURS", "12") or 12)
    except ValueError:
        interval_hours = 12.0
    if interval_hours <= 0:
        interval_hours = 12.0
    stale_after_hours = round(interval_hours * 2 + 2.0, 2)
    healthy = (
        status == "completed"
        and age_hours is not None
        and age_hours <= stale_after_hours
    )
    thread = get_market_graph_loop_status()
    return {
        "healthy": healthy,
        "last_completed_at": generated,
        "snapshot_age_hours": age_hours,
        "interval_hours": interval_hours,
        "stale_after_hours": stale_after_hours,
        "snapshot_status": status,
        "web_thread": {
            "running": thread.get("running"),
            "last_run": thread.get("last_run"),
            "note": (
                "In-process RAM on the process serving this request. "
                "Web dynos do not run the 12h loop. Use last_completed_at."
            ),
        },
    }


def _set_running(running: bool) -> None:
    with _STATE_LOCK:
        _STATE["running"] = running
        _STATE["running_since"] = _utc_now() if running else None


def _record_finish(result: Dict[str, Any]) -> None:
    with _STATE_LOCK:
        _STATE["last_run"] = {
            "finished_at": _utc_now(),
            "status": result.get("status", "completed"),
            "stats": {k: v for k, v in result.items() if k not in {"tensions", "matches", "refresh_queue", "sample"}},
            "sample_tensions": (result.get("tensions") or [])[:5],
            "sample_matches": (result.get("matches") or [])[:5],
            "error": result.get("error"),
        }


def industry_bucket(industry: Optional[str]) -> str:
    low = (industry or "").lower()
    if not low:
        return "unknown"
    for bucket, keys in _INDUSTRY_BUCKETS:
        if any(k in low for k in keys):
            return bucket
    return "other"


def tension_score(
    *,
    demand_count: int,
    hot_count: int,
    vendor_count: int,
    signal_strength: float,
) -> float:
    """Higher = more market tension (demand pressure vs thin supply coverage)."""
    if demand_count <= 0:
        return 0.0
    coverage = vendor_count / max(demand_count, 1)
    scarcity = max(0.0, 1.0 - min(1.0, coverage * 2.5))
    heat = min(1.0, hot_count / max(demand_count, 1))
    return round(min(100.0, (scarcity * 55.0) + (heat * 30.0) + (min(1.0, signal_strength) * 15.0)), 1)


def match_edge_score(
    *,
    buyer_industry: Optional[str],
    buyer_tier: str,
    buyer_score: float,
    vendor_industries: Sequence[str],
    vendor_categories: Sequence[str],
) -> float:
    bucket = industry_bucket(buyer_industry)
    vendor_text = " ".join([*(vendor_industries or []), *(vendor_categories or [])]).lower()
    industry_hit = 1.0 if bucket != "unknown" and bucket in vendor_text else 0.0
    if buyer_industry and any((buyer_industry or "").lower() in (v or "").lower() for v in vendor_industries):
        industry_hit = 1.0
    tier_boost = 1.0 if (buyer_tier or "").upper() == "HOT" else 0.55 if (buyer_tier or "").upper() == "WARM" else 0.25
    base = min(1.0, max(0.0, float(buyer_score) / 100.0))
    return round(min(100.0, (base * 45.0) + (industry_hit * 40.0) + (tier_boost * 15.0)), 1)


def _signal_texts(company) -> List[str]:
    texts: List[str] = []
    for s in company.signals or []:
        for attr in ("ingestion_raw_text", "signal_text"):
            val = getattr(s, attr, None)
            if val and str(val).strip():
                texts.append(str(val).strip())
                break
    return texts[:8]


def _load_demand_sample(db, *, limit: int) -> List[Dict[str, Any]]:
    from sqlalchemy.orm import joinedload

    from app.models.company import Company
    from app.services.lead_filter import classify_lead, pick_primary_score
    from app.services.work_unit_reconstruct import (
        reconstruct_work_units_from_texts,
        work_unit_summary,
    )

    rows = (
        db.query(Company)
        .options(joinedload(Company.scores), joinedload(Company.signals))
        .order_by(Company.updated_at.desc().nullslast(), Company.id.desc())
        .limit(max(limit * 4, 80))
        .all()
    )
    out: List[Dict[str, Any]] = []
    for company in rows:
        junk, _, pri = classify_lead(company, company.scores, company.signals)
        if junk or pri.tier not in {"HOT", "WARM"}:
            continue
        score_row = pick_primary_score(company.scores) if company.scores else None
        overall = float(getattr(score_row, "overall_intent_score", None) or pri.score or 0)
        signal_types = [
            str(getattr(s, "signal_type", "") or "")
            for s in (company.signals or [])
            if getattr(s, "signal_type", None)
        ]
        texts = _signal_texts(company)
        work = reconstruct_work_units_from_texts(
            texts,
            source_id=f"company:{company.id}",
        )
        out.append(
            {
                "company_id": int(company.id),
                "company_name": company.name,
                "industry": company.industry,
                "bucket": industry_bucket(company.industry),
                "tier": pri.tier,
                "score": overall,
                "signal_types": signal_types[:12],
                "updated_at": company.updated_at.isoformat() if company.updated_at else None,
                "website": company.website,
                "work": work_unit_summary(work),
                "required_primitives": work.required_primitives,
                "workflow_family": work.workflow_family,
            }
        )
        if len(out) >= limit:
            break
    return out


def _load_vendor_sample(db, *, limit: int) -> List[Dict[str, Any]]:
    from app.models.robot_catalog import Manufacturer
    from app.services.robot_primitives import primitives_from_vendor_text

    rows = (
        db.query(Manufacturer)
        .order_by(Manufacturer.confidence.desc().nullslast(), Manufacturer.updated_at.desc().nullslast())
        .limit(limit)
        .all()
    )
    out: List[Dict[str, Any]] = []
    for m in rows:
        industries = m.primary_industries if isinstance(m.primary_industries, list) else []
        categories = m.robot_categories if isinstance(m.robot_categories, list) else []
        buckets = {industry_bucket(str(i)) for i in industries}
        buckets.discard("unknown")
        caps = primitives_from_vendor_text(
            robot_categories=[str(c) for c in categories],
            name=m.name,
            primary_industries=[str(i) for i in industries],
        )
        out.append(
            {
                "manufacturer_id": str(m.id),
                "name": m.name,
                "slug": m.slug,
                "website": m.website,
                "primary_industries": [str(i) for i in industries[:8]],
                "robot_categories": [str(c) for c in categories[:8]],
                "buckets": sorted(buckets) or ["other"],
                "commercial_maturity": m.commercial_maturity,
                "confidence": float(m.confidence or 0),
                "supported_primitives": caps["supported_primitives"],
                "primitive_categories": caps["categories"],
                "capability_truth_state": caps["truth_state"],
            }
        )
    return out


def detect_tensions(
    demand: Sequence[Dict[str, Any]],
    vendors: Sequence[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    demand_by_bucket: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in demand:
        demand_by_bucket[row.get("bucket") or "other"].append(row)

    vendors_by_bucket: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for vendor in vendors:
        for bucket in vendor.get("buckets") or ["other"]:
            vendors_by_bucket[bucket].append(vendor)

    tensions: List[Dict[str, Any]] = []
    for bucket, buyers in demand_by_bucket.items():
        if bucket in {"unknown", "other"} and len(buyers) < 3:
            continue
        hot_count = sum(1 for b in buyers if b.get("tier") == "HOT")
        supply = vendors_by_bucket.get(bucket) or []
        sig_types = Counter(
            t for b in buyers for t in (b.get("signal_types") or []) if t
        )
        top_signals = [s for s, _ in sig_types.most_common(5)]
        strength = min(1.0, sum(sig_types.values()) / max(len(buyers) * 2, 1))
        score = tension_score(
            demand_count=len(buyers),
            hot_count=hot_count,
            vendor_count=len(supply),
            signal_strength=strength,
        )
        if score < 28:
            continue
        action = (
            "Prioritize outreach — buyers are hot and vendor coverage is thin."
            if hot_count >= max(2, len(buyers) // 3) and len(supply) <= 3
            else "Improve vendor↔buyer matches and refresh stale customer profiles in this vertical."
            if len(supply) > 0
            else "Add vendor coverage — demand exists with little catalog supply."
        )
        tensions.append(
            {
                "bucket": bucket,
                "tension_score": score,
                "demand_count": len(buyers),
                "hot_count": hot_count,
                "vendor_count": len(supply),
                "top_signals": top_signals,
                "actionable": action,
                "example_buyers": [
                    {"company_id": b["company_id"], "company_name": b["company_name"], "tier": b["tier"]}
                    for b in sorted(buyers, key=lambda x: (-(x.get("score") or 0)))[:5]
                ],
                "example_vendors": [
                    {"manufacturer_id": v["manufacturer_id"], "name": v["name"]}
                    for v in supply[:5]
                ],
            }
        )
    tensions.sort(key=lambda t: -(t.get("tension_score") or 0))
    return tensions


def _industry_aligned(buyer_industry: Optional[str], vendor: Dict[str, Any]) -> bool:
    bucket = industry_bucket(buyer_industry)
    vendor_text = " ".join(
        [*(vendor.get("primary_industries") or []), *(vendor.get("robot_categories") or [])]
    ).lower()
    if bucket != "unknown" and bucket in vendor_text:
        return True
    if buyer_industry and any(
        (buyer_industry or "").lower() in (v or "").lower()
        for v in (vendor.get("primary_industries") or [])
    ):
        return True
    return False


def propose_matches(
    demand: Sequence[Dict[str, Any]],
    vendors: Sequence[Dict[str, Any]],
    *,
    limit: int = 40,
) -> List[Dict[str, Any]]:
    from app.services.primitive_match import work_robot_match_score

    edges: List[Dict[str, Any]] = []
    for buyer in demand:
        ranked: List[Tuple[float, Dict[str, Any], Dict[str, Any]]] = []
        for vendor in vendors:
            industry_hit = _industry_aligned(buyer.get("industry"), vendor)
            score, detail = work_robot_match_score(
                required_primitives=buyer.get("required_primitives") or [],
                supported_primitives=vendor.get("supported_primitives") or [],
                workflow_family=str(buyer.get("workflow_family") or ""),
                industry_aligned=industry_hit,
                buyer_tier=str(buyer.get("tier") or ""),
                buyer_score=float(buyer.get("score") or 0),
            )
            # Keep legacy industry score as floor when no primitives on either side
            if detail.get("match_mode") == "industry_fallback":
                legacy = match_edge_score(
                    buyer_industry=buyer.get("industry"),
                    buyer_tier=str(buyer.get("tier") or ""),
                    buyer_score=float(buyer.get("score") or 0),
                    vendor_industries=vendor.get("primary_industries") or [],
                    vendor_categories=vendor.get("robot_categories") or [],
                )
                score = max(score, legacy)
            if score < 45 and not detail.get("hard_blockers"):
                continue
            # Still surface hard blockers (wrong machine) at low score for LEARN
            if detail.get("hard_blockers") and score < 20:
                continue
            ranked.append((score, vendor, detail))
        ranked.sort(key=lambda item: -item[0])
        for score, vendor, detail in ranked[:3]:
            confidence = round(min(1.0, max(0.0, float(score) / 100.0)), 3)
            work = buyer.get("work") or {}
            blockers = detail.get("hard_blockers") or []
            why = (
                f"Work Match {detail.get('work_match')}% ({detail.get('work_match_label')}) "
                f"on {work.get('workflow_family') or 'work'} → {vendor['name']}"
                if detail.get("match_mode") == "primitive_spine" and detail.get("work_match") is not None
                else (
                    f"{buyer.get('tier')} buyer in {buyer.get('industry') or 'unknown'} "
                    f"aligned to {vendor['name']} coverage"
                )
            )
            if blockers:
                why = f"{why}; blockers={','.join(blockers)}"
            edges.append(
                {
                    "buyer_company_id": buyer["company_id"],
                    "buyer_company_name": buyer["company_name"],
                    "buyer_tier": buyer.get("tier"),
                    "buyer_industry": buyer.get("industry"),
                    "manufacturer_id": vendor["manufacturer_id"],
                    "manufacturer_name": vendor["name"],
                    "match_score": score,
                    "work_match": detail.get("work_match"),
                    "work_match_label": detail.get("work_match_label"),
                    "workflow_family": buyer.get("workflow_family"),
                    "work_unit_id": work.get("work_unit_id"),
                    "required_primitives": buyer.get("required_primitives") or [],
                    "supported_primitives": vendor.get("supported_primitives") or [],
                    "matched_primitives": detail.get("matched") or [],
                    "missing_primitives": detail.get("missing") or [],
                    "hard_blockers": blockers,
                    "match_mode": detail.get("match_mode"),
                    "why": why,
                    "predicate": "MATCHES",
                    "subject_family": "ROBOT",
                    "object_family": "WORK",
                    "confidence": confidence,
                    "truth_state": "SIGNAL_INFERRED",
                    "source": "market_graph_loop_primitive_spine",
                    "layer": "knowledge",
                }
            )
    edges.sort(key=lambda e: -(e.get("match_score") or 0))
    return edges[:limit]


def build_loop_stages(
    *,
    demand_count: int,
    vendor_count: int,
    tension_count: int,
    match_count: int,
    refresh_queue_count: int,
    researched: int,
) -> Dict[str, Any]:
    """Map this run onto the canonical OBSERVE→LEARN stages."""
    return {
        "OBSERVE": {
            "status": "completed",
            "artifacts": ["labor_signals", "vendor_catalog"],
            "demand_sampled": demand_count,
            "vendors_sampled": vendor_count,
        },
        "UNDERSTAND": {
            "status": "completed",
            "note": "WORK units reconstructed from signal/job text onto primitives.v1",
            "artifacts": ["work_units", "required_primitives", "industry_buckets"],
        },
        "MATCH": {
            "status": "completed",
            "artifacts": ["primitive_spine_match_edges"],
            "match_count": match_count,
        },
        "PRIORITIZE": {
            "status": "completed",
            "artifacts": ["tensions", "refresh_queue"],
            "tension_count": tension_count,
            "refresh_queue_count": refresh_queue_count,
        },
        "ACT": {
            "status": "deferred",
            "note": "Seller outreach lives in Pipeline / CRM — not this worker",
        },
        "QUALIFY": {
            "status": "deferred",
            "note": "Customer-confirmed facts → Truth Graph writeback TBD",
        },
        "VERIFY": {
            "status": "deferred",
            "note": "Pilot / deployment / loss → DEPLOYMENT nodes TBD",
        },
        "LEARN": {
            "status": "partial" if researched == 0 else "completed",
            "artifacts": ["snapshot_cache", "optional_research_refresh"],
            "researched": researched,
            "note": "Persists Knowledge snapshot; Truth correction loop not yet wired",
        },
    }


def build_knowledge_truth_layers(
    *,
    demand: Sequence[Dict[str, Any]],
    vendors: Sequence[Dict[str, Any]],
    matches: Sequence[Dict[str, Any]],
    tensions: Sequence[Dict[str, Any]],
) -> Dict[str, Any]:
    """Split beliefs (Knowledge) from validated outcomes (Truth)."""
    return {
        "knowledge": {
            "node_families_touched": ["COMPANY", "LABOR", "WORK", "ROBOT", "OPPORTUNITY"],
            "center": "WORK",
            "spine": "ontology/primitives.v1.json",
            "note": (
                "WORK units inferred from signal/job text; robot capabilities from "
                "catalog categories — both on primitives.v1"
            ),
            "companies_sampled": len(demand),
            "work_units_with_primitives": sum(
                1 for d in demand if d.get("required_primitives")
            ),
            "robots_via_vendors": len(vendors),
            "vendors_with_primitives": sum(
                1 for v in vendors if v.get("supported_primitives")
            ),
            "inferred_match_edges": len(matches),
            "tension_hypotheses": len(tensions),
        },
        "truth": {
            "edges": [],
            "deployments": [],
            "note": (
                "Empty until QUALIFY/VERIFY write CUSTOMER_CONFIRMED / "
                "SITE_VERIFIED / DEPLOYMENT_VERIFIED / DISPROVED edges"
            ),
        },
    }


def build_refresh_queue(demand: Sequence[Dict[str, Any]], *, limit: int = 25) -> List[Dict[str, Any]]:
    """Customers whose values/opportunities may have shifted — prioritize for research refresh."""
    queue: List[Dict[str, Any]] = []
    for buyer in demand:
        if buyer.get("tier") != "HOT":
            continue
        queue.append(
            {
                "company_id": buyer["company_id"],
                "company_name": buyer["company_name"],
                "industry": buyer.get("industry"),
                "tier": buyer.get("tier"),
                "score": buyer.get("score"),
                "reason": "HOT buyer — re-check signals, contacts, and opportunity timing",
                "updated_at": buyer.get("updated_at"),
            }
        )
        if len(queue) >= limit:
            break
    return queue


def run_market_graph_loop(
    db=None,
    *,
    demand_limit: Optional[int] = None,
    vendor_limit: Optional[int] = None,
    persist: bool = True,
) -> Dict[str, Any]:
    """One OBSERVE → MATCH → PRIORITIZE → LEARN cycle (ACT/QUALIFY/VERIFY deferred)."""
    if not _LOCK.acquire(blocking=False):
        return {"status": "skipped", "reason": "already_running"}

    own_db = False
    try:
        _set_running(True)
        demand_limit = int(demand_limit or os.getenv("MARKET_GRAPH_DEMAND_LIMIT", "80"))
        vendor_limit = int(vendor_limit or os.getenv("MARKET_GRAPH_VENDOR_LIMIT", "200"))

        if db is None:
            from app.database import SessionLocal

            db = SessionLocal()
            own_db = True

        demand = _load_demand_sample(db, limit=demand_limit)
        vendors = _load_vendor_sample(db, limit=vendor_limit)
        tensions = detect_tensions(demand, vendors)
        matches = propose_matches(demand, vendors, limit=int(os.getenv("MARKET_GRAPH_MATCH_LIMIT", "40")))
        refresh_queue = build_refresh_queue(demand, limit=int(os.getenv("MARKET_GRAPH_REFRESH_LIMIT", "25")))

        # Best-effort research touch for top refresh candidates when enabled.
        researched = 0
        if os.getenv("MARKET_GRAPH_RUN_RESEARCH", "").strip().lower() in ("1", "true", "yes"):
            researched = _maybe_research_refresh(db, refresh_queue[:5])

        stages = build_loop_stages(
            demand_count=len(demand),
            vendor_count=len(vendors),
            tension_count=len(tensions),
            match_count=len(matches),
            refresh_queue_count=len(refresh_queue),
            researched=researched,
        )
        layers = build_knowledge_truth_layers(
            demand=demand, vendors=vendors, matches=matches, tensions=tensions
        )

        payload = {
            "status": "completed",
            "generated_at": _utc_now(),
            "architecture": {
                "doc": "docs/rfr_intelligence_architecture.md",
                "ontology": "ontology/rfr_graph.v1.json",
                "center": "WORK",
                "mantra": [
                    "Find the Work.",
                    "Match the Robot.",
                    "Test the Truth.",
                    "Learn from Every Deployment.",
                ],
            },
            "demand_sampled": len(demand),
            "vendors_sampled": len(vendors),
            "tension_count": len(tensions),
            "match_count": len(matches),
            "refresh_queue_count": len(refresh_queue),
            "researched": researched,
            "tensions": tensions[:20],
            "matches": matches[:40],
            "refresh_queue": refresh_queue[:25],
            "work_units": [
                {
                    "company_id": d["company_id"],
                    "company_name": d["company_name"],
                    **(d.get("work") or {}),
                }
                for d in demand
                if d.get("required_primitives")
            ][:30],
            "loop": list(CORE_LOOP_STAGES),
            "loop_stages": stages,
            "knowledge": layers["knowledge"],
            "truth": layers["truth"],
            # Legacy step names kept for ops dashboards
            "loop_ops": [
                "research_demand",
                "index_vendors",
                "detect_tension",
                "propose_matches",
                "queue_customer_refresh",
            ],
        }

        if persist:
            try:
                from app.services.pipeline_cache_store import cache_write

                cache_write(db, KEY_MARKET_GRAPH_LOOP, payload, ttl_minutes=360)
            except Exception as exc:
                logger.warning("market graph cache write failed: %s", exc)
                payload["cache_write_error"] = str(exc)[:240]
            try:
                from app.services.work_unit_store import persist_market_graph_work

                persisted = persist_market_graph_work(db, demand, matches)
                payload["persisted"] = persisted
            except Exception as exc:
                logger.warning("work unit persist failed: %s", exc)
                payload["persisted"] = {"error": str(exc)[:240]}
            try:
                from app.services.deployment_evidence_engine import seed_canonical_public_deployments

                if os.getenv("MARKET_GRAPH_SEED_DEPLOYMENT_EVIDENCE", "1").strip().lower() in (
                    "1",
                    "true",
                    "yes",
                    "",
                ):
                    payload["deployment_evidence_seeded"] = seed_canonical_public_deployments(db)
            except Exception as exc:
                logger.warning("deployment evidence seed failed: %s", exc)

        _record_finish(payload)
        print(
            f"[market-graph-loop] completed tensions={payload['tension_count']} "
            f"matches={payload['match_count']} refresh={payload['refresh_queue_count']}",
            flush=True,
        )
        return payload
    except Exception as exc:
        logger.exception("market graph loop failed: %s", exc)
        result = {
            "status": "failed",
            "error": str(exc)[:500],
            "traceback": traceback.format_exc()[-1500:],
        }
        _record_finish(result)
        return result
    finally:
        _set_running(False)
        if own_db and db is not None:
            db.close()
        _LOCK.release()


def _maybe_research_refresh(db, queue: Sequence[Dict[str, Any]]) -> int:
    if not queue:
        return 0
    if not (os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY")):
        return 0
    if os.getenv("LEAD_RESEARCH_AGENT_ENABLED", "").strip().lower() not in ("1", "true", "yes"):
        return 0
    try:
        from app.services.lead_research_agent import research_company_updates
    except Exception:
        return 0

    done = 0
    for item in queue:
        cid = item.get("company_id")
        if not cid:
            continue
        try:
            research_company_updates(db, int(cid), dry_run=False, notify=False)
            done += 1
        except Exception as exc:
            logger.warning("market graph research failed company_id=%s: %s", cid, exc)
    return done


def read_market_graph_snapshot(db=None) -> Optional[Dict[str, Any]]:
    try:
        from app.services.public_surface_cache import read_public_cache

        cached = read_public_cache(KEY_MARKET_GRAPH_LOOP, stale_ok=True)
        if isinstance(cached, dict) and cached:
            return cached
    except Exception:
        pass
    if db is None:
        return None
    try:
        from app.services.pipeline_cache_store import cache_read

        return cache_read(db, KEY_MARKET_GRAPH_LOOP)
    except Exception:
        return None
