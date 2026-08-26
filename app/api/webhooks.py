"""External webhooks for Cal outreach in SCOUT workflows."""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
import re
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.crm import CrmAccount
from app.models.lead_research import UserNotification
from app.models.outreach import OutreachMessage, OutreachReply
from app.models.robot_company import RobotCompany
from app.models.supply_outreach import SupplyOutreachMessage, SupplyOutreachReply
from app.services.resend_email import ResendEmailError, fetch_resend_received_email, send_email_via_resend
from app.services.sales_learning_agent import record_sales_experience
from app.services.sales_agent import handle_crm_reply_first_response, handle_supply_reply_first_response

router = APIRouter()

DELIVERY_EVENT_TYPES = {
    "email.sent",
    "email.delivered",
    "email.delivery_delayed",
    "email.opened",
    "email.clicked",
    "email.bounced",
    "email.complained",
    "email.suppressed",
}

DELIVERY_STATUS_BY_EVENT = {
    "email.sent": "sent",
    "email.delivered": "delivered",
    "email.delivery_delayed": "delivery_delayed",
    "email.opened": "opened",
    "email.clicked": "clicked",
    "email.bounced": "bounced",
    "email.complained": "complained",
    "email.suppressed": "suppressed",
}


def _uuid_for_session(db: Session):
    value = uuid.uuid4()
    bind = db.get_bind()
    if bind is not None and bind.dialect.name == "sqlite":
        return str(value)
    return value


def _svix_secret_bytes(secret: str) -> bytes:
    raw = (secret or "").strip()
    if raw.startswith("whsec_"):
        raw = raw[len("whsec_") :]
    try:
        return base64.b64decode(raw)
    except Exception:
        return raw.encode("utf-8")


def _verify_resend_signature(
    payload: bytes,
    svix_id: str | None,
    svix_timestamp: str | None,
    svix_signature: str | None,
    secret_env: str = "RESEND_WEBHOOK_SECRET",
) -> None:
    """Verify a Svix-signed Resend webhook.

    Each Resend webhook endpoint has its own signing secret. Pass `secret_env`
    to select the right env var:
    - Delivery events  → RESEND_WEBHOOK_SECRET  (default)
    - Inbound emails   → RESEND_INBOUND_WEBHOOK_SECRET (falls back to RESEND_WEBHOOK_SECRET)
    """
    # Prefer the specific secret; fall back to the shared one.
    secret = (os.getenv(secret_env) or os.getenv("RESEND_WEBHOOK_SECRET") or "").strip()
    if not secret:
        raise HTTPException(
            status_code=503,
            detail=f"Missing {secret_env} (or RESEND_WEBHOOK_SECRET) — set it in Fly.io secrets",
        )
    if not svix_id or not svix_timestamp or not svix_signature:
        raise HTTPException(status_code=400, detail="Missing webhook signature headers")
    signed = f"{svix_id}.{svix_timestamp}.".encode("utf-8") + payload
    expected = base64.b64encode(hmac.new(_svix_secret_bytes(secret), signed, hashlib.sha256).digest()).decode("utf-8")
    signatures = [part.split(",", 1)[1] if "," in part else part for part in svix_signature.split(" ")]
    if not any(hmac.compare_digest(expected, sig.strip()) for sig in signatures if sig.strip()):
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid webhook signature. If this is the inbound webhook, set "
                "RESEND_INBOUND_WEBHOOK_SECRET in Fly.io secrets to the signing secret "
                "shown on your Resend inbound webhook endpoint (different from delivery webhooks)."
            ),
        )


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


def _event_email_id(data: dict[str, Any]) -> str | None:
    value = data.get("email_id") or data.get("id")
    return str(value) if value else None


def _event_time() -> str:
    return datetime.now(timezone.utc).isoformat()


