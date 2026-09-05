"""Send Cal outreach with optional inline demo GIF (HTML multipart)."""
from __future__ import annotations

from typing import Any

from app.services.cal_email_demo import enrich_cal_email_with_demo
from app.services.resend_email import ResendEmailError, send_email_via_resend


def send_cal_email_via_resend(
    *,
    to_email: str | list[str],
    subject: str,
    body_text: str,
    from_display_name: str | None = "Cal · Ready For Robots",
    reply_to: str | None = None,
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
    idempotency_key: str | None = None,
    include_demo: bool = True,
) -> dict[str, Any]:
    """Resend send with Cal demo GIF embedded when enabled."""
    original_body = (body_text or "").strip()
    body_html = None
    attachments = None
    outbound_text = original_body
    if include_demo:
        enriched = enrich_cal_email_with_demo(original_body)
        body_html = enriched.get("body_html")
        attachments = enriched.get("attachments")
        outbound_text = enriched.get("body_text") or original_body

    try:
        return send_email_via_resend(
            to_email=to_email,
            subject=subject,
            body_text=outbound_text,
            body_html=body_html,
            from_display_name=from_display_name,
            reply_to=reply_to,
            cc=cc,
            bcc=bcc,
            attachments=attachments,
            idempotency_key=idempotency_key,
        )
    except ResendEmailError as exc:
        if include_demo and attachments:
            enriched = enrich_cal_email_with_demo(original_body, use_cid=False)
            return send_email_via_resend(
                to_email=to_email,
                subject=subject,
                body_text=enriched.get("body_text") or original_body,
                body_html=enriched.get("body_html"),
                from_display_name=from_display_name,
                reply_to=reply_to,
                cc=cc,
                bcc=bcc,
                idempotency_key=f"{idempotency_key}/url-fallback" if idempotency_key else None,
            )
        raise
