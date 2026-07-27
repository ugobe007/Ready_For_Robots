"""
Email Introduction Templates for Robot Company Outreach
Personalized email scripts for different workflow stages
"""
from typing import Dict, Optional

from app.services.agent_messaging import (
    CAL_VENDOR_OFFRAMP_LINE,
    VEGAS_DISTRIBUTION_LINE,
    cal_signature,
    cal_vendor_opening,
)
from app.services.cal_insights import pick_cal_insight


def _focus(company_data: Dict) -> str:
    parts = [
        company_data.get("robot_type"),
        company_data.get("product_category"),
        company_data.get("target_market"),
    ]
    cleaned = []
    seen = set()
    for part in parts:
        value = str(part or "").strip()
        key = value.lower()
        if not value or key in {"unknown", "none", "null"} or key in seen:
            continue
        seen.add(key)
        cleaned.append(value)
    return " and ".join(cleaned[:2]) if cleaned else "robot automation"


def _vendor_context(company_data: Dict) -> str:
    lead_score = company_data.get("lead_score")
    if isinstance(lead_score, (int, float)) and lead_score >= 85:
        return "Your company is showing up as a stronger fit in our recent deployment-side demand review."
    return "Your company looked relevant to a few buyer-side deployment patterns we are tracking."


def _insight_paragraph(company_data: Dict) -> str:
    trade_show = company_data.get("next_trade_show") or company_data.get("trade_show")
    shows = company_data.get("trade_shows")
    if not trade_show and isinstance(shows, list) and shows:
        trade_show = shows[0]
    return pick_cal_insight(
        company_name=str(company_data.get("company_name") or ""),
        trade_show=str(trade_show) if trade_show else None,
        robot_type=str(company_data.get("robot_type") or "") or None,
        allow_humor=True,
    )


def generate_intro_email(company_data: Dict) -> Dict[str, str]:
    """
    Generate personalized introduction email for initial outreach
    
    Args:
        company_data: Dictionary with company information
        
    Returns:
        Dict with subject, body, and suggested_followup_days
    """
    company_name = company_data.get('company_name', 'Your Company')
    robot_type = company_data.get('robot_type', 'robotics')
    us_presence = company_data.get('us_presence', 'none')
    
    focus = _focus(company_data)
    market_note = "U.S. market entry" if us_presence == "none" else "U.S. growth"
    subject = f"A deployment demand note for {company_name}"
    
    body = f"""Hello,

{cal_vendor_opening()}

{_insight_paragraph(company_data)}

I came across {company_name} because your work around {focus} looks relevant to real deployment demand we are seeing. {_vendor_context(company_data)}

If {market_note} is a priority, I can send over matched accounts and the operating signals behind each one. {VEGAS_DISTRIBUTION_LINE}

{CAL_VENDOR_OFFRAMP_LINE}

If useful, I can send the list first by email so your team can review asynchronously.

{cal_signature()}"""
    
    return {
        "subject": subject,
        "body": body,
        "suggested_followup_days": 3
    }


def generate_demo_request_email(company_data: Dict, contact_response: Optional[str] = None) -> Dict[str, str]:
    """
    Generate email requesting product demo/technical review
    """
    company_name = company_data.get('company_name', 'Your Company')
    robot_type = company_data.get('robot_type', 'robotics')
    
    subject = f"Deployment fit check for {company_name}"
    
    body = f"""Hello,

{cal_vendor_opening(reminder=True)}

{contact_response or "Thanks for the reply."}

The useful next step is a short deployment fit check, not a long presentation. I want to understand where your {robot_type} works best, what constraints matter, and which buyer signals should route to your team.

If you'd rather, I can send questions in email first and only schedule time if it looks worthwhile.

{cal_signature()}"""
    
    return {
        "subject": subject,
        "body": body,
        "suggested_followup_days": 5
    }


def generate_partnership_proposal_email(company_data: Dict, demo_notes: Optional[str] = None) -> Dict[str, str]:
    """
    Generate partnership proposal email after successful demo
    """
    company_name = company_data.get('company_name', 'Your Company')
    robot_type = company_data.get('robot_type', 'robotics')
    
    subject = f"Next deployment step for {company_name}"
    
    body = f"""Hello,

{cal_vendor_opening(reminder=True)}

Thanks again for walking through {company_name}. Based on what we discussed, I think the next step should stay focused: confirm the buyer categories where your {robot_type} is strongest, then map those to the hottest signal types we are seeing.

I can put that into a short deployment brief: which accounts look warm, what signals make them credible, and where your team likely has an advantage.

If you'd like, I can send the brief first and you can decide whether a call is useful.

{cal_signature()}"""
    
    return {
        "subject": subject,
        "body": body,
        "suggested_followup_days": 7
    }


