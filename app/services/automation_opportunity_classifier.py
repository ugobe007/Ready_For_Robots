"""
Automation Opportunity Classification

A Robot Job is human work a robot could be hired to do. An operational posting
(order picker, dishwasher, EVS tech) is the evidence that the work exists at a
named employer — it is the opportunity, never "contamination".

Routing (stored on ``robot_jobs.opportunity_tier``):

    1  ROBOT_JOBS / AUTOMATION_INTENT   employer already moving to automation
                                        (robot/AMR named, automation hire, RFP)  → daily email first
    2  AUTOMATION_READY                 automatable work + staffing pain, or work
                                        robots do commercially today              → pipeline
    3  AUTOMATABLE_WORK                 automatable work, no pain/intent yet       → nurture
    0  NOT_AN_OPPORTUNITY               robot builders / desk work — the ONLY drop

History: on 2026-10-11 tier 3 meant "human labor → reject" and a cleanup script
deleted ~14k rows on that basis. That reading is retired. Tier 3 is kept data.

Scoring lives in ``app.services.workflow_ontology`` (FIT × PAIN × INTENT).
"""
from __future__ import annotations

from enum import IntEnum

from app.services.workflow_ontology import OpportunityAnalysis, analyze_posting


class OpportunityTier(IntEnum):
    NOT_AN_OPPORTUNITY = 0
    ROBOT_JOBS = 1          # automation intent
    AUTOMATION_READY = 2
    AUTOMATABLE_WORK = 3

    # Back-compat names used by older scripts / tests.
    AUTOMATION_INTENT = 1
    SIGNALS = 2


class OpportunityClass(IntEnum):
    UNKNOWN = 0
    # Tier 1
    EXPLICIT_ROBOT = 11           # robot / AMR / cobot named as the employer's equipment
    EXPLICIT_AUTOMATION = 12      # automation program, tender, "looking to automate"
    AUTOMATION_LEADERSHIP = 21    # operator hiring automation / CI / controls talent
    # Tier 2
    LABOR_CHALLENGE = 23          # automatable work + staffing pain
    COMMERCIALLY_AUTOMATABLE = 25 # robots already do this at scale
    # Tier 3
    AUTOMATABLE_WORK = 31
    # Tier 0
    ROBOT_BUILDER = 40
    NO_PHYSICAL_WORKFLOW = 41

    # Retired meaning, kept so old rows/imports don't crash.
    INNOVATION_INVESTMENT = 22
    COST_REDUCTION = 24
    HUMAN_REQUISITION = 30


def _class_for(a: OpportunityAnalysis) -> OpportunityClass:
    if a.tier == 0:
        return OpportunityClass.ROBOT_BUILDER if a.builder else OpportunityClass.NO_PHYSICAL_WORKFLOW
    if a.tier == 1:
        if a.buyer_automation_role and not a.families:
            return OpportunityClass.AUTOMATION_LEADERSHIP
        if any(lbl in a.intent for lbl in ("operates_robots", "works_with_robots", "robot_operator_role")):
            return OpportunityClass.EXPLICIT_ROBOT
        return OpportunityClass.EXPLICIT_AUTOMATION
    if a.tier == 2:
        return OpportunityClass.LABOR_CHALLENGE if a.pain else OpportunityClass.COMMERCIALLY_AUTOMATABLE
    return OpportunityClass.AUTOMATABLE_WORK


def classify_opportunity_detail(title: str, description: str = "", company: str = "") -> OpportunityAnalysis:
    return analyze_posting(title, description, company)


def classify_opportunity(
    title: str, description: str = "", company: str = ""
) -> tuple[OpportunityTier, OpportunityClass]:
    a = analyze_posting(title, description, company)
    return OpportunityTier(a.tier), _class_for(a)


def should_create_robot_job(tier: OpportunityTier) -> bool:
    """Every automatable workflow is a Robot Job. Only tier 0 is not."""
    return int(tier) in (1, 2, 3)


def should_create_signal(tier: OpportunityTier) -> bool:
    """Signals mirror robot jobs (company timeline / recovery trail)."""
    return int(tier) in (1, 2, 3)


def should_reject(tier: OpportunityTier) -> bool:
    return int(tier) == 0


def get_signal_type(opp_class: OpportunityClass) -> str:
    mapping = {
        OpportunityClass.AUTOMATION_LEADERSHIP: "automation_leadership_hire",
        OpportunityClass.EXPLICIT_ROBOT: "robot_job",
        OpportunityClass.EXPLICIT_AUTOMATION: "robot_job",
        OpportunityClass.LABOR_CHALLENGE: "robot_job",
        OpportunityClass.COMMERCIALLY_AUTOMATABLE: "robot_job",
        OpportunityClass.AUTOMATABLE_WORK: "robot_job",
    }
    return mapping.get(opp_class, "market_intelligence")


def get_tier_name(tier: OpportunityTier) -> str:
    return {
        0: "not_an_opportunity",
        1: "automation_intent",
        2: "automation_ready",
        3: "automatable_work",
    }.get(int(tier), "unknown")


def get_class_name(opp_class: OpportunityClass) -> str:
    return OpportunityClass(int(opp_class)).name.lower()
