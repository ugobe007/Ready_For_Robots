"""Product presentation offer for a robot company — after Job Cards, behind pay.

Provider interface (Manus / Replit / OpenAI-compatible) is config-backed.
No API key → queue the request; never fake a finished deck.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any, Optional, Protocol

from sqlalchemy.orm import Session

from app.models.robot_submission import RobotPresentationRequest
from app.services.plan_entitlements import PLAN_PAID, resolve_plan_tier
from app.services.robot_url_safety import canonical_robot_url

logger = logging.getLogger(__name__)

STATUS_QUEUED = "queued"
STATUS_PAID_QUEUED = "paid_queued"
STATUS_BUILDING = "building"
STATUS_READY = "ready"
STATUS_FAILED = "failed"

JOBS_PRESENTATION_CTA = "Build a product presentation"
JOBS_PRESENTATION_HINT = (
    "After you have seen Job Cards: we can build a product presentation for this "
    "robot company. Sign up and pay first. We do not fake a finished deck."
)


def presentation_provider_name() -> str:
    raw = (os.getenv("JOBS_PRESENTATION_PROVIDER") or os.getenv("PRESENTATION_PROVIDER") or "none").strip().lower()
    if raw in {"manus", "replit", "openai", "chatgpt"}:
        return raw
    return "none"


def presentation_provider_configured() -> bool:
    name = presentation_provider_name()
    if name == "manus":
        return bool((os.getenv("MANUS_API_KEY") or "").strip())
    if name == "replit":
        return bool((os.getenv("REPLIT_API_KEY") or "").strip())
    if name in {"openai", "chatgpt"}:
        return bool((os.getenv("OPENAI_API_KEY") or os.getenv("CHATGPT_API_KEY") or "").strip())
    return False


class PresentationProvider(Protocol):
    name: str

    def enqueue(self, request: RobotPresentationRequest) -> dict[str, Any]:
        ...


class QueuedPresentationProvider:
    """Default: store the request. Do not invent a deck URL."""

    name = "none"

    def enqueue(self, request: RobotPresentationRequest) -> dict[str, Any]:
        request.status = STATUS_PAID_QUEUED if request.paid == "true" else STATUS_QUEUED
        request.provider = self.name
        request.deck_url = None
        request.note = (
            "Queued. We will build this presentation after payment is confirmed. "
            "A presentation provider is not connected yet — no finished deck."
        )
        return {"status": request.status, "provider": self.name, "deck_url": None}


class ConfiguredPresentationProvider:
    """Named provider with an API key. Enqueue only — never return a fake deck."""

    def __init__(self, name: str):
        self.name = name

    def enqueue(self, request: RobotPresentationRequest) -> dict[str, Any]:
        request.status = STATUS_BUILDING
        request.provider = self.name
        request.deck_url = None
        request.note = (
            f"Queued with {self.name}. Building starts after payment. "
            "No finished deck until the provider returns one."
        )
        return {"status": request.status, "provider": self.name, "deck_url": None}


def resolve_provider() -> PresentationProvider:
    if presentation_provider_configured():
        return ConfiguredPresentationProvider(presentation_provider_name())
    return QueuedPresentationProvider()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def request_payload(row: RobotPresentationRequest) -> dict[str, Any]:
    return {
        "id": row.id,
        "canonical_url": row.canonical_url,
        "submitted_url": row.submitted_url,
        "company_name": row.company_name,
        "product_name": row.product_name,
        "status": row.status,
        "provider": row.provider,
        "provider_job_id": row.provider_job_id,
        "deck_url": row.deck_url,
        "note": row.note,
        "paid": row.paid == "true",
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def queue_presentation(
    db: Session,
    user: dict,
    *,
    url: str,
    company_name: str | None = None,
    product_name: str | None = None,
) -> dict[str, Any]:
    canonical = canonical_robot_url(url)
    if not canonical:
        raise ValueError("A public robot URL is required.")
    plan = resolve_plan_tier(user, db)
    paid = plan == PLAN_PAID
    if not paid:
        raise PermissionError("Sign up and pay to order a product presentation.")
    uid = str(user.get("uid") or "")
    row = RobotPresentationRequest(
        user_id=uid[:64] if uid else None,
        canonical_url=canonical,
        submitted_url=(url or canonical)[:2000],
        company_name=(company_name or "")[:240] or None,
        product_name=(product_name or "")[:240] or None,
        status=STATUS_PAID_QUEUED,
        paid="true",
        created_at=_now(),
        updated_at=_now(),
    )
    provider = resolve_provider()
    result = provider.enqueue(row)
    db.add(row)
    db.commit()
    db.refresh(row)
    payload = request_payload(row)
    payload["queued"] = True
    payload["provider_configured"] = presentation_provider_configured()
    payload["cta"] = JOBS_PRESENTATION_CTA
    payload["hint"] = result.get("note") or row.note or JOBS_PRESENTATION_HINT
    return payload
