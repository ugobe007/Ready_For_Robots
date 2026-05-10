from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.waitlist import WaitlistSignup

router = APIRouter()


class WaitlistSignupIn(BaseModel):
    email: str = Field(..., min_length=3, max_length=320)
    name: Optional[str] = Field(None, max_length=200)
    company: Optional[str] = Field(None, max_length=240)
    useCase: Optional[str] = Field(None, max_length=2000)
    use_case: Optional[str] = Field(None, max_length=2000)
    source: Optional[str] = Field(None, max_length=120)


@router.post("")
def create_waitlist_signup(body: WaitlistSignupIn, db: Session = Depends(get_db)):
    email = body.email.lower().strip()
    if "@" not in email or "." not in email.rsplit("@", 1)[-1]:
        raise HTTPException(status_code=400, detail="Valid email is required")

    def _apply_fields(row: WaitlistSignup) -> None:
        row.name = body.name or row.name or None
        row.company = body.company or row.company or None
        row.use_case = body.use_case or body.useCase or row.use_case or None
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
