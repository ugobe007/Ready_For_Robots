"""Admin monitor for Cal assembly judgments and supply conversion loop."""
from __future__ import annotations

from typing import Any

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.models.sales_learning import SalesExperienceEvent
from app.services.cal_assembly_agent import get_cal_assembly_status

_CONVERSION_EVENT_TYPES = (
    "supply_signup_landing",
    "supply_signup_complete",
    "supply_email_opened",
    "supply_email_clicked",
    "supply_email_bounced",
    "supply_email_complained",
)


def record_cal_assembly_rejection(
    db: Session,
    *,
    channel: str,
    issues: list[str],
    robot_company_id: int | None = None,
    company_id: int | None = None,
    vendor_name: str = "",
    subject: str = "",
) -> None:
    from app.services.sales_learning_agent import record_sales_experience

    if not issues:
        return
    record_sales_experience(
        db,
        event_type="cal_assembly_rejected",
        outcome="blocked",
        robot_company_id=robot_company_id,
        company_id=company_id,
        channel=channel,
        note="; ".join(issues[:5])[:500],
        payload={
            "issues": issues[:8],
            "vendor_name": (vendor_name or "")[:120],
            "subject": (subject or "")[:200],
        },
    )


def get_cal_ops_monitor(db: Session, *, limit: int = 25) -> dict[str, Any]:
    lim = max(1, min(int(limit), 100))
    rejections = (
        db.query(SalesExperienceEvent)
        .filter(SalesExperienceEvent.event_type == "cal_assembly_rejected")
        .order_by(desc(SalesExperienceEvent.created_at))
        .limit(lim)
        .all()
    )
    conversion_rows = (
        db.query(SalesExperienceEvent.event_type, func.count(SalesExperienceEvent.id))
        .filter(SalesExperienceEvent.event_type.in_(_CONVERSION_EVENT_TYPES))
        .group_by(SalesExperienceEvent.event_type)
        .all()
    )
    recent_conversions = (
        db.query(SalesExperienceEvent)
        .filter(SalesExperienceEvent.event_type.in_(_CONVERSION_EVENT_TYPES))
        .order_by(desc(SalesExperienceEvent.created_at))
        .limit(lim)
        .all()
    )

    return {
        "assembly": get_cal_assembly_status(),
        "assembly_rejections": [
            {
                "id": str(row.id),
                "channel": row.channel,
                "robot_company_id": row.robot_company_id,
                "company_id": row.company_id,
                "note": row.note,
                "issues": (row.payload or {}).get("issues") or [],
                "vendor_name": (row.payload or {}).get("vendor_name"),
                "subject": (row.payload or {}).get("subject"),
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in rejections
        ],
        "conversion_counts": {event_type: int(count) for event_type, count in conversion_rows},
        "recent_conversions": [
            {
                "id": str(row.id),
                "event_type": row.event_type,
                "outcome": row.outcome,
                "robot_company_id": row.robot_company_id,
                "note": row.note,
                "payload": row.payload or {},
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in recent_conversions
        ],
    }
