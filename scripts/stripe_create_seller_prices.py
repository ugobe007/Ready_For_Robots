#!/usr/bin/env python3
"""Create the Founding seller ($49/mo) and Pro ($199/mo) prices in Stripe TEST mode.

Usage:
    STRIPE_SECRET_KEY=sk_test_... python3 scripts/stripe_create_seller_prices.py

Refuses live keys. Safe to re-run: prices are found by lookup_key before creating.
Prints the env vars to set (STRIPE_PRICE_FOUNDING_SELLER, STRIPE_PRICE_SELLER_PRO).
"""
from __future__ import annotations

import os
import sys

PLANS = (
    ("STRIPE_PRICE_FOUNDING_SELLER", "rfr_founding_seller_monthly", "Founding seller", 4900),
    ("STRIPE_PRICE_SELLER_PRO", "rfr_seller_pro_monthly", "Pro", 19900),
)


def main() -> int:
    key = (os.getenv("STRIPE_SECRET_KEY") or "").strip()
    if not key.startswith(("sk_test_", "rk_test_")):
        print("Refusing to run: STRIPE_SECRET_KEY must be a test-mode key (sk_test_ / rk_test_).")
        return 2

    import stripe

    stripe.api_key = key
    for env_name, lookup_key, product_name, amount in PLANS:
        found = stripe.Price.list(lookup_keys=[lookup_key], active=True, limit=1)
        if found.data:
            price = found.data[0]
        else:
            product = stripe.Product.create(
                name=f"Ready For Robots — {product_name}",
                metadata={"rfr_plan": lookup_key},
            )
            price = stripe.Price.create(
                product=product.id,
                currency="usd",
                unit_amount=amount,
                recurring={"interval": "month"},
                lookup_key=lookup_key,
                nickname=f"{product_name} monthly",
            )
        print(f"{env_name}={price.id}  # {product_name} ${amount // 100}/month, test mode")
    return 0


if __name__ == "__main__":
    sys.exit(main())
