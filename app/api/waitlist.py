from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.waitlist import WaitlistSignup
from app.services.cal_autonomy import get_cal_review_email

router = APIRouter()


class WaitlistSignupIn(BaseModel):
    email: str = Field(..., min_length=3, max_length=320)
    name: Optional[str] = Field(None, max_length=200)
    company: Optional[str] = Field(None, max_length=240)
    use_case: Optional[str] = Field(None, alias="useCase", max_length=2000)
    source: Optional[str] = Field(None, max_length=120)


class FoundingCustomerIn(BaseModel):
    email: str = Field(..., min_length=3, max_length=320)
    company: str = Field(..., min_length=1, max_length=240)
    name: Optional[str] = Field(None, max_length=200)


@router.post("")
def create_waitlist_signup(body: WaitlistSignupIn, db: Session = Depends(get_db)):
    email = body.email.lower().strip()
    if "@" not in email or "." not in email.rsplit("@", 1)[-1]:
        raise HTTPException(status_code=400, detail="Valid email is required")

    def _apply_fields(row: WaitlistSignup) -> None:
        row.name = body.name or row.name or None
        row.company = body.company or row.company or None
        row.use_case = body.use_case or row.use_case or None
        row.source = body.source or row.source or "pricing"

    row = db.query(WaitlistSignup).filter(WaitlistSignup.email == email).first()
    if row is None:
        row = WaitlistSignup(email=email)
        db.add(row)
    _apply_fields(row)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        row = db.query(WaitlistSignup).filter(WaitlistSignup.email == email).first()
        if row is None:
            raise HTTPException(status_code=409, detail="Signup conflict, please retry")
        _apply_fields(row)
        db.commit()
    db.refresh(row)
    return {
        "ok": True,
        "signup": {
            "id": row.id,
            "email": row.email,
            "name": row.name,
            "company": row.company,
            "useCase": row.use_case,
            "source": row.source,
            "createdAt": row.created_at.isoformat() if row.created_at else None,
        },
    }


def _notify_founding_customer(*, email: str, company: str, name: Optional[str]) -> bool:
    admin_email = get_cal_review_email()
    if not admin_email:
        return False
    from app.services.resend_email import ResendEmailError, send_email_via_resend

    subject = f"Founding customer inquiry — {company}"
    body = f"""New founding customer request from /pricing

Email: {email}
Company: {company}
Name: {name or "(not provided)"}

Follow up to discuss Premium workspace and founding terms.
"""
    try:
        send_email_via_resend(
            to_email=admin_email,
            subject=subject,
            body_text=body,
            from_display_name="Ready For Robots · leads",
            reply_to=email,
            idempotency_key=f"founding-customer/{email.lower()}",
        )
        return True
    except ResendEmailError:
        return False


@router.post("/founding-customer")
def create_founding_customer(body: FoundingCustomerIn, db: Session = Depends(get_db)):
    email = body.email.lower().strip()
    company = body.company.strip()
    if "@" not in email or "." not in email.rsplit("@", 1)[-1]:
        raise HTTPException(status_code=400, detail="Valid email is required")
    if not company:
        raise HTTPException(status_code=400, detail="Company is required")

    row = db.query(WaitlistSignup).filter(WaitlistSignup.email == email).first()
    if row is None:
        row = WaitlistSignup(email=email)
        db.add(row)
    row.name = body.name or row.name or None
    row.company = company or row.company or None
    row.use_case = row.use_case or "Founding customer — Premium workspace"
    row.source = "founding_customer"
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        row = db.query(WaitlistSignup).filter(WaitlistSignup.email == email).first()
        if row is None:
            raise HTTPException(status_code=409, detail="Signup conflict, please retry")
        row.name = body.name or row.name or None
        row.company = company or row.company or None
        row.use_case = row.use_case or "Founding customer — Premium workspace"
        row.source = "founding_customer"
        db.commit()
    db.refresh(row)

    notified = _notify_founding_customer(email=email, company=company, name=body.name)
    return {
        "ok": True,
        "notified": notified,
        "signup": {
            "id": row.id,
            "email": row.email,
            "name": row.name,
            "company": row.company,
            "source": row.source,
            "createdAt": row.created_at.isoformat() if row.created_at else None,
        },
    }
