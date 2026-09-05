"""
Sales lead enrichment agent — inference engine + learned ontology growth.

For each pipeline lead:
  1. Re-run lead inference (dossier, timing, CRM hints)
  2. Run semantic inference + ontology gap analysis
  3. Mine rich phrases / word shapes (LLM when configured, else heuristics)
  4. Persist per-lead ``agent_enrichment`` on crm_metadata
  5. Merge validated terms into the global learned ontology store
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Sequence

from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.signal import Signal
from app.services.inference_engine import analyze
from app.services.lead_contact_intelligence import enrich_company_contact_intelligence
from app.services.lead_inference_engine import refresh_company_inference
from app.services.learned_signal_ontology import (
    BUCKET_KEYS,
    MAX_RICH_FACTS_PER_LEAD,
    extract_heuristic_candidates,
    load_learned_store,
    merge_candidates_into_store,
    save_learned_store,
)
from app.services.robot_signal_ontology import match_ontology_features, signal_types_from_ontology_matches

logger = logging.getLogger(__name__)

DEFAULT_AGENT_BATCH_LIMIT = 300
MAX_AGENT_BATCH_LIMIT = 500

_AGENT_SYSTEM = """You are the ReadyForRobots sales intelligence agent.
Extract ONLY phrases and patterns that appear verbatim (or near-verbatim) in the provided lead text.
Do not invent companies, dollar amounts, or dates not present in the source.

Return strict JSON with keys:
- pain_words: string[] (single words, lowercase)
- buying_phrases: string[] (2-6 word buying-intent phrases from the text)
- trigger_expressions: string[] (short clauses indicating automation decisions)
- job_title_signals: string[]
- capex_financial_signals: string[]
- expansion_facility_signals: string[]
- regulatory_compliance_signals: string[]
- word_shapes: array of { "pattern": "regex string", "maps_to": "signal_type", "note": "why" }
- rich_facts: array of { "claim": "one sentence fact", "evidence_span": "short quote from text" }
- procurement_clues: string[]
- timing_clues: string[]

