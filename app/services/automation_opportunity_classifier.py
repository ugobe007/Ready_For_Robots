"""
Automation Opportunity Classification

Classifies job postings and market signals into tiers for proper routing:
- Tier 1 (ROBOT_JOBS): Explicit robot/automation requests → robot_jobs table → Daily email
- Tier 2 (SIGNALS): Market intelligence (leadership hires, investment, pain) → signals table
- Tier 3 (HUMAN_LABOR): Human requisitions → REJECT, do not persist

Based on the 5-class opportunity framework but separated into actionable routing rules.
"""
from enum import IntEnum
import re
from typing import Optional

class OpportunityTier(IntEnum):
    """Routing tier for automation opportunities"""
    ROBOT_JOBS = 1      # Explicit robot/automation requests → robot_jobs table
    SIGNALS = 2         # Market intelligence → signals table  
    HUMAN_LABOR = 3     # Human requisitions → REJECT

class OpportunityClass(IntEnum):
    """Detailed classification within each tier"""
    # Tier 1: ROBOT_JOBS
    EXPLICIT_ROBOT = 11         # "Need AMR for warehouse"
    EXPLICIT_AUTOMATION = 12    # "Want automated solution"
    
    # Tier 2: SIGNALS (Market Intelligence)
    AUTOMATION_LEADERSHIP = 21  # "Head of Automation", "Chief Robotics Officer"
    INNOVATION_INVESTMENT = 22  # Automation initiatives, M&A, innovation labs
    LABOR_CHALLENGE = 23        # "Can't find workers", high turnover
    COST_REDUCTION = 24         # "Reduce labor costs", efficiency focus
    
    # Tier 3: HUMAN_LABOR (Reject)
    HUMAN_REQUISITION = 30      # "Cook needed", "Hiring Warehouse Worker"
    
    UNKNOWN = 0

# ─── Tier 1: ROBOT_JOBS (Explicit Requests) ───────────────────────────────────

_ROBOT_ASK_RE = re.compile(
    r'\b(robot|amr|agv|cobot|humanoid|autonomous.*robot|delivery.*robot|'
    r'scrubber.*robot|scrubbing.*robot|palletiz(?:er|ing).*robot|'
    r'mobile.*robot|collaborative.*robot)\b',
    re.I
)

_AUTOMATION_ASK_RE = re.compile(
    r'\b(automat(?:e|ed|ion).*(?:solution|system)|autonomous.*system|'
    r'robotic.*system|automated.*(?:handling|cleaning|transport|picking|packing))\b',
    re.I
)

# ─── Tier 2: SIGNALS (Market Intelligence) ────────────────────────────────────

# Class 2A: Automation leadership hires
_AUTOMATION_LEADERSHIP_RE = re.compile(
    r'\b(head of (?:automation|robotics)|chief (?:robotics|automation) officer|'
    r'vp of (?:physical ai|robotics|automation)|director of (?:robotics|automation)|'
    r'robotics (?:integration|deployment) (?:director|manager)|'
    r'automation (?:strategy|program) (?:director|lead)|'
    r'chief robotist)\b',
    re.I
)

# Class 2B: Innovation/automation investment
_INNOVATION_INVESTMENT_RE = re.compile(
    r'\b(innovation lab|automation initiative|robotics.*investment|'
    r'digital transformation|industry 4\.0|smart.*(?:factory|warehouse)|'
    r'technology.*modernization)\b',
    re.I
)

# Class 2C: Labor challenges
_LABOR_CHALLENGE_RE = re.compile(
    r'\b(labor shortage|worker shortage|staffing (?:shortage|crisis)|'
    r'turnover.*(?:issue|problem|high)|retention.*(?:issue|problem)|'
    r'hard to find (?:workers|staff)|difficult to (?:recruit|hire)|'
    r"can'?t find (?:workers|staff|employees)|struggle to (?:hire|staff))\b",
    re.I
)

# Class 2D: Cost reduction focus
_COST_REDUCTION_RE = re.compile(
    r'\b(reduce.*labor.*cost|save.*labor|minimize.*(?:expense|overhead)|'
    r'lower.*(?:labor cost|operating cost)|cost.*(?:saving|reduction).*labor|'
    r'efficiency.*(?:gain|improvement)|productivity.*improvement)\b',
    re.I
)

# ─── Tier 3: HUMAN_LABOR (Reject) ─────────────────────────────────────────────

# Common human occupation titles
_HUMAN_OCCUPATION_RE = re.compile(
    r'\b(sterile processing technician|pharmacy technician|cook|chef|bartender|'
    r'mixologist|server|waiter|waitress|busser|dishwasher|food runner|'
    r'bricklayer|mason|carpenter|construction (?:worker|laborer)|'
    r'warehouse (?:worker|associate)|material handler|forklift operator|'
    r'order picker|packer|shipper|receiver|dock worker|'
    r'housekeeper|janitor|custodian|cleaner|room attendant|'
    r'front desk|receptionist|concierge|cashier|sales associate|'
    r'farm (?:worker|laborer)|harvest worker|field worker|'
    r'machine operator|cnc operator|production worker|line worker|'
    r'driver|security guard|groundskeeper|landscaper)\b',
    re.I
)

