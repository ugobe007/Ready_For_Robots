"""Push Ready For Robots leads to HubSpot CRM."""
from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

import requests
from sqlalchemy.orm import Session, joinedload

from app.models.company import Company
from app.models.score import Score
from app.services.hubspot_oauth import HubSpotError

logger = logging.getLogger(__name__)

HUBSPOT_API = "https://api.hubapi.com"


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


def push_company_to_hubspot(
    db: Session,
    *,
    token: str,
    company_id: int,
    deal_name: str | None = None,
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

    return {
        "hubspot_company_id": hs_company_id,
        "hubspot_deal_id": hs_deal_id,
        "company_id": company_id,
        "company_name": company.name,
    }
