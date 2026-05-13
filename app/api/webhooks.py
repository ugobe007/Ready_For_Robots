"""External webhooks for SCOUT outreach."""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
import re
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.crm import CrmAccount
from app.models.lead_research import UserNotification
from app.models.outreach import OutreachMessage, OutreachReply
from app.services.resend_email import ResendEmailError, fetch_resend_received_email, send_email_via_resend

router = APIRouter()


def _svix_secret_bytes(secret: str) -> bytes:
    raw = (secret or "").strip()
    if raw.startswith("whsec_"):
        raw = raw[len("whsec_") :]
    try:
        return base64.b64decode(raw)
    except Exception:
        return raw.encode("utf-8")


def _verify_resend_signature(payload: bytes, svix_id: str | None, svix_timestamp: str | None, svix_signature: str | None) -> None:
    secret = (os.getenv("RESEND_WEBHOOK_SECRET") or "").strip()
    if not secret:
        raise HTTPException(status_code=503, detail="Missing RESEND_WEBHOOK_SECRET")
    if not svix_id or not svix_timestamp or not svix_signature:
        raise HTTPException(status_code=400, detail="Missing webhook signature headers")
    signed = f"{svix_id}.{svix_timestamp}.".encode("utf-8") + payload
    expected = base64.b64encode(hmac.new(_svix_secret_bytes(secret), signed, hashlib.sha256).digest()).decode("utf-8")
    signatures = [part.split(",", 1)[1] if "," in part else part for part in svix_signature.split(" ")]
    if not any(hmac.compare_digest(expected, sig.strip()) for sig in signatures if sig.strip()):
        raise HTTPException(status_code=400, detail="Invalid webhook signature")


def _extract_addresses(value: Any) -> list[str]:
    if not value:
        return []
    if isinstance(value, str):
        values = [value]
    elif isinstance(value, list):
        values = [str(item.get("email") if isinstance(item, dict) else item) for item in value]
    else:
        values = [str(value)]
    out: list[str] = []
    for item in values:
        matches = re.findall(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", item)
        out.extend(matches or ([item.strip()] if "@" in item else []))
    return [x.lower() for x in out if x]


def _token_from_addresses(addresses: list[str]) -> str | None:
    for addr in addresses:
        local = addr.split("@", 1)[0]
        if "+" in local:
            token = local.split("+", 1)[1].strip()
            if token:
                return token
    return None


def _event_data(event: dict[str, Any]) -> dict[str, Any]:
    data = event.get("data")
    return data if isinstance(data, dict) else {}


def _fetch_received_if_needed(data: dict[str, Any]) -> dict[str, Any]:
    if data.get("text") or data.get("html") or data.get("body"):
        return data
    email_id = data.get("email_id") or data.get("id")
    if not email_id:
        return data
    try:
        fetched = fetch_resend_received_email(str(email_id))
        if isinstance(fetched, dict):
            merged = dict(data)
            merged.update(fetched)
            return merged
    except ResendEmailError:
        return data
    return data


def _notify_and_forward(db: Session, msg: OutreachMessage, reply: OutreachReply, account: CrmAccount | None) -> None:
    title = f"Reply received from {reply.from_email or 'sales opportunity'}"
    body = f"{account.name if account else 'A lead'} replied to SCOUT outreach."
    if msg.sender_user_id:
        db.add(
            UserNotification(
                user_id=msg.sender_user_id,
                company_id=msg.company_id,
                notification_type="outreach_reply",
                title=title,
                body=body,
                payload={
                    "crm_account_id": str(msg.crm_account_id),
                    "outreach_message_id": str(msg.id),
                    "outreach_reply_id": str(reply.id),
                    "from_email": reply.from_email,
                    "subject": reply.subject,
                },
            )
        )
    payload = msg.payload or {}
    forward_to = payload.get("reply_forward_email")
    if payload.get("reply_forwarding_enabled", True) and forward_to:
        try:
            send_email_via_resend(
                to_email=str(forward_to),
                subject=f"SCOUT reply: {reply.subject or account.name if account else 'outreach'}",
                body_text=(
                    f"SCOUT captured a reply from {reply.from_email or 'unknown sender'}.\n\n"
                    f"Account: {account.name if account else msg.crm_account_id}\n"
                    f"Subject: {reply.subject or ''}\n\n"
                    f"{reply.body_text or ''}"
                ),
                from_display_name="SCOUT",
                idempotency_key=f"scout-reply-forward/{reply.id}",
            )
        except Exception:
            # Keep inbound capture durable even if forwarding fails.
            pass


@router.post("/resend/inbound")
async def resend_inbound_webhook(
    request: Request,
    svix_id: str | None = Header(None, alias="svix-id"),
    svix_timestamp: str | None = Header(None, alias="svix-timestamp"),
    svix_signature: str | None = Header(None, alias="svix-signature"),
):
    payload = await request.body()
    _verify_resend_signature(payload, svix_id, svix_timestamp, svix_signature)
    event = await request.json()
    if event.get("type") != "email.received":
        return {"ok": True, "ignored": event.get("type")}
    data = _fetch_received_if_needed(_event_data(event))
    to_addresses = _extract_addresses(data.get("to") or data.get("recipients"))
    token = _token_from_addresses(to_addresses)
    if not token:
        return {"ok": True, "ignored": "no_reply_token"}

    db = SessionLocal()
    try:
        msg = db.query(OutreachMessage).filter(OutreachMessage.reply_token == token).first()
        if not msg:
            return {"ok": True, "ignored": "unknown_reply_token"}
        account = db.query(CrmAccount).filter(CrmAccount.id == msg.crm_account_id).first()
        reply = OutreachReply(
            outreach_message_id=msg.id,
            team_id=msg.team_id,
            crm_account_id=msg.crm_account_id,
            company_id=msg.company_id,
            from_email=(_extract_addresses(data.get("from")) or [None])[0],
            to_email=", ".join(to_addresses) if to_addresses else None,
            subject=data.get("subject"),
            body_text=data.get("text") or data.get("body") or data.get("html"),
            raw_payload=data,
            received_at=datetime.now(timezone.utc),
        )
        db.add(reply)
        if account:
            account.outreach_stage = "replied"
        _notify_and_forward(db, msg, reply, account)
        db.commit()
        return {"ok": True, "outreach_reply_id": str(reply.id)}
    finally:
        db.close()
