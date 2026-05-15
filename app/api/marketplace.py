"""Marketplace/workspace API for vendor, buyer, RFQ, and SCOUT automation objects."""
from __future__ import annotations

import json
import os
import shutil
import uuid
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Literal, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.auth_deps import _require_user
from app.api.user import _ensure_profile
from app.database import get_db
from app.models.crm import Team, TeamMember
from app.models.marketplace import (
    BuyerProfile,
    MarketplaceCommercialDocument,
    MarketplaceIntegrationConnection,
    OrganizationAsset,
    OrganizationProfile,
    Rfq,
    RfqProposal,
    RfqRequirement,
    RfqScheduleEvent,
    VendorProfile,
)

router = APIRouter()


OrganizationType = Literal["vendor", "buyer", "admin"]
AssetType = Literal["product_spec", "deck", "case_study", "pricing", "compliance", "proposal", "other"]
CommercialDocumentType = Literal["proposal", "quote", "invoice", "purchase_order"]
CommercialDocumentStatus = Literal["draft", "issued", "accepted", "rejected", "paid", "void"]
ConnectionType = Literal["mcp_server", "vendor_api", "erp", "crm", "storage", "infra"]


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
    decision_makers: list[dict[str, Any]] = Field(default_factory=list, max_length=100)
    procurement_workflow: dict[str, Any] = Field(default_factory=dict)
    po_preferences: dict[str, Any] = Field(default_factory=dict)


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
    project_description: Optional[str] = None
    timeline_summary: Optional[str] = None
    automation_category: Optional[str] = Field(None, max_length=120)
    status: Literal["draft", "published"] = "draft"
    budget_min: Optional[Decimal] = None
    budget_max: Optional[Decimal] = None
    currency: str = Field("USD", max_length=8)
    due_at: Optional[datetime] = None
    decision_makers: list[dict[str, Any]] = Field(default_factory=list, max_length=100)
    workflow_process: dict[str, Any] = Field(default_factory=dict)
    technical_specs: dict[str, Any] = Field(default_factory=dict)
    schedule: list[dict[str, Any]] = Field(default_factory=list, max_length=50)
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


class ScheduleEventBody(BaseModel):
    event_type: str = Field("deadline", max_length=64)
    title: str = Field(..., min_length=1, max_length=240)
    description: Optional[str] = None
    due_at: datetime
    reminder_offsets: list[int] = Field(default_factory=list, max_length=20)
    email_recipients: list[str] = Field(default_factory=list, max_length=100)
    payload: dict[str, Any] = Field(default_factory=dict)


class CommercialDocumentBody(BaseModel):
    rfq_id: Optional[uuid.UUID] = None
    proposal_id: Optional[uuid.UUID] = None
    buyer_team_id: uuid.UUID
    vendor_team_id: uuid.UUID
    document_type: CommercialDocumentType
    status: CommercialDocumentStatus = "draft"
    document_number: Optional[str] = Field(None, max_length=120)
    title: Optional[str] = Field(None, max_length=240)
    amount: Optional[Decimal] = None
    currency: str = Field("USD", max_length=8)
    due_at: Optional[datetime] = None
    issued_at: Optional[datetime] = None
    asset_ids: list[str] = Field(default_factory=list, max_length=100)
    payload: dict[str, Any] = Field(default_factory=dict)


class IntegrationConnectionBody(BaseModel):
    team_id: Optional[uuid.UUID] = None
    connection_type: ConnectionType = "mcp_server"
    name: str = Field(..., min_length=1, max_length=180)
    status: Literal["draft", "active", "paused", "error"] = "draft"
    base_url: Optional[str] = Field(None, max_length=1024)
    mcp_server_url: Optional[str] = Field(None, max_length=1024)
    auth_type: Optional[str] = Field(None, max_length=64)
    secret_ref: Optional[str] = Field(None, max_length=240)
    allowed_scopes: list[str] = Field(default_factory=list, max_length=100)
    config: dict[str, Any] = Field(default_factory=dict)


def _uid_uuid(user: dict) -> uuid.UUID:
    return uuid.UUID(str(user["uid"]))


def _money(v: Optional[Decimal]) -> Optional[float]:
    return float(v) if v is not None else None


def _upload_root() -> Path:
    return Path(os.getenv("MARKETPLACE_UPLOAD_DIR") or "uploads/marketplace").resolve()


