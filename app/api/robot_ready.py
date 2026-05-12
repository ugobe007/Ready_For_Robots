"""
Robot Ready API
===============
Lead generation service for robot companies.
Submit a robot URL, get matched with ideal customer companies.

POST /api/robot-ready/submit
  {
    "robot_name": "TUG T3",
    "url": "https://aethon.com/mobile-robots/tug",
    "email": "sales@company.com"  // optional
  }

Returns:
  {
    "robot_capabilities": { type, use_case, capabilities[] },
    "matched_companies": [ {...company with match_score, value_proposition, key_signals, recommended_action} ],
    "overall_strategy": "...",
    "estimated_deal_value": 500000,
    "top_industry": "Healthcare"
  }
"""
from fastapi import APIRouter, Depends
import re
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict
import requests
import threading
import time
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from app.database import get_db
from app.models.company import Company
from app.models.score import Score
from app.services.ontology import get_industry_prior
from app.services.lead_filter import classify_lead, pick_primary_score
from app.services.lead_signal_display import format_signal_for_sales, strip_extraction_artifacts

router = APIRouter()

# Cache only the lead-candidate index. Final matches are recomputed for every submitted URL.
LEAD_CANDIDATE_CACHE_TTL = 180
LEAD_CANDIDATE_INDEX_LIMIT = 350
LEAD_CANDIDATE_FINAL_LIMIT = 25
_lead_candidate_cache: dict = {}
_lead_candidate_lock = threading.Lock()

SIGNAL_LABELS = {
    "strategic_hire": "Leadership Hire",
    "capex": "CapEx Budget",
    "quality_bottleneck": "Quality Problem",
    "safety_incident": "Safety Incident",
    "labor_shortage": "Labor Shortage",
    "production_capacity": "At Capacity",
    "warehouse_throughput": "Warehouse Bottleneck",
    "packaging_automation": "Packaging Automation",
    "repetitive_process": "Repetitive Tasks",
    "expansion": "Expansion",
    "material_handling": "Material Handling",
    "funding_round": "Funding Round",
    "ma_activity": "M&A Activity",
    "job_posting": "Job Posting",
    "news": "News Signal",
    "automation_interest": "Automation Interest",
    "automation_intent": "Automation Intent",
    "robot_installation": "Robot Install",
    "pilot_success": "Pilot Success",
    "scale_expansion": "Scale Expansion",
    "vendor_selection": "Vendor Selection",
    "roi_documented": "ROI Documented",
    "economics_driven": "Economics Trigger",
    "competitive_response": "Competitive Pressure",
    "problem_solution": "Problem/Solution",
    "government_contract": "Gov Contract",
    "rfp_posted": "RFP Posted",
    "labor_pain": "Labor Pain",
}


class RobotSubmission(BaseModel):
    robot_name: str
    url: Optional[str] = None
    description: Optional[str] = None
    email: Optional[str] = None
    target_industries: Optional[List[str]] = None
    target_regions: Optional[List[str]] = None


def _submitted_domain(raw_url: Optional[str]) -> str:
    if not raw_url:
        return ""
    parsed = urlparse(raw_url if raw_url.startswith(("http://", "https://")) else f"https://{raw_url}")
    return parsed.netloc.replace("www.", "")