# Human hiring language patterns
_HUMAN_HIRING_RE = re.compile(
    r'\b(hiring|seeking|looking for|needed|wanted|join our team|apply now|'
    r'per hour|/hr|hourly|\$\d+|salary|full-time|part-time|full time|part time|'
    r'benefits|401k|health insurance|pto|paid time off|'
    r'experience required|must have|years of experience|degree required)\b',
    re.I
)

def classify_opportunity(title: str, description: str = "") -> tuple[OpportunityTier, OpportunityClass]:
    """
    Classify automation opportunity for routing.
    
    Args:
        title: Job posting title or headline
        description: Full job description text
        
    Returns:
        (tier, class) tuple where:
        - tier: ROBOT_JOBS (1), SIGNALS (2), or HUMAN_LABOR (3)
        - class: Detailed classification (11, 12, 21-24, 30, or 0)
    """
    text = f"{title} {description}".strip()
    title_lower = title.lower() if title else ""
    
    # ── Check Tier 1: ROBOT_JOBS (Explicit requests) ──────────────────────────
    
    if _ROBOT_ASK_RE.search(text):
        return (OpportunityTier.ROBOT_JOBS, OpportunityClass.EXPLICIT_ROBOT)
    
    if _AUTOMATION_ASK_RE.search(text):
        return (OpportunityTier.ROBOT_JOBS, OpportunityClass.EXPLICIT_AUTOMATION)
    
    # ── Check Tier 3: HUMAN_LABOR (Reject) ────────────────────────────────────
    # Check this BEFORE Tier 2 to catch human jobs with pain language
    
    if _HUMAN_OCCUPATION_RE.search(title_lower):
        return (OpportunityTier.HUMAN_LABOR, OpportunityClass.HUMAN_REQUISITION)
    
    if _HUMAN_HIRING_RE.search(text):
        return (OpportunityTier.HUMAN_LABOR, OpportunityClass.HUMAN_REQUISITION)
    
    # ── Check Tier 2: SIGNALS (Market Intelligence) ───────────────────────────
    
    if _AUTOMATION_LEADERSHIP_RE.search(text):
        return (OpportunityTier.SIGNALS, OpportunityClass.AUTOMATION_LEADERSHIP)
    
    if _INNOVATION_INVESTMENT_RE.search(text):
        return (OpportunityTier.SIGNALS, OpportunityClass.INNOVATION_INVESTMENT)
    
    if _LABOR_CHALLENGE_RE.search(text):
        return (OpportunityTier.SIGNALS, OpportunityClass.LABOR_CHALLENGE)
    
    if _COST_REDUCTION_RE.search(text):
        return (OpportunityTier.SIGNALS, OpportunityClass.COST_REDUCTION)
    
    # ── Unknown ────────────────────────────────────────────────────────────────
    
    return (OpportunityTier.SIGNALS, OpportunityClass.UNKNOWN)


def should_create_robot_job(tier: OpportunityTier) -> bool:
    """True if this opportunity should create a robot_jobs entry."""
    return tier == OpportunityTier.ROBOT_JOBS


def should_create_signal(tier: OpportunityTier) -> bool:
    """True if this opportunity should create a signals entry."""
    return tier == OpportunityTier.SIGNALS


def should_reject(tier: OpportunityTier) -> bool:
    """True if this opportunity should be rejected (not persisted)."""
    return tier == OpportunityTier.HUMAN_LABOR


def get_signal_type(opp_class: OpportunityClass) -> str:
    """Map opportunity class to signal type string."""
    mapping = {
        OpportunityClass.AUTOMATION_LEADERSHIP: "automation_leadership_hire",
        OpportunityClass.INNOVATION_INVESTMENT: "innovation_investment",
        OpportunityClass.LABOR_CHALLENGE: "labor_challenge",
        OpportunityClass.COST_REDUCTION: "cost_reduction_focus",
    }
    return mapping.get(opp_class, "market_intelligence")


def get_tier_name(tier: OpportunityTier) -> str:
    """Human-readable tier name."""
    names = {
        OpportunityTier.ROBOT_JOBS: "robot_jobs",
        OpportunityTier.SIGNALS: "signals",
        OpportunityTier.HUMAN_LABOR: "human_labor",
    }
    return names.get(tier, "unknown")


def get_class_name(opp_class: OpportunityClass) -> str:
    """Human-readable class name."""
    names = {
        OpportunityClass.EXPLICIT_ROBOT: "explicit_robot",
        OpportunityClass.EXPLICIT_AUTOMATION: "explicit_automation",
        OpportunityClass.AUTOMATION_LEADERSHIP: "automation_leadership",
        OpportunityClass.INNOVATION_INVESTMENT: "innovation_investment",
        OpportunityClass.LABOR_CHALLENGE: "labor_challenge",
        OpportunityClass.COST_REDUCTION: "cost_reduction",
        OpportunityClass.HUMAN_REQUISITION: "human_requisition",
        OpportunityClass.UNKNOWN: "unknown",
    }
    return names.get(opp_class, "unknown")