def _extract_problem_detail(data: dict[str, Any]) -> dict[str, Any]:
    """Pull the reason + hard/soft type from a Resend bounce/complaint/suppression.

    Resend nests these under ``data['bounce']`` / ``data['complaint']`` (with keys
    ``message``, ``type`` = Permanent|Transient|Undetermined, ``subType``) rather than
    at the top level — which is why ``problem_reason`` was always empty ("unknown")
    before. Falls back to top-level fields for older/flat payload shapes.
    """
    for key in ("bounce", "complaint", "failed"):
        obj = data.get(key)
        if isinstance(obj, dict):
            return {
                "reason": obj.get("message") or obj.get("description") or obj.get("reason"),
                "type": obj.get("type"),
                "subtype": obj.get("subType") or obj.get("sub_type") or obj.get("subtype"),
            }
    return {
        "reason": data.get("reason") or data.get("message") or data.get("error"),
        "type": data.get("type"),
        "subtype": data.get("subType") or data.get("sub_type"),
    }


def _delivery_payload(payload: dict[str, Any] | None, event_type: str, data: dict[str, Any]) -> dict[str, Any]:
    next_payload = dict(payload or {})
    events = list(next_payload.get("delivery_events") or [])
    events.append(
        {
            "type": event_type,
            "status": DELIVERY_STATUS_BY_EVENT.get(event_type, event_type.replace("email.", "")),
            "at": _event_time(),
            "to": _extract_addresses(data.get("to") or data.get("recipient") or data.get("recipients")),
            "reason": data.get("reason") or data.get("message") or data.get("error"),
        }
    )
    next_payload["delivery_events"] = events[-20:]
    next_payload["delivery_status"] = DELIVERY_STATUS_BY_EVENT.get(event_type, "tracked")
    if event_type == "email.delivered":
        next_payload["delivered_at"] = events[-1]["at"]
    elif event_type == "email.opened":
        next_payload["opened_at"] = events[-1]["at"]
    elif event_type == "email.clicked":
        next_payload["clicked_at"] = events[-1]["at"]
    elif event_type in {"email.bounced", "email.complained", "email.suppressed"}:
        detail = _extract_problem_detail(data)
        reason = detail.get("reason") or events[-1]["reason"] or "unknown"
        events[-1]["reason"] = reason
        ptype = (detail.get("type") or "").strip()
        next_payload["problem_at"] = events[-1]["at"]
        next_payload["problem_reason"] = reason
        if ptype:
            next_payload["problem_type"] = ptype
        if detail.get("subtype"):
            next_payload["problem_subtype"] = detail["subtype"]
        # Complaints are always terminal; bounces split hard (Permanent) vs soft.
        if event_type == "email.complained":
            next_payload["problem_class"] = "hard"
        elif ptype:
            next_payload["problem_class"] = "hard" if ptype.lower().startswith("perm") else "soft"
        else:
            next_payload["problem_class"] = "unknown"
    return next_payload


def _role_inbox_alternates(bounced: list[str], attempted: list[str]) -> list[str]:
    domains = []
    for email in bounced or attempted:
        if "@" in email:
            domain = email.rsplit("@", 1)[1].lower()
            if domain and domain not in domains:
                domains.append(domain)
    attempted_set = {email.lower() for email in attempted}
    alternates: list[str] = []
    for domain in domains:
        for local in ("partnerships", "events", "marketing", "sales"):
            candidate = f"{local}@{domain}"
            if candidate not in attempted_set and candidate not in alternates:
                alternates.append(candidate)
    return alternates


def _buyer_contact_alternates(bounced: list[str], attempted: list[str]) -> list[str]:
    domains = []
    for email in bounced or attempted:
        if "@" in email:
            domain = email.rsplit("@", 1)[1].lower()
            if domain and domain not in domains:
                domains.append(domain)
    attempted_set = {email.lower() for email in attempted}
    alternates: list[str] = []
    for domain in domains:
        for local in ("operations", "facilities", "procurement", "automation", "info"):
            candidate = f"{local}@{domain}"
            if candidate not in attempted_set and candidate not in alternates:
                alternates.append(candidate)
    return alternates


def _reply_to_with_new_token(reply_to: str | None, token: str) -> str | None:
    if not reply_to or "@" not in reply_to:
        return reply_to
    local, domain = reply_to.rsplit("@", 1)
    if "+" in local:
        local = local.split("+", 1)[0]
    return f"{local}+{token}@{domain}"


