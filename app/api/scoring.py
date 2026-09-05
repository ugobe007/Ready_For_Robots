from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.score import Score

router = APIRouter()

@router.get("/scores/{company_id}")
def get_score(company_id: int, db: Session = Depends(get_db)):
    score = db.query(Score).filter(Score.company_id == company_id).first()
    if score is None:
        raise HTTPException(status_code=404, detail="Score not found")
    return {
        "company_id": score.company_id,
        "automation_score": score.automation_score,
        "labor_pain_score": score.labor_pain_score,
        "expansion_score": score.expansion_score,
        "robotics_fit_score": score.robotics_fit_score,
        "overall_intent_score": score.overall_intent_score
    }

@router.post("/recalculate/{company_id}")
def recalculate(company_id: int):
    return {"status": "queued", "company_id": company_id}

@router.put("/scores/{company_id}")
def update_score(company_id: int, company_id_body: int, db: Session = Depends(get_db)):
    db_score = db.query(Score).filter(Score.company_id == company_id).first()
    if db_score is None:
        raise HTTPException(status_code=404, detail="Score not found")
    return {"company_id": db_score.company_id, "overall_intent_score": db_score.overall_intent_score}

@router.delete("/scores/{company_id}")
def delete_score(company_id: int, db: Session = Depends(get_db)):
    db_score = db.query(Score).filter(Score.company_id == company_id).first()
    if db_score is None:
        raise HTTPException(status_code=404, detail="Score not found")
    db.delete(db_score)
    db.commit()
    return {"detail": "Score deleted successfully"}