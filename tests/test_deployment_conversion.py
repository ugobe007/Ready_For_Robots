import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
import app.models  # noqa: F401 - register SQLAlchemy models
from app.models.crm import CrmAccount, Team
from app.models.sales_agent import SalesOpportunity
from app.models.sales_learning import SalesExperienceEvent
from app.services.deployment_conversion import (
    derive_conversion_label,
    ensure_deployment_opportunity,
    record_conversion_transition,
    set_opportunity_disposition,
)


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


@pytest.fixture()
def opportunity(db_session):
    opportunity = SalesOpportunity(
        id=str(uuid.uuid4()),
        opportunity_type="deployment",
        title="Autonomous forklift at Memphis facility",
        current_stage="new",
        disposition="active",
    )
    db_session.add(opportunity)
    db_session.commit()
    return opportunity


def _snapshot():
    return {
        "model_version": "call_priority.v0_1",
        "predicted_at": "2026-08-10T16:00:00Z",
        "facility_ref": "2314 S Lauderdale, Memphis, TN 38106",
        "robot_profile_id": "robot:reference_autonomous_forklift",
        "work_unit_ids": ["work_unit:finished_goods_transport"],
        "source_signal_ids": ["signal:riviana_forklift_posting"],
        "call_priority": "call_now",
        "dimensions": {
            "work_match": "very_high",
            "labor_pressure": "high",
            "operational_exposure": "high",
            "evidence_confidence": "strong",
            "account_resolvability": "high",
            "buyability": "qualify",
            "deployability": "unknown",
        },
    }


def _advance_to_prioritized(opportunity, db_session):
    record_conversion_transition(
        db_session,
        opportunity=opportunity,
        to_stage="discovered",
        actor="system",
        occurred_at="2026-08-10T16:00:00Z",
        evidence_level="e1_observed",
    )
    record_conversion_transition(
        db_session,
        opportunity=opportunity,
        to_stage="matched",
        actor="system",
        occurred_at="2026-08-10T16:01:00Z",
        evidence_level="e1_observed",
        facts_learned={"work_unit_ids": ["work_unit:finished_goods_transport"]},
    )
    return record_conversion_transition(
        db_session,
        opportunity=opportunity,
        to_stage="prioritized",
        actor="system",
        occurred_at="2026-08-10T16:02:00Z",
        evidence_level="e1_observed",
        prediction_snapshot=_snapshot(),
    )


def test_creates_permanent_discovered_opportunity_for_saved_account(db_session):
    team_id = uuid.uuid4()
    account_id = uuid.uuid4()
    db_session.add(Team(id=team_id, name="Robot Seller"))
    account = CrmAccount(id=account_id, team_id=team_id, name="Riviana Foods")
    db_session.add(account)
    db_session.commit()

    opportunity = ensure_deployment_opportunity(
        db_session,
        account=account,
        source_signal_ids=["signal:123"],
    )
    db_session.commit()

    assert opportunity.current_stage == "discovered"
    assert opportunity.disposition == "active"
    assert opportunity.payload["public_id"].startswith("RFR-OPP-2026-")
    event = db_session.query(SalesExperienceEvent).one()
    assert event.payload["evidence_level"] == "e1_observed"
    assert event.payload["facts_learned"]["source_signal_ids"] == ["signal:123"]


def test_prioritization_freezes_prediction_and_later_events_cannot_replace_it(opportunity, db_session):
    prioritized = _advance_to_prioritized(opportunity, db_session)
    contacted = record_conversion_transition(
        db_session,
        opportunity=opportunity,
        to_stage="contacted",
        actor="seller",
        occurred_at="2026-08-10T17:00:00Z",
        evidence_level="e1_observed",
        contact_result="connected",
    )

    assert prioritized.payload["prediction_snapshot"]["call_priority"] == "call_now"
    assert contacted.payload["prediction_snapshot"] == {}
    assert contacted.payload["contact_result"] == "connected"
    assert opportunity.current_stage == "contacted"
    assert opportunity.disposition == "active"


def test_contact_does_not_imply_qualified(opportunity, db_session):
    _advance_to_prioritized(opportunity, db_session)
    record_conversion_transition(
        db_session,
        opportunity=opportunity,
        to_stage="contacted",
        actor="seller",
        occurred_at="2026-08-10T17:00:00Z",
        evidence_level="e1_observed",
        contact_result="interested",
    )
    db_session.flush()
    assert opportunity.current_stage == "contacted"
    assert opportunity.current_stage != "qualified"
    events = db_session.query(SalesExperienceEvent).all()
    label = derive_conversion_label(events)
    assert label.contacted is True
    assert label.qualified is False


def test_prediction_requires_all_seven_dimensions(opportunity, db_session):
    snapshot = _snapshot()
    del snapshot["dimensions"]["buyability"]
    record_conversion_transition(
        db_session,
        opportunity=opportunity,
        to_stage="discovered",
        actor="system",
        occurred_at="2026-08-10T16:00:00Z",
        evidence_level="e1_observed",
    )

    with pytest.raises(ValueError, match="seven decision dimensions"):
        record_conversion_transition(
            db_session,
            opportunity=opportunity,
            to_stage="prioritized",
            actor="system",
            occurred_at="2026-08-10T16:02:00Z",
            evidence_level="e1_observed",
            prediction_snapshot=snapshot,
        )


