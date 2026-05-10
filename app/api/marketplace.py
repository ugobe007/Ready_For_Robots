"""Marketplace/workspace API for vendor, buyer, RFQ, and SCOUT automation objects."""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.auth_deps import _require_user
from app.api.user import _ensure_profile
from app.database import get_db
from app.models.crm import Team, TeamMember
from app.models.marketplace import (
    BuyerProfile,
    OrganizationAsset,
    OrganizationProfile,
    Rfq,
    RfqProposal,
    RfqRequirement,
    VendorProfile,
)

router = APIRouter()


OrganizationType = Literal["vendor", "buyer", "admin"]
AssetType = Literal["product_spec", "deck", "case_study", "pricing", "compliance", "proposal", "other"]


class OrganizationProfileBody(BaseModel):
    team_id: Optional[uuid.UUID] = None
    organization_type: OrganizationType = "vendor"
    display_name: Optional[str] = Field(None, max_length=240)
    website: Optional[str] = Field(None, max_length=512)
    description: Optional[str] = None
    automation_needs: list[str] = Field(default_factory=list, max_length=50)
    scout_preferences: dict[str, Any] = Field(default_factory=dict)
    robot_categories: list[str] = Field(default_factory=list, max_length=50)
    target_industries: list[str] = Field(default_factory=list, max_length=50)
    service_regions: list[str] = Field(default_factory=list, max_length=50)
    procurement_categories: list[str] = Field(default_factory=list, max_length=50)
    facility_types: list[str] = Field(default_factory=list, max_length=50)


class AssetBody(BaseModel):
    team_id: Optional[uuid.UUID] = None
    asset_type: AssetType = "other"
    filename: str = Field(..., min_length=1, max_length=512)
    mime_type: Optional[str] = Field(None, max_length=160)
    storage_path: Optional[str] = Field(None, max_length=1024)
    visibility: Literal["private", "rfq_response", "public"] = "private"
    metadata: dict[str, Any] = Field(default_factory=dict)


class RfqRequirementBody(BaseModel):
    requirement_type: str = Field("general", max_length=64)
    body: str = Field(..., min_length=1)
    priority: Literal["required", "preferred", "nice_to_have"] = "required"


class RfqBody(BaseModel):
    team_id: Optional[uuid.UUID] = None
    title: str = Field(..., min_length=1, max_length=240)
    summary: Optional[str] = None
    automation_category: Optional[str] = Field(None, max_length=120)
    status: Literal["draft", "published"] = "draft"
    budget_min: Optional[Decimal] = None
    budget_max: Optional[Decimal] = None
    currency: str = Field("USD", max_length=8)
    due_at: Optional[datetime] = None
    evaluation_criteria: list[str] = Field(default_factory=list, max_length=50)
    requirements: list[RfqRequirementBody] = Field(default_factory=list, max_length=100)


class ProposalBody(BaseModel):
    vendor_team_id: Optional[uuid.UUID] = None
    status: Literal["draft", "submitted"] = "draft"
    proposal_title: Optional[str] = Field(None, max_length=240)
    proposal_summary: Optional[str] = None
    price_estimate: Optional[Decimal] = None
    currency: str = Field("USD", max_length=8)
    asset_ids: list[str] = Field(default_factory=list, max_length=100)


def _uid_uuid(user: dict) -> uuid.UUID:
    return uuid.UUID(str(user["uid"]))


def _money(v: Optional[Decimal]) -> Optional[float]:
    return float(v) if v is not None else None


def _team_for_user(db: Session, uid: uuid.UUID, team_id: uuid.UUID) -> Team:
    team = (
        db.query(Team)
        .join(TeamMember, TeamMember.team_id == Team.id)
        .filter(TeamMember.user_id == uid, Team.id == team_id)
        .first()
    )
    if not team:
        raise HTTPException(status_code=404, detail="Workspace not found or access denied")
    return team


def _default_team(db: Session, uid: uuid.UUID, email: str) -> Team:
    _ensure_profile(db, str(uid), email)
    existing = (
        db.query(Team)
        .join(TeamMember, TeamMember.team_id == Team.id)
        .filter(TeamMember.user_id == uid)
        .order_by(Team.created_at.asc())
        .first()
    )
    if existing:
        return existing
    team = Team(name="My workspace", slug=None)
    db.add(team)
    db.flush()
    db.add(TeamMember(team_id=team.id, user_id=uid, role="owner"))
    db.commit()
    db.refresh(team)
    return team


def _resolve_team(db: Session, user: dict, team_id: Optional[uuid.UUID]) -> Team:
    uid = _uid_uuid(user)
    if team_id:
        return _team_for_user(db, uid, team_id)
    return _default_team(db, uid, user.get("email") or "")


def _ensure_org_profile(db: Session, team: Team, org_type: str = "vendor") -> OrganizationProfile:
    row = db.query(OrganizationProfile).filter(OrganizationProfile.team_id == team.id).first()
    if row:
        return row
    row = OrganizationProfile(team_id=team.id, organization_type=org_type, display_name=team.name)
    db.add(row)
    db.flush()
    return row


