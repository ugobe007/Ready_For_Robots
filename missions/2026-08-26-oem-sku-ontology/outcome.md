# Outcome — OEM/SKU ontology + FIND identity

**Date:** 2026-08-26
**Status:** code complete; prod DB apply leftover (no DATABASE_URL in this environment)
**Branch:** `cursor/oem-sku-ontology-009b`

## What shipped

1. **Ontology.** Loader `scripts/ingest_oem_sku_catalog.py` reads `docs/reference/readyforrobots_companies_and_robots.xlsx` → `ontology/oem_sku_catalog.v1.json` (61 companies, 133 named SKUs). Empty specs stay `UNKNOWN`. No invented payload/price. Stretch-on-Spot flagged, never stored.
2. **FIND index.** Compiled `app/data/vendor_robots_oem_sku_seed.json`. `vendor_robot_lookup` merges it after the jobs seed so existing richer SKUs (Dexmate Vega, Stretch) win; new named SKUs append.
3. **URL lookup.** Understanding `fetch_page` (no archive, 0.35–0.4s rate limit). Persist only fetched/verified pages in `app/data/oem_sku_url_lookup.json`.
4. **DB path.** Alembic `osku0a1b2c3d4` adds `lookup_host` + indexes on `manufacturers` / `robot_models`. `--apply` upserts those FIND catalog tables. No parallel robots table. SQLite smoke: 61 manufacturers, 133 models.

## Scrape results

| Status | N |
|--------|---|
| Verified URLs stored | **61** |
| Skipped (wrong-product or company-page-only) | **25** (Stretch + 2 sibling-path + 22 company-page-only) |
| Failed (404 / 403 / 429 / empty / SSRF) | **47** |
| Queued | **0** |
| Fetches this run | 90 + 9 resume |

Resume: `PYTHONPATH=. python3 scripts/ingest_oem_sku_catalog.py --lookup-urls`

## DB load

| | |
|--|--|
| Tables | `manufacturers`, `robot_families`, `robot_models` |
| SQLite smoke | 61 / 1-family-per-OEM / 133 (61 with `product_url`) |
| Prod | **dry-run** — `DATABASE_URL` / `HARNESS_DATABASE_URL` unavailable |

Leftover apply (do not invent credentials):

```bash
alembic upgrade head
PYTHONPATH=. python3 scripts/ingest_oem_sku_catalog.py --apply
```

## FIND smoke (catalog-first, no live OEM fetch)

| URL | Result |
|-----|--------|
| `https://www.universal-robots.com/products/ur20/` | Universal Robots → UR20, `home_fetch=skipped` |
| `https://www.dexmate.ai/product/vega` | Dexmate → Dexmate Vega (no regress) |
| Boston Dynamics Stretch | Commercial Stretch URL kept; Spot page is not stored on Stretch |

These rows are robots for work, not SIGNAL leads.

## Tests

`tests/test_oem_sku_catalog.py` (8) + vendor/catalog-first/jobs listing (37) green in a local venv. App-import HTTP listing test needs `reportlab` (env gap, unchanged).

## Follow-ups

- Set `DATABASE_URL` and run leftover apply on prod/Supabase.
- Re-run `--lookup-urls` for the 47 failed hosts (ABB TLS, Amazon 404, Figure 404, 429s).
- Parent opens draft PR (ManagePullRequest not in this agent tool set).