def _find_supply_crm_message(db: Session, supply_msg: SupplyOutreachMessage) -> OutreachMessage | None:
    if not supply_msg.resend_id:
        return None
    return db.query(OutreachMessage).filter(OutreachMessage.resend_id == supply_msg.resend_id).first()


def _notify_supply_delivery_problem(
    db: Session,
    supply_msg: SupplyOutreachMessage,
    crm_msg: OutreachMessage | None,
    problem: str,
    attempted_resend_to: str | None,
) -> None:
    if not crm_msg or not crm_msg.sender_user_id:
        return
    db.add(
        UserNotification(
            user_id=crm_msg.sender_user_id,
            notification_type="supply_outreach_delivery_problem",
            title="Cal found a delivery problem",
            body=(
                f"{problem} for {supply_msg.subject}. "
                + (f"Cal resent to {attempted_resend_to}." if attempted_resend_to else "No unused alternate email address was available.")
            ),
            payload={
                "supply_outreach_message_id": str(supply_msg.id),
                "outreach_message_id": str(crm_msg.id),
                "attempted_resend_to": attempted_resend_to,
            },
        )
    )


def _notify_crm_delivery_problem(db: Session, crm_msg: OutreachMessage, event_type: str, data: dict[str, Any]) -> None:
    if not crm_msg.sender_user_id:
        return
    status = DELIVERY_STATUS_BY_EVENT.get(event_type, "delivery_problem")
    reason = data.get("reason") or data.get("message") or data.get("error")
    db.add(
        UserNotification(
            user_id=crm_msg.sender_user_id,
            company_id=crm_msg.company_id,
            notification_type="outreach_delivery_problem",
            title="Cal found a delivery problem",
            body=(
                f"Cal saw {status} for {crm_msg.subject}. "
                "Review the CRM account and add another verified email address before resending."
            ),
            payload={
                "outreach_message_id": str(crm_msg.id),
                "crm_account_id": str(crm_msg.crm_account_id),
                "status": status,
                "reason": reason,
            },
        )
    )


def _handle_crm_delivery_problem(
    db: Session,
    crm_msg: OutreachMessage,
    event_type: str,
    data: dict[str, Any],
) -> None:
    payload = dict(crm_msg.payload or {})
    attempts = int(payload.get("automated_resend_attempts") or 0)
    bounced = _extract_addresses(data.get("to") or data.get("recipient") or data.get("recipients")) or [crm_msg.to_email]
    attempted = list({crm_msg.to_email.lower(), *(email.lower() for email in payload.get("attempted_recipients", []))})
    alternate = None
    problem = DELIVERY_STATUS_BY_EVENT.get(event_type, "delivery_problem")
    # Hardened: do NOT auto-resend to guessed role inboxes (operations@/info@/…).
    # Guessed mailboxes were the dominant bounce class and create bounce loops that
    # damage sender reputation. Cal contacts only verified addresses; on bounce we
    # record the problem and notify to add another verified contact.
    _ = (attempts, bounced, attempted)  # retained for payload/notify context
    if alternate:
        try:
            reply_token = f"{crm_msg.reply_token}-r{attempts + 1}"
            reply_to = _reply_to_with_new_token(crm_msg.reply_to, reply_token)
            send_result = send_email_via_resend(
                to_email=alternate,
                subject=crm_msg.subject,
                body_text=crm_msg.body_text,
                from_display_name="Cal",
                reply_to=reply_to,
                idempotency_key=f"crm-bounce-resend/{crm_msg.id}/{alternate}",
            )
            resend_msg = OutreachMessage(
                id=_uuid_for_session(db),
                team_id=crm_msg.team_id,
                crm_account_id=crm_msg.crm_account_id,
                company_id=crm_msg.company_id,
                sender_user_id=crm_msg.sender_user_id,
                to_email=alternate,
                from_email=send_result.get("from_email"),
                reply_to=reply_to,
                reply_token=reply_token,
                subject=crm_msg.subject,
                body_text=crm_msg.body_text,
                send_identity=crm_msg.send_identity,
                resend_id=send_result.get("resend_id"),
                status="resent",
                payload={
                    **payload,
                    "source": "crm_auto_resend",
                    "parent_outreach_message_id": str(crm_msg.id),
                    "trigger_event": event_type,
                    "delivery_status": "resent",
                    "attempted_recipients": [*attempted, alternate],
                },
                sent_at=datetime.now(timezone.utc),
            )
            db.add(resend_msg)
            payload["automated_resend_attempts"] = attempts + 1
            payload["automated_resend_to"] = alternate
            payload["cal_delivery_action"] = f"Resent to {alternate} after {problem}."
        except ResendEmailError as exc:
            payload["cal_delivery_action"] = f"Cal tried to resend after {problem}, but Resend rejected the alternate send: {exc}"
            alternate = None
    else:
        payload["cal_delivery_action"] = f"Cal found {problem}, but no unused alternate email address was available."
    crm_msg.payload = payload
    _notify_crm_delivery_problem(db, crm_msg, event_type, data)


