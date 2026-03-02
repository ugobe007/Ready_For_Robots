from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
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
def recalculate(company_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Re-fetch Google News signals for a single company, then re-score it.
    Runs in the background; returns immediately.
    """
    from app.models.company import Company
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    def _refresh(cid: int):
        from app.database import SessionLocal
        from app.models.company import Company as Co
        from app.models.score import Score as Sc
        from app.models.signal import Signal as Si
        from app.services.scoring_engine import compute_scores
        from app.services.lead_filter import clean_signals
        from app.scrapers.news_scraper import NewsScraper
        _db = SessionLocal()
        try:
            co = _db.query(Co).filter(Co.id == cid).first()
            if not co:
                return
            scraper = NewsScraper(db=_db)
            scraper.run_company_queries([co.name], max_per_company=8)
            all_sigs = _db.query(Si).filter(Si.company_id == cid).all()
            clean = clean_signals(all_sigs)
            scores = compute_scores(co, clean)
            s = _db.query(Sc).filter(Sc.company_id == cid).first()
            if not s:
                s = Sc(company_id=cid, **scores)
                _db.add(s)
            else:
                for k, v in scores.items():
                    setattr(s, k, v)
            _db.commit()
        except Exception as e:
            _db.rollback()
        finally:
            _db.close()

    background_tasks.add_task(_refresh, company_id)
    return {"status": "queued", "company_id": company_id, "company_name": company.name}

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