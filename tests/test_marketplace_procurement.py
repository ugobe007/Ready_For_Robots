import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401 - register SQLAlchemy models
from app.api.marketplace import (
    _parse_metadata,
    _safe_filename,
    _serialize_commercial_document,
    _serialize_connection,
    _serialize_rfq,
)
from app.database import Base
from app.models.marketplace import MarketplaceCommercialDocument, MarketplaceIntegrationConnection, Rfq


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_asset_upload_helpers_sanitize_filename_and_metadata():
    assert _safe_filename("../Robot Deck Final!.pdf") == "Robot_Deck_Final_.pdf"
    assert _parse_metadata('{"source":"operator","tags":["deck"]}') == {
        "source": "operator",
        "tags": ["deck"],
    }


def test_rfq_serializer_includes_procurement_context():
    buyer_team_id = uuid.uuid4()
    rfq = Rfq(
        id=uuid.uuid4(),
        buyer_team_id=buyer_team_id,
        title="Warehouse AMR RFP",
        summary="Need AMRs for picking support.",
        project_description="Deploy AMRs across two facilities.",
        timeline_summary="Pilot in Q3, rollout in Q4.",
        decision_makers=[{"name": "Jane Buyer", "title": "VP Operations"}],
        workflow_process={"steps": ["technical review", "pilot", "PO"]},
        technical_specs={"payload_lb": 80},
        schedule=[{"title": "Vendor questions due"}],
        evaluation_criteria=["safety", "ROI"],
    )

    out = _serialize_rfq(rfq)

    assert out["projectDescription"] == "Deploy AMRs across two facilities."
    assert out["timelineSummary"] == "Pilot in Q3, rollout in Q4."
    assert out["decisionMakers"][0]["title"] == "VP Operations"
    assert out["technicalSpecs"]["payload_lb"] == 80


def test_commercial_document_serializer_handles_quote_invoice_po():
    doc = MarketplaceCommercialDocument(
        id=uuid.uuid4(),
        rfq_id=uuid.uuid4(),
        buyer_team_id=uuid.uuid4(),
        vendor_team_id=uuid.uuid4(),
        document_type="quote",
        status="issued",
        document_number="Q-1001",
        title="AMR pilot quote",
        amount=125000,
        currency="USD",
        issued_at=datetime(2026, 5, 13, tzinfo=timezone.utc),
        asset_ids=["asset-1"],
        payload={"payment_terms": "Net 30"},
    )

    out = _serialize_commercial_document(doc)

    assert out["documentType"] == "quote"
    assert out["documentNumber"] == "Q-1001"
    assert out["amount"] == 125000.0
    assert out["payload"]["payment_terms"] == "Net 30"


def test_connection_serializer_uses_secret_reference_not_raw_credentials():
    row = MarketplaceIntegrationConnection(
        id=uuid.uuid4(),
        team_id=uuid.uuid4(),
        connection_type="mcp_server",
        name="RobotCo MCP",
        status="active",
        mcp_server_url="https://api.robotco.example/mcp",
        auth_type="api_key",
        secret_ref="harness-secret://robotco-api-key",
        allowed_scopes=["quotes:create", "invoices:read"],
        config={"rate_limit": "standard"},
    )

    out = _serialize_connection(row)

    assert out["connectionType"] == "mcp_server"
    assert out["secretRef"] == "harness-secret://robotco-api-key"
    assert "api_key_value" not in out