def _handle_supply_delivery_problem(
    db: Session,
    supply_msg: SupplyOutreachMessage,
    event_type: str,
    data: dict[str, Any],
) -> None:
    payload = dict(supply_msg.payload or {})
    attempts = int(payload.get("automated_resend_attempts") or 0)
    bounced = _extract_addresses(data.get("to") or data.get("recipient") or data.get("recipients")) or list(supply_msg.to_emails or [])
    attempted = list({*(email.lower() for email in (supply_msg.to_emails or [])), *(email.lower() for email in payload.get("attempted_recipients", []))})
    alternate = None
    problem = DELIVERY_STATUS_BY_EVENT.get(event_type, "delivery_problem")
    if attempts < 2:
        alternates = _role_inbox_alternates(bounced, attempted)
        alternate = alternates[0] if alternates else None
    crm_msg = _find_supply_crm_message(db, supply_msg)
    if alternate:
        try:
            send_result = send_email_via_resend(
                to_email=alternate,
                subject=supply_msg.subject,
                body_text=supply_msg.body_text,
                from_display_name="Cal",
                reply_to=supply_msg.reply_to,
                idempotency_key=f"supply-bounce-resend/{supply_msg.id}/{alternate}",
            )
            resend_msg = SupplyOutreachMessage(
                id=_uuid_for_session(db),
                robot_company_id=supply_msg.robot_company_id,
                to_emails=[alternate],
                from_email=send_result.get("from_email"),
                reply_to=supply_msg.reply_to,
                reply_token=f"{supply_msg.reply_token}-r{attempts + 1}",
                subject=supply_msg.subject,
                body_text=supply_msg.body_text,
                template_type=supply_msg.template_type,
                resend_id=send_result.get("resend_id"),
                status="resent",
                is_test=False,
                payload={
                    "source": "supply_pipeline_auto_resend",
                    "parent_supply_outreach_message_id": str(supply_msg.id),
                    "trigger_event": event_type,
                    "delivery_status": "resent",
                    "attempted_recipients": [*attempted, alternate],
                },
                approved_at=datetime.now(timezone.utc),
                sent_at=datetime.now(timezone.utc),
            )
            db.add(resend_msg)
            payload["automated_resend_attempts"] = attempts + 1
            payload["automated_resend_to"] = alternate
            payload["cal_delivery_action"] = f"Resent to {alternate} after {problem}."
        except ResendEmailError as exc:
            payload["cal_delivery_action"] = f"Cal tried to resend after {problem}, but Resend rejected the alternate send: {exc}"
            alternate = None
    else:
        payload["cal_delivery_action"] = f"Cal found {problem}, but no unused alternate email address was available."
    supply_msg.payload = payload
    _notify_supply_delivery_problem(db, supply_msg, crm_msg, problem, alternate)


