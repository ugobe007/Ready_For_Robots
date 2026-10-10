"""Pre-assembly enrichment for buyer leads cited in Cal supply outreach."""
from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.signal import Signal
from app.services.lead_enrichment_agent import enrich_lead_with_agent

logger = logging.getLogger(__name__)

_STALE_DAYS = 7


def _enrichment_stale(meta: dict[str, Any]) -> bool:
    updated = meta.get("updated_at") or meta.get("inference_snapshot", {}).get("updated_at")
    if not updated:
        return True
    try:
        ts = datetime.fromisoformat(str(updated).replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return ts < datetime.now(timezone.utc) - timedelta(days=_STALE_DAYS)
    except (TypeError, ValueError):
        return True


def ensure_supply_matches_enriched(
    db: Session,
    matches: list[dict[str, Any]],
    *,
    use_llm: bool | None = None,
    max_enrich: int = 6,
) -> tuple[list[dict[str, Any]], int]:
    """Refresh agent_enrichment on buyer leads before Cal assembly curates them."""
    if use_llm is None:
        use_llm = os.getenv("CAL_ENRICHMENT_LLM", "0").strip().lower() in ("1", "true", "yes")

    enriched = 0
    for match in matches[: max(1, max_enrich)]:
        company_id = int(match.get("id") or 0)
        if not company_id:
            continue
        company = db.query(Company).filter(Company.id == company_id).first()
        if not company:
            continue
        meta = dict(company.crm_metadata or {})
        existing = meta.get("agent_enrichment") or {}
        if existing.get("inference_snapshot") and not _enrichment_stale(existing):
            continue
        signals = (
            db.query(Signal)
            .filter(Signal.company_id == company_id)
            .order_by(Signal.created_at.desc())
            .limit(20)
            .all()
        )
        if not signals:
            continue
        try:
            enrich_lead_with_agent(
                company,
                signals,
                db,
                use_llm=use_llm,
                update_global_ontology=False,
            )
            enriched += 1
        except Exception as exc:
            db.rollback()
            logger.warning("Supply match enrichment failed company=%s: %s", company_id, exc)
    return matches, enriched


def enrichment_supply_eligible(company: Company) -> tuple[bool, str]:
    """Use persisted agent_enrichment to fail closed on weak buyer citations."""
    meta = (company.crm_metadata or {}).get("agent_enrichment") or {}
    if not meta:
        return True, ""

    snap = meta.get("inference_snapshot") or {}
    tier = str(snap.get("tier") or "").upper()
    if tier and tier not in ("HOT", "WARM"):
        return False, f"enrichment tier {tier} — supply requires HOT/WARM"

    research_markers = (
        "university",
        "dementia",
        "clinical trial",
        "research grant",
        "academic study",
        "phd",
        "laboratory",
    )
    for fact in meta.get("rich_facts") or []:
        if not isinstance(fact, dict):
            continue
        claim = str(fact.get("claim") or "").lower()
        if any(marker in claim for marker in research_markers):
            return False, "enrichment indicates academic/research buyer"

    procurement = meta.get("procurement_clues") or []
    timing = meta.get("timing_clues") or []
    gaps = meta.get("ontology_gaps") or []
    if gaps and not procurement and not timing and tier not in ("HOT",):
        return False, "enrichment gaps without procurement/timing evidence"

    return True, ""
