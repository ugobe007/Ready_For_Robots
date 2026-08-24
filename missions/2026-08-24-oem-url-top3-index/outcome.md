# Outcome — OEM URL top-3 index

**Date:** 2026-08-24
**Status:** code complete; production Fly still on previous revision until merge/deploy

## What shipped

- Compiler `scripts/compile_jobs_vendor_index.py` turns `docs/calibration/robot_vendor_seed_v1.json` into `app/data/vendor_robots_jobs_seed.json`.
- Jobs seed (this compile): **329 vendors, 380 robots**. Skipped: 72 already indexed, 66 generic names, 15 junk hosts, 12 not OEM, 6 no site.
- Merged FIND index: **408 vendors, 530 robots**.
- FIND lists **3 robots at a time** (backend cap + picker display cap).
- Parse order: product names, then nearby/seed description, then payload/runtime only if present.
- Retailer/research homepages (Amazon, Walmart, mi.com, …) are not OEM listings. ABB / Yaskawa aliases map to named robots (ASTI AMR; Yaskawa GP/HC).

## Examples

| URL | Top robots |
|-----|------------|
| https://www.mobile-industrial-robots.com/ | MiR250, MiR600, MiR1350 |
| https://ottomotors.com/ | OTTO 100, OTTO 750, OTTO 1500 |
| https://www.hairobotics.com/ | HAIPICK |
| https://www.universal-robots.com/ | UR3e, UR5e, UR10e |
| https://www.reflexrobotics.com/ | (existing humanoid index, unchanged) |

## Follow-ups

Deploy `ready-2-robot` after merge so production FIND uses catalog-first + this seed. Generic `AGV/AMR` rows stay unnamed until a later pass has real SKUs.