def _capture_delivery_event(db: Session, event_type: str, data: dict[str, Any]) -> dict[str, Any]:
    resend_id = _event_email_id(data)
    if not resend_id:
        return {"ok": True, "ignored": "missing_email_id"}
    status = DELIVERY_STATUS_BY_EVENT.get(event_type, "tracked")
    supply_msg = db.query(SupplyOutreachMessage).filter(SupplyOutreachMessage.resend_id == resend_id).first()
    crm_msg = db.query(OutreachMessage).filter(OutreachMessage.resend_id == resend_id).first()
    if not supply_msg and not crm_msg:
        return {"ok": True, "ignored": "unknown_resend_id", "resend_id": resend_id}
    if supply_msg:
        supply_msg.status = status
        supply_msg.payload = _delivery_payload(supply_msg.payload, event_type, data)
        if event_type in {"email.opened", "email.clicked", "email.bounced", "email.complained", "email.suppressed"}:
            from app.services.supply_conversion import record_supply_email_engagement

            record_supply_email_engagement(
                db,
                robot_company_id=supply_msg.robot_company_id,
                supply_message_id=str(supply_msg.id),
                event_type=event_type,
                data=data,
            )
        if event_type in {"email.bounced", "email.complained", "email.suppressed"}:
            _handle_supply_delivery_problem(db, supply_msg, event_type, data)
    if crm_msg:
        crm_msg.status = status
        crm_msg.payload = _delivery_payload(crm_msg.payload, event_type, data)
        if not supply_msg and event_type in {"email.bounced", "email.complained", "email.suppressed"}:
            _handle_crm_delivery_problem(db, crm_msg, event_type, data)
    db.commit()
    return {"ok": True, "event": event_type, "status": status, "resend_id": resend_id}


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
    body = f"{account.name if account else 'A lead'} replied to Cal. Review the thread and decide whether the next step should be handled by Cal, Max, or you."
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
                subject=f"Cal reply: {reply.subject or account.name if account else 'outreach'}",
                body_text=(
                    f"Cal captured a reply from {reply.from_email or 'unknown sender'}.\n\n"
                    f"Account: {account.name if account else msg.crm_account_id}\n"
                    f"Subject: {reply.subject or ''}\n\n"
                    "Use the admin workflow queue to decide the next step.\n\n"
                    f"{reply.body_text or ''}"
                ),
                from_display_name="Cal",
                idempotency_key=f"scout-reply-forward/{reply.id}",
            )
        except Exception:
            # Keep inbound capture durable even if forwarding fails.
            pass


def _notify_supply_and_forward(
    db: Session,
    supply_msg: SupplyOutreachMessage,
    reply: SupplyOutreachReply,
    robot_company: RobotCompany | None,
    crm_msg: OutreachMessage | None,
) -> None:
    if not crm_msg:
        return
    title = f"Robot-company reply from {reply.from_email or 'prospect'}"
    account_name = robot_company.company_name if robot_company else supply_msg.subject
    body = f"{account_name} replied to Cal. Review the thread and decide the next step."
    if crm_msg.sender_user_id:
        db.add(
            UserNotification(
                user_id=crm_msg.sender_user_id,
                notification_type="supply_outreach_reply",
                title=title,
                body=body,
                payload={
                    "robot_company_id": supply_msg.robot_company_id,
                    "supply_outreach_message_id": str(supply_msg.id),
                    "supply_outreach_reply_id": str(reply.id),
                    "from_email": reply.from_email,
                    "subject": reply.subject,
                },
            )
        )
    payload = crm_msg.payload or {}
    forward_to = payload.get("reply_forward_email")
    if payload.get("reply_forwarding_enabled", True) and forward_to:
        try:
            send_email_via_resend(
                to_email=str(forward_to),
                subject=f"Cal supply reply: {reply.subject or account_name}",
                body_text=(
                    f"Cal captured a robot-company reply from {reply.from_email or 'unknown sender'}.\n\n"
                    f"Robot company: {account_name}\n"
                    f"Subject: {reply.subject or ''}\n\n"
                    "Use the ReadyForRobots Inbox or Sales Console to decide the next step.\n\n"
                    f"{reply.body_text or ''}"
                ),
                from_display_name="Cal",
                idempotency_key=f"supply-reply-forward/{reply.id}",
            )
        except Exception:
            # Preserve inbound capture even if forwarding fails.
            pass