def _safe_filename(filename: str) -> str:
    base = Path(filename or "upload.bin").name
    return "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in base)[:160] or "upload.bin"


def _parse_metadata(raw: Optional[str]) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="metadata must be valid JSON") from exc
    if not isinstance(data, dict):
        raise HTTPException(status_code=400, detail="metadata must be a JSON object")
    return data


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
        "projectDescription": row.project_description,
        "timelineSummary": row.timeline_summary,
        "automationCategory": row.automation_category,
        "status": row.status,
        "budgetMin": _money(row.budget_min),
        "budgetMax": _money(row.budget_max),
        "currency": row.currency,
        "dueAt": row.due_at.isoformat() if row.due_at else None,
        "decisionMakers": row.decision_makers or [],
        "workflowProcess": row.workflow_process or {},
        "technicalSpecs": row.technical_specs or {},
        "schedule": row.schedule or [],
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


def _serialize_commercial_document(row: MarketplaceCommercialDocument) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "rfqId": str(row.rfq_id) if row.rfq_id else None,
        "proposalId": str(row.proposal_id) if row.proposal_id else None,
        "buyerTeamId": str(row.buyer_team_id),
        "vendorTeamId": str(row.vendor_team_id),
        "documentType": row.document_type,
        "status": row.status,
        "documentNumber": row.document_number,
        "title": row.title,
        "amount": _money(row.amount),
        "currency": row.currency,
        "dueAt": row.due_at.isoformat() if row.due_at else None,
        "issuedAt": row.issued_at.isoformat() if row.issued_at else None,
        "assetIds": row.asset_ids or [],
        "payload": row.payload or {},
        "createdAt": row.created_at.isoformat() if row.created_at else None,
    }


def _serialize_connection(row: MarketplaceIntegrationConnection) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "teamId": str(row.team_id),
        "connectionType": row.connection_type,
        "name": row.name,
        "status": row.status,
        "baseUrl": row.base_url,
        "mcpServerUrl": row.mcp_server_url,
        "authType": row.auth_type,
        "secretRef": row.secret_ref,
        "allowedScopes": row.allowed_scopes or [],
        "config": row.config or {},
        "lastCheckedAt": row.last_checked_at.isoformat() if row.last_checked_at else None,
        "createdAt": row.created_at.isoformat() if row.created_at else None,
    }


def _serialize_schedule_event(row: RfqScheduleEvent) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "rfqId": str(row.rfq_id),
        "eventType": row.event_type,
        "title": row.title,
        "description": row.description,
        "dueAt": row.due_at.isoformat() if row.due_at else None,
        "reminderOffsets": row.reminder_offsets or [],
        "emailRecipients": row.email_recipients or [],
        "status": row.status,
        "payload": row.payload or {},
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
            buyer.decision_makers = body.decision_makers
            buyer.procurement_workflow = body.procurement_workflow
            buyer.po_preferences = body.po_preferences
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


