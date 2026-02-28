"""
Dynamic Semantic Analysis API
==============================
Endpoints for real-time ontological parsing and intent inference.

POST /analyze/text           — analyze any raw text string
POST /analyze/company/{id}   — re-score a company from its stored signals
POST /analyze/explain        — full explainability output
GET  /analyze/concepts       — list ontology concept names
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.company import Company
from app.services.inference_engine import InferenceEngine
from app.services.nlp_classifier import classify, explain
from app.services.ontology import CONCEPTS, INFERENCE_RULES, INDUSTRY_PRIORS
from app.models.score import Score

router = APIRouter(prefix="/analyze", tags=["analyze"])
_engine = InferenceEngine()


# ── Request / Response models ──────────────────────────
class TextRequest(BaseModel):
    text: str
    industry: Optional[str] = None


class MultiTextRequest(BaseModel):
    texts: List[str]
    company_name: Optional[str] = ""
    industry: Optional[str] = None


# ── Endpoints ──────────────────────────────────────────

@router.post("/text")
def analyze_text(req: TextRequest):
    """
    Analyze a single text string through the ontological inference engine.
    Returns domain scores + fired rules + activated concepts.
    """
    result = _engine.infer(req.text, industry=req.industry)
    return result.to_api_dict()


@router.post("/multi")
def analyze_multi(req: MultiTextRequest):
    """
    Analyze multiple text fragments merged together.
    Useful for combining job descriptions, press releases, and about pages.
    """
    result = _engine.infer_multi(req.texts, industry=req.industry)
    return result.to_api_dict()


@router.post("/explain")
def explain_text(req: TextRequest):
    """
    Full explainability: scores + every activated concept + matched patterns.
    """
    return explain(req.text)


@router.post("/company/{company_id}")
def analyze_company(company_id: int, db: Session = Depends(get_db)):
    """
    Re-score a company from its stored signals using the full inference engine.
    Persists updated scores to the database.
    """
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    signal_texts = [
        f"{s.signal_type or ''} {s.signal_text or ''}"
        for s in (company.signals or [])
    ]

    result = _engine.infer_from_signals(
        signal_texts,
        company_name=company.name,
        industry=company.industry
    )

    # Persist to DB
    score_data = result.to_score_dict()
    s = db.query(Score).filter(Score.company_id == company_id).first()
    if not s:
        s = Score(company_id=company_id, **score_data)
        db.add(s)
    else:
        for k, v in score_data.items():
            setattr(s, k, v)
    db.commit()

    return {
        "company_id": company_id,
        "company_name": company.name,
        **result.to_api_dict()
    }


@router.get("/concepts")
def list_concepts():
    """Return all ontology concepts grouped by domain."""
    grouped: dict = {}
    for name, c in CONCEPTS.items():
        grouped.setdefault(c.domain, []).append({
            "name": name,
            "base_weight": c.base_weight,
            "synonyms": c.synonyms,
        })
    return {"domains": grouped}


@router.get("/rules")
def list_rules():
    """Return all inference rules."""
    return {
        "rules": [
            {
                "name": r.name,
                "conditions": r.conditions,
                "conclusion_domain": r.conclusion_domain,
                "boost": r.boost,
                "description": r.description,
            }
            for r in INFERENCE_RULES
        ]
    }


@router.get("/industry-priors")
def industry_priors():
    """Return industry robotics-fit prior scores."""
    return {"industry_priors": INDUSTRY_PRIORS}