Keep each list to at most 8 items. Regex patterns must be valid Python regex (use (?i) for case insensitivity)."""


@dataclass
class LeadAgentEnrichment:
    company_id: int
    company_name: str
    inference_refreshed: bool = False
    ontology_terms_added: int = 0
    ontology_gaps: List[str] = field(default_factory=list)
    matched_features: Dict[str, List[str]] = field(default_factory=dict)
    learned_candidates: Dict[str, Any] = field(default_factory=dict)
    rich_facts: List[Dict[str, Any]] = field(default_factory=list)
    procurement_clues: List[str] = field(default_factory=list)
    timing_clues: List[str] = field(default_factory=list)
    signal_types_effective: List[str] = field(default_factory=list)
    contact_intelligence: Dict[str, Any] = field(default_factory=dict)
    llm_used: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _signal_context(signals: Sequence[Any], *, max_signals: int = 20) -> tuple[str, List[str]]:
    texts: List[str] = []
    types: List[str] = []
    for s in list(signals or [])[:max_signals]:
        st = getattr(s, "signal_type", None) or (s.get("signal_type") if isinstance(s, dict) else None)
        if st:
            types.append(str(st))
        t = getattr(s, "signal_text", None) or (s.get("signal_text") if isinstance(s, dict) else None)
        if t:
            texts.append(str(t))
    return " ".join(texts)[:5000], types


def _ontology_gaps(text: str, db: Session) -> List[str]:
    """Features the dossier implies but base+learned ontology did not match."""
    gaps: List[str] = []
    low = text.lower()
    checks = [
        ("rfp or procurement language", r"\b(rfp|procurement|request for proposal|tender)\b"),
        ("deployment / rollout language", r"\b(deploy|rollout|go-live|pilot)\b"),
        ("capex / investment language", r"\b(capex|capital expenditure|automation budget|\$\d+[mb]?)\b"),
        ("labor pressure language", r"\b(labor shortage|staffing|turnover|unable to hire)\b"),
        ("facility expansion language", r"\b(new (warehouse|facility|plant|hotel|dc))\b"),
    ]
    matches = match_ontology_features(text, db=db)
    if not matches.has_any:
        for label, pat in checks:
            if re.search(pat, low, re.I):
                gaps.append(label)
    return gaps[:6]


def _llm_extract_candidates(
    *,
    company_name: str,
    industry: Optional[str],
    context: str,
    dossier: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    from app.services.llm_client import llm_json_completion

    user = json.dumps(
        {
            "company_name": company_name,
            "industry": industry,
            "signal_text": context[:4000],
            "inference_summary": {
                "specific_problem": dossier.get("specific_problem"),
                "why_lead": (dossier.get("why_lead") or [])[:4],
                "procurement": dossier.get("procurement"),
                "timetable": dossier.get("timetable"),
            },
        },
        ensure_ascii=False,
    )
    raw = llm_json_completion(_AGENT_SYSTEM, user, max_tokens=1800, temperature=0.2, timeout=45.0)
    if not raw:
        return None
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        m = re.search(r"\{[\s\S]*\}", raw)
        if not m:
            return None
        try:
            data = json.loads(m.group(0))
            return data if isinstance(data, dict) else None
        except json.JSONDecodeError:
            return None


def _merge_candidate_dicts(*parts: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    out: Dict[str, Any] = {k: [] for k in BUCKET_KEYS}
    out["word_shapes"] = []
    out["rich_facts"] = []
    out["procurement_clues"] = []
    out["timing_clues"] = []
    for part in parts:
        if not isinstance(part, dict):
            continue
        for key in BUCKET_KEYS:
            vals = part.get(key)
            if isinstance(vals, list):
                out[key].extend(str(v) for v in vals if v)
        for key in ("word_shapes", "rich_facts", "procurement_clues", "timing_clues"):
            vals = part.get(key)
            if isinstance(vals, list):
                out[key].extend(vals)
    return out


def enrich_lead_with_agent(
    company: Company,
    signals: Sequence[Any],
    db: Session,
    *,
    use_llm: bool = True,
    update_global_ontology: bool = True,
) -> LeadAgentEnrichment:
    """Full agent pass for one company."""
    context, sig_types = _signal_context(signals)
    result = LeadAgentEnrichment(
        company_id=int(company.id),
        company_name=company.name or "",
    )

    dossier = refresh_company_inference(company, signals, db)
    result.inference_refreshed = bool(dossier.is_lead)
    inf_dict = dossier.to_dict() if dossier.is_lead else {}

    intent = analyze(context, industry=company.industry)
    heuristic = extract_heuristic_candidates(
        context,
        industry=company.industry,
        fired_rules=intent.fired_rules,
    )
    llm_data: Optional[Dict[str, Any]] = None
    if use_llm and context.strip():
        llm_data = _llm_extract_candidates(
            company_name=company.name or "",
            industry=company.industry,
            context=context,
            dossier=inf_dict,
        )
        result.llm_used = llm_data is not None

    candidates = _merge_candidate_dicts(heuristic, llm_data)
    result.learned_candidates = {k: candidates.get(k) for k in BUCKET_KEYS if candidates.get(k)}
    if candidates.get("word_shapes"):
        result.learned_candidates["word_shapes"] = candidates["word_shapes"][:8]
    result.rich_facts = [
        f for f in (candidates.get("rich_facts") or [])
        if isinstance(f, dict) and f.get("claim")
    ][:MAX_RICH_FACTS_PER_LEAD]
    result.procurement_clues = [str(x) for x in (candidates.get("procurement_clues") or [])[:8]]
    result.timing_clues = [str(x) for x in (candidates.get("timing_clues") or [])[:8]]

    matches = match_ontology_features(context, db=db)
    result.matched_features = {
        "pain_words": list(matches.pain_words),
        "buying_phrases": list(matches.buying_phrases),
        "trigger_expressions": list(matches.trigger_expressions),
        "word_shape_hits": [s.get("pattern") for s in matches.word_shape_hits if isinstance(s, dict)],
    }
    result.ontology_gaps = _ontology_gaps(context, db)
    result.signal_types_effective = signal_types_from_ontology_matches(context, db=db)
    if not result.signal_types_effective and sig_types:
        result.signal_types_effective = list(dict.fromkeys(sig_types))[:6]

    try:
        result.contact_intelligence = enrich_company_contact_intelligence(
            company,
            signals,
            contacts=getattr(company, "contacts", None),
        )
    except Exception as exc:
        logger.warning("Contact intelligence enrichment failed id=%s: %s", company.id, exc)
        result.contact_intelligence = {
            "status": "error",
            "error": str(exc)[:220],
        }

    meta = dict(company.crm_metadata or {})
    meta["agent_enrichment"] = {
        **result.to_dict(),
        "inference_snapshot": {
            "specific_problem": inf_dict.get("specific_problem"),
            "why_lead": inf_dict.get("why_lead"),
            "procurement": inf_dict.get("procurement"),
            "timetable": inf_dict.get("timetable"),
            "robot_categories": inf_dict.get("robot_categories"),
            "intent_score": inf_dict.get("intent_score"),
            "tier": inf_dict.get("tier"),
        },
        "activated_concepts": (intent.activated_concepts or [])[:8],
        "fired_rules": [
            getattr(r, "description", str(r)) for r in (intent.fired_rules or [])[:5]
        ],
    }
    if result.contact_intelligence:
        meta["contact_intelligence"] = result.contact_intelligence
    company.crm_metadata = meta
    db.add(company)
    db.commit()

    if update_global_ontology and dossier.is_lead:
        store = load_learned_store(db)
        added = merge_candidates_into_store(
            store,
            candidates,
            source_company_id=company.id,
        )
        save_learned_store(db, store)
        result.ontology_terms_added = added

    return result


def run_sales_leads_enrichment_batch(
    db: Session,
    *,
    limit: int = DEFAULT_AGENT_BATCH_LIMIT,
    company_ids: Optional[List[int]] = None,
    use_llm: bool = True,
) -> Dict[str, Any]:
    from app.services.pipeline_inference_batch import select_top_pipeline_company_ids

    lim = max(1, min(int(limit), MAX_AGENT_BATCH_LIMIT))
    ids = company_ids if company_ids is not None else select_top_pipeline_company_ids(db, limit=lim)

    enriched = 0
    failed = 0
    terms_added = 0
    llm_used_count = 0
    errors: List[Dict[str, Any]] = []

    for cid in ids:
        company = db.query(Company).filter(Company.id == cid).first()
        if not company:
            continue
        signals = (
            db.query(Signal)
            .filter(Signal.company_id == company.id)
            .order_by(Signal.created_at.desc())
            .limit(20)
            .all()
        )
        if not signals:
            continue
        try:
            row = enrich_lead_with_agent(company, signals, db, use_llm=use_llm)
            if row.inference_refreshed:
                enriched += 1
            terms_added += row.ontology_terms_added
            if row.llm_used:
                llm_used_count += 1
        except Exception as exc:
            failed += 1
            db.rollback()
            logger.warning("Lead enrichment agent failed id=%s: %s", cid, exc)
            if len(errors) < 20:
                errors.append({"company_id": cid, "error": str(exc)[:200]})

    store = load_learned_store(db)
    return {
        "requested": len(ids),
        "enriched": enriched,
        "failed": failed,
        "ontology_terms_added_total": terms_added,
        "llm_used_count": llm_used_count,
        "learned_ontology_size": {
            k: len((store.get("buckets") or {}).get(k) or [])
            for k in BUCKET_KEYS
        },
        "word_shapes_count": len(store.get("word_shapes") or []),
        "errors": errors,
    }


def run_sales_leads_enrichment_batch_and_refresh_caches(
    *,
    limit: int = DEFAULT_AGENT_BATCH_LIMIT,
    use_llm: bool = True,
) -> Dict[str, Any]:
    from app.database import SessionLocal
    from app.services.public_surface_cache import (
        hydrate_public_surface_caches,
        refresh_all_public_surface_caches,
    )

    db = SessionLocal()
    try:
        stats = run_sales_leads_enrichment_batch(db, limit=limit, use_llm=use_llm)
    finally:
        db.close()

    try:
        db2 = SessionLocal()
        try:
            refresh_all_public_surface_caches(db2)
            hydrate_public_surface_caches()
            stats["cache_refresh"] = "ok"
        finally:
            db2.close()
    except Exception as exc:
        logger.warning("Enrichment agent batch cache refresh failed: %s", exc)
        stats["cache_refresh"] = f"failed: {exc}"

    logger.info("Sales lead enrichment agent batch complete: %s", stats)
    return stats