def scrape_robot_page(url: str) -> str:
    """Scrape robot product page and extract text content"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; RobotReadyBot/1.0)'
        }
        resp = requests.get(url, headers=headers, timeout=(3, 5))
        resp.raise_for_status()
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text
        text = soup.get_text(separator=' ', strip=True)
        
        # Limit to first 5000 chars to avoid token overflow
        return text[:5000]
    except Exception as e:
        return f"Error scraping {url}: {str(e)}"


def analyze_robot_capabilities(robot_name: str, page_text: str) -> Dict:
    """
    Extract robot capabilities from scraped text.
    In production, this would use LLM to analyze the page.
    For now, using keyword matching.
    """
    text_lower = f"{robot_name or ''} {page_text or ''}".lower()
    
    # Determine robot type
    robot_type = "Unknown"
    if any(kw in text_lower for kw in ['delivery', 'transport', 'courier', 'cart']):
        robot_type = "Delivery/Transport"
    elif any(kw in text_lower for kw in ['disinfect', 'uv', 'sanitize', 'clean']):
        robot_type = "Disinfection/Cleaning"
    elif any(kw in text_lower for kw in ['service', 'serve', 'hospitality', 'restaurant']):
        robot_type = "Service Robot"
    elif any(kw in text_lower for kw in ['warehouse', 'amr', 'agv', 'logistics', 'picking']):
        robot_type = "Warehouse/Logistics"
    elif any(kw in text_lower for kw in ['surgery', 'patient', 'medical', 'healthcare']):
        robot_type = "Medical/Healthcare"
    
    # Determine use case
    use_case = "General Automation"
    if 'hotel' in text_lower or 'hospitality' in text_lower:
        use_case = "Hospitality Services"
    elif re.search(r"\bhospitals?\b|\bhealthcare\b|\bmedical\b|\bclinic\b|\bpatient\b", text_lower):
        use_case = "Healthcare Operations"
    elif 'warehouse' in text_lower or 'distribution' in text_lower:
        use_case = "Warehouse Logistics"
    elif 'restaurant' in text_lower or 'food service' in text_lower:
        use_case = "Food Service"
    
    # Extract capabilities (simple keyword matching)
    capabilities = []
    capability_keywords = {
        'autonomous navigation': ['autonomous', 'navigation', 'lidar', 'mapping'],
        'payload delivery': ['payload', 'delivery', 'transport', 'carry'],
        'UV disinfection': ['uv', 'disinfect', 'sanitize'],
        'temperature control': ['temperature', 'refrigerat', 'heated'],
        'multi-floor': ['elevator', 'multi-floor', 'multiple floors'],
        'human interaction': ['touchscreen', 'voice', 'interface', 'interact'],
        'cloud connected': ['cloud', 'fleet', 'dashboard', 'analytics'],
        'HIPAA compliant': ['hipaa', 'compliant', 'secure'],
    }
    
    for cap, keywords in capability_keywords.items():
        if any(kw in text_lower for kw in keywords):
            capabilities.append(cap)
    
    return {
        "type": robot_type,
        "use_case": use_case,
        "capabilities": capabilities,
        "profile_score": min(100, 35 + (15 if robot_type != "Unknown" else 0) + (10 if use_case != "General Automation" else 0) + min(40, len(capabilities) * 8)),
    }


def _signal_label(signal_type: str) -> str:
    return SIGNAL_LABELS.get(signal_type, (signal_type or "signal").replace("_", " ").title())


def _extract_key_signals(signals: List) -> List[Dict]:
    hot_signal_types = {
        'funding_round', 'strategic_hire', 'capex', 'labor_shortage', 'expansion',
        'automation_intent', 'robot_installation', 'vendor_selection', 'rfp_posted',
    }
    ordered = sorted(signals or [], key=lambda s: float(getattr(s, "signal_strength", 0) or 0), reverse=True)
    picked = []
    seen_types = set()
    for sig in ordered:
        signal_type = getattr(sig, "signal_type", "") or "news"
        if picked and signal_type not in hot_signal_types and len(picked) >= 3:
            continue
        if signal_type in seen_types:
            continue
        text = format_signal_for_sales(getattr(sig, "signal_text", ""), max_chars=260)
        if not text:
            continue
        seen_types.add(signal_type)
        picked.append({
            "signal_type": signal_type,
            "signal_label": _signal_label(signal_type),
            "display_text": text,
            "raw_text": strip_extraction_artifacts(getattr(sig, "signal_text", "")),
            "source_url": getattr(sig, "source_url", None),
        })
        if len(picked) >= 5:
            break
    return picked


def _build_lead_candidate_index(db: Session) -> List[Dict]:
    latest_score = (
        db.query(
            Score.company_id.label("company_id"),
            func.max(Score.overall_intent_score).label("best_score"),
        )
        .group_by(Score.company_id)
        .subquery()
    )
    rows = (
        db.query(Company)
        .join(latest_score, latest_score.c.company_id == Company.id)
        .options(joinedload(Company.scores), joinedload(Company.signals))
        .order_by(latest_score.c.best_score.desc())
        .limit(LEAD_CANDIDATE_INDEX_LIMIT)
        .all()
    )

    candidates = []
    for company in rows:
        score = pick_primary_score(company.scores)
        signals = company.signals or []
        if not score or not signals:
            continue
        junk, junk_reason, pri = classify_lead(company, score, signals)
        if junk:
            continue
        key_signals = _extract_key_signals(signals)
        if not key_signals:
            continue
        candidates.append({
            "id": company.id,
            "company_name": company.name,
            "industry": company.industry,
            "location_city": company.location_city,
            "location_state": company.location_state,
            "employee_estimate": company.employee_estimate,
            "overall_intent_score": float(score.overall_intent_score or 0),
            "priority_tier": pri.tier,
            "priority_score": round(pri.score, 1),
            "priority_reasons": pri.reasons,
            "signals": key_signals,
            "signal_count": len(signals),
            "junk_reason": junk_reason,
        })
    return candidates


def _get_fresh_lead_candidate_index(db: Session) -> List[Dict]:
    now = time.monotonic()
    with _lead_candidate_lock:
        entry = _lead_candidate_cache.get("v1")
        if entry and now - entry["ts"] <= LEAD_CANDIDATE_CACHE_TTL:
            return entry["data"]

    candidates = _build_lead_candidate_index(db)
    with _lead_candidate_lock:
        _lead_candidate_cache["v1"] = {"ts": time.monotonic(), "data": candidates}
    return candidates


def warm_robot_ready_candidate_cache() -> None:
    """Prebuild the scan candidate index in the background after app startup."""
    def _warm():
        try:
            from app.database import SessionLocal

            db = SessionLocal()
            try:
                _get_fresh_lead_candidate_index(db)
            finally:
                db.close()
        except Exception:
            pass

    threading.Thread(target=_warm, daemon=True, name="robot-ready-candidate-warmer").start()


def _industry_match_score(robot_use_case: str, industry: str) -> int:
    industry_lower = (industry or "").lower()
    use_case_lower = (robot_use_case or "").lower()
    if "healthcare" in use_case_lower and "healthcare" in industry_lower:
        return 40
    if "hospitality" in use_case_lower and any(x in industry_lower for x in ["hospitality", "hotel"]):
        return 40
    if "warehouse" in use_case_lower and any(x in industry_lower for x in ["logistics", "warehouse", "fulfillment", "supply"]):
        return 40
    if "food" in use_case_lower and any(x in industry_lower for x in ["food", "restaurant"]):
        return 40
    return int(get_industry_prior(industry or "") * 30)


def _capability_signal_bonus(robot_caps: Dict, signals: List[Dict]) -> int:
    text = " ".join(
        [
            robot_caps.get("type", ""),
            robot_caps.get("use_case", ""),
            " ".join(robot_caps.get("capabilities") or []),
        ]
    ).lower()
    signal_text = " ".join(
        f"{s.get('signal_type', '')} {s.get('display_text', '')}" for s in signals
    ).lower()
    bonus = 0
    if any(x in text for x in ["warehouse", "payload", "transport", "delivery"]) and any(x in signal_text for x in ["warehouse", "throughput", "material", "expansion", "labor"]):
        bonus += 12
    if any(x in text for x in ["service", "hospitality", "food"]) and any(x in signal_text for x in ["labor", "service", "restaurant", "hospitality"]):
        bonus += 12
    if any(x in text for x in ["medical", "healthcare", "disinfection"]) and any(x in signal_text for x in ["healthcare", "hospital", "safety", "infection"]):
        bonus += 12
    if any(x in text for x in ["navigation", "cloud", "fleet"]) and any(x in signal_text for x in ["automation", "robot", "vendor", "pilot"]):
        bonus += 8
    return min(24, bonus)


def match_companies(robot_caps: Dict, db: Session, target_industries: List[str] = None, target_regions: List[str] = None) -> List[Dict]:
    """
    Match robot capabilities with companies in the database.
    Returns top matches with scores and customized pitches.
    Filters by target industries and regions if specified.
    """
    candidates = _get_fresh_lead_candidate_index(db)
    matches = []
    
    # Region mapping for filtering
    REGION_STATES = {
        'Northeast US': ['NY', 'NJ', 'PA', 'MA', 'CT', 'RI', 'VT', 'NH', 'ME'],
        'Southeast US': ['FL', 'GA', 'NC', 'SC', 'VA', 'AL', 'MS', 'TN', 'KY', 'WV'],
        'Midwest US': ['OH', 'MI', 'IN', 'IL', 'WI', 'MN', 'IA', 'MO', 'ND', 'SD', 'NE', 'KS'],
        'Southwest US': ['TX', 'OK', 'AR', 'LA', 'NM', 'AZ'],
        'West Coast US': ['CA', 'OR', 'WA', 'NV', 'ID', 'UT', 'CO', 'MT', 'WY'],
        'Canada': ['ON', 'BC', 'AB', 'QC'],
        'United Kingdom': ['UK', 'GB'],
        'Europe': ['UK', 'GB', 'DE', 'FR', 'IT', 'ES'],
        'Global': [],  # Accept all
    }
    
    for candidate in candidates:
        # Filter by industry if specified
        if target_industries:
            company_industry = candidate.get("industry") or ""
            if not any(target_ind.lower() in company_industry.lower() for target_ind in target_industries):
                continue
        
        # Filter by region if specified
        if target_regions and 'Global' not in target_regions:
            company_state = candidate.get("location_state") or ""
            matches_region = False
            for region in target_regions:
                allowed_states = REGION_STATES.get(region, [])
                if not allowed_states:  # Global
                    matches_region = True
                    break
                if company_state in allowed_states:
                    matches_region = True
                    break
            if not matches_region:
                continue
        
        # Calculate match score based on:
        # 1. Industry fit
        # 2. Overall intent score
        # 3. Specific signals
        
        match_score = 0.0
        industry = candidate.get("industry") or ""
        signals = candidate.get("signals") or []
        
        # Industry matching
        robot_use_case = robot_caps.get("use_case", "")
        industry_match = _industry_match_score(robot_use_case, industry)
        match_score += industry_match
        
        # Intent score (0-100 scale, weight 30%)
        match_score += (candidate.get("overall_intent_score") or 0) * 0.3
        
        # Signal boost
        signal_boost = min(20, (candidate.get("signal_count") or len(signals)) * 2)  # up to 20 points
        match_score += signal_boost
        match_score += _capability_signal_bonus(robot_caps, signals)
        
        match_score = min(100, int(match_score))
        
        if match_score < 30:  # Skip low matches
            continue
        
        # Generate value proposition
        value_prop = generate_value_prop(candidate, robot_caps, signals)
        
        # Recommended action
        action = "Reach out with personalized demo offer"
        signal_types = {s.get("signal_type") for s in signals}
        if 'strategic_hire' in signal_types:
            action = "Contact new executive with ROI-focused pitch"
        elif 'funding_round' in signal_types:
            action = "Pitch during budget planning window"
        elif 'expansion' in signal_types:
            action = "Propose as part of new facility build-out"
        elif _capability_signal_bonus(robot_caps, signals) >= 12:
            action = "Lead with the capability-fit use case from the scanned URL"
        
        matches.append({
            "id": candidate.get("id"),
            "company_name": candidate.get("company_name"),
            "industry": candidate.get("industry"),
            "location_city": candidate.get("location_city"),
            "location_state": candidate.get("location_state"),
            "employee_estimate": candidate.get("employee_estimate"),
            "priority_tier": candidate.get("priority_tier"),
            "priority_score": candidate.get("priority_score"),
            "priority_reasons": candidate.get("priority_reasons", []),
            "match_score": match_score,
            "value_proposition": value_prop,
            "key_signals": [s.get("display_text") for s in signals[:3]],
            "signals": signals[:5],
            "recommended_action": action,
            "score": {
                "overall_score": candidate.get("overall_intent_score"),
                "lead_value_score": match_score,
                "signal_score": min(100, (candidate.get("signal_count") or 0) * 10),
            },
            "share_summary": value_prop,
            "gtm": {
                "readiness_label": candidate.get("priority_tier"),
                "why_now": candidate.get("priority_reasons", []),
                "suggested_motion": action,
            },
        })
    
    # Sort by match score
    matches.sort(key=lambda x: x['match_score'], reverse=True)
    
    return matches[:25]  # Return top 25


def generate_value_prop(company, robot_caps: Dict, signals: List) -> str:
    """Generate customized value proposition for this specific company"""
    if isinstance(company, dict):
        company_name = company.get("company_name") or "this account"
        industry = company.get("industry") or "your industry"
    else:
        company_name = company.name
        industry = company.industry or "your industry"
    robot_type = robot_caps.get("type", "robot")
    
    # Check for labor signals
    signal_types = {
        s.get("signal_type") if isinstance(s, dict) else getattr(s, "signal_type", None)
        for s in (signals or [])
    }
    has_labor_pain = bool(signal_types & {'labor_shortage', 'job_posting', 'labor_pain'})
    has_expansion = 'expansion' in signal_types
    has_funding = 'funding_round' in signal_types
    
    if has_labor_pain:
        return f"Help {company_name} solve staffing challenges with automated {robot_type.lower()} - reduce dependence on hard-to-find labor while improving service consistency."
    elif has_expansion:
        return f"Scale {company_name}'s new facilities efficiently with {robot_type.lower()} from day one - no ramp-up delays, consistent performance across all locations."
    elif has_funding:
        return f"{company_name} just raised capital - perfect timing to invest in {robot_type.lower()} that delivers measurable ROI and competitive advantage."
    else:
        return f"Increase operational efficiency at {company_name} with {robot_type.lower()} - reduce costs, improve throughput, and free staff for higher-value work."


def generate_overall_strategy(matches: List[Dict], robot_caps: Dict) -> str:
    """Generate overall outreach strategy"""
    if not matches:
        return "No strong matches found. Consider expanding your target industries or refining your robot's use case description."
    
    hot_count = len([m for m in matches if m.get('priority_tier') == 'HOT'])
    top_industry = max(set([m['industry'] for m in matches if m.get('industry')]), 
                      key=lambda x: sum(1 for m in matches if m.get('industry') == x))
    
    strategy = f"""
