# Mission: Wire OEM/SKU catalog into ontology + FIND identity

**Date:** 2026-08-26
**Agent:** ProductSurface + Deploy
**Status:** in_progress
**Type:** build

## Goal

Ingest the operator workbook (`docs/reference/readyforrobots_companies_and_robots.xlsx`, 61 OEMs / 133 named SKUs) into the ontology the matcher already reads, look up real product URLs with the existing fetch path, and load OEM + SKU + host into the FIND catalog tables so submit-URL identifies the company quickly.

## Acceptance criteria

- [ ] Named SKUs land in `ontology/oem_sku_catalog.v1.json` and `app/data/vendor_robots_oem_sku_seed.json` (COMPANY → PRODUCT). Empty specs stay UNKNOWN. No invented payload/price.
- [ ] Stretch-on-Spot and other wrong-product URLs are flagged and never stored.
- [ ] Loader script can re-run the ingest; URL lookup is rate-limited and persists only fetched/verified pages.
- [ ] FIND host lookup resolves catalog OEMs (UR20, Dexmate Vega unchanged). These rows are robots for work, not SIGNAL leads.
- [ ] DB upsert targets `manufacturers` + `robot_models` (with `lookup_host` indexes). No parallel robots table. Apply command documented if DATABASE_URL is missing.
- [ ] Targeted pytest green. No Hermes / Cal / Vercel AI Gateway.

## Out of scope

Fake specs. Treating OEMs as Job Card employers. Force push / merge. Live crawl of every SKU page after the rate-limit budget.
