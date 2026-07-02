"""Track vendor signup funnel from Cal supply outreach emails."""
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.services.sales_learning_agent import record_sales_experience
from app.services.site_analytics_service import EVENT_SUPPLY_SIGNUP_LANDING, record_site_event


def _parse_int(value: Any) -> int | None:
    try:
        parsed = int(str(value).strip())
        return parsed if parsed > 0 else None
    except (TypeError, ValueError):
        return None


def record_supply_signup_landing(
    db: Session,
    *,
    page: str,
    robot_company_id: int | None = None,
    message_token: str | None = None,
    utm_source: str | None = None,
    referrer: str | None = None,
    completed: bool = False,
) -> None:
    """Persist a supply-email attribution landing or completed signup."""
    event_type = "supply_signup_complete" if completed else "supply_signup_landing"
    payload = {
        "page": page,
        "robot_company_id": robot_company_id,
        "message_token": message_token,
        "utm_source": utm_source,
        "referrer": referrer,
    }
    record_site_event(
        db,
        EVENT_SUPPLY_SIGNUP_LANDING if not completed else "supply_signup_complete",
        payload,
    )
    record_sales_experience(
        db,
        event_type=event_type,
        outcome="observed" if not completed else "qualified",
        robot_company_id=robot_company_id,
        channel="web",
        payload={k: v for k, v in payload.items() if v is not None},
        note=f"Supply conversion {'completed' if completed else 'landing'} on {page}",
    )
    db.commit()


def record_supply_email_engagement(
    db: Session,
    *,
    robot_company_id: int | None,
    supply_message_id: str | None,
    event_type: str,
    data: dict[str, Any] | None = None,
) -> None:
    mapping = {
        "email.opened": ("supply_email_opened", "observed"),
        "email.clicked": ("supply_email_clicked", "observed"),
        "email.bounced": ("supply_email_bounced", "negative"),
        "email.complained": ("supply_email_complained", "negative"),
        "email.suppressed": ("supply_email_suppressed", "negative"),
    }
    mapped = mapping.get(event_type)
    if not mapped:
        return
    sales_event, outcome = mapped
    record_sales_experience(
        db,
        event_type=sales_event,
        outcome=outcome,
        robot_company_id=robot_company_id,
        channel="email",
        payload={
            "supply_outreach_message_id": supply_message_id,
            "resend_event": event_type,
            **({"reason": (data or {}).get("reason")} if (data or {}).get("reason") else {}),
        },
    )


def parse_supply_attribution(payload: dict[str, Any]) -> tuple[int | None, str | None, str | None]:
    robot_company_id = _parse_int(payload.get("robot_company_id") or payload.get("rc"))
    message_token = str(payload.get("message_token") or payload.get("msg") or "").strip() or None
    utm_source = str(payload.get("utm_source") or "").strip() or None
    return robot_company_id, message_token, utm_source
