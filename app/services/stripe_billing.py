"""Stripe Checkout, Customer Portal, and subscription → plan sync."""
from __future__ import annotations

import logging
import os
from typing import Any, Optional

from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)

VALID_TIERS = frozenset({"pro", "premium"})
_price_cache: dict[str, str] = {}


def stripe_enabled() -> bool:
    return bool((os.getenv("STRIPE_SECRET_KEY") or "").strip())


def stripe_key_mode() -> str:
    """'live', 'test', or 'unknown' — inferred from the secret key prefix (never the value)."""
    key = (os.getenv("STRIPE_SECRET_KEY") or "").strip()
    if key.startswith(("sk_live", "rk_live")):
        return "live"
    if key.startswith(("sk_test", "rk_test")):
        return "test"
    return "unknown"


def is_test_key_on_production() -> bool:
    """True when a test-mode Stripe key is running on the real public domain.

    This is the silent revenue killer: checkout 'works' (returns a Stripe URL) but
    real cards can never be charged, so paid subscriptions stay at zero. Surface it.
    """
    if stripe_key_mode() != "test":
        return False
    site = _site_url().lower()
    return "readyforrobots.com" in site and "localhost" not in site


_TEST_KEY_WARNED = False


def _warn_if_test_key_on_production() -> None:
    global _TEST_KEY_WARNED
    if _TEST_KEY_WARNED or not is_test_key_on_production():
        return
    _TEST_KEY_WARNED = True
    logger.error(
        "STRIPE IN TEST MODE ON PRODUCTION (%s): checkout returns a valid URL but real "
        "cards cannot be charged — paid subscriptions will stay at zero. Set live "
        "STRIPE_SECRET_KEY, STRIPE_PRICE_PRO/PREMIUM, and STRIPE_WEBHOOK_SECRET.",
        _site_url(),
    )


def _site_url() -> str:
    raw = (os.getenv("PUBLIC_SITE_URL") or "https://readyforrobots.com").strip().strip("'\"")
    # Secrets pasted from shell commands sometimes include trailing garbage.
    for sep in ("'", '"', " \\"):
        if sep in raw:
            raw = raw.split(sep, 1)[0].strip()
    raw = raw.rstrip("/")
    if not raw.startswith(("http://", "https://")):
        raw = f"https://{raw.lstrip('/')}"
    return raw


def _api_base() -> str:
    return (os.getenv("STRIPE_SUCCESS_API_BASE") or os.getenv("VITE_PUBLIC_API_URL") or "https://ready-2-robot.fly.dev").rstrip("/")


def _price_env_for_tier(tier: str) -> Optional[str]:
    slug = (tier or "").strip().lower()
    if slug == "pro":
        return (os.getenv("STRIPE_PRICE_PRO") or os.getenv("STRIPE_PRICE_ID_PRO") or "").strip() or None
    if slug == "premium":
        return (os.getenv("STRIPE_PRICE_PREMIUM") or os.getenv("STRIPE_PRICE_ID_PREMIUM") or "").strip() or None
    return None


def _product_env_for_tier(tier: str) -> Optional[str]:
    slug = (tier or "").strip().lower()
    if slug == "pro":
        return (os.getenv("STRIPE_PRODUCT_PRO") or "").strip() or None
    if slug == "premium":
        return (os.getenv("STRIPE_PRODUCT_PREMIUM") or "").strip() or None
    return None


def _default_price_for_product(product_id: str) -> Optional[str]:
    pid = (product_id or "").strip()
    if not pid:
        return None
    if pid in _price_cache:
        return _price_cache[pid]
    if not stripe_enabled():
        return None
    try:
        stripe = _stripe_client()
        product = stripe.Product.retrieve(pid, expand=["default_price"])
        default_price = product.get("default_price")
        if isinstance(default_price, str):
            price_id = default_price
        elif isinstance(default_price, dict):
            price_id = default_price.get("id")
        else:
            prices = stripe.Price.list(product=pid, active=True, limit=1)
            data = prices.get("data") or []
            price_id = data[0]["id"] if data else None
        if price_id:
            _price_cache[pid] = price_id
            return price_id
    except Exception as exc:
        logger.warning("Could not resolve Stripe price for product %s: %s", pid, exc)
    return None