def _ensure_type_profile(db: Session, team_id: uuid.UUID, org_type: str) -> None:
    if org_type == "vendor" and not db.query(VendorProfile).filter(VendorProfile.team_id == team_id).first():
        db.add(VendorProfile(team_id=team_id))
    if org_type == "buyer" and not db.query(BuyerProfile).filter(BuyerProfile.team_id == team_id).first():
        db.add(BuyerProfile(team_id=team_id))


def _scout_capabilities(org_type: str) -> list[dict[str, str]]:
    if org_type == "buyer":
        return [
            {"id": "rfq_drafting", "label": "Draft RFQs from operational needs"},
            {"id": "vendor_matching", "label": "Match RFQs to qualified robotics vendors"},
            {"id": "proposal_triage", "label": "Score proposals against requirements"},
            {"id": "procurement_followup", "label": "Track questions, deadlines, and vendor replies"},
        ]
    return [
        {"id": "lead_activation", "label": "Activate sales motions from matched leads"},
        {"id": "asset_selection", "label": "Pick approved specs, decks, and case studies for each buyer"},
        {"id": "proposal_assist", "label": "Draft RFQ responses and ROI narratives"},
        {"id": "reply_monitoring", "label": "Track responses and meeting-ready leads"},
    ]


def _serialize_org(team: Team, profile: OrganizationProfile) -> dict[str, Any]:
    return {
        "team": {
            "id": str(team.id),
            "name": team.name,
            "slug": team.slug,
        },
        "profile": {
            "id": str(profile.id),
            "organizationType": profile.organization_type,
            "displayName": profile.display_name,
            "website": profile.website,
            "description": profile.description,
            "automationNeeds": profile.automation_needs or [],
            "scoutPreferences": profile.scout_preferences or {},
        },
        "scoutCapabilities": _scout_capabilities(profile.organization_type),
    }


def _serialize_asset(asset: OrganizationAsset) -> dict[str, Any]:
    return {
        "id": str(asset.id),
        "teamId": str(asset.team_id),
        "assetType": asset.asset_type,
        "filename": asset.filename,
        "mimeType": asset.mime_type,
        "storagePath": asset.storage_path,
        "visibility": asset.visibility,
        "metadata": asset.asset_metadata or {},
        "createdAt": asset.created_at.isoformat() if asset.created_at else None,
    }


def _serialize_rfq(row: Rfq, requirements: Optional[list[RfqRequirement]] = None) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "buyerTeamId": str(row.buyer_team_id),
        "title": row.title,
        "summary": row.summary,
        "automationCategory": row.automation_category,
        "status": row.status,
        "budgetMin": _money(row.budget_min),
        "budgetMax": _money(row.budget_max),
        "currency": row.currency,
        "dueAt": row.due_at.isoformat() if row.due_at else None,
        "evaluationCriteria": row.evaluation_criteria or [],
        "scoutSummary": row.scout_summary or {},
        "requirements": [
            {
                "id": str(req.id),
                "requirementType": req.requirement_type,
                "body": req.body,
                "priority": req.priority,
            }
            for req in (requirements or [])
        ],
        "createdAt": row.created_at.isoformat() if row.created_at else None,
    }


def _serialize_proposal(row: RfqProposal) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "rfqId": str(row.rfq_id),
        "vendorTeamId": str(row.vendor_team_id),
        "status": row.status,
        "proposalTitle": row.proposal_title,
        "proposalSummary": row.proposal_summary,
        "priceEstimate": _money(row.price_estimate),
        "currency": row.currency,
        "assetIds": row.asset_ids or [],
        "scoutResponsePlan": row.scout_response_plan or {},
        "createdAt": row.created_at.isoformat() if row.created_at else None,
    }


@router.get("/organization")
def get_organization_profile(
    team_id: Optional[uuid.UUID] = Query(None),
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
):
    team = _resolve_team(db, user, team_id)
    profile = _ensure_org_profile(db, team)
    _ensure_type_profile(db, team.id, profile.organization_type)
    db.commit()
    db.refresh(profile)
    return _serialize_org(team, profile)


@router.put("/organization")
def put_organization_profile(
    body: OrganizationProfileBody,
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
):
    team = _resolve_team(db, user, body.team_id)
    profile = _ensure_org_profile(db, team, body.organization_type)
    profile.organization_type = body.organization_type
    profile.display_name = body.display_name or profile.display_name or team.name
    profile.website = body.website
    profile.description = body.description
    profile.automation_needs = body.automation_needs
    profile.scout_preferences = body.scout_preferences
    if body.display_name:
        team.name = body.display_name
    _ensure_type_profile(db, team.id, body.organization_type)
    if body.organization_type == "vendor":
        vendor = db.query(VendorProfile).filter(VendorProfile.team_id == team.id).first()
        if vendor:
            vendor.robot_categories = body.robot_categories
            vendor.target_industries = body.target_industries
            vendor.service_regions = body.service_regions
    if body.organization_type == "buyer":
        buyer = db.query(BuyerProfile).filter(BuyerProfile.team_id == team.id).first()
        if buyer:
            buyer.procurement_categories = body.procurement_categories
            buyer.facility_types = body.facility_types
    db.commit()
    db.refresh(profile)
    return _serialize_org(team, profile)


