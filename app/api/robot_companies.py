"""
Robot Companies API
Lead generation system for robotics vendors
Focus: Chinese companies entering U.S. market
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from typing import Any, List, Optional
from datetime import datetime
from pydantic import BaseModel

from app.database import get_db
from app.models.company import Company
from app.models.robot_company import RobotCompany
from app.services.email_templates import get_email_template
from app.services.resend_email import ResendEmailError, send_email_via_resend
from app.services.vendor_scoring import compute_vendor_list_score

router = APIRouter(prefix="/api/robot-companies", tags=["robot-companies"])


class SendRobotCompanyEmailRequest(BaseModel):
    to_email: str
    template_type: str = "intro"
    subject: Optional[str] = None
    body: Optional[str] = None


def _split_terms(*values: Any) -> set[str]:
    terms: set[str] = set()
    for value in values:
        if not value:
            continue
        raw = str(value).lower().replace("/", " ").replace("-", " ")
        for part in raw.replace("&", " ").replace(",", " ").split():
            if len(part) >= 3:
                terms.add(part.strip())
    return terms


def _robot_market_terms(rc: RobotCompany) -> set[str]:
    terms = _split_terms(rc.robot_type, rc.target_market, rc.product_category)
    aliases = {
        "amr": {"warehouse", "logistics", "fulfillment", "distribution", "material", "handling"},
        "cobot": {"manufacturing", "assembly", "industrial", "production"},
        "industrial": {"manufacturing", "assembly", "production", "factory"},
        "service": {"hospitality", "healthcare", "retail", "cleaning"},
        "vision": {"inspection", "quality", "manufacturing", "safety"},
        "humanoid": {"warehouse", "manufacturing", "service", "hospitality"},
    }
    for term in list(terms):
        terms.update(aliases.get(term, set()))
    return terms


def _lead_terms(company: Company) -> set[str]:
    profile = company.automation_profile or {}
    requirements = []
    if isinstance(profile, dict):
        requirements = profile.get("requirements") or profile.get("automation_requirements") or []
    signal_terms = [s.signal_type for s in (company.signals or [])[:5]]
    return _split_terms(company.industry, company.sub_industry, company.crm_metadata, requirements, signal_terms)


def _lead_score(company: Company, vendor_terms: set[str]) -> float:
    score = 0.0
    if company.scores:
        score += max(float(s.overall_intent_score or 0) for s in company.scores)
    lead_terms = _lead_terms(company)
    overlap = vendor_terms.intersection(lead_terms)
    score += min(25.0, len(overlap) * 6.0)
    score += min(15.0, len(company.signals or []) * 2.5)
    return round(score, 1)


def _match_buyer_leads(db: Session, rc: RobotCompany, limit: int = 3) -> list[dict[str, Any]]:
    vendor_terms = _robot_market_terms(rc)
    candidates = (
        db.query(Company)
        .options(joinedload(Company.signals), joinedload(Company.scores))
        .filter(Company.is_internal.is_(True))
        .order_by(Company.updated_at.desc().nullslast(), Company.created_at.desc().nullslast())
        .limit(300)
        .all()
    )
    ranked = sorted(
        (
            {
                "id": c.id,
                "company_name": c.name,
                "industry": c.industry,
                "location": ", ".join(x for x in [c.location_city, c.location_state] if x) or None,
                "score": _lead_score(c, vendor_terms),
                "signal": (c.signals[0].signal_text if c.signals else None),
                "signal_type": (c.signals[0].signal_type if c.signals else None),
                "why_match": _why_match(rc, c, vendor_terms),
            }
            for c in candidates
        ),
        key=lambda row: row["score"],
        reverse=True,
    )
    return [row for row in ranked if row["score"] > 0][:limit]


def _why_match(rc: RobotCompany, company: Company, vendor_terms: set[str]) -> str:
    overlap = sorted(vendor_terms.intersection(_lead_terms(company)))
    if overlap:
        return f"Matches {rc.company_name}'s market around {', '.join(overlap[:4])}."
    if company.industry and rc.target_market:
        return f"{company.industry} lead aligns with target market: {rc.target_market}."
    return "Buyer has active automation signals that may fit this robot category."


def _contact_strategy(rc: RobotCompany) -> dict[str, Any]:
    targets = []
    if rc.partnerships_contact:
        targets.append({"role": "Partnerships", "contact": rc.partnerships_contact, "priority": 1})
    if rc.sales_contact:
        targets.append({"role": "Sales leadership", "contact": rc.sales_contact, "priority": 2})
    if rc.contact_email:
        targets.append({"role": "General contact", "contact": rc.contact_email, "priority": 3})
    if not targets:
        targets.append({"role": "Market development or partnerships leader", "contact": rc.website, "priority": 4})
    return {
        "primary": targets[0],
        "targets": targets,
        "research_notes": [
            "Confirm current U.S. market owner or partnerships lead.",
            "Look for VP Sales, Head of Partnerships, Channel, or Business Development.",
            "Use LinkedIn/company site if direct email is missing.",
        ],
    }


def _vendor_signup_email(rc: RobotCompany, matches: list[dict[str, Any]]) -> dict[str, str]:
    subject = f"3 buyer leads for {rc.company_name}"
    lead_lines = "\n".join(
        f"- {m['company_name']} ({m.get('industry') or 'industry unknown'}): {m.get('why_match')}"
        for m in matches[:3]
    ) or "- We have buyer matches ready to review once your team is onboarded."
    body = f"""Hi {rc.company_name} team,