def price_id_for_tier(tier: str) -> Optional[str]:
    """Checkout price ID — accepts STRIPE_PRICE_* or resolves from STRIPE_PRODUCT_*."""
    direct = _price_env_for_tier(tier)
    if direct:
        return direct
    product_id = _product_env_for_tier(tier)
    if product_id:
        return _default_price_for_product(product_id)
    return None


def tier_for_price_id(price_id: str) -> Optional[str]:
    pid = (price_id or "").strip()
    if not pid:
        return None
    for tier in ("pro", "premium"):
        resolved = price_id_for_tier(tier)
        if resolved == pid:
            return tier
    mapping = {
        (_price_env_for_tier("pro") or ""): "pro",
        (_price_env_for_tier("premium") or ""): "premium",
    }
    return mapping.get(pid)


def billing_config_payload() -> dict[str, Any]:
    pro_price = price_id_for_tier("pro")
    premium_price = price_id_for_tier("premium")
    enabled = stripe_enabled() and bool(pro_price or premium_price)
    _warn_if_test_key_on_production()
    return {
        "enabled": enabled,
        "pro_available": bool(pro_price),
        "premium_available": bool(premium_price),
        "display_prices": {"pro": 49, "premium": 129},
        "checkout_tiers": [t for t, pid in (("pro", pro_price), ("premium", premium_price)) if pid],
        # Ops guardrail: 'test' here on the live domain means no real revenue can be collected.
        "mode": stripe_key_mode(),
        "test_mode_on_production": is_test_key_on_production(),
    }


def _stripe_client():
    import stripe

    key = (os.getenv("STRIPE_SECRET_KEY") or "").strip()
    if not key:
        raise RuntimeError("STRIPE_SECRET_KEY is not configured")
    stripe.api_key = key
    return stripe


def _ensure_profile_row(db: Session, user_id: str, email: str) -> None:
    db.execute(
        text("""
            INSERT INTO user_profiles (id, email, billing_tier)
            VALUES (:uid, :email, 'free')
            ON CONFLICT (id) DO UPDATE SET
                email = COALESCE(NULLIF(:email, ''), user_profiles.email)
        """),
        {"uid": user_id, "email": email or ""},
    )


def apply_billing_to_user(
    db: Session,
    *,
    user_id: str,
    email: str,
    billing_tier: str,
    stripe_customer_id: Optional[str] = None,
    stripe_subscription_id: Optional[str] = None,
    stripe_subscription_status: Optional[str] = None,
) -> dict[str, Any]:
    """Persist billing on user_profiles and Supabase JWT app_metadata."""
    from app.services.supabase_admin import update_user_app_metadata

    tier = (billing_tier or "free").strip().lower()
    if tier not in VALID_TIERS and tier != "free":
        tier = "free"

    _ensure_profile_row(db, user_id, email)
    db.execute(
        text("""
            UPDATE user_profiles
            SET billing_tier = :tier,
                stripe_customer_id = COALESCE(:customer_id, stripe_customer_id),
                stripe_subscription_id = COALESCE(:subscription_id, stripe_subscription_id),
                stripe_subscription_status = COALESCE(:status, stripe_subscription_status),
                updated_at = now()
            WHERE id = :uid
        """),
        {
            "uid": user_id,
            "tier": tier,
            "customer_id": stripe_customer_id,
            "subscription_id": stripe_subscription_id,
            "status": stripe_subscription_status,
        },
    )
    db.commit()

    meta_patch: dict[str, Any] = {"plan_tier": tier}
    if stripe_customer_id:
        meta_patch["stripe_customer_id"] = stripe_customer_id
    if stripe_subscription_id:
        meta_patch["stripe_subscription_id"] = stripe_subscription_id
    if stripe_subscription_status:
        meta_patch["stripe_subscription_status"] = stripe_subscription_status
    synced = update_user_app_metadata(user_id, meta_patch)
    return {"billing_tier": tier, "supabase_synced": synced}


