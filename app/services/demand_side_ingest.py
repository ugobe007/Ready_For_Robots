"""Demand-side buyer ingestion — curated operator companies → Cal buyer leads.

News discovery structurally surfaces robot *makers* (supply), not the operators
who *buy* robots (demand), and the Apollo key is free-tier (no org/people search),
so net-new buyer supply has to come from a curated operator source. This module
takes a real operating buyer ({name, domain, industry, why-now signals}) and runs
it through the SAME machinery the scraper uses — dedupe → Company → Signal →
Score → classify_lead tier → Cal CrmAccount + draft — so it lands in Cal's
HOT/WARM queue. Hunter then verifies the contact at send time (the only enrichment
path that works), and the recipient-trust gate keeps guessed addresses out.

Signals here drive scoring/tiering only; ``cal_buyer_outreach_body`` composes the
email from name + industry and never quotes signal text, so sector-level signal
copy cannot leak a false claim into an email.
"""
from __future__ import annotations

import logging
from types import SimpleNamespace
from typing import Any, Iterable, Optional, Sequence

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.score import Score
from app.models.signal import Signal
from app.services.company_domain import normalize_website_domain, persist_company_domain
from app.services.inference_engine import analyze_signals
from app.services.lead_filter import classify_lead

logger = logging.getLogger(__name__)

# (signal_type, signal_text_template, strength). {name}/{industry} are filled in.
SignalSpec = tuple[str, str, float]


def _find_existing(db: Session, name: str, domain: str | None) -> Optional[Company]:
    """Dedupe against the ~720 existing buyers: domain first, then exact name."""
    dom = normalize_website_domain(domain) if domain else None
    if dom:
        hit = db.query(Company).filter(Company.website_domain == dom).first()
        if hit:
            return hit
    return db.query(Company).filter(func.lower(Company.name) == (name or "").strip().lower()).first()


def _score_dict_for(name: str, industry: str | None, signal_texts: Sequence[str]) -> dict[str, float]:
    result = analyze_signals(list(signal_texts), company_name=name, industry=industry)
    return result.to_score_dict()


def _classify_tier(company: Any, score_row: Any, signals: Sequence[Any]) -> tuple[bool, str, str]:
    junk, reason, pri = classify_lead(company, score_row, list(signals))
    tier = "JUNK" if junk else (getattr(pri, "tier", None) or "COLD")
    return junk, reason, tier


def _rendered_signals(name: str, industry: str, specs: Iterable[SignalSpec]) -> list[SignalSpec]:
    out: list[SignalSpec] = []
    for stype, template, strength in specs:
        text = template.replace("{name}", name).replace("{industry}", industry)
        out.append((stype, text, float(strength)))
    return out


def preview_operator_tier(
    *, name: str, industry: str, signals: Iterable[SignalSpec], employee_estimate: int | None = None
) -> dict[str, Any]:
    """Predict tier WITHOUT touching the DB — transient Company/Signal/Score."""
    rendered = _rendered_signals(name, industry, signals)
    texts = [t for _, t, _ in rendered]
    score_data = _score_dict_for(name, industry, texts)
    transient_company = SimpleNamespace(
        id=-1, name=name, industry=industry, employee_estimate=employee_estimate,
        website="https://example.com", crm_metadata={}, scores=[], signals=[],
    )
    transient_signals = [
        SimpleNamespace(signal_type=st, signal_text=tx, signal_strength=stg)
        for st, tx, stg in rendered
    ]
    transient_score = SimpleNamespace(**score_data)
    junk, reason, tier = _classify_tier(transient_company, transient_score, transient_signals)
    return {
        "name": name,
        "tier": tier,
        "junk": junk,
        "reason": reason,
        "overall_intent_score": round(float(score_data.get("overall_intent_score", 0.0)), 1),
    }


