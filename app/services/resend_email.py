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
    reply_to = (os.getenv("RESEND_REPLY_TO") or "").strip()

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
    if reply_to:
        payload["reply_to"] = reply_to

    try:
        resp = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
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
        "reply_to": reply_to or None,
    }