def create_checkout_session(
    *,
    user_id: str,
    email: str,
    tier: str,
) -> dict[str, Any]:
    slug = (tier or "").strip().lower()
    if slug not in VALID_TIERS:
        raise ValueError(f"Unsupported tier: {tier}")
    price_id = price_id_for_tier(slug)
    if not price_id:
        raise RuntimeError(f"Stripe price not configured for tier '{slug}'")

    stripe = _stripe_client()
    site = _site_url()
    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=f"{site}/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{site}/pricing?checkout=cancelled",
        client_reference_id=user_id,
        customer_email=email or None,
        allow_promotion_codes=True,
        metadata={"user_id": user_id, "plan_tier": slug},
        subscription_data={"metadata": {"user_id": user_id, "plan_tier": slug}},
    )
    return {"checkout_url": session.url, "session_id": session.id}


def create_portal_session(*, stripe_customer_id: str) -> dict[str, Any]:
    if not stripe_customer_id:
        raise ValueError("No Stripe customer on file")
    stripe = _stripe_client()
    session = stripe.billing_portal.Session.create(
        customer=stripe_customer_id,
        return_url=f"{_site_url()}/profile",
    )
    return {"portal_url": session.url}


def sync_checkout_session(db: Session, *, user_id: str, email: str, session_id: str) -> dict[str, Any]:
    stripe = _stripe_client()
    session = stripe.checkout.Session.retrieve(session_id, expand=["subscription"])
    if session.client_reference_id and str(session.client_reference_id) != str(user_id):
        raise PermissionError("Checkout session does not belong to this user")
    if session.payment_status != "paid" and session.status != "complete":
        return {"status": "pending", "payment_status": session.payment_status}

    tier = (session.metadata or {}).get("plan_tier") or "pro"
    customer_id = str(session.customer or "")
    subscription = session.subscription
    subscription_id = subscription.id if hasattr(subscription, "id") else str(subscription or "")
    status = subscription.status if hasattr(subscription, "status") else "active"

    if subscription and hasattr(subscription, "items"):
        items = subscription.items.data if hasattr(subscription.items, "data") else []
        if items:
            price_id = items[0].price.id if items[0].price else None
            mapped = tier_for_price_id(price_id or "")
            if mapped:
                tier = mapped

    result = apply_billing_to_user(
        db,
        user_id=user_id,
        email=email,
        billing_tier=tier,
        stripe_customer_id=customer_id or None,
        stripe_subscription_id=subscription_id or None,
        stripe_subscription_status=status,
    )
    return {"status": "active", **result}


def handle_stripe_webhook(db: Session, payload: bytes, sig_header: str) -> dict[str, Any]:
    secret = (os.getenv("STRIPE_WEBHOOK_SECRET") or "").strip()
    if not secret:
        raise RuntimeError("STRIPE_WEBHOOK_SECRET is not configured")

    stripe = _stripe_client()
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, secret)
    except Exception as exc:
        raise ValueError(str(exc)) from exc

    event_type = event["type"]
    data = event["data"]["object"]

    if event_type == "checkout.session.completed":
        return _handle_checkout_completed(db, data)
    if event_type in ("customer.subscription.updated", "customer.subscription.created"):
        return _handle_subscription_updated(db, data)
    if event_type == "customer.subscription.deleted":
        return _handle_subscription_deleted(db, data)

    return {"status": "ignored", "event_type": event_type}