def ingest_operator_buyer(
    db: Session,
    *,
    name: str,
    domain: str | None,
    industry: str,
    signals: Iterable[SignalSpec],
    employee_estimate: int | None = None,
    city: str | None = None,
    state: str | None = None,
    country: str = "US",
    source: str = "demand_side_curated",
    create_crm: bool = True,
) -> dict[str, Any]:
    """Persist one operator buyer through the full pipeline and (optionally) draft.

    Returns {name, status: new|existing|updated, tier, junk, made_crm, ...}.
    """
    name = (name or "").strip()
    industry = (industry or "Unknown").strip()
    dom = normalize_website_domain(domain) if domain else None
    rendered = _rendered_signals(name, industry, signals)

    existing = _find_existing(db, name, domain)
    is_new = existing is None
    if existing is not None:
        company = existing
    else:
        company = Company(
            name=name,
            website=f"https://{dom}" if dom else None,
            industry=industry,
            employee_estimate=employee_estimate,
            location_city=city,
            location_state=state,
            location_country=country,
            source=source,
            is_internal=True,
        )
        db.add(company)
        db.commit()
        db.refresh(company)
        if dom:
            persist_company_domain(company, dom)
            db.commit()

    # Attach signals (dedupe by exact text so re-runs are idempotent).
    added_signals = 0
    for stype, text, strength in rendered:
        dup = (
            db.query(Signal)
            .filter(Signal.company_id == company.id, Signal.signal_text == text)
            .first()
        )
        if not dup:
            db.add(
                Signal(
                    company_id=company.id,
                    signal_type=stype,
                    signal_text=text,
                    signal_strength=min(float(strength), 1.0),
                    source_url=source,
                )
            )
            added_signals += 1
    if added_signals:
        db.commit()

    # Score from the full current signal set.
    sigs = db.query(Signal).filter(Signal.company_id == company.id).all()
    score_data = _score_dict_for(company.name, company.industry, [s.signal_text for s in sigs])
    score_row = db.query(Score).filter(Score.company_id == company.id).first()
    if score_row:
        for k, v in score_data.items():
            setattr(score_row, k, v)
    else:
        score_row = Score(company_id=company.id, **score_data)
        db.add(score_row)
    db.commit()

    junk, reason, tier = _classify_tier(company, company.scores, sigs)

    made_crm = False
    crm_reason = None
    if create_crm and not junk and tier in ("HOT", "WARM"):
        made_crm, crm_reason = _ensure_cal_crm_account(db, company)
    elif create_crm:
        crm_reason = f"tier={tier} junk={junk}" if junk else f"tier={tier} (not HOT/WARM)"

    return {
        "name": company.name,
        "company_id": company.id,
        "status": "new" if is_new else "existing",
        "tier": tier,
        "junk": junk,
        "reason": reason,
        "overall_intent_score": round(float(score_data.get("overall_intent_score", 0.0)), 1),
        "added_signals": added_signals,
        "made_crm": made_crm,
        "crm_reason": crm_reason,
    }


def _ensure_cal_crm_account(db: Session, company: Company) -> tuple[bool, str]:
    """Create the Cal CRM account + buyer draft (idempotent) for a scored company."""
    from app.models.crm import CrmAccount
    from app.services.cal_autonomy import _draft_and_store, resolve_cal_admin_context

    ctx = resolve_cal_admin_context(db)
    if not ctx:
        return False, "no Cal admin context (admin-cal-outreach team / CAL_ADMIN_USER_ID)"
    _uid, team = ctx
    acct = (
        db.query(CrmAccount)
        .filter(CrmAccount.company_id == company.id, CrmAccount.team_id == team.id)
        .first()
    )
    drafted, _refreshed = _draft_and_store(
        db,
        company=company,
        acct=acct,
        team=team,
        existing={},
        regenerate=acct is None,
        stale_before=None,
    )
    db.commit()
    return (drafted or acct is not None), "ok"


def ingest_operator_batch(
    db: Session,
    operators: Sequence[dict[str, Any]],
    *,
    create_crm: bool = True,
) -> dict[str, Any]:
    """Ingest many operators; returns a summary with per-row results."""
    rows: list[dict[str, Any]] = []
    new = existing = hot = warm = crm = 0
    for op in operators:
        try:
            res = ingest_operator_buyer(db, create_crm=create_crm, **op)
        except Exception as exc:  # never let one bad row kill the batch
            logger.exception("ingest failed for %s", op.get("name"))
            rows.append({"name": op.get("name"), "error": str(exc)[:200]})
            db.rollback()
            continue
        rows.append(res)
        if res["status"] == "new":
            new += 1
        else:
            existing += 1
        if res["tier"] == "HOT":
            hot += 1
        elif res["tier"] == "WARM":
            warm += 1
        if res["made_crm"]:
            crm += 1
    return {
        "total": len(operators),
        "new_companies": new,
        "existing_companies": existing,
        "hot": hot,
        "warm": warm,
        "crm_accounts_ready": crm,
        "rows": rows,
    }