@router.post("/assets/upload")
def upload_asset(
    team_id: Optional[str] = Form(None),
    asset_type: AssetType = Form("other"),
    visibility: Literal["private", "rfq_response", "public"] = Form("private"),
    metadata: Optional[str] = Form(None),
    file: UploadFile = File(...),
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
):
    parsed_team_id = uuid.UUID(team_id) if team_id else None
    team = _resolve_team(db, user, parsed_team_id)
    safe_name = _safe_filename(file.filename or "upload.bin")
    storage_dir = _upload_root() / str(team.id)
    storage_dir.mkdir(parents=True, exist_ok=True)
    storage_name = f"{uuid.uuid4()}_{safe_name}"
    storage_path = storage_dir / storage_name
    with storage_path.open("wb") as out:
        shutil.copyfileobj(file.file, out)
    asset = OrganizationAsset(
        team_id=team.id,
        uploaded_by_user_id=_uid_uuid(user),
        asset_type=asset_type,
        filename=safe_name,
        mime_type=file.content_type,
        storage_path=str(storage_path),
        visibility=visibility,
        asset_metadata={**_parse_metadata(metadata), "bytes": storage_path.stat().st_size},
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
        project_description=body.project_description,
        timeline_summary=body.timeline_summary,
        automation_category=body.automation_category,
        status=body.status,
        budget_min=body.budget_min,
        budget_max=body.budget_max,
        currency=body.currency,
        due_at=body.due_at,
        decision_makers=body.decision_makers,
        workflow_process=body.workflow_process,
        technical_specs=body.technical_specs,
        schedule=body.schedule,
        evaluation_criteria=body.evaluation_criteria,
        scout_summary={
            "next": "SCOUT can match this RFQ to vendor profiles, prepare Cal clarifying questions, and score submitted proposals.",
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


@router.post("/rfqs/{rfq_id}/schedule")
def create_rfq_schedule_event(
    rfq_id: uuid.UUID,
    body: ScheduleEventBody,
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
):
    rfq = db.query(Rfq).filter(Rfq.id == rfq_id).first()
    if not rfq:
        raise HTTPException(status_code=404, detail="RFQ not found")
    _team_for_user(db, _uid_uuid(user), rfq.buyer_team_id)
    event = RfqScheduleEvent(
        rfq_id=rfq.id,
        event_type=body.event_type,
        title=body.title,
        description=body.description,
        due_at=body.due_at,
        reminder_offsets=body.reminder_offsets,
        email_recipients=body.email_recipients,
        payload={
            **body.payload,
            "email_status": "scheduled",
            "next": "Cal should email prospective robot companies before this deadline.",
        },
    )
    db.add(event)
    rfq.schedule = [*(rfq.schedule or []), {"title": body.title, "due_at": body.due_at.isoformat(), "event_type": body.event_type}]
    db.commit()
    db.refresh(event)
    return _serialize_schedule_event(event)


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
        "next": "SCOUT should compare the proposal against RFQ requirements, attach approved assets, and prepare Cal's buyer-facing follow-up.",
        "guardrails": ["use approved materials only", "respect proposal deadline", "flag missing requirements"],
    }
    db.commit()
    db.refresh(proposal)
    return _serialize_proposal(proposal)


@router.post("/commercial-documents")
def create_commercial_document(
    body: CommercialDocumentBody,
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
):
    # Either side can create a commercial document if they belong to the buyer or vendor workspace.
    uid = _uid_uuid(user)
    try:
        _team_for_user(db, uid, body.vendor_team_id)
    except HTTPException:
        _team_for_user(db, uid, body.buyer_team_id)
    doc = MarketplaceCommercialDocument(
        rfq_id=body.rfq_id,
        proposal_id=body.proposal_id,
        buyer_team_id=body.buyer_team_id,
        vendor_team_id=body.vendor_team_id,
        created_by_user_id=uid,
        document_type=body.document_type,
        status=body.status,
        document_number=body.document_number,
        title=body.title,
        amount=body.amount,
        currency=body.currency,
        due_at=body.due_at,
        issued_at=body.issued_at,
        asset_ids=body.asset_ids,
        payload=body.payload,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return _serialize_commercial_document(doc)


@router.get("/commercial-documents")
def list_commercial_documents(
    team_id: Optional[uuid.UUID] = Query(None),
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
):
    team = _resolve_team(db, user, team_id)
    rows = (
        db.query(MarketplaceCommercialDocument)
        .filter((MarketplaceCommercialDocument.buyer_team_id == team.id) | (MarketplaceCommercialDocument.vendor_team_id == team.id))
        .order_by(MarketplaceCommercialDocument.created_at.desc())
        .limit(100)
        .all()
    )
    return {"documents": [_serialize_commercial_document(row) for row in rows]}


@router.post("/connections")
def create_integration_connection(
    body: IntegrationConnectionBody,
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
):
    team = _resolve_team(db, user, body.team_id)
    row = MarketplaceIntegrationConnection(
        team_id=team.id,
        created_by_user_id=_uid_uuid(user),
        connection_type=body.connection_type,
        name=body.name,
        status=body.status,
        base_url=body.base_url,
        mcp_server_url=body.mcp_server_url,
        auth_type=body.auth_type,
        # Store a reference to a secret manager entry, never raw credentials.
        secret_ref=body.secret_ref,
        allowed_scopes=body.allowed_scopes,
        config=body.config,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _serialize_connection(row)


@router.get("/connections")
def list_integration_connections(
    team_id: Optional[uuid.UUID] = Query(None),
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
):
    team = _resolve_team(db, user, team_id)
    rows = (
        db.query(MarketplaceIntegrationConnection)
        .filter(MarketplaceIntegrationConnection.team_id == team.id)
        .order_by(MarketplaceIntegrationConnection.created_at.desc())
        .all()
    )
    return {"connections": [_serialize_connection(row) for row in rows]}
