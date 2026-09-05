"""Persist and load WORK units + work matches for Pipeline / market graph."""
from __future__ import annotations

import hashlib
import logging
from typing import Any, Dict, Iterable, List, Optional, Sequence

logger = logging.getLogger(__name__)


def _text_hash(text: str) -> str:
    return hashlib.sha1((text or "").encode("utf-8")).hexdigest()


def upsert_work_unit(
    db,
    *,
    company_id: Optional[int],
    work: Dict[str, Any],
    raw_excerpt: Optional[str] = None,
) -> Any:
    """Insert or update a WorkUnitRecord from work_unit_summary dict."""
    from app.models.work_graph import WorkUnitRecord

    wid = work.get("work_unit_id")
    if not wid:
        return None
    row = db.query(WorkUnitRecord).filter(WorkUnitRecord.work_unit_id == wid).one_or_none()
    if row is None and company_id is not None:
        # Prefer updating latest row for company when hash/family matches
        row = (
            db.query(WorkUnitRecord)
            .filter(WorkUnitRecord.company_id == int(company_id))
            .order_by(WorkUnitRecord.updated_at.desc())
            .first()
        )
        if row and row.workflow_family != work.get("workflow_family"):
            row = None
    if row is None:
        row = WorkUnitRecord(work_unit_id=wid)
        db.add(row)

    row.company_id = int(company_id) if company_id is not None else row.company_id
    row.workflow_family = str(work.get("workflow_family") or "unknown")
    row.task = work.get("task")
    row.object = work.get("object")
    row.origin = work.get("origin")
    row.destination = work.get("destination")
    row.action_chain = list(work.get("required_primitives") or [])
    row.primitive_evidence = list(work.get("primitive_evidence") or [])
    row.payload_kg_hint = work.get("payload_kg_hint")
    row.shift_hint = work.get("shift_hint")
    row.job_title = work.get("job_title")
    row.confidence = float(work.get("confidence") or 0)
    row.truth_state = str(work.get("truth_state") or "SIGNAL_INFERRED")
    row.source = str(work.get("source") or "work_unit_reconstruct_v1")
    if raw_excerpt:
        row.raw_excerpt = raw_excerpt[:2000]
        row.source_text_hash = _text_hash(raw_excerpt)
    return row


def upsert_work_match(
    db,
    *,
    work_unit_row,
    company_id: int,
    match: Dict[str, Any],
) -> Any:
    from app.models.work_graph import WorkMatchRecord

    mid = match.get("manufacturer_id")
    row = (
        db.query(WorkMatchRecord)
        .filter(
            WorkMatchRecord.company_id == int(company_id),
            WorkMatchRecord.manufacturer_id == (str(mid) if mid is not None else None),
        )
        .one_or_none()
    )
    if row is None:
        row = WorkMatchRecord(company_id=int(company_id), manufacturer_id=str(mid) if mid else None)
        db.add(row)
    row.work_unit_pk = work_unit_row.id
    row.manufacturer_name = match.get("manufacturer_name")
    row.match_score = float(match.get("match_score") or 0)
    row.work_match = match.get("work_match")
    row.work_match_label = match.get("work_match_label")
    row.match_mode = match.get("match_mode")
    row.hard_blockers = list(match.get("hard_blockers") or [])
    row.matched_primitives = list(match.get("matched_primitives") or [])
    row.missing_primitives = list(match.get("missing_primitives") or [])
    row.required_primitives = list(match.get("required_primitives") or [])
    row.supported_primitives = list(match.get("supported_primitives") or [])
    row.truth_state = str(match.get("truth_state") or "SIGNAL_INFERRED")
    row.source = str(match.get("source") or "market_graph_loop")
    row.why = match.get("why")
    return row


def persist_market_graph_work(
    db,
    demand: Sequence[Dict[str, Any]],
    matches: Sequence[Dict[str, Any]],
) -> Dict[str, int]:
    """Write WORK units + match edges from a market-graph cycle."""
    try:
        from app.models.work_graph import WorkUnitRecord  # noqa: F401
    except Exception:
        return {"work_units": 0, "work_matches": 0, "error": 1}

    units = 0
    edges = 0
    by_company: Dict[int, Any] = {}
    try:
        for d in demand:
            cid = d.get("company_id")
            work = d.get("work")
            if not cid or not work:
                continue
            row = upsert_work_unit(db, company_id=int(cid), work=work)
            if row is not None:
                by_company[int(cid)] = row
                units += 1
        db.flush()

        for m in matches:
            cid = m.get("buyer_company_id")
            if not cid:
                continue
            row = by_company.get(int(cid))
            if row is None:
                continue
            upsert_work_match(db, work_unit_row=row, company_id=int(cid), match=m)
            edges += 1
        db.commit()
    except Exception as exc:
        logger.warning("persist_market_graph_work failed: %s", exc)
        try:
            db.rollback()
        except Exception:
            pass
        return {"work_units": 0, "work_matches": 0, "error": 1}

    return {"work_units": units, "work_matches": edges}


