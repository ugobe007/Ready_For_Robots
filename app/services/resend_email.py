import os
from typing import Any

import requests


class ResendEmailError(Exception):
    """Raised when Resend email send fails."""


def _format_from_header(from_email: str, display_name: str | None) -> str:
    fe = (from_email or "").strip()
    dn = (display_name or "").strip()
    if not fe:
        return fe
    if not dn:
        return fe
    if "<" in fe and ">" in fe:
        return fe
    return f"{dn} <{fe}>"


def send_email_via_resend(
    *,
    to_email: str,
    subject: str,
    body_text: str,
    from_display_name: str | None = None,
    reply_to: str | None = None,
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    """
    Send an email with Resend.

    Required env vars:
    - RESEND_API_KEY
    - RESEND_FROM_EMAIL

    Optional env vars:
    - RESEND_REPLY_TO
    """
    api_key = (os.getenv("RESEND_API_KEY") or "").strip()
    from_email = (os.getenv("RESEND_FROM_EMAIL") or "").strip()
    default_reply_to = (os.getenv("RESEND_REPLY_TO") or "").strip()

    if not api_key:
        raise ResendEmailError("Missing RESEND_API_KEY")
    if not from_email:
        raise ResendEmailError("Missing RESEND_FROM_EMAIL")
    if not to_email or "@" not in to_email:
        raise ResendEmailError("Recipient email is required")

    payload: dict[str, Any] = {
        "from": _format_from_header(from_email, from_display_name),
        "to": [to_email],
        "subject": subject,
        "text": body_text,
    }
    clean_cc = [x.strip() for x in (cc or []) if x and "@" in x]
    clean_bcc = [x.strip() for x in (bcc or []) if x and "@" in x]
    if clean_cc:
        payload["cc"] = clean_cc
    if clean_bcc:
        payload["bcc"] = clean_bcc
    effective_reply_to = (reply_to or default_reply_to).strip()
    if effective_reply_to:
        payload["reply_to"] = effective_reply_to

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key[:256]

    try:
        resp = requests.post(
            "https://api.resend.com/emails",
            headers=headers,
            json=payload,
            timeout=20,
        )
    except requests.RequestException as exc:
        raise ResendEmailError(f"Resend request failed: {exc}") from exc

    if resp.status_code >= 400:
        detail = resp.text
        raise ResendEmailError(
            f"Resend rejected email ({resp.status_code}): {detail}"
        )

    data = resp.json() if resp.content else {}
    return {
        "resend_id": data.get("id"),
        "from_email": from_email,
        "reply_to": effective_reply_to or None,
        "cc": clean_cc,
        "bcc": clean_bcc,
    }


def fetch_resend_received_email(email_id: str) -> dict[str, Any]:
    api_key = (os.getenv("RESEND_API_KEY") or "").strip()
    if not api_key:
        raise ResendEmailError("Missing RESEND_API_KEY")
    if not email_id:
        raise ResendEmailError("email_id is required")
    try:
        resp = requests.get(
            f"https://api.resend.com/emails/receiving/{email_id}",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=20,
        )
    except requests.RequestException as exc:
        raise ResendEmailError(f"Resend receive lookup failed: {exc}") from exc
    if resp.status_code >= 400:
        raise ResendEmailError(f"Resend receive lookup rejected ({resp.status_code}): {resp.text}")
    return resp.json() if resp.content else {}
