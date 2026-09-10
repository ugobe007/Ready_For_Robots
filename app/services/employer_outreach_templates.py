"""
Employer Demand-Side Outreach Templates for Ready For Robots
Targeting VPs of Operations, Directors of Automation, General Managers, and Supply Chain Leads.

Leverages:
1. RaaS vs. CapEx Financial Engine ($8,500/mo RaaS vs $200,000 CapEx)
2. Shift Multiplier & Speed Parity Math (1, 2, 3 Shifts)
3. Robot Job Placement & Automation Feasibility Audit
"""
from typing import Dict, Optional


def _format_greeting(contact_name: Optional[str], company_name: str) -> str:
    if contact_name and contact_name.strip() and contact_name.lower() != "decision maker":
        first_name = contact_name.strip().split()[0]
        return f"Hi {first_name},"
    if company_name and company_name.strip():
        return f"Hi {company_name} Operations Team,"
    return "Hello,"


def generate_raas_economics_email(
    company_name: str,
    contact_name: Optional[str] = None,
    job_title: Optional[str] = None,
    robot_task: Optional[str] = "palletizing and material handling",
    current_shifts: int = 2,
) -> Dict[str, str]:
    """
    Angle 1: Financial & RaaS vs. CapEx Economics (CFO / VP of Operations)
    Highlights: $8,500/mo RaaS option vs $200k CapEx, shift multipliers, zero upfront balance sheet friction.
    """
    greeting = _format_greeting(contact_name, company_name)
    title_context = f"in your role as {job_title}" if job_title else "leading operations"
    
    subject = f"The $8,500/mo RaaS vs. CapEx math for {company_name}"
    
    body = f"""{greeting}

I noticed your team's footprint at {company_name}, and wanted to share a financial model that's changing how enterprise logistics leaders evaluate automated jobs.

Most robotics distributors still pitch $200,000+ upfront CapEx purchases with long payback windows. But with recent humanoid and mobile RaaS (Robots-as-a-Service) options—now standardized around ~$8,500/month—the ROI calculation shifts dramatically:

• Single-Shift Operating Expense: ~$8.5k/mo lowers upfront capital risk and keeps equipment off balance-sheet debt.
• Multi-Shift Advantage ({current_shifts} shifts): Running {current_shifts} shifts drops the effective hourly robot cost to under $18/hr—beating local turnover and overtime costs.
• 5-Year TCO Comparison: $535k total RaaS spend vs $400k CapEx purchase, giving {company_name} flexibility as hardware rapidly evolves.

We built an interactive RaaS vs CapEx ROI engine to model exact payload, shift counts, and speed-parity metrics for {robot_task}.

Would you be open to reviewing a custom 2-minute ROI breakdown for {company_name}?

Best regards,

Cal | Ready For Robots Demand Team
https://www.readyforrobots.com/roi-calculator
"""
    return {
        "subject": subject,
        "body": body,
        "target_persona": "VP Operations / CFO",
        "angle": "RaaS Financial Economics"
    }


def generate_unfilled_robot_job_email(
    company_name: str,
    contact_name: Optional[str] = None,
    job_title: Optional[str] = None,
    facility_location: Optional[str] = None,
    task_description: Optional[str] = "case picking and palletizing",
) -> Dict[str, str]:
    """
    Angle 2: Operational Friction & Unfilled Robot Jobs (Director of Automation / Plant Manager)
    Highlights: High labor turnover, hard-to-staff shift vacancies, task-matched hardware qualified in days.
    """
    greeting = _format_greeting(contact_name, company_name)
    location_str = f" at your {facility_location} facility" if facility_location else ""
    
    subject = f"Replacing hard-to-staff {task_description} shifts at {company_name}"
    
    body = f"""{greeting}

I'm reaching out because high warehouse turnover and rising overtime costs are forcing operations leaders to rethink how repetitive manual shifts get filled{location_str}.

At Ready For Robots, we work directly with enterprise employers to map specific 'robot jobs'—like {task_description}—to qualified hardware and deployment-ready integrators.

Rather than spending months evaluating fragmented distributors who don't understand the technology, we provide:

1. Exact Task Feasibility: Direct payload, reach, and speed-parity matching against proven OEM hardware.
2. Verified RaaS Availability: Deployment-ready units available at ~$8,500/mo without 12-month procurement delays.
3. Turnkey ROI Benchmark: Immediate comparison of human hourly rates vs. single/multi-shift robotic OpEx.

Are you available for a 15-minute operational alignment call next week to see matched options for {company_name}?

Best,

Cal | Ready For Robots
https://www.readyforrobots.com
"""
    return {
        "subject": subject,
        "body": body,
        "target_persona": "Director of Automation / Plant Manager",
        "angle": "Unfilled Robot Jobs & Operations"
    }


def generate_no_capex_pilot_email(
    company_name: str,
    contact_name: Optional[str] = None,
    job_title: Optional[str] = None,
    workflow_name: Optional[str] = "end-of-line palletizing and sorting",
) -> Dict[str, str]:
    """
    Angle 3: Low-Risk Audit / Pilot (Supply Chain VP / General Manager)
    Highlights: Review-first, zero-risk assessment of automated jobs with live performance benchmarks.
    """
    greeting = _format_greeting(contact_name, company_name)
    
    subject = f"Feasibility audit for automating {workflow_name} at {company_name}"
    
    body = f"""{greeting}

Most automation proposals stall because local distributors force heavy upfront commitments before you see real floor metrics.

We're taking a different approach for {company_name}: an objective, 5-minute automation feasibility audit for {workflow_name}.

We evaluate three core metrics up front:
• Shift Breakeven Point: Determining exact shift thresholds where robotic OpEx beats manual labor.
• Speed & Throughput Parity: Calculating required unit-per-hour output vs. human baseline.
• OEM RaaS Terms: Securing guaranteed ~$8.5k/mo RaaS rates with included software and maintenance.

If useful, I can send a custom financial & technical audit document formatted specifically for {company_name}'s review—no sales call required first.

Would you like me to send over the audit outline?

Best,

Cal | Ready For Robots
https://www.readyforrobots.com/roi-calculator
"""
    return {
        "subject": subject,
        "body": body,
        "target_persona": "VP Supply Chain / General Manager",
        "angle": "No-CapEx Feasibility Audit"
    }


def get_employer_outreach_sequence(
    company_name: str,
    contact_name: Optional[str] = None,
    job_title: Optional[str] = None,
    task_description: Optional[str] = None,
) -> Dict[str, Dict[str, str]]:
    """
    Generate complete 3-step outreach sequence for an employer target.
    """
    return {
        "touch_1_financial": generate_raas_economics_email(company_name, contact_name, job_title, task_description),
        "touch_2_operations": generate_unfilled_robot_job_email(company_name, contact_name, job_title, task_description=task_description),
        "touch_3_audit": generate_no_capex_pilot_email(company_name, contact_name, job_title, workflow_name=task_description),
    }