def best_work_overlays_for_companies(db, company_ids: Iterable[int]) -> Dict[int, Dict[str, Any]]:
    """
    Best Work Match + WORK summary per company for Pipeline cards.
    Prefers highest work_match / match_score; includes work unit even if no match.
    """
    ids = sorted({int(i) for i in company_ids if i is not None})
    if not ids:
        return {}
    try:
        from app.models.work_graph import WorkMatchRecord, WorkUnitRecord
    except Exception:
        return {}

    out: Dict[int, Dict[str, Any]] = {}
    try:
        units = (
            db.query(WorkUnitRecord)
            .filter(WorkUnitRecord.company_id.in_(ids))
            .order_by(WorkUnitRecord.updated_at.desc())
            .all()
        )
        seen_u: set[int] = set()
        for u in units:
            cid = int(u.company_id) if u.company_id is not None else None
            if cid is None or cid in seen_u:
                continue
            seen_u.add(cid)
            out[cid] = {
                "work_unit_id": u.work_unit_id,
                "workflow_family": u.workflow_family,
                "work_task": u.task,
                "work_object": u.object,
                "work_origin": u.origin,
                "work_destination": u.destination,
                "required_primitives": list(u.action_chain or []),
                "work_confidence": float(u.confidence or 0),
                "work_match": None,
                "work_match_label": None,
                "match_score": None,
                "manufacturer_name": None,
                "hard_blockers": [],
                "comparable_deployment": None,
            }

        matches = (
            db.query(WorkMatchRecord)
            .filter(WorkMatchRecord.company_id.in_(ids))
            .order_by(WorkMatchRecord.work_match.desc().nullslast(), WorkMatchRecord.match_score.desc())
            .all()
        )
        seen_m: set[int] = set()
        for m in matches:
            cid = int(m.company_id)
            if cid in seen_m:
                continue
            seen_m.add(cid)
            base = out.get(cid) or {}
            base.update(
                {
                    "work_match": m.work_match,
                    "work_match_label": m.work_match_label,
                    "match_score": float(m.match_score or 0),
                    "manufacturer_name": m.manufacturer_name,
                    "hard_blockers": list(m.hard_blockers or []),
                    "match_mode": m.match_mode,
                    "why": m.why,
                }
            )
            if not base.get("work_unit_id"):
                base["required_primitives"] = list(m.required_primitives or [])
            out[cid] = base
    except Exception as exc:
        logger.debug("best_work_overlays_for_companies: %s", exc)
        return out

    # Attach one comparable deployment evidence snippet when available
    try:
        from app.services.deployment_evidence_engine import comparable_evidence_for_work

        for cid, overlay in list(out.items()):
            fam = overlay.get("workflow_family")
            prims = overlay.get("required_primitives") or []
            ev = comparable_evidence_for_work(db, workflow_family=fam, required_primitives=prims)
            if ev:
                overlay["comparable_deployment"] = ev
    except Exception:
        pass

    return out


def ensure_work_unit_for_company(db, company) -> Optional[Dict[str, Any]]:
    """Reconstruct + persist WORK for a company if missing (Pipeline fallback)."""
    from app.services.work_unit_reconstruct import (
        reconstruct_work_units_from_texts,
        work_unit_summary,
    )

    texts: List[str] = []
    for s in getattr(company, "signals", None) or []:
        for attr in ("ingestion_raw_text", "signal_text"):
            val = getattr(s, attr, None)
            if val and str(val).strip():
                texts.append(str(val).strip())
                break
    if not texts:
        return None
    wu = reconstruct_work_units_from_texts(texts, source_id=f"company:{company.id}")
    summary = work_unit_summary(wu)
    try:
        upsert_work_unit(db, company_id=int(company.id), work=summary, raw_excerpt="\n".join(texts)[:2000])
        db.commit()
    except Exception as exc:
        logger.debug("ensure_work_unit_for_company persist: %s", exc)
        try:
            db.rollback()
        except Exception:
            pass
    return summary
