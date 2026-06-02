from __future__ import annotations

import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.robot_buyer_lead import RobotBuyerLead
from app.services.resend_email import ResendEmailError, send_email_via_resend

router = APIRouter()

ROBOT_TYPES = {
    "humanoid",
    "amr_warehouse",
    "cobot_industrial",
    "service_hospitality",
    "cleaning",
    "food_processing",
    "healthcare",
    "agriculture",
    "other",
}

IMPLEMENTATION_TIMELINES = {
    "immediate_0_3mo",
    "near_term_3_6mo",
    "this_year_6_12mo",
    "next_year_12_24mo",
    "exploring",
}


class RobotBuyerLeadIn(BaseModel):
    email: str = Field(..., min_length=3, max_length=320)
    name: Optional[str] = Field(None, max_length=200)
    company: str = Field(..., min_length=1, max_length=240)
    phone: Optional[str] = Field(None, max_length=40)
    job_title: Optional[str] = Field(None, alias="jobTitle", max_length=160)
    use_case: str = Field(..., alias="useCase", min_length=10, max_length=4000)
    robot_type: str = Field(..., alias="robotType", max_length=80)
    implementation_timeline: str = Field(..., alias="implementationTimeline", max_length=80)
    source: Optional[str] = Field(None, max_length=120)
    website: Optional[str] = Field(None, max_length=200)


def _valid_email(email: str) -> bool:
    e = email.lower().strip()
    return "@" in e and "." in e.rsplit("@", 1)[-1]


def _notify_owner(row: RobotBuyerLead) -> dict:
    owner_email = (
        os.getenv("BUYER_LEAD_NOTIFY_EMAIL")
        or os.getenv("REPORT_DOWNLOAD_NOTIFY_EMAIL")
        or os.getenv("OWNER_EMAIL")
        or (os.getenv("ADMIN_EMAILS", "").split(",")[0].strip() if os.getenv("ADMIN_EMAILS") else "")
    ).strip()
    if not owner_email:
        return {"sent": False, "reason": "No owner notification email configured"}
    try:
        result = send_email_via_resend(
            to_email=owner_email,
            subject=f"New robot buyer lead — {row.company}",
            from_display_name="ReadyForRobots",
            body_text=(
                "New company looking for robots:\n\n"
                f"Company: {row.company}\n"
                f"Contact: {row.name or '-'}\n"
                f"Email: {row.email}\n"
                f"Phone: {row.phone or '-'}\n"
                f"Title: {row.job_title or '-'}\n"
                f"Robot type: {row.robot_type}\n"
                f"Timeline: {row.implementation_timeline}\n"
                f"Use case:\n{row.use_case}\n\n"
                f"Source: {row.source or '-'}\n"
                f"Lead id: {row.id}\n"
            ),
        )
        return {"sent": True, **result}
    except ResendEmailError as exc:
        return {"sent": False, "reason": str(exc)}


def _serialize(row: RobotBuyerLead) -> dict:
    return {
        "id": row.id,
        "email": row.email,
        "name": row.name,
        "company": row.company,
        "phone": row.phone,
        "jobTitle": row.job_title,
        "useCase": row.use_case,
        "robotType": row.robot_type,
        "implementationTimeline": row.implementation_timeline,
        "source": row.source,
        "createdAt": row.created_at.isoformat() if row.created_at else None,
    }


@router.post("")
def create_robot_buyer_lead(body: RobotBuyerLeadIn, db: Session = Depends(get_db)):
    if body.website and body.website.strip():
        raise HTTPException(status_code=400, detail="Invalid submission")

    email = body.email.lower().strip()
    if not _valid_email(email):
        raise HTTPException(status_code=400, detail="Valid email is required")

    robot_type = body.robot_type.strip().lower()
    if robot_type not in ROBOT_TYPES:
        raise HTTPException(status_code=400, detail="Invalid robot type")

    timeline = body.implementation_timeline.strip().lower()
    if timeline not in IMPLEMENTATION_TIMELINES:
        raise HTTPException(status_code=400, detail="Invalid implementation timeline")

    company = body.company.strip()
    use_case = body.use_case.strip()
    if not company:
        raise HTTPException(status_code=400, detail="Company is required")
    if len(use_case) < 10:
        raise HTTPException(status_code=400, detail="Please describe your use case (at least 10 characters)")

    row = RobotBuyerLead(
        email=email,
        name=(body.name or "").strip() or None,
        company=company,
        phone=(body.phone or "").strip() or None,
        job_title=(body.job_title or "").strip() or None,
        use_case=use_case,
        robot_type=robot_type,
        implementation_timeline=timeline,
        source=(body.source or "find_robots").strip() or "find_robots",
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    return {
        "ok": True,
        "lead": _serialize(row),
        "ownerNotification": _notify_owner(row),
    }
