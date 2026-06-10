"""
Inline lead rescoring — used when Celery is disabled (SKIP_CELERY=1 on Fly).
"""
from __future__ import annotations

import logging
import os
from typing import Dict, Sequence

from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.score import Score
from app.models.signal import Signal
from app.services.scoring_engine import compute_scores

logger = logging.getLogger(__name__)


def skip_celery_enabled() -> bool:
    return os.getenv("SKIP_CELERY", "").strip().lower() in ("1", "true", "yes")


def rescore_companies_in_process(db: Session, company_ids: Sequence[int]) -> int:
    """Recompute Score rows for the given companies. Returns count updated."""
    ids = [int(i) for i in company_ids if i]
    if not ids:
        return 0
    updated = 0
    for cid in ids:
        company = db.query(Company).filter(Company.id == cid).first()
        if not company:
            continue
        signals = db.query(Signal).filter(Signal.company_id == company.id).all()
        if not signals:
            continue
        score_data = compute_scores(company, signals)
        score = db.query(Score).filter(Score.company_id == company.id).first()
        if not score:
            score = Score(company_id=company.id)
            db.add(score)
        score.overall_intent_score = score_data.get("overall_intent_score", 0)
        score.automation_score = score_data.get("automation_score", 0)
        score.labor_pain_score = score_data.get("labor_pain_score", 0)
        score.expansion_score = score_data.get("expansion_score", 0)
        score.robotics_fit_score = score_data.get("robotics_fit_score", 0)
        updated += 1
    if updated:
        db.commit()
    return updated


def queue_or_inline_rescore(
    db: Session,
    company_ids: Sequence[int],
    *,
    prefer_inline: bool | None = None,
) -> Dict[str, object]:
    """
    Rescore companies via Celery when available; otherwise inline (Fly default).
    """
    ids = [int(i) for i in company_ids if i]
    if not ids:
        return {"mode": "none", "updated": 0}

    inline = prefer_inline if prefer_inline is not None else skip_celery_enabled()
    if not inline:
        try:
            from worker.celery_worker import celery_app

            celery_app.send_task("worker.tasks.rescore_all_companies_task")
            return {"mode": "celery", "updated": len(ids)}
        except Exception as exc:
            logger.warning("Celery rescore failed, falling back to inline: %s", exc)

    try:
        n = rescore_companies_in_process(db, ids)
        return {"mode": "inline", "updated": n}
    except Exception as exc:
        logger.warning("Inline rescore failed: %s", exc)
        db.rollback()
        return {"mode": "failed", "updated": 0, "error": str(exc)[:200]}
