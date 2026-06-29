"""Push and pull Ready For Robots leads with HubSpot CRM."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import requests
from sqlalchemy.orm import Session, joinedload

from app.models.company import Company
from app.models.crm import CrmAccount
from app.models.score import Score
from app.services.crm_engagement_sync import sync_account_stage_to_engagement
from app.services.hubspot_oauth import HubSpotError
from app.services.integration_connections import PROVIDER_HUBSPOT, _find_connection

logger = logging.getLogger(__name__)

HUBSPOT_API = "https://api.hubapi.com"

HUBSPOT_DEAL_STAGE_MAP = {
    "appointmentscheduled": "meeting",
    "qualifiedtobuy": "qualified",
    "presentationscheduled": "meeting",
    "decisionmakerboughtin": "proposal",
    "contractsent": "negotiation",
    "closedwon": "closed_won",
    "closedlost": "closed_lost",
}


def _hubspot_request(method: str, path: str, token: str, *, json_body: dict | None = None) -> dict[str, Any]:
    resp = requests.request(
        method,
        f"{HUBSPOT_API}{path}",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json=json_body,
        timeout=30,
    )
    if resp.status_code >= 400:
        raise HubSpotError(f"HubSpot API {path} failed ({resp.status_code}): {resp.text[:400]}")
    if not resp.text.strip():
        return {}
    return resp.json()


def _company_domain(company: Company) -> str | None:
    website = (company.website or "").strip()
    if not website:
        return None
    from urllib.parse import urlparse

    parsed = urlparse(website if "://" in website else f"https://{website}")
    host = (parsed.netloc or parsed.path or "").lower().removeprefix("www.")
    return host or None


def _record_hubspot_link(
    db: Session,
    *,
    team_id: UUID,
    company_id: int,
    hubspot_company_id: str | None,
    hubspot_deal_id: str | None,
) -> None:
    row = _find_connection(db, team_id, PROVIDER_HUBSPOT)
    if not row:
        return
    cfg = dict(row.config or {})
    links = dict(cfg.get("hubspot_links") or {})
    links[str(company_id)] = {
        "hubspot_company_id": hubspot_company_id,
        "hubspot_deal_id": hubspot_deal_id,
        "synced_at": datetime.now(timezone.utc).isoformat(),
    }
    cfg["hubspot_links"] = links
    row.config = cfg
    db.add(row)


def _outreach_stage_for_hubspot_deal(dealstage: str | None) -> str | None:
    key = (dealstage or "").strip().lower()
    if not key:
        return None
    return HUBSPOT_DEAL_STAGE_MAP.get(key)


def sync_hubspot_deals_to_crm(db: Session, *, team_id: UUID, token: str) -> dict[str, Any]:
    row = _find_connection(db, team_id, PROVIDER_HUBSPOT)
    if not row:
        raise HubSpotError("HubSpot is not connected")
    links = (row.config or {}).get("hubspot_links") or {}
    if not isinstance(links, dict) or not links:
        return {"updated": 0, "checked": 0, "message": "No HubSpot links to sync yet — push a lead first."}

    updated = 0
    checked = 0
    for company_key, link in links.items():
        if not isinstance(link, dict):
            continue
        deal_id = link.get("hubspot_deal_id")
        if not deal_id:
            continue
        checked += 1
        deal = _hubspot_request("GET", f"/crm/v3/objects/deals/{deal_id}", token, json_body=None)
        props = deal.get("properties") or {}
        stage = _outreach_stage_for_hubspot_deal(props.get("dealstage"))
        if not stage:
            continue
        try:
            company_id = int(company_key)
        except ValueError:
            continue
        account = (
            db.query(CrmAccount)
            .filter(CrmAccount.team_id == team_id, CrmAccount.company_id == company_id)
            .first()
        )
        if not account:
            continue
        if account.outreach_stage == stage:
            continue
        account.outreach_stage = stage
        sync_account_stage_to_engagement(db, account)
        db.add(account)
        updated += 1

    if updated:
        db.commit()
    return {"updated": updated, "checked": checked}


def push_company_to_hubspot(
    db: Session,
    *,
    token: str,
    company_id: int,
    deal_name: str | None = None,
    team_id: UUID | None = None,
) -> dict[str, Any]:
    company = (
        db.query(Company)
        .options(joinedload(Company.scores))
        .filter(Company.id == company_id)
        .first()
    )
    if not company:
        raise HubSpotError(f"Company {company_id} not found")

    domain = _company_domain(company)
    score = None
    if company.scores:
        score = max((float(s.overall_intent_score or 0) for s in company.scores), default=0.0)

    company_props = {
        "name": company.name,
        "domain": domain,
        "industry": company.industry,
        "description": f"Ready For Robots intent score: {score:.0f}" if score else None,
    }
    company_props = {k: v for k, v in company_props.items() if v}

    hs_company = _hubspot_request(
        "POST",
        "/crm/v3/objects/companies",
        token,
        json_body={"properties": company_props},
    )
    hs_company_id = hs_company.get("id")

    deal_props = {
        "dealname": deal_name or f"{company.name} — automation pursuit",
        "dealstage": "appointmentscheduled",
        "pipeline": "default",
        "description": f"Synced from Ready For Robots. Intent score: {score:.0f}" if score else "Synced from Ready For Robots",
    }
    deal_props = {k: v for k, v in deal_props.items() if v}
    hs_deal = _hubspot_request(
        "POST",
        "/crm/v3/objects/deals",
        token,
        json_body={"properties": deal_props},
    )
    hs_deal_id = hs_deal.get("id")

    if hs_company_id and hs_deal_id:
        _hubspot_request(
            "PUT",
            f"/crm/v4/objects/deals/{hs_deal_id}/associations/companies/{hs_company_id}",
            token,
            json_body=[
                {
                    "associationCategory": "HUBSPOT_DEFINED",
                    "associationTypeId": 5,
                }
            ],
        )

    if team_id:
        _record_hubspot_link(
            db,
            team_id=team_id,
            company_id=company_id,
            hubspot_company_id=str(hs_company_id) if hs_company_id else None,
            hubspot_deal_id=str(hs_deal_id) if hs_deal_id else None,
        )
        db.commit()

    return {
        "hubspot_company_id": hs_company_id,
        "hubspot_deal_id": hs_deal_id,
        "company_id": company_id,
        "company_name": company.name,
    }