def _user_id_from_metadata(meta: dict[str, Any]) -> Optional[str]:
    uid = (meta or {}).get("user_id") or (meta or {}).get("client_reference_id")
    return str(uid).strip() if uid else None


def _handle_checkout_completed(db: Session, session: dict[str, Any]) -> dict[str, Any]:
    user_id = session.get("client_reference_id") or _user_id_from_metadata(session.get("metadata") or {})
    if not user_id:
        return {"status": "skipped", "reason": "missing user_id"}
    tier = (session.get("metadata") or {}).get("plan_tier") or "pro"
    email = (session.get("customer_details") or {}).get("email") or session.get("customer_email") or ""
    return apply_billing_to_user(
        db,
        user_id=str(user_id),
        email=str(email or ""),
        billing_tier=str(tier),
        stripe_customer_id=str(session.get("customer") or "") or None,
        stripe_subscription_id=str(session.get("subscription") or "") or None,
        stripe_subscription_status="active",
    )


def _handle_subscription_updated(db: Session, subscription: dict[str, Any]) -> dict[str, Any]:
    user_id = _user_id_from_metadata(subscription.get("metadata") or {})
    status = (subscription.get("status") or "").lower()
    customer_id = str(subscription.get("customer") or "") or None
    subscription_id = str(subscription.get("id") or "") or None

    tier = "free"
    items = (subscription.get("items") or {}).get("data") or []
    if items:
        price_id = ((items[0] or {}).get("price") or {}).get("id")
        mapped = tier_for_price_id(price_id or "")
        if mapped:
            tier = mapped

    if status in ("canceled", "unpaid", "incomplete_expired"):
        tier = "free"

    if not user_id and customer_id:
        row = db.execute(
            text("SELECT id, email FROM user_profiles WHERE stripe_customer_id = :cid LIMIT 1"),
            {"cid": customer_id},
        ).fetchone()
        if row:
            user_id = str(row.id)
            email = row.email or ""
        else:
            return {"status": "skipped", "reason": "unknown customer"}
    else:
        row = db.execute(
            text("SELECT email FROM user_profiles WHERE id = :uid"),
            {"uid": user_id},
        ).fetchone()
        email = (row.email if row else "") or ""

    if not user_id:
        return {"status": "skipped", "reason": "missing user_id"}

    return apply_billing_to_user(
        db,
        user_id=str(user_id),
        email=str(email),
        billing_tier=tier,
        stripe_customer_id=customer_id,
        stripe_subscription_id=subscription_id,
        stripe_subscription_status=status or None,
    )


def _handle_subscription_deleted(db: Session, subscription: dict[str, Any]) -> dict[str, Any]:
    user_id = _user_id_from_metadata(subscription.get("metadata") or {})
    customer_id = str(subscription.get("customer") or "") or None
    if not user_id and customer_id:
        row = db.execute(
            text("SELECT id, email FROM user_profiles WHERE stripe_customer_id = :cid LIMIT 1"),
            {"cid": customer_id},
        ).fetchone()
        if not row:
            return {"status": "skipped", "reason": "unknown customer"}
        user_id = str(row.id)
        email = row.email or ""
    else:
        row = db.execute(
            text("SELECT email FROM user_profiles WHERE id = :uid"),
            {"uid": user_id},
        ).fetchone()
        email = (row.email if row else "") or ""

    if not user_id:
        return {"status": "skipped", "reason": "missing user_id"}

    return apply_billing_to_user(
        db,
        user_id=str(user_id),
        email=str(email),
        billing_tier="free",
        stripe_customer_id=customer_id,
        stripe_subscription_id=None,
        stripe_subscription_status="canceled",
    )


def get_stripe_customer_id(db: Session, user_id: str) -> Optional[str]:
    row = db.execute(
        text("SELECT stripe_customer_id FROM user_profiles WHERE id = :uid"),
        {"uid": user_id},
    ).fetchone()
    if not row:
        return None
    return (row.stripe_customer_id or "").strip() or None