def generate_followup_email(company_data: Dict, previous_contact: str, days_since_contact: int) -> Dict[str, str]:
    """
    Generate follow-up email for non-responsive leads
    """
    company_name = company_data.get('company_name', 'Your Company')
    robot_type = company_data.get('robot_type', 'robotics')
    
    if days_since_contact <= 7:
        tone = "friendly reminder"
        urgency = "I know you're busy, but I wanted to circle back..."
    elif days_since_contact <= 14:
        tone = "value-added followup"
        urgency = "I wanted to share some relevant market intelligence..."
    else:
        tone = "last attempt"
        urgency = "I'll assume this isn't a priority right now, but wanted to reach out one last time..."
    
    subject = f"Re: deployment demand note for {company_name}"
    
    if tone == "friendly reminder":
        body = f"""Hello,

{cal_vendor_opening(reminder=True)}

Following up on my note about {company_name} and the deployment demand we are seeing around {robot_type}.

If this is close to a market you care about, I can send a short list of accounts and why each one looks credible.

{cal_signature()}"""
    
    elif tone == "value-added followup":
        body = f"""Hello,

{cal_vendor_opening(reminder=True)}

I wanted to send one more useful angle rather than just bump the same email.

We are seeing more buyer activity around {robot_type}, and the warmer accounts usually have a specific signal behind them: hiring, expansion, budget movement, RFP language, or public operational pressure.

If that would help {company_name}, I can send a few examples and the context behind each one. If your team is using Vegas as a launchpad, we can also map local commercial intros and buyer routing.

Open to a quick look next week? If the signal trail is not strong enough, I will tell you that directly.

{cal_signature()}"""
    
    else:  # last attempt
        body = f"""Hello,

{cal_vendor_opening(reminder=True)}

I will close the loop here.

If deployment demand becomes relevant for {company_name}, I am happy to reconnect and share what we are seeing around {robot_type}.

{cal_signature()}"""
    
    return {
        "subject": subject,
        "body": body,
        "suggested_followup_days": 14 if tone != "last attempt" else None
    }


def generate_trade_show_invitation_email(company_data: Dict, trade_show: str, date: str) -> Dict[str, str]:
    """
    Generate email inviting company to trade show or scheduling booth meeting
    """
    company_name = company_data.get('company_name', 'Your Company')
    robot_type = company_data.get('robot_type', 'robotics')
    
    subject = f"Will {company_name} be at {trade_show}?"
    
    body = f"""Hello,

{cal_vendor_opening()}

{_insight_paragraph({**company_data, "trade_show": trade_show})}

Are you planning to attend {trade_show} in {date}? I am asking because events are where warm accounts become real conversations.

If {company_name} will be there, I can compare your {robot_type} focus against the accounts we are seeing and flag which meetings look highest-value.

If useful, I can send that list before the show so your team can decide whether a call is even needed.

{cal_signature()}"""
    
    return {
        "subject": subject,
        "body": body,
        "suggested_followup_days": 5
    }


def generate_hot_lead_priority_email(company_data: Dict) -> Dict[str, str]:
    """
    Generate high-priority email for HOT leads (score >= 85)
    """
    company_name = company_data.get('company_name', 'Your Company')
    robot_type = company_data.get('robot_type', 'robotics')
    lead_score = company_data.get('lead_score', 85)
    unique_selling_points = company_data.get('unique_selling_points', [])
    
    subject = f"Higher-confidence accounts for {company_name}"
    
    usp_line = ", ".join(unique_selling_points[:3]) if unique_selling_points else f"{robot_type} technology"
    
    body = f"""Hello,

{cal_vendor_opening()}

{company_name} is showing up as a higher-priority fit in our system. The reason is not just that you make {robot_type}; it is the combination of your focus ({usp_line}) and the buyer-side deployment signals we are seeing.

If useful, I can send the first few accounts and why each one looks warm. We can also map how Ready For Robots handles channel routing and buyer context.

If helpful, I can send that list first and you can decide whether a short call is warranted.

{cal_signature()}"""
    
    return {
        "subject": subject,
        "body": body,
        "suggested_followup_days": 2
    }


# Email template selector
def get_email_template(workflow_stage: str, company_data: Dict, **kwargs) -> Dict[str, str]:
    """
    Get appropriate email template based on workflow stage
    
    Args:
        workflow_stage: Current stage (research, outreach, demo, proposal, etc.)
        company_data: Company information
        **kwargs: Additional context (contact_response, demo_notes, etc.)
        
    Returns:
        Dict with subject, body, suggested_followup_days
    """
    templates = {
        'research': generate_intro_email,
        'outreach': generate_intro_email,
        'demo': generate_demo_request_email,
        'proposal': generate_partnership_proposal_email,
        'negotiation': generate_partnership_proposal_email,
        'followup': generate_followup_email,
        'trade_show': generate_trade_show_invitation_email,
        'hot_lead': generate_hot_lead_priority_email
    }
    
    # Default to intro email if stage not found
    template_func = templates.get(workflow_stage, generate_intro_email)
    
    return template_func(company_data, **kwargs)
