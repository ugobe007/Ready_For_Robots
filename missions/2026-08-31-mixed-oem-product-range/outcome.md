# Outcome — mixed OEM product range

**Date:** 2026-08-31
**Branch:** `cursor/mixed-oem-product-range-009b`
**Status:** shipped on branch (Fly production not yet deployed)

## What shipped

Per-SKU FIND class from **work language → morphology → non-generic catalog class**. Generic `service_robot` is no longer a company dump. Company hubs expose `product_range` / `mixed_range`. Evidence-backed overlay `ontology/mixed_oem_sku_catalog.v1.json` merged like the vertical catalog. Live extract still wins.

Cleaning drones (Lucidbots Sherpa) stay `cleaning_drone`, not floor `cleaning` and not avionics. Floor specialists stay `cleaning`. Workbook `cleaning_robot` maps to FIND `cleaning`. `cleaning_drone` is a **configuration class**, not a 21st FIND tile (pstack still requires 20 tiles).

Jobs-seed `Keenon T8` collides with overlay `T8` (2-char model after a brand prefix). Overlay work copy / class wins over a thin `service_robot` dump. Family blob `AMR scrubbers` is not a named SKU.

## OEM classification (range + sample products)

| OEM | Hub range | Sample products |
|-----|-----------|-----------------|
| PUDU | serving, cleaning, humanoid | BellaBot serving; PuduBot 2 serving; CC1 cleaning; D9 humanoid |
| Keenon | serving, cleaning, hospitality, humanoid | Dinerbot T5 / T8 / T11 serving; C30 / C55 cleaning; Butlerbot W3 hospitality; XMAN-R1 / XMAN-F1 humanoid |
| UBTech | humanoid (+ Cruzr unclassified social) | Walker / Walker X humanoid — not waiters |
| AgiBot | humanoid | G1 / X2 / A2 embodied humanoids — not waiters |
| MagicLab | humanoid + quadruped | MagicBot X1 / Gen1 humanoid; MagicDog quadruped (`/en/dog`) |
| Deep Robotics | quadruped + humanoid | X20 / X30 quadruped; DR02 humanoid |
| Pringle Robotics | serving, cleaning | BellaBot serving; CC1 cleaning (Pudu-built SKUs named on pringlerobotics.ai) |
| Bear Robotics | serving, cleaning, amr | Servi / Servi Plus serving; Servi Clean cleaning |
| AotingBots | cleaning | SW80 A, SW55 A |
| Kärcher | cleaning | KIRA B 50 / B 200 / CV 50 / CV 60/1 only — not mop SKUs |
| Richtech | serving, cleaning | ADAM / Scotty serving; DUST-E MX cleaning (homepage 429) |
| CenoBots | cleaning | S5, L3, L4, L50, SP50 |
| Lucid Bots | cleaning_drone | Sherpa Drone / Sherpa Drone NDAA — not floor scrubbers |
| ECOVACS Commercial | cleaning | DEEBOT PRO M1, DEEBOT PRO K1 VAC |
| Avidbots | cleaning | Neo, Neo 2W, Kas |
| Gausium | cleaning | Phantas, Marvel, Vacuum 40, Scrubber 75 |
| PolarX | cleaning | Star50, Star60, Star40 |
| Tennant | (no named robotic SKU) | Live product listing HTTP 500; no T7AMR invented; `AMR scrubbers` family blob dropped |
| SEER | humanoid only | No named cleaner SKU on the listing page |

Thin SKUs without work or morphology copy stay unclassified (per-product lookup) rather than `service_robot`. Discovered listing names no longer inherit a sibling SKU class (PUDUA1 is not BellaBot serving).

## Tests

- `tests/test_mixed_oem_product_range.py` — Lucidbots, Pudu Bella vs CC1, Keenon waiter vs cleaner, Bear, Gausium/Avidbots/Ecovacs, Kaercher KIRA-only, Tennant no invented SKU, 20 FIND tiles
- vitest `knownOemLineups` + `jobsWorkflow` (`cleaning_drone` configuration, not tile)
- `python3 scripts/pstack_release.py --local` How / Act / Critic green

## Production gap

Fly `GET /api/oem-listing?url=https://www.pudurobotics.com/en` still returns every SKU as `service_robot` (pre-this-branch). Local listing splits serving / cleaning / humanoid. Needs Fly deploy after merge.

## Not invented

No PuduBot 3, no MagicBot Z1, no Lite3, no Tennant T7AMR. PUDUA1/D1/SH1 pages had no work copy — left unclassified. Kaercher overlay is robotic KIRA only. Richtech cleaning SKUs beyond DUST-E MX not invented from a 429 page.

## Leftovers / picker fallbacks

#195 remains open — not merged. Do not add pudu to `pstack/release.yaml` `find_urls` until Fly has this code.

Unclassified named SKUs (operator picker if live extract is silent): Pudu FlashBot / PUDUA1 / D1 / SH1; Keenon Peanut / M2 / S300 / S100; Bear Carti; Richtech MATRADEE / LUCKI / MEDBOT / AIDY / Scorpion / Titan; Gausium CD/WS docks. Tennant and SEER have no named robotic cleaning SKU in cache (`Seer Humanoid` is a class dump, not a product).
