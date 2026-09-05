"""
Admin — partner workspaces (The Robot Guild, etc.).

  GET  /api/admin/partners/the-robot-guild/trade-shows
  POST /api/admin/partners/the-robot-guild/trade-shows/refresh
"""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api.auth_deps import require_admin
from app.database import get_db
from app.models.partner_trade_show import PartnerTradeShow
from app.services.trade_show_scraper import scrape_and_upsert_trade_shows

router = APIRouter(prefix="/partners", dependencies=[Depends(require_admin)])

PARTNER_THE_ROBOT_GUILD = "the_robot_guild"


def _row_to_dict(r: PartnerTradeShow) -> Dict[str, Any]:
    return {
        "id": r.id,
        "partner_slug": r.partner_slug,
        "name": r.name,
        "summary": r.summary,
        "location": r.location,
        "start_date": r.start_date.isoformat() if r.start_date else None,
        "end_date": r.end_date.isoformat() if r.end_date else None,
        "event_url": r.event_url,
        "source_page_url": r.source_page_url,
        "exhibitor_hints": r.exhibitor_hints or [],
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "updated_at": r.updated_at.isoformat() if r.updated_at else None,
    }


@router.get("/the-robot-guild/trade-shows")
def list_the_robot_guild_trade_shows(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """Curated robot-relevant trade shows for [The Robot Guild](https://www.therobotguild.com/) partner GTM."""
    rows = (
        db.query(PartnerTradeShow)
        .filter(PartnerTradeShow.partner_slug == PARTNER_THE_ROBOT_GUILD)
        .order_by(desc(PartnerTradeShow.start_date), PartnerTradeShow.name)
        .all()
    )
    return [_row_to_dict(r) for r in rows]


@router.post("/the-robot-guild/trade-shows/refresh")
def refresh_the_robot_guild_trade_shows(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Re-fetch seed URLs, parse JSON-LD events, upsert rows.
    Best-effort exhibitor hints = OEM names found in page text (not official floor lists).
    """
    return scrape_and_upsert_trade_shows(db, partner_slug=PARTNER_THE_ROBOT_GUILD)
