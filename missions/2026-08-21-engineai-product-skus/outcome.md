# Outcome: Discover EngineAI SKUs from manufacturer product URLs

**Date:** 2026-08-21
**Type:** build
**Status:** on branch

## What changed

EngineAI homepage already lists PM01 / T800 / JS01 / SA01 / SE01 / S2 as `product-{sku}.html` links. `_discover_product_names` only spotted a Western SKU allowlist, so FIND skipped the picker (`products: []`, company-level facts).

- Harvest SKU-shaped slugs from manufacturer `product-` / `products/` paths
- Ignore generic paths (`product-purchase`)
- Cap discovered products at 8
- Bump profile cache namespace to `robot_profile_v3` so production does not keep the stale empty-product EngineAI row after #71

Not an OEM allowlist expansion.

Live EngineAI homepage: products `T800, PM01, SA01, JS01, S2, SE01`, `needs_product_choice=True`, domain `engineai.com.cn`.

## Follow-up

Fly deploy required for production picker. #71 already deployed; this busts the 6h cache that still has `products: []`.
