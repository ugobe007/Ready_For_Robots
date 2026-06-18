"""
Saved proposal text + PDF export.

Mounted at prefix /api/proposals in app/main.py — routes here are relative (no /api prefix).
"""
from __future__ import annotations

import html
import io
import uuid
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.auth_deps import _require_user
from app.database import get_db

router = APIRouter()


def _uid_uuid(user: dict) -> uuid.UUID:
    return uuid.UUID(str(user["uid"]))


class ProposalUpsert(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=500)
    proposal_text: str = Field(..., min_length=1)
    company_id: Optional[int] = None
    contact_email: Optional[str] = Field(None, max_length=320)


class ProposalOut(BaseModel):
    id: str
    company_name: str
    proposal_text: str
    company_id: Optional[int] = None
    contact_email: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ProposalPdfIn(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=500)
    proposal_text: str = Field(..., min_length=1)
    robot_category: Optional[str] = Field(None, max_length=120)
    signal: Optional[str] = Field(None, max_length=500)
    scout_score: Optional[int] = Field(None, ge=0, le=100)


class ProposalGenerateIn(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=500)
    company_id: Optional[int] = None
    industry: Optional[str] = Field(None, max_length=200)
    robot_category: Optional[str] = Field(None, max_length=120)
    signal: Optional[str] = Field(None, max_length=500)
    scout_score: Optional[int] = Field(None, ge=0, le=100)
    contact_email: Optional[str] = Field(None, max_length=320)


def _row_to_proposal_out(row: Any) -> ProposalOut:
    m = row._mapping if hasattr(row, "_mapping") else dict(row)
    return ProposalOut(
        id=str(m["id"]),
        company_name=m["company_name"],
        proposal_text=m["proposal_text"],
        company_id=m.get("company_id"),
        contact_email=m.get("contact_email"),
        created_at=m["created_at"],
        updated_at=m["updated_at"],
    )


@router.post("", response_model=ProposalOut)
def upsert_proposal(
    body: ProposalUpsert,
    db: Session = Depends(get_db),
    user: dict = Depends(_require_user),
):
    uid = _uid_uuid(user)
    q = text("""
        INSERT INTO pipeline_proposals
            (id, user_id, company_id, company_name, proposal_text, contact_email, created_at, updated_at)
        VALUES
            (gen_random_uuid(), :uid, :cid, :cn, :pt, :em, now(), now())
        ON CONFLICT ON CONSTRAINT uq_pipeline_proposals_user_company_name
        DO UPDATE SET
            proposal_text = EXCLUDED.proposal_text,
            contact_email = EXCLUDED.contact_email,
            company_id = EXCLUDED.company_id,
            updated_at = now()
        RETURNING id, user_id, company_id, company_name, proposal_text, contact_email, created_at, updated_at
    """)
    row = db.execute(
        q,
        {
            "uid": uid,
            "cid": body.company_id,
            "cn": body.company_name.strip(),
            "pt": body.proposal_text,
            "em": body.contact_email,
        },
    ).fetchone()
    db.commit()
    if not row:
        raise HTTPException(status_code=500, detail="Upsert failed")
    return _row_to_proposal_out(row)


@router.get("", response_model=list[ProposalOut])
def list_proposals(
    db: Session = Depends(get_db),
    user: dict = Depends(_require_user),
):
    uid = _uid_uuid(user)
    rows = db.execute(
        text("""
            SELECT id, company_id, company_name, proposal_text, contact_email, created_at, updated_at
            FROM pipeline_proposals
            WHERE user_id = :uid
            ORDER BY updated_at DESC
        """),
        {"uid": uid},
    ).fetchall()
    return [_row_to_proposal_out(r) for r in rows]


