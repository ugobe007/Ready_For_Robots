"""
CRM bridge: StageGate robot_companies ↔ companies + CrmAccount + Score.

Keeps one canonical semantic_frame on company.crm_metadata so Cal Admin and
Supply Pipeline generate the same StageGate voice from the same parse.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.crm import CrmAccount, Team
from app.models.robot_company import RobotCompany
from app.models.score import Score
from app.services.stagegate_voice import (
    semantic_frame_from_market_intel,
    stagegate_outreach_email,
)

logger = logging.getLogger(__name__)

OUTREACH_PIPELINE = "stagegate"
COMPANY_SOURCE = "stagegate_oem"
CAL_TEAM_SLUG = "admin-cal-outreach"


def get_cal_outreach_team(db: Session) -> Team:
    """Shared admin Cal team (same slug as admin_extended._admin_team)."""
    team = db.query(Team).filter(Team.slug == CAL_TEAM_SLUG).first()
    if team:
        return team
    team = Team(name="Cal Outreach (Admin)", slug=CAL_TEAM_SLUG)
    db.add(team)
    db.flush()
    return team


def _intent_score(rc: RobotCompany) -> float:
    score = float(rc.lead_score or 0)
    mi = rc.market_intelligence if isinstance(rc.market_intelligence, dict) else {}
    oem = mi.get("stagegate_oem") if isinstance(mi.get("stagegate_oem"), dict) else {}
    oem_score = oem.get("oem_need_score")
    if oem_score is not None:
        score = max(score, float(oem_score))
    return round(score, 1)


def _industry_label(rc: RobotCompany) -> str:
    mi = rc.market_intelligence if isinstance(rc.market_intelligence, dict) else {}
    oem = mi.get("stagegate_oem") if isinstance(mi.get("stagegate_oem"), dict) else {}
    icp = oem.get("icp")
    if icp:
        return str(icp)
    return rc.robot_type or "Robotics OEM"


def _semantic_frame_dict(rc: RobotCompany) -> Optional[dict[str, Any]]:
    mi = rc.market_intelligence if isinstance(rc.market_intelligence, dict) else {}
    frame = mi.get("semantic_frame")
    if isinstance(frame, dict):
        return frame
    oem = mi.get("stagegate_oem")
    if isinstance(oem, dict) and isinstance(oem.get("semantic_frame"), dict):
        return oem["semantic_frame"]
    return None


def _source_headline(rc: RobotCompany) -> str:
    mi = rc.market_intelligence if isinstance(rc.market_intelligence, dict) else {}
    oem = mi.get("stagegate_oem")
    if isinstance(oem, dict):
        return str(oem.get("source_headline") or "")
    return ""


def build_stagegate_draft(
    rc: RobotCompany,
    *,
    company: Optional[Company] = None,
) -> dict[str, str]:
    """Single draft builder for Supply Pipeline and Cal Admin."""
    meta = (company.crm_metadata if company else None) or {}
    if isinstance(meta, dict) and meta.get("semantic_frame"):
        frame = semantic_frame_from_market_intel(meta)
    else:
        frame = semantic_frame_from_market_intel(rc.market_intelligence)
    return stagegate_outreach_email(
        rc.company_name,
        semantic_frame=frame,
        source_text=_source_headline(rc),
        trade_show=rc.next_trade_show,
    )


def cal_draft_for_stagegate_company(company: Company) -> dict[str, str]:
    """Cal Admin draft from linked company.crm_metadata."""
    meta = company.crm_metadata if isinstance(company.crm_metadata, dict) else {}
    frame = semantic_frame_from_market_intel(meta)
    return stagegate_outreach_email(
        company.name or "your team",
        semantic_frame=frame,
        source_text=_source_headline_from_meta(meta),
        trade_show=meta.get("next_trade_show"),
    )


def _source_headline_from_meta(meta: dict[str, Any]) -> str:
    oem = meta.get("stagegate_oem")
    if isinstance(oem, dict):
        return str(oem.get("source_headline") or "")
    return str(meta.get("semantic_summary") or "")


def is_stagegate_company(company: Company) -> bool:
    meta = company.crm_metadata if isinstance(company.crm_metadata, dict) else {}
    return meta.get("outreach_pipeline") == OUTREACH_PIPELINE


def _upsert_company(db: Session, rc: RobotCompany) -> Company:
    mi = rc.market_intelligence if isinstance(rc.market_intelligence, dict) else {}
    linked_id = mi.get("crm_company_id")

    company: Optional[Company] = None
    if linked_id:
        company = db.query(Company).filter(Company.id == int(linked_id)).first()
    if not company:
        company = db.query(Company).filter(Company.name.ilike(rc.company_name)).first()

    frame = _semantic_frame_dict(rc)
    summary = mi.get("semantic_summary")
    crm_meta: dict[str, Any] = {
        "outreach_pipeline": OUTREACH_PIPELINE,
        "robot_company_id": rc.id,
        "semantic_summary": summary,
        "stagegate_oem": mi.get("stagegate_oem"),
        "next_trade_show": rc.next_trade_show,
    }
    if frame:
        crm_meta["semantic_frame"] = frame

    if company:
        existing_meta = dict(company.crm_metadata or {})
        existing_meta.update(crm_meta)
        company.crm_metadata = existing_meta
        company.website = company.website or rc.website
        company.industry = company.industry or _industry_label(rc)
        company.source = company.source or COMPANY_SOURCE
        if rc.next_trade_show:
            meta = dict(company.crm_metadata or {})
            meta["next_trade_show"] = rc.next_trade_show
            company.crm_metadata = meta
    else:
        company = Company(
            name=rc.company_name,
            website=rc.website,
            industry=_industry_label(rc),
            source=COMPANY_SOURCE,
            crm_metadata=crm_meta,
        )
        db.add(company)
        db.flush()

    return company


def _upsert_score(db: Session, company: Company, rc: RobotCompany) -> Score:
    intent = _intent_score(rc)
    score = db.query(Score).filter(Score.company_id == company.id).first()
    if score:
        score.overall_intent_score = max(float(score.overall_intent_score or 0), intent)
        score.robotics_fit_score = max(float(score.robotics_fit_score or 0), intent * 0.85)
    else:
        score = Score(
            company_id=company.id,
            overall_intent_score=intent,
            robotics_fit_score=intent * 0.85,
            automation_score=intent * 0.5,
        )
        db.add(score)
    return score


def _upsert_crm_account(
    db: Session,
    company: Company,
    rc: RobotCompany,
    *,
    refresh_draft: bool,
) -> CrmAccount:
    team = get_cal_outreach_team(db)
    acct = (
        db.query(CrmAccount)
        .filter(
            CrmAccount.team_id == team.id,
            CrmAccount.company_id == company.id,
        )
        .first()
    )
    if not acct:
        acct = (
            db.query(CrmAccount)
            .filter(
                CrmAccount.team_id == team.id,
                CrmAccount.name.ilike(rc.company_name),
            )
            .first()
        )

    draft = build_stagegate_draft(rc, company=company)

    if acct:
        acct.company_id = company.id
        acct.name = rc.company_name
        acct.website = acct.website or rc.website or company.website
        acct.industry = acct.industry or company.industry
        acct.account_type = "vendor"
        acct.contact_email = acct.contact_email or rc.contact_email
        if refresh_draft or not (acct.outreach_draft or "").strip():
            acct.outreach_draft = draft["body"]
            acct.outreach_stage = acct.outreach_stage or "draft_ready"
    else:
        acct = CrmAccount(
            team_id=team.id,
            company_id=company.id,
            name=rc.company_name,
            website=rc.website or company.website,
            industry=company.industry,
            account_type="vendor",
            contact_email=rc.contact_email,
            outreach_draft=draft["body"],
            outreach_stage="draft_ready",
        )
        db.add(acct)
        db.flush()

    return acct


def _link_robot_company(rc: RobotCompany, company: Company, acct: CrmAccount) -> None:
    mi = dict(rc.market_intelligence or {})
    mi["crm_company_id"] = company.id
    mi["crm_account_id"] = str(acct.id)
    rc.market_intelligence = mi


def sync_robot_company_to_crm(
    db: Session,
    rc: RobotCompany,
    *,
    refresh_draft: bool = False,
) -> dict[str, Any]:
    """
    Bridge one StageGate prospect into companies + Score + admin CrmAccount.
    Idempotent — safe to call on every OEM upsert.
    """
    if not rc or not (rc.company_name or "").strip():
        return {"synced": False, "reason": "missing_name"}

    tier = (rc.priority_tier or "").lower()
    intent = _intent_score(rc)
    if tier not in ("hot", "warm") and intent < 45:
        return {"synced": False, "reason": "below_warm_threshold", "intent": intent}

    company = _upsert_company(db, rc)
    score = _upsert_score(db, company, rc)
    acct = _upsert_crm_account(db, company, rc, refresh_draft=refresh_draft)
    _link_robot_company(rc, company, acct)
    db.add(rc)
    db.add(company)

    logger.info(
        "StageGate CRM bridge: %s → company_id=%s crm_account_id=%s score=%.0f",
        rc.company_name,
        company.id,
        acct.id,
        score.overall_intent_score,
    )
    return {
        "synced": True,
        "robot_company_id": rc.id,
        "company_id": company.id,
        "crm_account_id": str(acct.id),
        "intent_score": float(score.overall_intent_score or 0),
        "semantic_summary": (company.crm_metadata or {}).get("semantic_summary"),
    }


def sync_all_stagegate_prospects(
    db: Session,
    *,
    refresh_draft: bool = False,
    min_score: int = 45,
) -> dict[str, Any]:
    """Backfill bridge for existing robot_companies (StageGate OEM sources)."""
    rows = (
        db.query(RobotCompany)
        .filter(
            RobotCompany.data_source.ilike("%stagegate%"),
            RobotCompany.lead_score >= min_score,
        )
        .order_by(RobotCompany.lead_score.desc())
        .all()
    )
    stats = {"candidates": len(rows), "synced": 0, "skipped": 0, "errors": []}
    for rc in rows:
        try:
            result = sync_robot_company_to_crm(db, rc, refresh_draft=refresh_draft)
            if result.get("synced"):
                stats["synced"] += 1
            else:
                stats["skipped"] += 1
        except Exception as exc:
            stats["errors"].append({"robot_company_id": rc.id, "name": rc.company_name, "error": str(exc)})
    db.commit()
    return stats


def bridge_status(rc: RobotCompany) -> dict[str, Any]:
    """Lightweight link info for Supply Pipeline UI."""
    mi = rc.market_intelligence if isinstance(rc.market_intelligence, dict) else {}
    return {
        "crm_company_id": mi.get("crm_company_id"),
        "crm_account_id": mi.get("crm_account_id"),
        "semantic_summary": mi.get("semantic_summary"),
        "outreach_pipeline": OUTREACH_PIPELINE if mi.get("crm_company_id") else None,
    }