Ready For Robots is building a two-sided robotics marketplace: buyers with live automation signals on one side, and robot companies that can serve those opportunities on the other.

SCOUT matched {rc.company_name} to these buyer opportunities:

{lead_lines}

We only show three matches in this note, but the full workflow can deliver qualified leads directly to your inbox with context, timing, and why each buyer appears ready for outreach.

The next step is to create a Ready For Robots account so your team can receive lead matches, review the buyer context, and decide which opportunities to pursue. Would you be open to setting up a short call with Ready For Robots this week so we can show you the lead flow and confirm the right markets for {rc.company_name}?

Best,
Ready For Robots"""
    return {"subject": subject, "body": body}


def _supply_agent_row(db: Session, rc: RobotCompany) -> dict[str, Any]:
    matches = _match_buyer_leads(db, rc, limit=3)
    contact = _contact_strategy(rc)
    draft = _vendor_signup_email(rc, matches)
    enriched = _enrich_robot_company(rc)
    return {
        "robot_company": enriched,
        "contact_strategy": contact,
        "lead_matches": matches,
        "email": draft,
        "cta": {
            "signup": "Create a Ready For Robots account to receive matched leads in your inbox.",
            "meeting": "Set up a short call with Ready For Robots to tune target markets and lead delivery.",
        },
        "review_required": True,
    }


def _enrich_robot_company(c: RobotCompany) -> dict[str, Any]:
    """JSON-serializable dict with computed vendor_list_score for UI sorting."""
    d = jsonable_encoder(c)
    d.update(compute_vendor_list_score(c))
    return d


@router.get("/")
def get_robot_companies(
    skip: int = 0,
    limit: int = 50,
    country: Optional[str] = None,
    robot_type: Optional[str] = None,
    us_presence: Optional[str] = None,
    priority_tier: Optional[str] = None,
    market_entry_wave: Optional[str] = None,
    distributor_needed: Optional[str] = None,
    min_score: int = 0,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get robot companies with filtering
    
    Filters:
    - country: China, US, EU, Korea, Japan
    - robot_type: industrial, AMR, cobot, humanoid, service, vision
    - us_presence: office, distributor, none
    - priority_tier: hot, warm, cold
    - market_entry_wave: wave_1, wave_2, wave_3
    - distributor_needed: yes, maybe, no
    - min_score: minimum lead score (0-100)
    - search: company name search
    """
    query = db.query(RobotCompany)
    
    if country:
        query = query.filter(RobotCompany.country == country)
    
    if robot_type:
        query = query.filter(RobotCompany.robot_type == robot_type)
    
    if us_presence:
        query = query.filter(RobotCompany.us_presence == us_presence)
    
    if priority_tier:
        query = query.filter(RobotCompany.priority_tier == priority_tier)
    
    if market_entry_wave:
        query = query.filter(RobotCompany.market_entry_wave == market_entry_wave)
    
    if distributor_needed:
        query = query.filter(RobotCompany.distributor_needed == distributor_needed)
    
    if min_score > 0:
        query = query.filter(RobotCompany.lead_score >= min_score)
    
    if search:
        query = query.filter(RobotCompany.company_name.ilike(f"%{search}%"))
    
    # Order by lead score descending (count before pagination)
    query = query.order_by(RobotCompany.lead_score.desc())
    total = query.count()
    companies = query.offset(skip).limit(limit).all()

    return {
        "companies": [_enrich_robot_company(c) for c in companies],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/hot-leads")
def get_hot_leads(
    min_score: int = 80,
    db: Session = Depends(get_db)
):
    """Get HOT priority leads (score >= 80) ready for outreach"""
    companies = db.query(RobotCompany).filter(
        RobotCompany.priority_tier == "hot",
        RobotCompany.lead_score >= min_score
    ).order_by(RobotCompany.lead_score.desc()).all()
    
    return {
        "hot_leads": [_enrich_robot_company(c) for c in companies],
        "count": len(companies),
    }


@router.get("/chinese-companies")
def get_chinese_companies(
    us_presence: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get Chinese robotics companies
    Filter by U.S. presence: none (needs distribution), distributor (has some), office (established)
    """
    query = db.query(RobotCompany).filter(RobotCompany.country == "China")
    
    if us_presence:
        query = query.filter(RobotCompany.us_presence == us_presence)
    
    companies = query.order_by(RobotCompany.lead_score.desc()).all()
    
    return {
        "companies": [_enrich_robot_company(c) for c in companies],
        "total": len(companies),
        "filter": us_presence or "all",
    }


@router.get("/market-entry-waves")
def get_market_entry_waves(db: Session = Depends(get_db)):
    """
    Get companies grouped by market entry wave
    Wave 1: 2020-2024 (established)
    Wave 2: 2024-2026 (expanding)
    Wave 3: 2025-2027 (emerging)
    """
    wave_1 = db.query(RobotCompany).filter(
        RobotCompany.market_entry_wave == "wave_1"
    ).order_by(RobotCompany.lead_score.desc()).all()
    
    wave_2 = db.query(RobotCompany).filter(
        RobotCompany.market_entry_wave == "wave_2"
    ).order_by(RobotCompany.lead_score.desc()).all()
    
    wave_3 = db.query(RobotCompany).filter(
        RobotCompany.market_entry_wave == "wave_3"
    ).order_by(RobotCompany.lead_score.desc()).all()
    
    return {
        "wave_1": {
            "companies": [_enrich_robot_company(c) for c in wave_1],
            "count": len(wave_1),
            "description": "Already Entered U.S. (2020-2024)",
        },
        "wave_2": {
            "companies": [_enrich_robot_company(c) for c in wave_2],
            "count": len(wave_2),
            "description": "Rapid Expansion (2024-2026)",
        },
        "wave_3": {
            "companies": [_enrich_robot_company(c) for c in wave_3],
            "count": len(wave_3),
            "description": "Next-Generation AI Robots (2025-2027)",
        },
    }


@router.get("/needs-distribution")
def get_needs_distribution(db: Session = Depends(get_db)):
    """Get companies that explicitly need U.S. distribution"""
    companies = db.query(RobotCompany).filter(
        RobotCompany.distributor_needed == "yes"
    ).order_by(RobotCompany.lead_score.desc()).all()
    
    return {
        "companies": [_enrich_robot_company(c) for c in companies],
        "count": len(companies),
        "message": "Companies actively seeking U.S. distribution partners",
    }


@router.get("/by-robot-type")
def get_by_robot_type(db: Session = Depends(get_db)):
    """Get companies grouped by robot type"""
    types = ["industrial", "cobot", "AMR", "humanoid", "service", "vision"]
    
    result = {}
    for robot_type in types:
        companies = db.query(RobotCompany).filter(
            RobotCompany.robot_type == robot_type
        ).order_by(RobotCompany.lead_score.desc()).all()
        
        result[robot_type] = {
            "companies": [_enrich_robot_company(c) for c in companies],
            "count": len(companies),
        }
    
    return result


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """Get database statistics"""
    total = db.query(RobotCompany).count()
    
    chinese_companies = db.query(RobotCompany).filter(
        RobotCompany.country == "China"
    ).count()
    
    needs_distribution = db.query(RobotCompany).filter(
        RobotCompany.distributor_needed == "yes"
    ).count()
    
    hot_leads = db.query(RobotCompany).filter(
        RobotCompany.priority_tier == "hot"
    ).count()
    
    no_us_presence = db.query(RobotCompany).filter(
        RobotCompany.us_presence == "none"
    ).count()
    
    return {
        "total_companies": total,
        "chinese_companies": chinese_companies,
        "needs_distribution": needs_distribution,
        "hot_leads": hot_leads,
        "no_us_presence": no_us_presence,
        "opportunity": f"{no_us_presence} companies with NO U.S. presence need market entry support"
    }


@router.get("/{company_id}")
def get_robot_company(company_id: int, db: Session = Depends(get_db)):
    """Get single robot company by ID"""
    company = db.query(RobotCompany).filter(RobotCompany.id == company_id).first()
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    return _enrich_robot_company(company)


@router.put("/{company_id}/outreach")
def update_outreach_status(
    company_id: int,
    status: str,
    notes: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Update outreach status
    Status: not_contacted, contacted, responded, meeting_scheduled, partnership
    """
    company = db.query(RobotCompany).filter(RobotCompany.id == company_id).first()
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    company.outreach_status = status
    company.last_contact_date = datetime.now()
    
    if notes:
        if company.outreach_notes:
            company.outreach_notes += f"\n\n[{datetime.now().strftime('%Y-%m-%d')}] {notes}"
        else:
            company.outreach_notes = f"[{datetime.now().strftime('%Y-%m-%d')}] {notes}"
    
    db.commit()
    db.refresh(company)

    return _enrich_robot_company(company)


@router.get("/search/by-trade-show")
def search_by_trade_show(
    trade_show: str = Query(..., description="Automate, ProMat, CES, Hannover"),
    db: Session = Depends(get_db)
):
    """Find companies attending specific trade shows"""
    companies = db.query(RobotCompany).filter(
        RobotCompany.trade_shows.contains([trade_show])
    ).order_by(RobotCompany.lead_score.desc()).all()
    
    return {
        "trade_show": trade_show,
        "companies": [_enrich_robot_company(c) for c in companies],
        "count": len(companies),
    }


@router.post("/")
def create_robot_company(company_data: dict, db: Session = Depends(get_db)):
    """Create new robot company lead"""
    company = RobotCompany(**company_data)
    db.add(company)
    db.commit()
    db.refresh(company)
    return _enrich_robot_company(company)


@router.put("/{company_id}")
def update_robot_company(
    company_id: int,
    company_data: dict,
    db: Session = Depends(get_db)
):
    """Update robot company"""
    company = db.query(RobotCompany).filter(RobotCompany.id == company_id).first()
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    for key, value in company_data.items():
        setattr(company, key, value)
    
    db.commit()
    db.refresh(company)

    return _enrich_robot_company(company)


@router.put("/{company_id}/workflow")
def update_workflow(
    company_id: int,
    workflow_data: dict,
    db: Session = Depends(get_db)
):
    """
    Update workflow next steps for a company
    Body: {
        "workflow_stage": "demo|outreach|proposal|negotiation|partnership",
        "next_action": "Schedule product demo",
        "next_action_date": "2026-03-15",
        "assigned_to": "Sales Team",
        "workflow_notes": "CEO interested in AMR solutions",
        "blockers": null
    }
    """
    company = db.query(RobotCompany).filter(RobotCompany.id == company_id).first()
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Update workflow fields
    if "workflow_stage" in workflow_data:
        old_stage = company.workflow_stage
        company.workflow_stage = workflow_data["workflow_stage"]
        
        # Log to history
        history = company.workflow_history or []
        history.append({
            "date": datetime.now().strftime('%Y-%m-%d %H:%M'),
            "stage": workflow_data["workflow_stage"],
            "previous_stage": old_stage,
            "action": workflow_data.get("next_action", "Stage updated")
        })
        company.workflow_history = history
    
    if "next_action" in workflow_data:
        company.next_action = workflow_data["next_action"]
    if "next_action_date" in workflow_data:
        company.next_action_date = datetime.fromisoformat(workflow_data["next_action_date"])
    if "assigned_to" in workflow_data:
        company.assigned_to = workflow_data["assigned_to"]
    if "workflow_notes" in workflow_data:
        # Append to running log
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        existing = company.workflow_notes or ""
        company.workflow_notes = f"{existing}\n[{timestamp}] {workflow_data['workflow_notes']}".strip()
    if "blockers" in workflow_data:
        company.blockers = workflow_data["blockers"]
    
    db.commit()
    db.refresh(company)
    
    return {
        "message": "Workflow updated",
        "company": company.company_name,
        "workflow_stage": company.workflow_stage,
        "next_action": company.next_action,
        "next_action_date": str(company.next_action_date) if company.next_action_date else None
    }


@router.get("/workflow/upcoming")
def get_upcoming_actions(days: int = 7, db: Session = Depends(get_db)):
    """
    Get companies with upcoming next actions in the next N days
    """
    from datetime import timedelta
    
    cutoff_date = datetime.now() + timedelta(days=days)
    
    companies = db.query(RobotCompany).filter(
        RobotCompany.next_action_date <= cutoff_date,
        RobotCompany.next_action_date >= datetime.now()
    ).order_by(RobotCompany.next_action_date).all()
    
    return {
        "upcoming_actions": [
            {
                "id": c.id,
                "company_name": c.company_name,
                "workflow_stage": c.workflow_stage,
                "next_action": c.next_action,
                "next_action_date": str(c.next_action_date),
                "assigned_to": c.assigned_to,
                "priority_tier": c.priority_tier,
                "lead_score": c.lead_score,
                "blockers": c.blockers
            }
            for c in companies
        ],
        "count": len(companies),
        "days": days
    }


@router.get("/agent/supply-side")
def supply_side_agent(
    limit: int = Query(10, ge=1, le=50),
    min_score: int = Query(0, ge=0, le=100),
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Research robot companies, identify who to contact, match up to 3 buyer leads,
    and draft signup/meeting outreach for review.
    """
    query = db.query(RobotCompany)
    if min_score:
        query = query.filter(RobotCompany.lead_score >= min_score)
    if search:
        query = query.filter(RobotCompany.company_name.ilike(f"%{search}%"))
    companies = query.order_by(RobotCompany.lead_score.desc(), RobotCompany.updated_at.desc().nullslast()).limit(limit).all()
    rows = [_supply_agent_row(db, rc) for rc in companies]
    return {
        "agent": "robot_company_supply_pipeline",
        "review_required": True,
        "instructions": "Review contact strategy and drafted email before sending. Each email shows only 3 buyer matches.",
        "companies": rows,
        "count": len(rows),
    }


@router.get("/{company_id}/email")
def generate_email(
    company_id: int,
    template_type: str = Query("intro", description="intro, demo, proposal, followup, trade_show, hot_lead"),
    db: Session = Depends(get_db)
):
    """
    Generate personalized email for company outreach
    
    Template types:
    - intro: Initial introduction email
    - demo: Request product demonstration
    - proposal: Partnership proposal after demo
    - followup: Follow-up for non-responsive leads
    - trade_show: Trade show meeting invitation
    - hot_lead: High-priority outreach for hot leads
    """
    company = db.query(RobotCompany).filter(RobotCompany.id == company_id).first()
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Convert company to dict for template
    company_data = {
        'company_name': company.company_name,
        'robot_type': company.robot_type,
        'target_market': company.target_market,
        'us_presence': company.us_presence,
        'lead_score': company.lead_score,
        'unique_selling_points': company.unique_selling_points or [],
        'website': company.website
    }
    
    # Use workflow_stage if template_type is 'auto'
    if template_type == 'auto':
        template_type = company.workflow_stage or 'intro'
    
    email = get_email_template(template_type, company_data)
    
    return {
        "company_id": company_id,
        "company_name": company.company_name,
        "template_type": template_type,
        "email": email
    }


@router.post("/{company_id}/email/log")
def log_email_sent(
    company_id: int,
    email_data: dict,
    db: Session = Depends(get_db)
):
    """
    Log that an email was sent to a company
    Updates workflow notes and last contact date
    """
    company = db.query(RobotCompany).filter(RobotCompany.id == company_id).first()
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Update last contact date
    company.last_contact_date = datetime.now()
    
    # Log to workflow notes
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    template_type = email_data.get('template_type', 'email')
    subject = email_data.get('subject', 'Email sent')
    
    existing = company.workflow_notes or ""
    company.workflow_notes = f"{existing}\n[{timestamp}] Sent {template_type} email: {subject}".strip()
    
    # Update outreach status if not contacted yet
    if company.outreach_status == 'not_contacted':
        company.outreach_status = 'contacted'
    
    db.commit()
    db.refresh(company)
    
    return {
        "message": "Email logged successfully",
        "company": company.company_name,
        "last_contact_date": str(company.last_contact_date)
    }


@router.post("/{company_id}/email/send")
def send_email(
    company_id: int,
    payload: SendRobotCompanyEmailRequest,
    db: Session = Depends(get_db),
):
    """
    Send outreach email via Resend and log activity.
    """
    company = db.query(RobotCompany).filter(RobotCompany.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    company_data = {
        "company_name": company.company_name,
        "robot_type": company.robot_type,
        "target_market": company.target_market,
        "us_presence": company.us_presence,
        "lead_score": company.lead_score,
        "unique_selling_points": company.unique_selling_points or [],
        "website": company.website,
    }
    template_type = (payload.template_type or "intro").strip() or "intro"
    email = get_email_template(template_type, company_data)
    subject = payload.subject or email.get("subject", "Partnership Opportunity")
    body = payload.body or email.get("body", "")

    try:
        send_result = send_email_via_resend(
            to_email=payload.to_email,
            subject=subject,
            body_text=body,
        )
    except ResendEmailError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    company.last_contact_date = datetime.now()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    existing = company.workflow_notes or ""
    company.workflow_notes = (
        f"{existing}\n[{timestamp}] Sent {template_type} email to {payload.to_email}: {subject}"
    ).strip()
    if company.outreach_status == "not_contacted":
        company.outreach_status = "contacted"

    db.commit()
    db.refresh(company)

    return {
        "message": "Email sent via Resend",
        "company": company.company_name,
        "to_email": payload.to_email,
        "template_type": template_type,
        "subject": subject,
        "resend_id": send_result.get("resend_id"),
        "from_email": send_result.get("from_email"),
        "reply_to": send_result.get("reply_to"),
        "last_contact_date": str(company.last_contact_date),
    }


@router.post("/{company_id}/email/test-send")
def test_send_email(
    company_id: int,
    payload: SendRobotCompanyEmailRequest,
    db: Session = Depends(get_db),
):
    """
    Send a test outreach email via Resend without mutating workflow state.
    """
    company = db.query(RobotCompany).filter(RobotCompany.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    company_data = {
        "company_name": company.company_name,
        "robot_type": company.robot_type,
        "target_market": company.target_market,
        "us_presence": company.us_presence,
        "lead_score": company.lead_score,
        "unique_selling_points": company.unique_selling_points or [],
        "website": company.website,
    }
    template_type = (payload.template_type or "intro").strip() or "intro"
    email = get_email_template(template_type, company_data)
    raw_subject = payload.subject or email.get("subject", "Partnership Opportunity")
    subject = f"[TEST] {raw_subject}"
    body = payload.body or email.get("body", "")

    try:
        send_result = send_email_via_resend(
            to_email=payload.to_email,
            subject=subject,
            body_text=body,
        )
    except ResendEmailError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "message": "Test email sent via Resend",
        "company": company.company_name,
        "to_email": payload.to_email,
        "template_type": template_type,
        "subject": subject,
        "resend_id": send_result.get("resend_id"),
        "from_email": send_result.get("from_email"),
        "reply_to": send_result.get("reply_to"),
    }