@router.post("/generate")
def generate_proposal(
    body: ProposalGenerateIn,
    db: Session = Depends(get_db),
    user: dict = Depends(_require_user),
):
    from app.services.proposal_generator import generate_proposal_text

    uid = _uid_uuid(user)
    result = generate_proposal_text(
        db,
        uid=uid,
        company_name=body.company_name.strip(),
        industry=body.industry,
        robot_category=body.robot_category,
        signal=body.signal,
        scout_score=body.scout_score,
        contact_email=body.contact_email,
    )
    db.execute(
        text("""
            INSERT INTO pipeline_proposals
                (id, user_id, company_id, company_name, proposal_text, contact_email, created_at, updated_at)
            VALUES
                (gen_random_uuid(), :uid, :cid, :cn, :pt, :em, now(), now())
            ON CONFLICT ON CONSTRAINT uq_pipeline_proposals_user_company_name
            DO UPDATE SET
                proposal_text = EXCLUDED.proposal_text,
                contact_email = EXCLUDED.contact_email,
                company_id = EXCLUDED.company_id,
                updated_at = now()
        """),
        {
            "uid": uid,
            "cid": body.company_id,
            "cn": body.company_name.strip(),
            "pt": result["proposal"],
            "em": body.contact_email,
        },
    )
    db.commit()
    return result


def _load_sender_footer(db: Session, uid: uuid.UUID) -> tuple[str, str, str]:
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


@router.post("/pdf")
def proposal_pdf(
    body: ProposalPdfIn,
    db: Session = Depends(get_db),
    user: dict = Depends(_require_user),
):
    uid = _uid_uuid(user)
    sender_name, sender_title, sender_company = _load_sender_footer(db, uid)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=inch * 0.75,
        leftMargin=inch * 0.75,
        topMargin=inch * 0.75,
        bottomMargin=inch * 1.0,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "PropTitle",
        parent=styles["Heading1"],
        fontSize=16,
        textColor=colors.HexColor("#0f766e"),
        spaceAfter=14,
    )
    body_style = ParagraphStyle(
        "PropBody",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
    )
    footer_style = ParagraphStyle(
        "PropFooter",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.grey,
        spaceBefore=24,
    )

    story: list[Any] = []
    safe_title = html.escape(body.company_name.strip())
    story.append(Paragraph(f"Proposal — {safe_title}", title_style))
    story.append(Spacer(1, 12))

    meta_bits = []
    if body.robot_category:
        meta_bits.append(f"Category: {html.escape(body.robot_category)}")
    if body.scout_score is not None:
        meta_bits.append(f"SCOUT score: {body.scout_score}")
    if body.signal:
        meta_bits.append(f"Signal: {html.escape(body.signal[:200])}")
    if meta_bits:
        story.append(Paragraph(" · ".join(meta_bits), footer_style))
        story.append(Spacer(1, 8))

    for chunk in body.proposal_text.replace("\r\n", "\n").split("\n"):
        line = chunk.strip() or " "
        story.append(Paragraph(html.escape(line), body_style))

    footer_html = (
        f"<b>{html.escape(sender_name)}</b><br/>"
        f"{html.escape(sender_title)} · {html.escape(sender_company)}"
    )
    story.append(Paragraph(footer_html, footer_style))

    doc.build(story)
    buffer.seek(0)
    fn = "".join(c if c.isalnum() or c in "._-" else "_" for c in body.company_name.strip()[:80]) + "_proposal.pdf"
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{fn}"'},
    )


@router.get("/{proposal_id}", response_model=ProposalOut)
def get_proposal(
    proposal_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(_require_user),
):
    uid = _uid_uuid(user)
    try:
        pid = uuid.UUID(proposal_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid proposal id") from None
    row = db.execute(
        text("""
            SELECT id, company_id, company_name, proposal_text, contact_email, created_at, updated_at
            FROM pipeline_proposals
            WHERE id = :id AND user_id = :uid
        """),
        {"id": pid, "uid": uid},
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return _row_to_proposal_out(row)


@router.delete("/{proposal_id}")
def delete_proposal(
    proposal_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(_require_user),
):
    uid = _uid_uuid(user)
    try:
        pid = uuid.UUID(proposal_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid proposal id") from None
    r = db.execute(
        text("DELETE FROM pipeline_proposals WHERE id = :id AND user_id = :uid"),
        {"id": pid, "uid": uid},
    )
    db.commit()
    if r.rowcount == 0:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return {"deleted": True}
