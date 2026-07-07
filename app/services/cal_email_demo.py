"""
Cal email demo snippet — inline animated GIF for outreach (plays in inbox, no click).

Uses a hosted GIF URL by default (Gmail, Apple Mail, preview). Optional CID embed
via CAL_EMAIL_DEMO_USE_CID=1 — often fails in webmail.
"""
from __future__ import annotations

import base64
import html
import os
import re
from pathlib import Path
from typing import Any

_CAL_DEMO_CID = "cal-pipeline-demo"
_REPO_GIF = (
    Path(__file__).resolve().parents[2]
    / "readyforrobots-new"
    / "client"
    / "public"
    / "marketing"
    / "cal-pipeline-demo.gif"
)


def cal_demo_gif_path() -> Path | None:
    """Local file for optional CID embed."""
    candidates = [
        _REPO_GIF,
        Path(__file__).resolve().parents[1] / "static" / "marketing" / "cal-pipeline-demo.gif",
        Path("/code/static/marketing/cal-pipeline-demo.gif"),
    ]
    override = (os.getenv("CAL_EMAIL_DEMO_GIF_PATH") or "").strip()
    if override:
        candidates.insert(0, Path(override))
    for path in candidates:
        if path.is_file():
            return path
    return None


def _site_url() -> str:
    return (os.getenv("PUBLIC_SITE_URL") or "https://readyforrobots.com").rstrip("/")


def cal_demo_gif_url() -> str:
    return (os.getenv("CAL_EMAIL_DEMO_GIF_URL") or "").strip() or f"{_site_url()}/marketing/cal-pipeline-demo.gif"


def cal_meme_gif_url() -> str:
    return (os.getenv("CAL_MEME_GIF_URL") or "").strip() or f"{_site_url()}/marketing/cal-meme-monday.gif"


def cal_preview_page_url() -> str:
    return f"{_site_url()}/preview"


def cal_demo_gif_bytes() -> bytes:
    path = cal_demo_gif_path()
    if path:
        return path.read_bytes()
    return b""


def cal_demo_use_cid() -> bool:
    return os.getenv("CAL_EMAIL_DEMO_USE_CID", "").strip().lower() in ("1", "true", "yes")


def cal_demo_enabled() -> bool:
    if os.getenv("CAL_EMAIL_DEMO_ENABLED", "1").strip().lower() in ("0", "false", "no"):
        return False
    return bool(cal_demo_gif_url()) or cal_demo_gif_path() is not None


def build_cal_demo_html(
    *,
    img_src: str,
    preview_url: str | None = None,
    alt: str | None = None,
) -> str:
    """Email-safe table layout — hosted GIF autoplays when images are enabled."""
    alt_text = html.escape(
        alt or "Monday pipeline: Cal identifies a priority account and prepares outreach"
    )
    src = html.escape(img_src, quote=True)
    link = html.escape(preview_url or cal_preview_page_url(), quote=True)
    return f"""<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="margin:20px 0 0 0;max-width:280px;">
  <tr>
    <td style="padding:10px 0 0 0;border-top:1px solid #e5e7eb;">
      <p style="margin:0 0 6px 0;font-family:Arial,Helvetica,sans-serif;font-size:10px;line-height:1.4;color:#6b7280;">
        <strong style="color:#047857;">Cal · pipeline preview</strong> · 6-sec loop
      </p>
      <img src="{src}" alt="{alt_text}" width="280" height="95" style="display:block;width:100%;max-width:280px;height:auto;border-radius:6px;border:0;" />
      <p style="margin:5px 0 0 0;font-family:Arial,Helvetica,sans-serif;font-size:10px;line-height:1.35;color:#9ca3af;">
        <a href="{link}" style="color:#059669;">View full preview</a>
      </p>
    </td>
  </tr>
</table>"""


def _text_to_html_paragraphs(body_text: str) -> str:
    chunks = re.split(r"\n\s*\n", (body_text or "").strip())
    parts: list[str] = []
    for chunk in chunks:
        if not chunk.strip():
            continue
        escaped = html.escape(chunk.strip()).replace("\n", "<br />")
        parts.append(
            '<p style="margin:0 0 14px 0;font-family:Arial,Helvetica,sans-serif;'
            f'font-size:14px;line-height:1.55;color:#111827;">{escaped}</p>'
        )
    return "\n".join(parts)


_DEMO_MARKERS = (
    "cal-pipeline-demo.gif",
    "Cal · pipeline preview",
    "Cal pipeline preview",
    "View full preview",
)


def _strip_existing_demo_from_text(body_text: str) -> str:
    """Remove prior demo embeds/notes so enrich is idempotent (one GIF only)."""
    text = (body_text or "").strip()
    if not text:
        return text
    cleaned: list[str] = []
    for line in text.splitlines():
        low = line.strip().lower()
        if any(marker.lower() in low for marker in _DEMO_MARKERS):
            continue
        if "/preview" in low and ("loop" in low or "pipeline" in low or "cal" in low):
            continue
        cleaned.append(line)
    return "\n".join(cleaned).strip()


def _inject_plaintext_demo_note(body_text: str) -> str:
    """No URL in plaintext — avoids inbox link unfurl duplicating the HTML GIF."""
    return (body_text or "").strip()


def cal_demo_attachment(*, use_cid: bool = True) -> dict[str, Any] | None:
    """Optional Resend CID attachment — off by default."""
    if not use_cid:
        return None
    raw = cal_demo_gif_bytes()
    if not raw:
        return None
    return {
        "filename": "cal-pipeline-demo.gif",
        "content": base64.b64encode(raw).decode("ascii"),
        "content_type": "image/gif",
        "content_id": _CAL_DEMO_CID,
    }


def _resolve_img_src(*, use_cid: bool) -> tuple[str, list[dict[str, Any]] | None]:
    """Hosted URL first — works in browsers, Gmail, and the preview endpoint."""
    if use_cid and cal_demo_use_cid():
        attachment = cal_demo_attachment(use_cid=True)
        if attachment:
            return f"cid:{_CAL_DEMO_CID}", [attachment]
    return cal_demo_gif_url(), None


def enrich_cal_email_with_demo(
    body_text: str,
    *,
    use_cid: bool = False,
    insert_at_bottom: bool = True,
    include_plaintext_note: bool = True,
) -> dict[str, Any]:
    """
    Wrap Cal body with HTML demo block at the bottom + optional plaintext demo link.

    Returns: body_text, body_html, attachments
    """
    text = _strip_existing_demo_from_text((body_text or "").strip())
    result: dict[str, Any] = {
        "body_text": _inject_plaintext_demo_note(text) if include_plaintext_note else text,
        "body_html": None,
        "attachments": None,
    }

    if not cal_demo_enabled():
        return result

    img_src, attachments = _resolve_img_src(use_cid=use_cid)
    result["attachments"] = attachments

    demo_block = build_cal_demo_html(img_src=img_src, preview_url=cal_preview_page_url())
    letter_html = _text_to_html_paragraphs(text)

    if insert_at_bottom:
        letter_html = f"{letter_html}\n{demo_block}"

    result["body_html"] = (
        "<!DOCTYPE html>\n"
        '<html><head><meta charset="utf-8"></head>\n'
        '<body style="margin:0;padding:20px;background:#ffffff;">\n'
        f"{letter_html}\n"
        "</body></html>"
    )
    return result
