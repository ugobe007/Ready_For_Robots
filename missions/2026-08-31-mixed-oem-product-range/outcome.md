# Outcome — mixed OEM product range

**Date:** 2026-08-31
**Branch:** `cursor/mixed-oem-product-range-009b`
**Status:** shipped on branch (Fly production not yet deployed)

## What shipped

Per-SKU FIND class from **work language → morphology → non-generic catalog class**. Generic `service_robot` is no longer a company dump. Company hubs expose `product_range` / `mixed_range`. Evidence-backed overlay `ontology/mixed_oem_sku_catalog.v1.json` merged like the vertical catalog.

## OEM classification (range + sample products)

| OEM | Hub range | Sample products |
|-----|-----------|-----------------|
| PUDU | serving, cleaning, humanoid | BellaBot serving; CC1 cleaning; D9 humanoid (official bipedal page) |
| Keenon | serving, cleaning, hospitality | Dinerbot T5 / T11 serving; C30 / C55 cleaning; Butlerbot W3 hospitality |
| UBTech | humanoid (+ Cruzr unclassified social) | Walker / Walker X humanoid — not waiters |
| AgiBot | humanoid | G1 / X2 / A2 embodied humanoids — not waiters |
| MagicLab | humanoid + quadruped | MagicBot X1 / Gen1 humanoid; MagicDog quadruped (`/en/dog`) |
| Deep Robotics | quadruped + humanoid | X20 / X30 quadruped (official product pages); DR02 humanoid (official dr02.html) |

Thin SKUs without work or morphology copy stay unclassified (per-product lookup) rather than `service_robot`.

## Tests

- `tests/test_mixed_oem_product_range.py` — 7 passed (no fetch/facts)
- `tests/test_fnb_service_extract.py` + oem catalog + jobs listing + SKU-not-tile + ag classes — 69 passed
- pstack pytest (release, healthcare, ontology) — 64 passed
- `pstack_release.py --local` — How / Act / Critic green
- vitest `knownOemLineups` + `jobsWorkflow` — 43 passed

## Production gap

Fly `GET /api/oem-listing?url=https://www.pudurobotics.com/en` still returns every SKU as `service_robot` (pre-this-branch). Local listing splits serving / cleaning / humanoid. Needs Fly deploy after merge.

## Not invented

No PuduBot 3, no MagicBot Z1 (homepage `/en` 404 this pass), no Lite3 row (news mentions only). PUDUA1/D1/SH1 pages had no work copy — left unclassified.

## Leftovers

#195 remains open/conflicting — not merged. Keenon T8/T3/S100 lack product-page work copy in cache. Cruzr stays unclassified (reception copy, not a waiter and not bipedal evidence).

## What shipped

Per-SKU FIND class from **work language → morphology → non-generic catalog class**. Generic `service_robot` is no longer a company dump. Company hubs expose `product_range` / `mixed_range`. Evidence-backed overlay `ontology/mixed_oem_sku_catalog.v1.json` merged like the vertical catalog.

## OEM classification (range + sample products)

| OEM | Hub range | Sample products |
|-----|-----------|-----------------|
| PUDU | serving, cleaning, humanoid | BellaBot serving; CC1 cleaning; D9 humanoid (official bipedal page) |
| Keenon | serving, cleaning, hospitality | Dinerbot T5 / T11 serving; C30 / C55 cleaning; Butlerbot W3 hospitality |
| UBTech | humanoid (+ Cruzr unclassified social) | Walker / Walker X humanoid — not waiters |
| AgiBot | humanoid | G1 / X2 / A2 embodied humanoids — not waiters |
| MagicLab | humanoid + quadruped | MagicBot X1 / Gen1 humanoid; MagicDog quadruped (`/en/dog`) |
| Deep Robotics | quadruped + humanoid | X20 / X30 quadruped (official product pages); DR02 humanoid (official dr02.html) |

Thin SKUs without work or morphology copy stay unclassified (per-product lookup) rather than `service_robot`.

## Tests

- `tests/test_mixed_oem_product_range.py` (no fetch/facts)
- vitest `knownOemLineups` + `jobsWorkflow` Pudu mixed lookups
- Targeted pytest: fnb extract, oem catalog, jobs listing, SKU-not-tile, ag classes

## Not invented

No PuduBot 3, no MagicBot Z1 (homepage 404 on `/en` this pass), no Lite3 row (news mentions only). PUDUA1/D1/SH1 pages had no work copy — left unclassified.

## Leftovers

Fly production still serves pre-this-branch FIND until deploy. #195 remains open/conflicting — not merged. Keenon T8/T3/S100 lack product-page work copy in cache.