def _capture_supply_reply(
    db: Session,
    msg: SupplyOutreachMessage,
    data: dict[str, Any],
    to_addresses: list[str],
) -> SupplyOutreachReply:
    reply = SupplyOutreachReply(
        supply_outreach_message_id=msg.id,
        robot_company_id=msg.robot_company_id,
        from_email=(_extract_addresses(data.get("from")) or [None])[0],
        to_email=", ".join(to_addresses) if to_addresses else None,
        subject=data.get("subject"),
        body_text=data.get("text") or data.get("body") or data.get("html"),
        raw_payload=data,
        received_at=datetime.now(timezone.utc),
    )
    db.add(reply)
    msg.status = "replied"
    db.flush()
    return reply


@router.post("/resend/delivery")
async def resend_delivery_webhook(
    request: Request,
    svix_id: str | None = Header(None, alias="svix-id"),
    svix_timestamp: str | None = Header(None, alias="svix-timestamp"),
    svix_signature: str | None = Header(None, alias="svix-signature"),
):
    """Outbound delivery events (sent, delivered, opened, clicked, bounced)."""
    payload = await request.body()
    _verify_resend_signature(payload, svix_id, svix_timestamp, svix_signature, secret_env="RESEND_WEBHOOK_SECRET")
    event = await request.json()
    event_type = str(event.get("type") or "")
    if event_type not in DELIVERY_EVENT_TYPES:
        return {"ok": True, "ignored": event_type}
    db = SessionLocal()
    try:
        return _capture_delivery_event(db, event_type, _event_data(event))
    finally:
        db.close()


