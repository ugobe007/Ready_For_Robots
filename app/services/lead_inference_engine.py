"""
Lead Inference Engine
=====================
Logic chain for every candidate lead — answers, in order:

  1. Is this a lead or junk news?
  2. If lead: what is it for? why? specific problem? problem size?
  3. Which robot types match? RFP/quote process? timetable?
  4. What is the lead value score?

Orchestrates existing modules (text_classifier, company_validator, inference_engine,
automation_profile, lead_value, gtm_readiness, crm_extractor) into one dossier
with corollary references (signals, concepts, rules, article URL).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Sequence
from types import SimpleNamespace

from app.services.automation_profile import infer_automation_profile
from app.services.crm_extractor import _extract_budget, _extract_timing
from app.services.gtm_readiness import compute_gtm_readiness
from app.services.inference_engine import analyze
from app.services.lead_filter import priority_tier
from app.services.lead_name_gate import check_lead_name
from app.services.lead_value import compute_lead_value
from app.services.lead_project_timing import merge_project_timing_into_crm_metadata, resolve_project_timing

# Problem language → human label
_PROBLEM_PATTERNS: List[tuple[re.Pattern[str], str]] = [
    (re.compile(r"(?i)\blabor\s+(shortage|crisis|gap|pain|challenge)"), "Labor shortage / staffing gap"),
    (re.compile(r"(?i)\b(unable to hire|can't find enough|hard to fill|turnover)"), "Hiring / retention pressure"),
    (re.compile(r"(?i)\b(warehouse|throughput|fulfillment)\s+(bottleneck|constraint|capacity)"), "Throughput / capacity constraint"),
    (re.compile(r"(?i)\b(automation|robot|robotic)\s+(initiative|program|investment|rollout|deploy)"), "Active automation initiative"),
    (re.compile(r"(?i)\b(packaging|palletiz|sortation|pick.?and.?place|material handling)"), "Material handling / line automation need"),
    (re.compile(r"(?i)\b(housekeeping|room service|luggage|staffing)\s+(shortage|delay|pressure)"), "Guest-service / housekeeping labor gap"),
    (re.compile(r"(?i)\b(capex|capital expenditure|automation budget)"), "Capital budget for automation"),
]

_SCALE_PATTERNS: List[tuple[re.Pattern[str], str]] = [
    (re.compile(r"(?i)(\d[\d,]*)\s+employees?\b"), "employees"),
    (re.compile(r"(?i)(\d[\d,]*)\s+(hotels?|stores?|restaurants?|warehouses?|facilities?|sites?|locations?)\b"), "locations"),
    (re.compile(r"(?i)(\d[\d,]*)\s+(robots?|amrs?|agvs?)\b"), "robot_fleet"),
]


@dataclass
class LeadInferenceDossier:
    is_lead: bool
    disposition: str  # lead | junk | news_item | enrichment_only
    confidence: float = 0.0
    junk_reason: Optional[str] = None
    gate_evidence: List[str] = field(default_factory=list)

    lead_for: str = ""
    why_lead: List[str] = field(default_factory=list)
    specific_problem: str = ""
    problem_size: Dict[str, Any] = field(default_factory=dict)

    robot_categories: List[str] = field(default_factory=list)
    application_areas: List[str] = field(default_factory=list)
    deployment_contexts: List[str] = field(default_factory=list)
    sizing_notes: str = ""

    procurement: Dict[str, Any] = field(default_factory=dict)
    timetable: Dict[str, Any] = field(default_factory=dict)

    intent_score: float = 0.0
    tier: str = "COLD"
    tier_reasons: List[str] = field(default_factory=list)
    lead_value_score: float = 0.0
    score_components: Dict[str, Any] = field(default_factory=dict)
    gtm_readiness: Dict[str, Any] = field(default_factory=dict)

    references: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _reject(name: str, reason: str, evidence: List[str], confidence: float = 0.85) -> LeadInferenceDossier:
    return LeadInferenceDossier(
        is_lead=False,
        disposition="junk",
        confidence=confidence,
        junk_reason=reason,
        gate_evidence=evidence,
        references=[{"type": "gate", "label": reason, "evidence": evidence}],
    )


def _gate_lead_vs_junk(name: str, context_text: str) -> Optional[LeadInferenceDossier]:
    """Return rejection dossier if candidate fails boolean name gates (before ontology)."""
    name = (name or "").strip()
    ok, reason = check_lead_name(name)
    if not ok:
        return _reject(name, reason, [reason])

    # Article-level: is there buyer intent in the surrounding text?
    if context_text:
        from app.services.lead_filter import _buyer_opportunity_gate

        class _Sig:
            def __init__(self, text: str):
                self.signal_type = "news"
                self.signal_text = text

        ok_buyer, buyer_reason = _buyer_opportunity_gate(
            [_Sig(context_text[:3000])],
            company_name=name,
        )
        if not ok_buyer:
            return _reject(
                name,
                buyer_reason or "oem_pr_article_gate",
                [buyer_reason or "buyer opportunity gate"],
                confidence=0.78,
            )

        intent = analyze(context_text[:3000])
        if intent.overall_intent < 0.08:
            return _reject(
                name,
                "no_buyer_intent_in_article",
                [f"overall_intent={intent.overall_intent:.3f}"],
                confidence=0.72,
            )

    return None


def _extract_problem(text: str) -> str:
    hits: List[str] = []
    for pat, label in _PROBLEM_PATTERNS:
        if pat.search(text) and label not in hits:
            hits.append(label)
    if hits:
        return hits[0] if len(hits) == 1 else "; ".join(hits[:3])
    return "Operational automation opportunity — confirm specific pain on discovery call"


def _extract_problem_size(text: str, employee_estimate: Optional[int]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if employee_estimate:
        out["employees"] = employee_estimate
        out["scale_label"] = _employee_scale_label(employee_estimate)
    for pat, key in _SCALE_PATTERNS:
        m = pat.search(text)
        if m and key not in out:
            raw = m.group(1).replace(",", "")
            try:
                out[key] = int(raw)
            except ValueError:
                out[key] = raw
    budgets = _extract_budget([(text, "")])
    if budgets:
        top = max(budgets, key=lambda b: b.amount_usd)
        out["budget_usd"] = top.amount_usd
        out["budget_label"] = top.amount_str
    if not out.get("scale_label") and out.get("locations"):
        loc = out["locations"]
        if isinstance(loc, int) and loc >= 50:
            out["scale_label"] = "multi-site operator"
        elif isinstance(loc, int) and loc >= 10:
            out["scale_label"] = "regional operator"
    return out


def _employee_scale_label(n: int) -> str:
    if n >= 10_000:
        return "enterprise"
    if n >= 1_000:
        return "large"
    if n >= 200:
        return "mid-market"
    return "growth-stage"


def _build_procurement_and_timetable(text: str) -> tuple[Dict[str, Any], Dict[str, Any]]:
    timing_sigs = _extract_timing([(text, "")])
    proc: Dict[str, Any] = {"has_rfp": False, "process_hints": []}
    timetable: Dict[str, Any] = {"window": None, "signals": []}

    blob = text.lower()
    if re.search(r"(?i)\b(rfp|rfq|rfi|request for proposal|invitation to bid|solicitation)\b", blob):
        proc["has_rfp"] = True
        proc["process_hints"].append("formal RFP/RFQ language detected")
    if re.search(r"(?i)\b(vendor selection|pilot|proof of concept|poc\b|integrator)\b", blob):
        proc["process_hints"].append("vendor selection / pilot phase")
    if re.search(r"(?i)\b(quote|pricing|proposal due|bid deadline)\b", blob):
        proc["process_hints"].append("quote or proposal deadline mentioned")

    if timing_sigs:
        top = max(timing_sigs, key=lambda t: t.confidence)
        timetable["window"] = top.label
        timetable["signals"] = [
            {"label": t.label, "raw": t.raw_text[:120], "confidence": round(t.confidence, 2)}
            for t in timing_sigs[:4]
        ]
    else:
        if re.search(r"(?i)\b(this|next)\s+(quarter|year)\b", blob):
            timetable["window"] = "near-term (this/next quarter)"
        elif re.search(r"(?i)\b(within|in)\s+\d+\s+months?\b", blob):
            m = re.search(r"(?i)\b(within|in)\s+(\d+)\s+months?\b", blob)
            if m:
                timetable["window"] = f"within {m.group(2)} months"

    return proc, timetable


def _build_references(
    *,
    article_url: Optional[str],
    signal_types: Sequence[str],
    intent_result,
    profile_dict: Dict[str, Any],
) -> List[Dict[str, Any]]:
    refs: List[Dict[str, Any]] = []
    if article_url:
        refs.append({"type": "article", "url": article_url})
    for st in signal_types[:6]:
        refs.append({"type": "signal_type", "value": st})
    for rule in (intent_result.fired_rules or [])[:5]:
        refs.append({
            "type": "inference_rule",
            "rule": rule.rule_name,
            "description": rule.description,
            "boost_domain": rule.conclusion_domain,
        })
    for concept in (intent_result.activated_concepts or [])[:6]:
        refs.append({
            "type": "concept",
            "name": concept.get("concept"),
            "domain": concept.get("domain"),
            "confidence": concept.get("confidence"),
        })
    if profile_dict.get("robot_categories"):
        refs.append({"type": "robot_match", "categories": profile_dict["robot_categories"]})
    return refs


def evaluate_lead_candidate(
    *,
    company_name: str,
    context_text: str = "",
    article_url: Optional[str] = None,
    signal_types: Optional[Sequence[str]] = None,
    industry: Optional[str] = None,
    employee_estimate: Optional[int] = None,
    is_new_company: bool = True,
) -> LeadInferenceDossier:
    """
    Full logic pass on a candidate name + article context.
    Call before INSERT in scrapers; call refresh_company_inference after signals exist.
    """
    rejection = _gate_lead_vs_junk(company_name, context_text)
    if rejection:
        return rejection

    text = (context_text or "")[:4000]
    sig_types = list(signal_types or [])
    if not sig_types and text:
        sig_types = ["news"]

    intent = analyze(text, industry=industry)
    intent_100 = round(intent.overall_intent * 100, 1)

    signal_dicts = [{"signal_type": st, "raw_text": text} for st in sig_types]
    profile = infer_automation_profile(
        industry=industry,
        signals=signal_dicts,
        company_name=company_name,
    )
    profile_dict = profile.to_dict()

    problem = _extract_problem(text)
    problem_size = _extract_problem_size(text, employee_estimate)
    procurement, timetable = _build_procurement_and_timetable(text)

    pri = priority_tier(
        overall_score=intent_100,
        industry=industry,
        signal_types=sig_types,
        signal_count=len(sig_types),
        employee_estimate=employee_estimate,
    )

    lv = compute_lead_value(
        intent_100,
        employee_estimate,
        profile_dict,
        signal_dicts,
        extra_timeline_text=text[:500],
    )

    gtm = compute_gtm_readiness(
        [
            SimpleNamespace(signal_type=st, signal_text=text, created_at=None)
            for st in sig_types
        ],
        pri.tier,
        pri.reasons,
        automation_profile=profile_dict,
    )

    why: List[str] = list(pri.reasons[:4])
    if intent.fired_rules:
        why.append(intent.fired_rules[0].description)
    if problem and problem not in why:
        why.insert(0, problem)
    if procurement.get("has_rfp"):
        why.append("Formal procurement (RFP/RFQ) language in source")

    lead_for_parts: List[str] = []
    if profile.application_areas:
        lead_for_parts.append(profile.application_areas[0].replace("_", " "))
    elif profile.deployment_contexts:
        lead_for_parts.append(profile.deployment_contexts[0].replace("_", " "))
    else:
        lead_for_parts.append("robotics / automation deployment")
    lead_for = f"{company_name} — {lead_for_parts[0]}"

    refs = _build_references(
        article_url=article_url,
        signal_types=sig_types,
        intent_result=intent,
        profile_dict=profile_dict,
    )

    disposition = "lead" if is_new_company else "enrichment_only"

    return LeadInferenceDossier(
        is_lead=True,
        disposition=disposition,
        confidence=min(0.95, 0.55 + intent.overall_intent),
        gate_evidence=["passed identity gates", f"intent={intent.overall_intent:.3f}"],
        lead_for=lead_for,
        why_lead=why[:6],
        specific_problem=problem,
        problem_size=problem_size,
        robot_categories=profile_dict.get("robot_categories") or [],
        application_areas=profile_dict.get("application_areas") or [],
        deployment_contexts=profile_dict.get("deployment_contexts") or [],
        sizing_notes=profile_dict.get("sizing_notes") or "",
        procurement=procurement,
        timetable=timetable,
        intent_score=intent_100,
        tier=pri.tier,
        tier_reasons=list(pri.reasons),
        lead_value_score=lv["lead_value_score"],
        score_components={
            **(lv.get("components") or {}),
            "procurement_hints": lv.get("procurement_hints") or [],
        },
        gtm_readiness=gtm,
        references=refs,
    )


def persist_lead_inference(
    company,
    dossier: LeadInferenceDossier,
    db,
    *,
    signal_blob: str = "",
    signal_types: Optional[Sequence[str]] = None,
) -> None:
    """Merge dossier into company.crm_metadata and refresh automation_profile."""
    meta = dict(company.crm_metadata or {})
    inf_dict = dossier.to_dict()
    proc_strength = float((dossier.score_components or {}).get("procurement_timeline") or 0)
    project_timing = resolve_project_timing(
        tier=dossier.tier,
        crm_metadata=meta,
        lead_inference=inf_dict,
        signal_blob=signal_blob,
        signal_types=[r.get("value") for r in dossier.references if r.get("type") == "signal_type"],
        procurement_hints=(dossier.score_components or {}).get("procurement_hints")
        if isinstance(dossier.score_components, dict)
        else [],
        intent_score=dossier.intent_score,
        procurement_strength=proc_strength,
    )
    company.crm_metadata = merge_project_timing_into_crm_metadata(
        meta, project_timing, lead_inference=inf_dict
    )

    if dossier.is_lead and dossier.robot_categories:
        ap = dict(company.automation_profile or {})
        ap.update({
            "deployment_contexts": dossier.deployment_contexts,
            "robot_categories": dossier.robot_categories,
            "application_areas": dossier.application_areas,
            "sizing_notes": dossier.sizing_notes,
            "confidence": ap.get("confidence") or "medium",
            "source": "lead_inference_v1",
        })
        company.automation_profile = ap

    db.add(company)


def refresh_company_inference(company, signals: Sequence[Any], db) -> LeadInferenceDossier:
    """Re-run inference + CRM extraction after signals exist (API / post-scrape enrichment)."""
    from app.services.crm_extractor import build_crm_metadata_dict, extract

    sig_types: List[str] = []
    texts: List[str] = []
    for s in signals or []:
        st = getattr(s, "signal_type", None) or (s.get("signal_type") if isinstance(s, dict) else None)
        if st:
            sig_types.append(st)
        t = getattr(s, "signal_text", None) or (s.get("signal_text") if isinstance(s, dict) else None)
        if t:
            texts.append(str(t))
    context = " ".join(texts)[:4000]

    dossier = evaluate_lead_candidate(
        company_name=company.name,
        context_text=context,
        signal_types=sig_types,
        industry=company.industry,
        employee_estimate=company.employee_estimate,
        is_new_company=False,
    )
    if dossier.is_lead and db is not None:
        sig_list = list(signals or [])
        try:
            descriptors = extract(company, sig_list, db)
            crm = build_crm_metadata_dict(descriptors)
            merged = dict(company.crm_metadata or {})
            merged.update(crm)
            company.crm_metadata = merged
        except Exception:
            pass
        dossier.score_components = dossier.score_components or {}
        if isinstance(dossier.score_components, dict):
            lv_hints = compute_lead_value(
                dossier.intent_score,
                company.employee_estimate,
                company.automation_profile,
                sig_list,
                extra_timeline_text=context[:500],
            )
            dossier.score_components["procurement_hints"] = lv_hints.get("procurement_hints") or []
            dossier.score_components["procurement_timeline"] = (
                (lv_hints.get("components") or {}).get("procurement_timeline")
            )
        persist_lead_inference(company, dossier, db, signal_blob=context, signal_types=sig_types)
        db.commit()
    return dossier
