# Outcome — OEM full catalog (named SKUs per company)

**Date:** 2026-08-26
**Status:** partial by design — verified named SKUs only; industrial catalogs not exhausted
**Branch:** `cursor/oem-full-catalog-009b`

## What shipped

1. **Discovery.** `app/services/oem_sku_discover.py` + `--discover-skus` on `scripts/ingest_oem_sku_catalog.py`. Walks official listing pages / sitemaps on verified OEM hosts via Understanding `fetch_page` (no archive, 0.4s rate limit). Named models only. 404/403/429 stay failed. Resume file: `app/data/oem_sku_discovery.json`.
2. **Merge pin.** `vendor_robot_lookup` treats `UR20` / `Universal Robots UR20` as one SKU and overlays a SKU-path `product_url` onto the richer jobs-seed row. Dexmate Vega and commercial Stretch keep specs/claims.
3. **Index.** Ontology `oem_sku_catalog.v1.json` and FIND seed `vendor_robots_oem_sku_seed.json` rebuilt from the workbook plus verified listing SKUs. Empty specs stay `UNKNOWN`.
4. **Scrub.** First loose pass ingested nav/TV/news titles; those rows were dropped. Remaining extras are named product pages.

These rows are robots for work, not SIGNAL leads or Job Card employers.

## SKU counts

| | N |
|--|--|
| Workbook (#150) | **133** |
| After this mission | **188** |
| Newly indexed named SKUs | **55** |
| Companies | **61** (unchanged) |
| Catalog rows with verified `product_url` | **117** |

## OEMs completed vs remaining

Listing pass completed (no further listing URLs in the current budget): **27**.

Visited but still partial (more listing pages, `oem_cap`, or no extra named models on the pages we fetched): **34**.

**New named SKUs landed for:** 1X (Neo), Aethon (T3), Bear (Carti 100), Ecovacs (Deebot X12S), Figure (FIGURE 03), Gausium (6), Keenon (10), OTTO (1200), Pudu (4), Seegrid (4), UBTECH (Walker / Walker S2 / Alpha 1E), Unitree (12), Yaskawa GP series (10).

**No extra named models from the listing pages we could verify** (not a claim that the OEM has only the workbook rows): ABB, FANUC, KUKA, Universal Robots (already 9), MiR, Locus, Intuitive, Tesla, and most single-SKU service OEMs. FANUC/ABB/KUKA official catalogs are much larger; their `/products` hubs did not yield named model URLs in this fetch budget.

**Unitree L2** is indexed from `unitree.com/L2` (page mentioned L2). It may be a LiDAR, not a mobile robot — left as a named product URL, not guessed away.

## Scrape stats (last resume + prior)

| Status | N |
|--------|---|
| Verified product pages kept after scrub | **91** |
| Failed (404 / 403 / 429 / sku_not_on_page / empty) | **220** |
| Skipped (wrong-product / sibling) | **38** |
| Queued (budget / oem_cap) | **186** |
| Fetches this resume | **280** (plus 320 + 300 earlier) |
| Scrubbed junk titles | **6** this pass (154 in the first loose pass) |

Resume (do not invent SKUs):

```bash
PYTHONPATH=. python3 scripts/ingest_oem_sku_catalog.py --discover-skus --rate-limit 0.4 --max-fetches 300 --max-new-per-oem 12
```

## DB load

`DATABASE_URL` / `HARNESS_DATABASE_URL` unavailable. Seed JSON is the FIND index.

Leftover apply:

```bash
alembic upgrade head
PYTHONPATH=. python3 scripts/ingest_oem_sku_catalog.py --apply
```

## FIND smoke (catalog-first, no live OEM fetch)

| URL | Result |
|-----|--------|
| `https://www.universal-robots.com/products/ur20/` | Universal Robots → Universal Robots UR20 (jobs-seed name, SKU path pinned) |
| `https://www.dexmate.ai/product/vega` | Dexmate → Dexmate Vega (no regress) |
| `https://bostondynamics.com/products/stretch` | Boston Dynamics → Stretch (not Spot) |
| `https://www.figure.ai/figure` | Figure AI → Figure 03 |
| `https://www.keenon.com/en/product/C55` | Keenon → C55 |
| `https://www.unitree.com/go2/` | Unitree → GO2 |

## Tests

`tests/test_oem_sku_catalog.py` + `tests/test_vendor_robot_lookup.py` — 19 passed.

## Follow-ups

- Resume discovery for Yaskawa remainder (GP/AR/HC beyond the 12-SKU cap) and FANUC/ABB/KUKA model list pages.
- Set `DATABASE_URL` and run leftover `--apply`.
- Parent opens draft PR (ManagePullRequest not in this agent tool set).
