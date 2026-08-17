"""Canonical physical-deployment conversion events for robot opportunities.

V1 contract (docs/v1):
- Monotonic truth stages end at deployed (site_review replaces legacy site_* / economic_* / expanding).
- watch / paused / lost are dispositions and must not erase established truth.
- Prediction snapshots freeze at prioritized and are immutable thereafter.
- Seven decision dimensions (no standalone deployment_readiness).
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.crm import CrmAccount
from app.models.sales_agent import SalesOpportunity
from app.models.sales_learning import SalesExperienceEvent
from app.services.sales_learning_agent import record_sales_experience


CONVERSION_STAGES = (
    "discovered",
    "matched",
    "prioritized",
    "contacted",
    "engaged",
    "qualified",
    "site_review",
    "pilot",
    "deployed",
)

# Legacy stages still present on historical events / callers.
LEGACY_STAGE_ALIASES = {
    "site_verified": "site_review",
    "solution_fit": "site_review",
    "economic_fit": "site_review",
    "expanding": "deployed",
}

DISPOSITIONS = ("active", "watch", "paused", "lost")
DISPOSITION_COMMANDS = frozenset({"watch", "paused", "lost", "resume", "active"})

EVIDENCE_LEVELS = (
    "e1_observed",
    "e2_customer_confirmed",
    "e3_work_verified",
    "e4_environment_verified",
    "e5_performance_verified",
)
STAGE_MINIMUM_EVIDENCE = {
    "discovered": "e1_observed",
    "matched": "e1_observed",
    "prioritized": "e1_observed",
    "contacted": "e1_observed",
    "engaged": "e2_customer_confirmed",
    "qualified": "e3_work_verified",
    "site_review": "e4_environment_verified",
    "pilot": "e4_environment_verified",
    "deployed": "e5_performance_verified",
}
CONTACT_RESULTS = {
    "no_response", "connected", "wrong_person", "referred", "interested",
    "not_interested", "already_automated", "active_automation_project",
    "future_project", "no_budget", "no_labor_problem", "wrong_workflow", "wrong_robot",
}
LOSS_REASONS = {
    "work_incorrectly_inferred", "task_not_repetitive", "volume_too_low",
    "mixed_role_not_separable", "payload_insufficient", "reach_insufficient",
    "speed_insufficient", "navigation_problem", "manipulation_problem",
    "environment_incompatible", "labor_too_inexpensive", "roi_too_long",
    "integration_too_expensive", "budget_unavailable", "no_champion",
    "management_not_supportive", "it_security_blocked", "procurement_blocked",
    "workforce_blocked", "competing_priority", "project_awarded",
    "budget_cycle_passed", "facility_moving", "expansion_delayed", "not_ready",
    "existing_vendor", "incumbent_automation", "competitor_selected",
    "internal_solution", "insufficient_evidence", "account_unresolvable",
    "no_response", "other",
}
DECISION_DIMENSIONS = {
    "work_match",
    "labor_pressure",
    "operational_exposure",
    "buyability",
    "deployability",
    "evidence_confidence",
    "account_resolvability",
}
CALL_PRIORITIES = {
    "call_now",
    "qualify",
    "watch",
    "wrong_robot",
    "insufficient_evidence",
    "do_not_surface",
}
# Accepted aliases mapped to OpenAPI values.
CALL_PRIORITY_ALIASES = {
    "unresolvable": "do_not_surface",
}

EVENT_SCHEMA_VERSION = "deployment_conversion_event.v1"


@dataclass(frozen=True)
class ConversionLabel:
    contacted: bool
    engaged: bool
    qualified: bool
    site_review: bool
    pilot: bool
    deployed: bool
    disposition: str
    terminal_reason: str | None

    @property
    def site_verified(self) -> bool:
        """Deprecated alias for site_review (legacy callers)."""
        return self.site_review

    @property
    def expanding(self) -> bool:
        """Deprecated: expanding is no longer a truth stage."""
        return False


def normalize_stage(stage: str | None) -> str:
    value = (stage or "new").strip().lower()
    return LEGACY_STAGE_ALIASES.get(value, value)


def normalize_call_priority(priority: str | None) -> str | None:
    if priority is None:
        return None
    value = priority.strip().lower()
    return CALL_PRIORITY_ALIASES.get(value, value)


def ensure_deployment_opportunity(
    db: Session,
    *,
    account: CrmAccount,
    owner_user_id=None,
    source_signal_ids: list[str] | None = None,
) -> SalesOpportunity:
    """Find or create the permanent opportunity identity at DISCOVERED."""
    opportunity = (
        db.query(SalesOpportunity)
        .filter(
            SalesOpportunity.opportunity_type == "deployment",
            SalesOpportunity.crm_account_id == _uuid_value(db, account.id),
        )
        .first()
    )
    if opportunity:
        return opportunity
    opportunity_id = _new_uuid(db)
    public_id = f"RFR-OPP-{datetime.now(timezone.utc).year}-{str(opportunity_id).replace('-', '')[:8].upper()}"
    opportunity = SalesOpportunity(
        id=opportunity_id,
        opportunity_type="deployment",
        team_id=_uuid_value(db, account.team_id),
        crm_account_id=_uuid_value(db, account.id),
        company_id=account.company_id,
        owner_user_id=_uuid_value(db, owner_user_id or account.owner_user_id),
        title=f"{account.name} deployment opportunity",
        current_stage="new",
        disposition="active",
        payload={"public_id": public_id},
    )
    db.add(opportunity)
    db.flush()
    record_conversion_transition(
        db,
        opportunity=opportunity,
        to_stage="discovered",
        actor="system",
        occurred_at=datetime.now(timezone.utc).isoformat(),
        evidence_level="e1_observed",
        facts_learned={"source_signal_ids": source_signal_ids or []},
    )
    return opportunity


def set_opportunity_disposition(
    db: Session,
    *,
    opportunity: SalesOpportunity,
    disposition: str,
    actor: str,
    occurred_at: str,
    reason: str | None = None,
    evidence_level: str = "e1_observed",
    facts_learned: dict[str, Any] | None = None,
) -> SalesExperienceEvent:
    """Change disposition without moving monotonic truth state backward."""
    disposition = disposition.strip().lower()
    if disposition == "resume":
        disposition = "active"
    if disposition not in DISPOSITIONS:
        raise ValueError(f"Unknown opportunity disposition: {disposition}")

    from_stage = normalize_stage(opportunity.current_stage)
    if from_stage == "new" and disposition == "lost":
        raise ValueError("An opportunity must be discovered before it can be lost")
    if disposition == "lost" and reason not in LOSS_REASONS:
        raise ValueError("Lost disposition requires a controlled reason")
    if disposition != "lost" and reason is not None:
        raise ValueError("Non-lost disposition changes cannot carry a loss reason")

    evidence_level = evidence_level.strip().lower()
    if evidence_level not in EVIDENCE_LEVELS:
        raise ValueError(f"Unknown evidence level: {evidence_level}")

    previous = _get_disposition(opportunity)
    payload = {
        "schema_version": EVENT_SCHEMA_VERSION,
        "from_stage": from_stage,
        "to_stage": from_stage,
        "from_disposition": previous,
        "to_disposition": disposition,
        "actor": actor,
        "occurred_at": occurred_at,
        "evidence_level": evidence_level,
        "contact_result": None,
        "reason": reason,
        "prediction_snapshot": {},
        "evidence": [],
        "facts_learned": facts_learned or {},
    }
    event = record_sales_experience(
        db,
        event_type="deployment_conversion_disposition_changed",
        outcome="lost" if disposition == "lost" else "observed",
        team_id=opportunity.team_id,
        user_id=opportunity.owner_user_id,
        crm_account_id=opportunity.crm_account_id,
        sales_opportunity_id=opportunity.id,
        company_id=opportunity.company_id,
        robot_company_id=opportunity.robot_company_id,
        confidence=1.0,
        payload=payload,
    )
    _apply_disposition(opportunity, disposition)
    return event


def record_conversion_transition(
    db: Session,
    *,
    opportunity: SalesOpportunity,
    to_stage: str,
    actor: str,
    occurred_at: str,
    evidence_level: str,
    prediction_snapshot: dict[str, Any] | None = None,
    contact_result: str | None = None,
    reason: str | None = None,
    evidence: list[dict[str, Any]] | None = None,
    facts_learned: dict[str, Any] | None = None,
) -> SalesExperienceEvent:
    """Append one monotonic truth transition and update live opportunity state.

    Compatibility: callers may pass disposition-only commands (`watch`, `paused`,
    `lost`, `resume`) as `to_stage`; those update disposition only and leave
    `current_stage` unchanged.
    """
    requested = (to_stage or "").strip().lower()
    if requested in DISPOSITION_COMMANDS:
        target_disposition = "active" if requested == "resume" else requested
        return set_opportunity_disposition(
            db,
            opportunity=opportunity,
            disposition=target_disposition,
            actor=actor,
            occurred_at=occurred_at,
            reason=reason,
            evidence_level=evidence_level,
            facts_learned=facts_learned,
        )

    from_stage = normalize_stage(opportunity.current_stage)
    # Legacy rows stored lost as a truth stage — treat as disposition and recover.
    if from_stage == "lost":
        _apply_disposition(opportunity, "lost")
        from_stage = "discovered"
        opportunity.current_stage = from_stage

    to_stage = normalize_stage(to_stage)
    evidence_level = evidence_level.strip().lower()
    _validate_transition(from_stage, to_stage, reason)
    _validate_evidence_level(to_stage, evidence_level)
    if contact_result is not None and contact_result not in CONTACT_RESULTS:
        raise ValueError(f"Unknown contact result: {contact_result}")

    snapshot = prediction_snapshot or {}
    if to_stage == "prioritized":
        _validate_prediction_snapshot(snapshot)
    elif snapshot:
        raise ValueError("prediction_snapshot is immutable and may only be recorded at prioritized")

    current_disposition = _get_disposition(opportunity)
    payload = {
        "schema_version": EVENT_SCHEMA_VERSION,
        "from_stage": from_stage,
        "to_stage": to_stage,
        "from_disposition": current_disposition,
        "to_disposition": current_disposition,
        "actor": actor,
        "occurred_at": occurred_at,
        "evidence_level": evidence_level,
        "contact_result": contact_result,
        "reason": reason,
        "prediction_snapshot": snapshot,
        "evidence": evidence or [],
        "facts_learned": facts_learned or {},
    }
    event = record_sales_experience(
        db,
        event_type="deployment_conversion_stage_changed",
        outcome=_event_outcome(to_stage),
        team_id=opportunity.team_id,
        user_id=opportunity.owner_user_id,
        crm_account_id=opportunity.crm_account_id,
        sales_opportunity_id=opportunity.id,
        company_id=opportunity.company_id,
        robot_company_id=opportunity.robot_company_id,
        confidence=1.0,
        payload=payload,
    )
    opportunity.current_stage = to_stage
    if facts_learned:
        opportunity.payload = {**(opportunity.payload or {}), "latest_facts": facts_learned}
    return event


def derive_conversion_label(events: list[SalesExperienceEvent]) -> ConversionLabel:
    """Derive milestone labels from verified conversion events only."""
    highest_index = -1
    terminal_reason = None
    disposition = "active"
    for event in events:
        payload = event.payload or {}
        if event.event_type == "deployment_conversion_disposition_changed":
            next_disposition = (payload.get("to_disposition") or "").strip().lower()
            if next_disposition in DISPOSITIONS:
                disposition = next_disposition
            if next_disposition == "lost":
                terminal_reason = payload.get("reason")
            continue
        if event.event_type != "deployment_conversion_stage_changed":
            continue
        stage = normalize_stage(payload.get("to_stage"))
        if stage in CONVERSION_STAGES:
            highest_index = max(highest_index, CONVERSION_STAGES.index(stage))
        # Legacy lost-as-stage events
        if stage == "lost":
            disposition = "lost"
            terminal_reason = payload.get("reason")

    def reached(stage: str) -> bool:
        return highest_index >= CONVERSION_STAGES.index(stage)

    return ConversionLabel(
        contacted=reached("contacted"),
        engaged=reached("engaged"),
        qualified=reached("qualified"),
        site_review=reached("site_review"),
        pilot=reached("pilot"),
        deployed=reached("deployed"),
        disposition=disposition,
        terminal_reason=terminal_reason,
    )


def _get_disposition(opportunity: SalesOpportunity) -> str:
    raw = getattr(opportunity, "disposition", None)
    if raw:
        return str(raw).strip().lower()
    payload = opportunity.payload or {}
    value = str(payload.get("disposition") or "active").strip().lower()
    return value if value in DISPOSITIONS else "active"


def _apply_disposition(opportunity: SalesOpportunity, disposition: str) -> None:
    if hasattr(opportunity, "disposition"):
        opportunity.disposition = disposition
    opportunity.status = "closed" if disposition == "lost" else "open"
    opportunity.payload = {**(opportunity.payload or {}), "disposition": disposition}


def _validate_transition(from_stage: str, to_stage: str, reason: str | None) -> None:
    if to_stage not in CONVERSION_STAGES:
        raise ValueError(f"Unknown deployment conversion stage: {to_stage}")
    if reason is not None:
        raise ValueError("Non-terminal transitions cannot carry a loss reason")
    if from_stage == "new":
        if to_stage != "discovered":
            raise ValueError("A new opportunity must first become discovered")
        return
    if from_stage not in CONVERSION_STAGES:
        raise ValueError(f"Unknown current deployment conversion stage: {from_stage}")
    if CONVERSION_STAGES.index(to_stage) <= CONVERSION_STAGES.index(from_stage):
        raise ValueError(f"Conversion stages must advance monotonically: {from_stage} -> {to_stage}")


def _validate_evidence_level(stage: str, evidence_level: str) -> None:
    if evidence_level not in EVIDENCE_LEVELS:
        raise ValueError(f"Unknown evidence level: {evidence_level}")
    minimum = STAGE_MINIMUM_EVIDENCE[stage]
    if EVIDENCE_LEVELS.index(evidence_level) < EVIDENCE_LEVELS.index(minimum):
        raise ValueError(f"{stage} requires at least {minimum}")


def _validate_prediction_snapshot(snapshot: dict[str, Any]) -> None:
    dimensions = set(snapshot.get("dimensions") or {})
    if dimensions != DECISION_DIMENSIONS:
        raise ValueError("Prediction snapshot must contain all seven decision dimensions")
    priority = normalize_call_priority(snapshot.get("call_priority"))
    if priority not in CALL_PRIORITIES:
        raise ValueError("Prediction snapshot requires a controlled call_priority")
    snapshot["call_priority"] = priority
    if not snapshot.get("model_version") or not snapshot.get("predicted_at"):
        raise ValueError("Prediction snapshot requires model_version and predicted_at")
    if not snapshot.get("facility_ref") or not snapshot.get("robot_profile_id"):
        raise ValueError("Prediction snapshot requires facility_ref and robot_profile_id")
    if not snapshot.get("work_unit_ids") or not snapshot.get("source_signal_ids"):
        raise ValueError("Prediction snapshot requires Work Units and source signals")


def _event_outcome(stage: str) -> str:
    if stage in {"qualified", "site_review"}:
        return "qualified"
    if stage in {"pilot", "deployed"}:
        return "won"
    return "observed"


def _uuid_value(db: Session, value):
    if value is None:
        return None
    if db.bind and db.bind.dialect.name == "sqlite":
        return str(value)
    return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))


def _new_uuid(db: Session):
    value = uuid.uuid4()
    return str(value) if db.bind and db.bind.dialect.name == "sqlite" else value
