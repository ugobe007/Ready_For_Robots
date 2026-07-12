"""Reconcile outreach delivery status from Resend when webhooks are missed.

Messages are created as ``sent`` and only advance to ``delivered`` / ``bounced`` /
``complained`` when a Resend webhook arrives. When events are missed (webhook downtime,
an unsubscribed event type, signature failures) messages get stuck at ``sent`` — which
silently corrupts the deliverability circuit breaker's denominator.

This pulls the authoritative ``last_event`` from Resend's GET /emails/{id} for a bounded
batch of stuck messages and finalizes their status. Setting a message to ``bounced`` also
enrolls its address in global suppression automatically (address_previously_bounced reads
the same status), so a reconciled bounce is never re-sent.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

# Resend last_event → our terminal OutreachMessage.status. Non-terminal events
# (sent, scheduled, queued, delivery_delayed) are intentionally left as "sent".
_TERMINAL = {
    "delivered": "delivered",
    "bounced": "bounced",
    "complained": "complained",
}


def reconcile_pending_deliveries(db, *, limit: int = 60, min_age_minutes: int = 30) -> dict:
    """Finalize up to ``limit`` messages stuck in 'sent' using Resend's authoritative status.

    Only touches messages older than ``min_age_minutes`` (a delivered/bounced event needs
    time to land). Returns a small summary; never raises into the caller.
    """
    if not (os.getenv("RESEND_API_KEY") or "").strip():
        return {"checked": 0, "updated": 0, "skipped": "no_api_key"}

    from app.models.outreach import OutreachMessage
    from app.services.resend_email import ResendEmailError, fetch_resend_email_status

    cutoff = datetime.now(timezone.utc) - timedelta(minutes=max(0, min_age_minutes))
    rows = (
        db.query(OutreachMessage)
        .filter(
            OutreachMessage.status == "sent",
            OutreachMessage.resend_id.isnot(None),
            OutreachMessage.sent_at.isnot(None),
            OutreachMessage.sent_at <= cutoff,
        )
        .order_by(OutreachMessage.sent_at.asc())
        .limit(max(1, limit))
        .all()
    )

    checked = 0
    updated = 0
    by_status: dict[str, int] = {}
    for msg in rows:
        checked += 1
        try:
            data = fetch_resend_email_status(msg.resend_id)
        except ResendEmailError as exc:
            logger.info("[reconcile] status lookup failed for %s: %s", msg.resend_id, exc)
            continue
        last_event = (data.get("last_event") or "").lower().replace("email.", "").strip()
        new_status = _TERMINAL.get(last_event)
        if not new_status or new_status == msg.status:
            continue
        msg.status = new_status
        payload = dict(msg.payload or {})
        payload["delivery_status"] = new_status
        payload["reconciled_from_resend"] = last_event
        payload["reconciled_at"] = datetime.now(timezone.utc).isoformat()
        msg.payload = payload
        updated += 1
        by_status[new_status] = by_status.get(new_status, 0) + 1

    if updated:
        db.commit()
    return {"checked": checked, "updated": updated, "by_status": by_status}
