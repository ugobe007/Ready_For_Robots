"""Generate structured sales proposal text for pipeline deals."""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def _template_proposal(
    *,
    company_name: str,
    industry: str | None,
    robot_category: str | None,
    signal: str | None,
    scout_score: int | None,
    sender_company: str,
    sender_name: str,
    sender_title: str,
) -> str:
    industry_label = industry or "your industry"
    robot = robot_category or "automation"
    signal_line = signal or "recent automation and operations signals"
    score_line = f"SCOUT score: {scout_score}/100" if scout_score is not None else "SCOUT-qualified opportunity"
    return f"""EXECUTIVE SUMMARY
{company_name} shows timely buying intent in {industry_label}. {score_line}. This proposal outlines a focused {robot} path tied to the signal we are tracking.

THE OPPORTUNITY
{company_name} is facing operational pressure reflected in this signal: {signal_line}. Teams in similar situations typically need a deployment plan that reduces labor strain, improves throughput, and creates measurable ROI within two quarters.

PROPOSED SOLUTION
We recommend a phased {robot} rollout scoped to the workflow implied by the signal — starting with one high-friction process, validating uptime and labor savings, then expanding to adjacent tasks once baseline KPIs are proven.

EXPECTED OUTCOMES
• 25–40% reduction in manual touch time on the target workflow
• Improved shift coverage without proportional headcount growth
• Clear ROI model within 90 days of pilot launch

NEXT STEPS
1. 15-minute discovery call to confirm scope and stakeholders
2. On-site or virtual workflow assessment
3. Custom ROI model and deployment recommendation

ABOUT {sender_company.upper()}
{sender_name}, {sender_title}, represents {sender_company} — we help operators in {industry_label} deploy practical robotics with signal-driven qualification and vendor-agnostic guidance.
"""


def _openai_proposal(prompt: str) -> str | None:
    api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    if not api_key:
        return None
    try:
        import openai

        client = openai.OpenAI(api_key=api_key)
        model = (os.getenv("SCOUT_PROPOSAL_MODEL") or os.getenv("SCOUT_CHAT_MODEL") or "gpt-4o-mini").strip()
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You write concise, specific B2B robotics proposals. No buzzwords."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.35,
        )
        return (resp.choices[0].message.content or "").strip() or None
    except Exception as exc:
        logger.warning("OpenAI proposal generation failed: %s", exc)
        return None


def _load_sender_footer(db: Session, uid) -> tuple[str, str, str]:
    from sqlalchemy import text

    row = db.execute(
        text("""
            SELECT sender_name, sender_title, sender_company
            FROM user_settings
            WHERE user_id = :uid
        """),
        {"uid": uid},
    ).fetchone()
    if not row:
        return ("Your Name", "Sales", "ReadyForRobots")
    m = row._mapping if hasattr(row, "_mapping") else dict(row)
    return (
        (m.get("sender_name") or "Your Name").strip() or "Your Name",
        (m.get("sender_title") or "Sales").strip() or "Sales",
        (m.get("sender_company") or "ReadyForRobots").strip() or "ReadyForRobots",
    )


def generate_proposal_text(
    db: Session,
    *,
    uid,
    company_name: str,
    industry: str | None = None,
    robot_category: str | None = None,
    signal: str | None = None,
    scout_score: int | None = None,
    contact_email: str | None = None,
) -> dict[str, Any]:
    sender_name, sender_title, sender_company = _load_sender_footer(db, uid)
    prompt = f"""Generate a professional B2B robotics proposal for:
Company: {company_name}
Industry: {industry or "Unknown"}
Robot category: {robot_category or "automation"}
Signal: {signal or "automation interest"}
Score: {scout_score or "N/A"}
Contact: {contact_email or "unknown"}
Sender: {sender_name} at {sender_company}

Sections: EXECUTIVE SUMMARY, THE OPPORTUNITY, PROPOSED SOLUTION, EXPECTED OUTCOMES (bullets), NEXT STEPS, ABOUT {sender_company.upper()}.
350-500 words. Be specific to the signal."""

    proposal = _openai_proposal(prompt) or _template_proposal(
        company_name=company_name,
        industry=industry,
        robot_category=robot_category,
        signal=signal,
        scout_score=scout_score,
        sender_company=sender_company,
        sender_name=sender_name,
        sender_title=sender_title,
    )
    return {
        "proposal": proposal,
        "company_name": company_name,
        "sender_company": sender_company,
        "sender_name": sender_name,
        "sender_title": sender_title,
        "generated_at": int(datetime.now(timezone.utc).timestamp() * 1000),
    }