@router.post("/resend/inbound")
async def resend_inbound_webhook(
    request: Request,
    svix_id: str | None = Header(None, alias="svix-id"),
    svix_timestamp: str | None = Header(None, alias="svix-timestamp"),
    svix_signature: str | None = Header(None, alias="svix-signature"),
):
    payload = await request.body()
    _verify_resend_signature(payload, svix_id, svix_timestamp, svix_signature, secret_env="RESEND_INBOUND_WEBHOOK_SECRET")
    event = await request.json()
    event_type = event.get("type")
    data = _event_data(event)
    if event_type in DELIVERY_EVENT_TYPES:
        db = SessionLocal()
        try:
            return _capture_delivery_event(db, str(event_type), data)
        finally:
            db.close()
    if event_type != "email.received":
        return {"ok": True, "ignored": event_type}
    data = _fetch_received_if_needed(data)
    to_addresses = _extract_addresses(data.get("to") or data.get("recipients"))
    token = _token_from_addresses(to_addresses)
    if not token:
        return {"ok": True, "ignored": "no_reply_token"}

    db = SessionLocal()
    try:
        # Idempotency: use svix_id (unique per Resend delivery attempt) stored in
        # raw_payload to reject duplicate webhook deliveries on Resend retries.
        if svix_id:
            existing_crm = (
                db.query(OutreachReply)
                .filter(OutreachReply.raw_payload["_svix_id"].astext == svix_id)
                .first()
            )
            if existing_crm:
                return {"ok": True, "deduplicated": True, "outreach_reply_id": str(existing_crm.id)}
            existing_supply = (
                db.query(SupplyOutreachReply)
                .filter(SupplyOutreachReply.raw_payload["_svix_id"].astext == svix_id)
                .first()
            )
            if existing_supply:
                return {"ok": True, "deduplicated": True, "supply_outreach_reply_id": str(existing_supply.id)}

        msg = db.query(OutreachMessage).filter(OutreachMessage.reply_token == token).first()
        if not msg:
            supply_msg = (
                db.query(SupplyOutreachMessage)
                .filter(SupplyOutreachMessage.reply_token == token)
                .first()
            )
            if supply_msg:
                crm_msg = _find_supply_crm_message(db, supply_msg)
                supply_reply = _capture_supply_reply(db, supply_msg, {**data, "_svix_id": svix_id or ""}, to_addresses)
                robot_company = (
                    db.query(RobotCompany)
                    .filter(RobotCompany.id == supply_msg.robot_company_id)
                    .first()
                )
                _notify_supply_and_forward(db, supply_msg, supply_reply, robot_company, crm_msg)
                agent_action = handle_supply_reply_first_response(
                    db,
                    supply_msg,
                    supply_reply,
                    robot_company,
                    team_id=crm_msg.team_id if crm_msg else None,
                    owner_user_id=crm_msg.sender_user_id if crm_msg else None,
                )
                db.commit()
                return {
                    "ok": True,
                    "supply_outreach_reply_id": str(supply_reply.id),
                    "sales_agent_action_id": str(agent_action.id),
                    "sales_agent_action_status": agent_action.status,
                }
            from app.services.jobs_crm import capture_inbound_message, find_application_by_reply_token

            jobs_app = find_application_by_reply_token(db, token)
            if jobs_app:
                inbound = capture_inbound_message(
                    db,
                    jobs_app,
                    body=data.get("text") or data.get("body") or data.get("html") or "",
                    from_email=(_extract_addresses(data.get("from")) or [None])[0],
                    to_email=", ".join(to_addresses) if to_addresses else None,
                    subject=data.get("subject"),
                    provider_id=str(data.get("email_id") or data.get("id") or svix_id or "") or None,
                )
                db.commit()
                return {
                    "ok": True,
                    "job_application_id": str(jobs_app.id),
                    "application_message_id": str(inbound.id),
                }
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
            raw_payload={**data, "_svix_id": svix_id or ""},
            received_at=datetime.now(timezone.utc),
        )
        db.add(reply)
        msg.status = "replied"

        # Classify the reply (LLM-first, keyword fallback) so the cadence can react
        # to intent and the weekly learning report can attribute it to the send's
        # trust-first angle (msg.payload.variant_id). Never let this drop a reply.
        from app.services.reply_classifier import classify_reply

        try:
            cls = classify_reply(reply.subject, reply.body_text)
        except Exception:  # noqa: BLE001
            from app.services.reply_classifier import ReplyClassification

            cls = ReplyClassification("other", "neutral", "keyword")
        reply.detected_intent = cls.intent
        reply.sentiment = cls.sentiment

        if account:
            from app.services.sequence_runner import (
                block_enrollment_for_reply,
                pause_enrollment_for_reply,
            )

            if cls.intent in ("unsubscribe", "not_a_fit"):
                # Hard opt-out: stop the cadence and suppress all future auto-sends.
                block_enrollment_for_reply(db, crm_account_id=account.id, reason=cls.intent)
                account.outreach_stage = "opted_out" if cls.intent == "unsubscribe" else "not_a_fit"
                if msg.company_id:
                    from app.models.company import Company

                    company_row = (
                        db.query(Company).filter(Company.id == msg.company_id).first()
                    )
                    if company_row is not None:
                        cmeta = dict(company_row.crm_metadata or {})
                        cmeta["do_not_contact"] = True
                        cmeta["do_not_contact_reason"] = cls.intent
                        company_row.crm_metadata = cmeta
            elif cls.intent == "auto_reply":
                # Autoresponder — not a human reply; keep the cadence paused, no more.
                account.outreach_stage = "contacted"
                pause_enrollment_for_reply(db, crm_account_id=account.id)
            else:
                account.outreach_stage = "replied"
                pause_enrollment_for_reply(db, crm_account_id=account.id)

            outcome = {
                "positive": "positive_reply",
                "negative": "negative_reply",
                "neutral": "nurture_reply",
            }.get(cls.sentiment, "replied")
            record_sales_experience(
                db,
                event_type="email_reply_received",
                outcome=outcome,
                team_id=msg.team_id,
                user_id=msg.sender_user_id,
                crm_account_id=msg.crm_account_id,
                company_id=msg.company_id,
                channel="email",
                payload={
                    "outreach_message_id": str(msg.id),
                    "outreach_reply_id": str(reply.id),
                    "detected_intent": cls.intent,
                    "sentiment": cls.sentiment,
                    "classifier": cls.source,
                    "variant_id": (msg.payload or {}).get("variant_id"),
                },
            )
        _notify_and_forward(db, msg, reply, account)
        agent_action = handle_crm_reply_first_response(db, msg, reply, account)
        db.commit()
        return {
            "ok": True,
            "outreach_reply_id": str(reply.id),
            "sales_agent_action_id": str(agent_action.id),
            "sales_agent_action_status": agent_action.status,
        }
    finally:
        db.close()
