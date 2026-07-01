"""Stripe billing helpers and DB-backed plan resolution."""
from __future__ import annotations

import os

import pytest

from app.services.plan_entitlements import PLAN_PAID, resolve_billing_tier_slug, resolve_plan_tier
from app.services.stripe_billing import billing_config_payload, price_id_for_tier, tier_for_price_id


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
