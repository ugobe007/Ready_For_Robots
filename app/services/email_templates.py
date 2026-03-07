"""
Email Introduction Templates for Robot Company Outreach
Personalized email scripts for different workflow stages
"""
from datetime import datetime
from typing import Dict, Optional


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
    target_market = company_data.get('target_market', 'automation')
    us_presence = company_data.get('us_presence', 'none')
    
    # Personalize based on U.S. presence
    if us_presence == 'none':
        angle = "breaking into the U.S. market"
        value_prop = "We specialize in connecting Chinese robotics companies with U.S. distributors, system integrators, and end customers."
    elif us_presence == 'distributor':
        angle = "expanding your U.S. distributor network"
        value_prop = "We help established robotics companies scale their U.S. presence through strategic partnerships with regional distributors and system integrators."
    else:
        angle = "growing your U.S. market share"
        value_prop = "We connect robotics companies with qualified system integrators and end customers across North America."
    
    subject = f"U.S. Market Entry Partnership - {company_name}"
    
    body = f"""Hi [First Name],

I came across {company_name} and was impressed by your {robot_type} solutions for {target_market}. I noticed you're {angle}, and I think there's a strong fit for collaboration.

{value_prop}

**What We Offer:**
• Access to 500+ vetted U.S. system integrators and distributors
• Market entry strategy and localization support
• Trade show coordination (Automate, ProMat, MODEX)
• Lead generation and customer introductions

**Why This Matters Now:**
The U.S. {target_market} automation market is growing 23% YoY, with strong demand for proven {robot_type} technology. Companies that establish partnerships in Q1 2026 are capturing the early-mover advantage.

Would you be open to a 20-minute call next week to explore how we can accelerate your U.S. growth?

Best regards,
[Your Name]
Ready For Robots
www.readyforrobots.com

P.S. We recently helped [Similar Company] expand from 2 to 15 U.S. distributors in 6 months. Happy to share that playbook.
"""
    
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
    
    subject = f"Demo Request: Technical Review of {company_name} {robot_type.upper()}"
    
    body = f"""Hi [First Name],

Thanks for getting back to me! {contact_response or "I appreciate your interest in exploring the U.S. market."}

To best support your U.S. market entry, I'd like to schedule a technical demo of your {robot_type} solutions. This will help us:

1. **Understand Your Technology** - Specs, capabilities, unique advantages
2. **Identify Target Customers** - Which U.S. industries/applications are the best fit
3. **Map Partner Network** - Which of our 500+ integrators align with your tech
4. **Build Go-to-Market Plan** - Positioning, pricing, support requirements

**Proposed Agenda (60 minutes):**
• Product demonstration (30 min)
• U.S. market opportunity discussion (15 min)
• Partnership model and next steps (15 min)

**Availability:**
I'm flexible on timing. What works best for your team?
- [Date Option 1] at [Time] EST
- [Date Option 2] at [Time] EST
- Or suggest a time that works for you

Looking forward to seeing your technology in action!

Best,
[Your Name]
Ready For Robots
"""
    
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
    target_market = company_data.get('target_market', 'automation')
    
    subject = f"Partnership Proposal: U.S. Market Entry Plan for {company_name}"
    
    body = f"""Hi [First Name],

Thank you for the excellent demo last week. Your {robot_type} technology is impressive, and I can see strong market fit in the U.S. {target_market} sector.

Based on our discussion, I've outlined a partnership approach:

**PHASE 1: Market Entry Foundation (Months 1-2)**
• Identify 10-15 target system integrators aligned with your technology
• Localize marketing materials and technical documentation
• Set up demo unit program for qualified partners
• Plan trade show presence (Automate 2026 or ProMat 2026)

**PHASE 2: Partner Onboarding (Months 2-4)**
• Introduce your team to vetted integrators
• Facilitate technical training and certification
• Support first customer deployments
• Generate case studies and success stories

**PHASE 3: Scale & Growth (Months 4-12)**
• Expand to 20-30 active integrator partnerships
• Regional market penetration (focus on [region based on tech])
• End customer lead generation program
• Quarterly business reviews and optimization

**Investment & Terms:**
I've attached a detailed proposal with partnership structure, pricing, and expected ROI.

**Next Steps:**
Let's schedule a 30-minute call to review the proposal and address any questions. 

Are you available [Date/Time options]?

Best regards,
[Your Name]
Ready For Robots

Attachment: Partnership_Proposal_{company_name}.pdf
"""
    
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
    
    subject = f"Re: U.S. Market Entry Partnership - {company_name}"
    
    if tone == "friendly reminder":
        body = f"""Hi [First Name],

{urgency}

I sent a note last week about helping {company_name} expand into the U.S. {robot_type} market. 

Quick recap:
• We connect Chinese robotics companies with U.S. distributors/integrators
• 500+ vetted partners in our network
• Full market entry support (demos, trade shows, lead gen)

Is this something worth exploring? Even a quick 15-minute call could clarify if there's a fit.

Best,
[Your Name]
"""
    
    elif tone == "value-added followup":
        body = f"""Hi [First Name],

{urgency}

I've been tracking the U.S. {robot_type} market and thought this might interest you:

**Recent Trends:**
• 3 new Chinese {robot_type} companies entered U.S. in Q4 2025
• Average time to first customer: 4-6 months with distributor network
• Trade show ROI: Companies exhibiting at Automate see 3x more inbound leads

**Opportunity:**
Automate 2026 (May) is coming up. Early booth reservations are closing in 2 weeks. If you're considering U.S. expansion, this could be a strategic entry point.

Would you like to discuss a trade show strategy + distributor outreach plan?

Best,
[Your Name]
"""
    
    else:  # last attempt
        body = f"""Hi [First Name],

{urgency}

I understand timing might not be right for U.S. market expansion. No worries at all.

If things change, I'm here to help. We're always tracking the {robot_type} market and would be happy to reconnect when it makes sense for {company_name}.

Feel free to reach out anytime.

Best regards,
[Your Name]
Ready For Robots
"""
    
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
    
    subject = f"Meet at {trade_show} {date.split('-')[0]} - U.S. Market Entry Discussion"
    
    body = f"""Hi [First Name],

Are you planning to attend {trade_show} in {date}? It's one of the best events for {robot_type} companies looking to break into the U.S. market.

**Why {trade_show} Matters:**
• 30,000+ qualified buyers and integrators
• Direct access to decision-makers in {robot_type} adoption
• Perfect venue for product demos and partnership discussions

**Let's Meet:**
If you're attending, I'd love to schedule 30 minutes to:
1. Introduce you to potential U.S. distributors (we'll have 10+ at the show)
2. Review your technology and market positioning
3. Discuss partnership opportunities

If you're NOT attending but interested in U.S. expansion, we can arrange virtual introductions to integrators who will be there.

**My Schedule:**
I'm available:
• [Date] 10am-12pm, 2pm-4pm
• [Date] 9am-11am, 1pm-5pm

Let me know what works!

Best,
[Your Name]
Ready For Robots

P.S. We're hosting a private reception for Chinese robotics companies on [Date] evening. Would love to have {company_name} join if you're in town.
"""
    
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
    
    subject = f"🔥 U.S. Market Opportunity for {company_name} - High Priority"
    
    usp_bullets = "\n".join([f"• {usp}" for usp in unique_selling_points[:3]]) if unique_selling_points else f"• Cutting-edge {robot_type} technology"
    
    body = f"""Hi [First Name],

I've been tracking {company_name} and I'm reaching out because you're uniquely positioned for rapid U.S. market success.

**Why You Stand Out:**
{usp_bullets}

**The Opportunity:**
We have 3 U.S. system integrators actively searching for {robot_type} solutions RIGHT NOW. They're:
• Currently evaluating competitive products
• Ready to commit to partnerships in Q1 2026
• Looking for proven technology with strong support

**Fast Track Process:**
If you're interested, I can arrange introductions THIS WEEK. Here's the timeline:
• Day 1-2: Share your tech overview with integrators
• Day 3-5: Schedule demo calls
• Week 2: Partnership discussions if there's mutual fit

This is time-sensitive - they're making decisions in the next 2-3 weeks.

Can we connect for 15 minutes in the next 48 hours?

**Calendar Link:** [Insert scheduling link]
**Direct Line:** [Phone number]

Best,
[Your Name]
Ready For Robots

P.S. Score: {lead_score}/100 - You're in the top 5% of companies we track for U.S. market readiness.
"""
    
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
