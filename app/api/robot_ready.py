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
from sqlalchemy.orm import Session
from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict
import requests
from bs4 import BeautifulSoup
from app.database import get_db
from app.models.company import Company
from app.services.ontology import get_industry_prior

router = APIRouter()


class RobotSubmission(BaseModel):
    robot_name: str
    url: str
    email: Optional[str] = None


def scrape_robot_page(url: str) -> str:
    """Scrape robot product page and extract text content"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; RobotReadyBot/1.0)'
        }
        resp = requests.get(url, headers=headers, timeout=10)
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
    text_lower = page_text.lower()
    
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
    if 'hospital' in text_lower or 'healthcare' in text_lower:
        use_case = "Healthcare Operations"
    elif 'hotel' in text_lower or 'hospitality' in text_lower:
        use_case = "Hospitality Services"
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
    }


def match_companies(robot_caps: Dict, db: Session) -> List[Dict]:
    """
    Match robot capabilities with companies in the database.
    Returns top matches with scores and customized pitches.
    """
    # Get all companies with their signals
    companies = db.query(Company).limit(1000).all()
    
    matches = []
    
    for company in companies:
        if not company.scores:
            continue
        
        score = company.scores
        signals = company.signals or []
        
        # Calculate match score based on:
        # 1. Industry fit
        # 2. Overall intent score
        # 3. Specific signals
        
        match_score = 0.0
        industry = company.industry or ""
        
        # Industry matching
        industry_match = 0
        robot_use_case = robot_caps.get("use_case", "").lower()
        if "healthcare" in robot_use_case and "healthcare" in industry.lower():
            industry_match = 40
        elif "hospitality" in robot_use_case and "hospitality" in industry.lower():
            industry_match = 40
        elif "warehouse" in robot_use_case and "logistics" in industry.lower():
            industry_match = 40
        elif "food" in robot_use_case and "food" in industry.lower():
            industry_match = 40
        else:
            # Generic match based on industry prior
            industry_match = int(get_industry_prior(industry) * 30)
        
        match_score += industry_match
        
        # Intent score (0-100 scale, weight 30%)
        match_score += (score.overall_intent_score or 0) * 0.3
        
        # Signal boost
        signal_boost = min(20, len(signals) * 2)  # up to 20 points
        match_score += signal_boost
        
        match_score = min(100, int(match_score))
        
        if match_score < 30:  # Skip low matches
            continue
        
        # Generate value proposition
        value_prop = generate_value_prop(company, robot_caps, signals)
        
        # Extract key signals
        key_signals = []
        hot_signal_types = ['funding_round', 'strategic_hire', 'capex', 'labor_shortage', 'expansion']
        for sig in signals[:5]:
            if sig.signal_type in hot_signal_types:
                key_signals.append(f"{sig.signal_type.replace('_', ' ').title()}: {sig.signal_text[:80]}...")
        
        # Recommended action
        action = "Reach out with personalized demo offer"
        if any(s.signal_type == 'strategic_hire' for s in signals):
            action = "Contact new executive with ROI-focused pitch"
        elif any(s.signal_type == 'funding_round' for s in signals):
            action = "Pitch during budget planning window"
        elif any(s.signal_type == 'expansion' for s in signals):
            action = "Propose as part of new facility build-out"
        
        matches.append({
            "company_name": company.name,
            "industry": company.industry,
            "location_city": company.location_city,
            "location_state": company.location_state,
            "employee_estimate": company.employee_estimate,
            "priority_tier": getattr(company, 'priority_tier', 'COLD'),
            "match_score": match_score,
            "value_proposition": value_prop,
            "key_signals": key_signals[:3],
            "recommended_action": action,
        })
    
    # Sort by match score
    matches.sort(key=lambda x: x['match_score'], reverse=True)
    
    return matches[:25]  # Return top 25


def generate_value_prop(company: Company, robot_caps: Dict, signals: List) -> str:
    """Generate customized value proposition for this specific company"""
    company_name = company.name
    industry = company.industry or "your industry"
    robot_type = robot_caps.get("type", "robot")
    
    # Check for labor signals
    has_labor_pain = any(s.signal_type in ['labor_shortage', 'job_posting'] for s in signals)
    has_expansion = any(s.signal_type == 'expansion' for s in signals)
    has_funding = any(s.signal_type == 'funding_round' for s in signals)
    
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
    1. Scrape URL
    2. Analyze capabilities
    3. Match with companies
    4. Generate strategy
    """
    # Scrape robot page
    page_text = scrape_robot_page(submission.url)
    
    # Analyze capabilities
    robot_caps = analyze_robot_capabilities(submission.robot_name, page_text)
    
    # Match with companies
    matched_companies = match_companies(robot_caps, db)
    
    # Generate strategy
    overall_strategy = generate_overall_strategy(matched_companies, robot_caps)
    
    # Estimate deal value (rough calculation)
    hot_matches = [m for m in matched_companies if m.get('priority_tier') == 'HOT']
    estimated_value = len(hot_matches) * 50000  # Assume avg $50K deal
    
    # Determine top industry
    if matched_companies:
        industries = [m['industry'] for m in matched_companies if m.get('industry')]
        top_industry = max(set(industries), key=industries.count) if industries else "Multiple"
    else:
        top_industry = "None"
    
    return {
        "robot_name": submission.robot_name,
        "robot_capabilities": robot_caps,
        "matched_companies": matched_companies,
        "overall_strategy": overall_strategy,
        "estimated_deal_value": estimated_value,
        "top_industry": top_industry,
        "total_leads": len(matched_companies),
    }