def test_prediction_rejects_standalone_deployment_readiness(opportunity, db_session):
    snapshot = _snapshot()
    snapshot["dimensions"]["deployment_readiness"] = "unknown"
    record_conversion_transition(
        db_session,
        opportunity=opportunity,
        to_stage="discovered",
        actor="system",
        occurred_at="2026-08-10T16:00:00Z",
        evidence_level="e1_observed",
    )
    with pytest.raises(ValueError, match="seven decision dimensions"):
        record_conversion_transition(
            db_session,
            opportunity=opportunity,
            to_stage="prioritized",
            actor="system",
            occurred_at="2026-08-10T16:02:00Z",
            evidence_level="e1_observed",
            prediction_snapshot=snapshot,
        )


def test_prediction_requires_reproducible_work_graph_inputs(opportunity, db_session):
    snapshot = _snapshot()
    snapshot["source_signal_ids"] = []
    record_conversion_transition(
        db_session,
        opportunity=opportunity,
        to_stage="discovered",
        actor="system",
        occurred_at="2026-08-10T16:00:00Z",
        evidence_level="e1_observed",
    )

    with pytest.raises(ValueError, match="Work Units and source signals"):
        record_conversion_transition(
            db_session,
            opportunity=opportunity,
            to_stage="prioritized",
            actor="system",
            occurred_at="2026-08-10T16:02:00Z",
            evidence_level="e1_observed",
            prediction_snapshot=snapshot,
        )


def test_evidence_ladder_blocks_unverified_qualification(opportunity, db_session):
    _advance_to_prioritized(opportunity, db_session)

    with pytest.raises(ValueError, match="e3_work_verified"):
        record_conversion_transition(
            db_session,
            opportunity=opportunity,
            to_stage="qualified",
            actor="seller",
            occurred_at="2026-08-11T16:00:00Z",
            evidence_level="e2_customer_confirmed",
        )


def test_watch_disposition_does_not_move_truth_state_backward(opportunity, db_session):
    _advance_to_prioritized(opportunity, db_session)
    record_conversion_transition(
        db_session,
        opportunity=opportunity,
        to_stage="contacted",
        actor="seller",
        occurred_at="2026-08-10T17:00:00Z",
        evidence_level="e1_observed",
        contact_result="connected",
    )
    set_opportunity_disposition(
        db_session,
        opportunity=opportunity,
        disposition="watch",
        actor="seller",
        occurred_at="2026-08-10T18:00:00Z",
    )
    assert opportunity.current_stage == "contacted"
    assert opportunity.disposition == "watch"


def test_losses_require_discovery_and_controlled_reason(opportunity, db_session):
    with pytest.raises(ValueError, match="must be discovered"):
        record_conversion_transition(
            db_session,
            opportunity=opportunity,
            to_stage="lost",
            actor="seller",
            occurred_at="2026-08-10T16:00:00Z",
            evidence_level="e1_observed",
            reason="payload_insufficient",
        )
    record_conversion_transition(
        db_session,
        opportunity=opportunity,
        to_stage="discovered",
        actor="system",
        occurred_at="2026-08-10T16:00:00Z",
        evidence_level="e1_observed",
    )
    with pytest.raises(ValueError, match="controlled reason"):
        record_conversion_transition(
            db_session,
            opportunity=opportunity,
            to_stage="lost",
            actor="seller",
            occurred_at="2026-08-10T17:00:00Z",
            evidence_level="e1_observed",
            reason="vibes",
        )
    record_conversion_transition(
        db_session,
        opportunity=opportunity,
        to_stage="lost",
        actor="seller",
        occurred_at="2026-08-10T17:30:00Z",
        evidence_level="e1_observed",
        reason="payload_insufficient",
    )
    assert opportunity.current_stage == "discovered"
    assert opportunity.disposition == "lost"
    assert opportunity.status == "closed"


def test_labels_use_highest_verified_stage_not_generic_crm_activity():
    events = [
        SalesExperienceEvent(event_type="crm_outreach_sent", outcome="sent", payload={}),
        SalesExperienceEvent(
            event_type="deployment_conversion_stage_changed",
            outcome="observed",
            payload={"to_stage": "contacted"},
        ),
        SalesExperienceEvent(
            event_type="deployment_conversion_stage_changed",
            outcome="qualified",
            payload={"to_stage": "qualified"},
        ),
        SalesExperienceEvent(
            event_type="deployment_conversion_disposition_changed",
            outcome="lost",
            payload={"to_disposition": "lost", "reason": "budget_unavailable"},
        ),
    ]

    label = derive_conversion_label(events)

    assert label.contacted is True
    assert label.engaged is True
    assert label.qualified is True
    assert label.site_review is False
    assert label.site_verified is False
    assert label.pilot is False
    assert label.deployed is False
    assert label.expanding is False
    assert label.disposition == "lost"
    assert label.terminal_reason == "budget_unavailable"


def test_legacy_site_verified_alias_maps_to_site_review(opportunity, db_session):
    _advance_to_prioritized(opportunity, db_session)
    for stage, evidence in [
        ("contacted", "e1_observed"),
        ("engaged", "e2_customer_confirmed"),
        ("qualified", "e3_work_verified"),
    ]:
        record_conversion_transition(
            db_session,
            opportunity=opportunity,
            to_stage=stage,
            actor="seller",
            occurred_at="2026-08-11T16:00:00Z",
            evidence_level=evidence,
            contact_result="connected" if stage == "contacted" else None,
        )
    record_conversion_transition(
        db_session,
        opportunity=opportunity,
        to_stage="site_verified",
        actor="seller",
        occurred_at="2026-08-12T16:00:00Z",
        evidence_level="e4_environment_verified",
    )
    assert opportunity.current_stage == "site_review"
