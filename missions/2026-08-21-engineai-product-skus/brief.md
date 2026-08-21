# Mission: Discover EngineAI SKUs from manufacturer product URLs

**Date:** 2026-08-21
**Type:** build
**Agents:** LeadQuality / ProductSurface
**Status:** in progress

## Goal

`https://en.engineai.com.cn/` FIND shows a product picker (PM01, T800, …) instead of skipping to company-level jobs with `products: []`.

## Why

Homepage already links `product-pm01.html`, `product-t800.html`, etc. Identity only spotted a Western SKU allowlist (`Digit`, `Neo`, …), so EngineAI SKUs were invisible. Not an allowlist expansion — harvest manufacturer product paths.

Also bump `robot_profile` cache to v3 so production does not keep the stale empty-product EngineAI profile (6h TTL) after #71.

## Acceptance

- [x] `_sku_from_product_href("…/product-pm01.html") == "PM01"`
- [x] EngineAI-shaped homepage → products include PM01 and T800; `product-purchase` ignored
- [x] Digit still discovered without a `product-` path
- [x] Cache namespace `robot_profile_v3`
- [x] Tests pass
- [x] Live EngineAI fetch → needs_product_choice, products PM01/T800/…
