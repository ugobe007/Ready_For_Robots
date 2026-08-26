# Mission: Catalogue every named robot per OEM

**Date:** 2026-08-26
**Agent:** ProductSurface + Deploy
**Status:** partial (verified SKUs indexed; industrial catalogs not exhausted)
**Type:** build

## Goal

For each robot company in the OEM/SKU catalog, discover and index **all named products** from verified official hosts. COMPANY → PRODUCT (named SKU) → FIND lookup. Never company → category → jobs. Never treat OEMs as Job Card employers or SIGNAL leads.

Workbook seed (#150) is 61 OEMs / 133 named SKUs. This mission expands beyond those rows using official product listing pages only.

## Acceptance criteria

- [x] Named SKUs discovered from verified company/product hosts land in `ontology/oem_sku_catalog.v1.json` and `app/data/vendor_robots_oem_sku_seed.json`. Empty specs stay UNKNOWN. No invented SKUs or rental $.
- [x] Stretch-on-Spot and sibling-wrong URLs are never stored. Series blobs (`UR Series`) are rejected when named models exist.
- [x] Verified URLs persist in `app/data/oem_sku_url_lookup.json`. Discovery is resume-friendly. 404/403/429 = failed, not guessed.
- [x] Dedup keeps Dexmate Vega / commercial Stretch richer jobs-seed rows; product URL still pins the SKU (UR20-style collision fixed).
- [x] `--apply` documented if DATABASE_URL is missing. No invented credentials.
- [x] Tests: new SKUs indexed; Vega no regress; no junk series blobs.
- [x] If 61 × full catalogs does not finish in one run: complete as many OEMs as verified URLs allow; leave resume command + per-OEM counts in `outcome.md`. Do not fake completeness.

## Out of scope

Hermes, Cal, Vercel AI Gateway, MARKET_GRAPH_RUN_RESEARCH, invented economics, SIGNAL hop, matcher deletion, treating OEMs as employers.