**Recommended Go-to-Market Strategy:**

1. **Priority Outreach** ({hot_count} companies)
   Focus first on HOT-tier matches showing active buying signals (funding, exec hires, expansion). 
   These are ready to evaluate solutions now.

2. **Industry Focus: {top_industry}**
   Your robot shows strongest fit in {top_industry}. Build case studies and references here first.

3. **Key Talking Points:**
   - Lead with labor efficiency and cost reduction
   - Emphasize consistent service quality vs. human variability  
   - Quantify ROI: typical payback in 12-18 months
   - Position as strategic advantage, not just cost-cutting

4. **Next Steps:**
   - Reach out to top 5 matches this week with personalized emails
   - Offer exclusive pilot program at discounted rate
   - Request intro calls with operations leaders (not just IT/innovation)
   - Follow up on expansion/funding signals within 2 weeks while budget is fresh
"""
    return strategy.strip()


@router.post("/submit")
def submit_robot(submission: RobotSubmission, db: Session = Depends(get_db)):
    """
    Process robot submission:
    1. Get robot data (scrape URL OR use description)
    2. Analyze capabilities
    3. Match with companies
    4. Generate strategy
    """
    # Get robot page content
    if submission.url:
        # Scrape URL if provided
        page_text = scrape_robot_page(submission.url)
        if page_text.lower().startswith("error scraping"):
            domain = _submitted_domain(submission.url)
            page_text = f"{submission.robot_name or domain} robotics automation solution from {domain}. {submission.description or ''}".strip()
    elif submission.description:
        # Use provided description
        page_text = submission.description
    else:
        return {"error": "Please provide either a URL or description of your robot"}
    
    # Analyze capabilities
    robot_caps = analyze_robot_capabilities(submission.robot_name, page_text)
    
    # Match with companies (with optional filters)
    matched_companies = match_companies(
        robot_caps, 
        db, 
        target_industries=submission.target_industries,
        target_regions=submission.target_regions
    )
    
    # Generate strategy
    overall_strategy = generate_overall_strategy(matched_companies, robot_caps)
    
    # Estimate deal value (rough calculation based on company size)
    hot_matches = [m for m in matched_companies if m.get('priority_tier') == 'HOT']
    estimated_value = 0
    for match in hot_matches:
        emp = match.get('employee_estimate', 0) or 0
        # Estimate robots needed based on employee count
        if emp >= 100000:
            deal_size = 500000  # Enterprise
        elif emp >= 20000:
            deal_size = 250000  # Large
        elif emp >= 5000:
            deal_size = 150000  # Mid-market
        elif emp >= 1000:
            deal_size = 75000   # Regional
        else:
            deal_size = 35000   # SMB
        estimated_value += deal_size
    
    # Determine top industry
    if matched_companies:
        industries = [m['industry'] for m in matched_companies if m.get('industry')]
        top_industry = max(set(industries), key=industries.count) if industries else "Multiple"
    else:
        top_industry = "None"
    
    return {
        "robot_name": submission.robot_name,
        "submitted_url": submission.url,
        "robot_capabilities": robot_caps,
        "matched_companies": matched_companies,
        "overall_strategy": overall_strategy,
        "estimated_deal_value": estimated_value,
        "top_industry": top_industry,
        "total_leads": len(matched_companies),
    }
