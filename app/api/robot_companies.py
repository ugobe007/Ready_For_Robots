"""
Robot Companies API
Lead generation system for robotics vendors
Focus: Chinese companies entering U.S. market
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models.robot_company import RobotCompany

router = APIRouter(prefix="/api/robot-companies", tags=["robot-companies"])


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
    
    # Order by lead score descending
    query = query.order_by(RobotCompany.lead_score.desc())
    
    companies = query.offset(skip).limit(limit).all()
    total = query.count()
    
    return {
        "companies": companies,
        "total": total,
        "skip": skip,
        "limit": limit
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
        "hot_leads": companies,
        "count": len(companies)
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
        "companies": companies,
        "total": len(companies),
        "filter": us_presence or "all"
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
            "companies": wave_1,
            "count": len(wave_1),
            "description": "Already Entered U.S. (2020-2024)"
        },
        "wave_2": {
            "companies": wave_2,
            "count": len(wave_2),
            "description": "Rapid Expansion (2024-2026)"
        },
        "wave_3": {
            "companies": wave_3,
            "count": len(wave_3),
            "description": "Next-Generation AI Robots (2025-2027)"
        }
    }


@router.get("/needs-distribution")
def get_needs_distribution(db: Session = Depends(get_db)):
    """Get companies that explicitly need U.S. distribution"""
    companies = db.query(RobotCompany).filter(
        RobotCompany.distributor_needed == "yes"
    ).order_by(RobotCompany.lead_score.desc()).all()
    
    return {
        "companies": companies,
        "count": len(companies),
        "message": "Companies actively seeking U.S. distribution partners"
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
            "companies": companies,
            "count": len(companies)
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
    
    return company


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
    
    return company


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
        "companies": companies,
        "count": len(companies)
    }


@router.post("/")
def create_robot_company(company_data: dict, db: Session = Depends(get_db)):
    """Create new robot company lead"""
    company = RobotCompany(**company_data)
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


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
    
    return company


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
