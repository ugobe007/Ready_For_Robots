"""
Physically merge duplicate `companies` rows that share the same `website_domain`:
re-point foreign keys to the canonical company, then delete losers.

Canonical choice matches `pick_canonical_company` (intent score, signals, id).
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session, joinedload

from app.models.company import Company
from app.models.signal import Signal
from app.models.score import Score
from app.models.contact import Contact
from app.models.lead_rep_feedback import LeadRepFeedback
from app.services.company_domain import pick_canonical_company
from app.services.automation_profile import build_automation_profile_dict_from_company


def _merge_crm_accounts(db: Session, loser_id: int, canonical_id: int) -> None:
    """Respect uq_crm_accounts_team_company: merge engagements then drop duplicate account rows."""
    try:
        from app.models.crm import CrmAccount, CrmEngagement
    except ImportError:
        return

    accounts = db.query(CrmAccount).filter(CrmAccount.company_id == loser_id).all()
    for acc in accounts:
        twin = (
            db.query(CrmAccount)
            .filter(
                CrmAccount.team_id == acc.team_id,
                CrmAccount.company_id == canonical_id,
            )
            .first()
        )
        if twin:
            db.query(CrmEngagement).filter(CrmEngagement.crm_account_id == acc.id).update(
                {"crm_account_id": twin.id},
                synchronize_session=False,
            )
            db.delete(acc)
        else:
            acc.company_id = canonical_id


def _repoint_user_tables(db: Session, loser_id: int, canonical_id: int) -> None:
    """user_saved_companies (unique user+company), user_list_companies (PK list+company), ai_reports."""
    db.execute(
        text(
            """
            DELETE FROM user_saved_companies
            WHERE company_id = :loser
              AND user_id IN (
                SELECT user_id FROM user_saved_companies WHERE company_id = :canonical
              )
            """
        ),
        {"loser": loser_id, "canonical": canonical_id},
    )
    db.execute(
        text(
            """
            UPDATE user_saved_companies SET company_id = :canonical
            WHERE company_id = :loser
            """
        ),
        {"loser": loser_id, "canonical": canonical_id},
    )

    db.execute(
        text(
            """
            DELETE FROM user_list_companies
            WHERE company_id = :loser
              AND list_id IN (
                SELECT list_id FROM user_list_companies WHERE company_id = :canonical
              )
            """
        ),
        {"loser": loser_id, "canonical": canonical_id},
    )
    db.execute(
        text(
            """
            UPDATE user_list_companies SET company_id = :canonical
            WHERE company_id = :loser
            """
        ),
        {"loser": loser_id, "canonical": canonical_id},
    )

    db.execute(
        text(
            """
            UPDATE ai_reports SET company_id = :canonical
            WHERE company_id = :loser
            """
        ),
        {"loser": loser_id, "canonical": canonical_id},
    )


def _dedupe_contacts_for_company(db: Session, company_id: int) -> None:
    """Drop duplicate contacts sharing the same normalized email on one company."""
    bind = db.get_bind()
    dialect = bind.dialect.name if bind else "postgresql"
    if dialect == "sqlite":
        db.execute(
            text(
                """
                DELETE FROM contacts
                WHERE id IN (
                  SELECT c1.id FROM contacts c1
                  INNER JOIN contacts c2
                    ON c1.company_id = c2.company_id
                    AND c1.id > c2.id
                    AND LOWER(COALESCE(c1.email,'')) = LOWER(COALESCE(c2.email,''))
                    AND c1.company_id = :cid
                )
                """
            ),
            {"cid": company_id},
        )
    else:
        db.execute(
            text(
                """
                DELETE FROM contacts c1
                USING contacts c2
                WHERE c1.company_id = c2.company_id
                  AND c1.id > c2.id
                  AND LOWER(COALESCE(c1.email,'')) = LOWER(COALESCE(c2.email,''))
                  AND c1.company_id = :cid
                """
            ),
            {"cid": company_id},
        )


def merge_one_loser_into_canonical(db: Session, loser_id: int, canonical_id: int) -> None:
    if loser_id == canonical_id:
        return

    _merge_crm_accounts(db, loser_id, canonical_id)

    db.query(Signal).filter(Signal.company_id == loser_id).update(
        {"company_id": canonical_id},
        synchronize_session=False,
    )
    db.query(Score).filter(Score.company_id == loser_id).update(
        {"company_id": canonical_id},
        synchronize_session=False,
    )
    db.query(Contact).filter(Contact.company_id == loser_id).update(
        {"company_id": canonical_id},
        synchronize_session=False,
    )

    _repoint_user_tables(db, loser_id, canonical_id)

    _dedupe_contacts_for_company(db, canonical_id)

    db.query(LeadRepFeedback).filter(LeadRepFeedback.company_id == loser_id).update(
        {"company_id": canonical_id},
        synchronize_session=False,
    )

    loser = db.query(Company).filter(Company.id == loser_id).first()
    if loser:
        db.delete(loser)

    canonical = (
        db.query(Company)
        .options(joinedload(Company.signals))
        .filter(Company.id == canonical_id)
        .first()
    )
    if canonical:
        try:
            canonical.automation_profile = build_automation_profile_dict_from_company(canonical)
        except Exception:
            pass


def merge_duplicate_companies_by_domain(
    db: Session,
    dry_run: bool = True,
    domain_filter: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Group companies by `website_domain`; for each group with 2+ rows, merge non-canonical
    rows into the canonical company.

    If `domain_filter` is set, only process that normalized domain (for targeted repair).
    """
    q = db.query(Company).filter(Company.website_domain.isnot(None))
    if domain_filter:
        q = q.filter(Company.website_domain == domain_filter.strip().lower())
    companies = q.all()

    groups: Dict[str, List[Company]] = defaultdict(list)
    for c in companies:
        if c.website_domain:
            groups[c.website_domain].append(c)

    plan: List[Dict[str, Any]] = []
    for dom, peers in groups.items():
        if len(peers) < 2:
            continue
        canonical = pick_canonical_company(peers)
        if not canonical:
            continue
        losers = [p for p in peers if p.id != canonical.id]
        plan.append(
            {
                "website_domain": dom,
                "canonical_id": canonical.id,
                "loser_ids": [p.id for p in losers],
            }
        )

    if dry_run:
        total_losers = sum(len(p["loser_ids"]) for p in plan)
        return {
            "dry_run": True,
            "groups": len(plan),
            "companies_to_delete": total_losers,
            "plan": plan,
        }

    deleted: List[int] = []
    try:
        for entry in plan:
            cid = entry["canonical_id"]
            for lid in entry["loser_ids"]:
                merge_one_loser_into_canonical(db, lid, cid)
                deleted.append(lid)
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {
        "dry_run": False,
        "groups": len(plan),
        "deleted_company_ids": deleted,
        "merged_into": {p["website_domain"]: p["canonical_id"] for p in plan},
    }