@router.get("/assets")
def list_assets(
    team_id: Optional[uuid.UUID] = Query(None),
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
):
    team = _resolve_team(db, user, team_id)
    rows = (
        db.query(OrganizationAsset)
        .filter(OrganizationAsset.team_id == team.id)
        .order_by(OrganizationAsset.created_at.desc())
        .all()
    )
    return {"assets": [_serialize_asset(row) for row in rows]}


@router.post("/assets")
def create_asset(
    body: AssetBody,
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
):
    team = _resolve_team(db, user, body.team_id)
    asset = OrganizationAsset(
        team_id=team.id,
        uploaded_by_user_id=_uid_uuid(user),
        asset_type=body.asset_type,
        filename=body.filename,
        mime_type=body.mime_type,
        storage_path=body.storage_path,
        visibility=body.visibility,
        asset_metadata=body.metadata,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return _serialize_asset(asset)


@router.get("/rfqs")
def list_rfqs(
    team_id: Optional[uuid.UUID] = Query(None),
    include_drafts: bool = Query(False),
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
):
    team = _resolve_team(db, user, team_id)
    conditions = [Rfq.status == "published", Rfq.buyer_team_id == team.id]
    if include_drafts:
        conditions.append(Rfq.buyer_team_id == team.id)
    rows = (
        db.query(Rfq)
        .filter(or_(*conditions))
        .order_by(Rfq.created_at.desc())
        .limit(100)
        .all()
    )
    return {"rfqs": [_serialize_rfq(row) for row in rows]}


@router.post("/rfqs")
def create_rfq(
    body: RfqBody,
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
):
    team = _resolve_team(db, user, body.team_id)
    profile = _ensure_org_profile(db, team, "buyer")
    profile.organization_type = "buyer"
    _ensure_type_profile(db, team.id, "buyer")
    row = Rfq(
        buyer_team_id=team.id,
        created_by_user_id=_uid_uuid(user),
        title=body.title,
        summary=body.summary,
        automation_category=body.automation_category,
        status=body.status,
        budget_min=body.budget_min,
        budget_max=body.budget_max,
        currency=body.currency,
        due_at=body.due_at,
        evaluation_criteria=body.evaluation_criteria,
        scout_summary={
            "next": "SCOUT can match this RFQ to vendor profiles, draft clarifying questions, and score submitted proposals.",
            "automation": ["vendor matching", "requirements scoring", "proposal comparison", "deadline tracking"],
        },
    )
    db.add(row)
    db.flush()
    reqs = [
        RfqRequirement(
            rfq_id=row.id,
            requirement_type=req.requirement_type,
            body=req.body,
            priority=req.priority,
        )
        for req in body.requirements
    ]
    for req in reqs:
        db.add(req)
    db.commit()
    db.refresh(row)
    return _serialize_rfq(row, reqs)


@router.post("/rfqs/{rfq_id}/proposals")
def create_or_update_proposal(
    rfq_id: uuid.UUID,
    body: ProposalBody,
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
):
    rfq = db.query(Rfq).filter(Rfq.id == rfq_id).first()
    if not rfq:
        raise HTTPException(status_code=404, detail="RFQ not found")
    vendor_team = _resolve_team(db, user, body.vendor_team_id)
    profile = _ensure_org_profile(db, vendor_team, "vendor")
    profile.organization_type = "vendor"
    _ensure_type_profile(db, vendor_team.id, "vendor")
    proposal = (
        db.query(RfqProposal)
        .filter(RfqProposal.rfq_id == rfq_id, RfqProposal.vendor_team_id == vendor_team.id)
        .first()
    )
    if not proposal:
        proposal = RfqProposal(rfq_id=rfq_id, vendor_team_id=vendor_team.id, submitted_by_user_id=_uid_uuid(user))
        db.add(proposal)
    proposal.status = body.status
    proposal.proposal_title = body.proposal_title
    proposal.proposal_summary = body.proposal_summary
    proposal.price_estimate = body.price_estimate
    proposal.currency = body.currency
    proposal.asset_ids = body.asset_ids
    proposal.scout_response_plan = {
        "next": "SCOUT should compare the proposal against RFQ requirements, attach approved assets, and draft buyer-facing follow-up.",
        "guardrails": ["use approved materials only", "respect proposal deadline", "flag missing requirements"],
    }
    db.commit()
    db.refresh(proposal)
    return _serialize_proposal(proposal)
