"""Stripe billing — checkout, portal, webhook, post-checkout sync."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.auth_deps import _require_user
from app.database import get_db
from app.services.stripe_billing import (
    billing_config_payload,
    create_checkout_session,
    create_portal_session,
    get_stripe_customer_id,
    handle_stripe_webhook,
    stripe_enabled,
    sync_checkout_session,
)

router = APIRouter()


class CheckoutBody(BaseModel):
    tier: str = Field(..., description="pro or premium")


@router.get("/config")
def billing_config():
    return billing_config_payload()


@router.post("/checkout")
def start_checkout(
    body: CheckoutBody,
    user: dict = Depends(_require_user),
):
    if not stripe_enabled():
        raise HTTPException(status_code=503, detail="Stripe billing is not configured yet")
    try:
        return create_checkout_session(
            user_id=user["uid"],
            email=user.get("email") or "",
            tier=body.tier,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/portal")
def billing_portal(
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
):
    if not stripe_enabled():
        raise HTTPException(status_code=503, detail="Stripe billing is not configured yet")
    customer_id = get_stripe_customer_id(db, user["uid"])
    if not customer_id:
        raise HTTPException(status_code=400, detail="No active subscription on file")
    try:
        return create_portal_session(stripe_customer_id=customer_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/sync")
def sync_after_checkout(
    session_id: str,
    user: dict = Depends(_require_user),
    db: Session = Depends(get_db),
):
    if not session_id.strip():
        raise HTTPException(status_code=400, detail="session_id is required")
    if not stripe_enabled():
        raise HTTPException(status_code=503, detail="Stripe billing is not configured yet")
    try:
        return sync_checkout_session(
            db,
            user_id=user["uid"],
            email=user.get("email") or "",
            session_id=session_id.strip(),
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig = request.headers.get("stripe-signature") or request.headers.get("Stripe-Signature")
    if not sig:
        raise HTTPException(status_code=400, detail="Missing Stripe-Signature header")
    try:
        return handle_stripe_webhook(db, payload, sig)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
