"""Stripe billing helpers and DB-backed plan resolution."""
from __future__ import annotations

import os

import pytest

from app.services.plan_entitlements import PLAN_PAID, resolve_billing_tier_slug, resolve_plan_tier
from app.services.stripe_billing import (
    _as_dict,
    billing_config_payload,
    price_id_for_tier,
    tier_for_price_id,
)


class _FakeStripeObj:
    """Mimics stripe-python's StripeObject: data lives in ``_data`` and
    ``.get()`` / ``dict()`` blow up (the exact bug that broke checkout sync)."""

    def __init__(self, data):
        self._data = {
            k: _FakeStripeObj(v) if isinstance(v, dict) else v for k, v in data.items()
        }

    def __getattr__(self, name):
        try:
            return self._data[name]
        except KeyError as exc:  # matches real lib: .get raises AttributeError
            raise AttributeError(name) from exc

    def __iter__(self):
        raise KeyError(0)  # dict(obj) explodes, like the deployed lib


def test_as_dict_recursively_flattens_stripe_object():
    session = _FakeStripeObj(
        {
            "id": "cs_live_x",
            "payment_status": "paid",
            "metadata": {"plan_tier": "pro", "user_id": "u1"},
            "subscription": {
                "id": "sub_1",
                "status": "active",
                "items": {"data": [{"price": {"id": "price_pro"}}]},
            },
        }
    )
    d = _as_dict(session)
    assert d["payment_status"] == "paid"
    assert d["metadata"]["plan_tier"] == "pro"
    sub = d["subscription"]
    assert sub["status"] == "active"
    assert sub["items"]["data"][0]["price"]["id"] == "price_pro"


def test_as_dict_handles_none_and_plain_dict():
    assert _as_dict(None) == {}
    assert _as_dict({"a": 1}) == {"a": 1}


def test_price_id_for_tier(monkeypatch):
    monkeypatch.setenv("STRIPE_PRICE_PRO", "price_pro_test")
    monkeypatch.setenv("STRIPE_PRICE_PREMIUM", "price_premium_test")
    assert price_id_for_tier("pro") == "price_pro_test"
    assert price_id_for_tier("premium") == "price_premium_test"
    assert tier_for_price_id("price_pro_test") == "pro"


def test_billing_config_disabled_without_keys(monkeypatch):
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    monkeypatch.delenv("STRIPE_PRICE_PRO", raising=False)
    payload = billing_config_payload()
    assert payload["enabled"] is False


def test_billing_config_enabled_with_price(monkeypatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_x")
    monkeypatch.setenv("STRIPE_PRICE_PRO", "price_pro_test")
    payload = billing_config_payload()
    assert payload["enabled"] is True
    assert payload["pro_available"] is True


def test_site_url_sanitizes_mangled_secret(monkeypatch):
    from app.services.stripe_billing import _site_url

    monkeypatch.setenv("PUBLIC_SITE_URL", "https://readyforrobots.com' \\\\   -a ready-2-robot")
    assert _site_url() == "https://readyforrobots.com"
    monkeypatch.setenv("PUBLIC_SITE_URL", "readyforrobots.com")
    assert _site_url() == "https://readyforrobots.com"


def test_resolve_plan_tier_from_db_billing(monkeypatch):
    class FakeResult:
        billing_tier = "pro"

    class FakeExecute:
        def fetchone(self):
            return FakeResult()

    class FakeDB:
        def execute(self, *_args, **_kwargs):
            return FakeExecute()

    monkeypatch.delenv("ADMIN_EMAILS", raising=False)
    user = {"uid": "user-1", "email": "buyer@example.com", "plan_tier": ""}
    assert resolve_billing_tier_slug(user, db=FakeDB()) == "pro"
    assert resolve_plan_tier(user, db=FakeDB()) == PLAN_PAID
