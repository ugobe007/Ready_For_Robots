# Outcome — Indexed OEM homepages skip live fetch

**Date:** 2026-08-24
**Status:** code complete, tests green; production Fly not deployed from this branch

## Diff

- `app/services/robot_understanding_v1/pipeline.py` — if the vendor index has robots for the host, stub the homepage and skip `fetch_page`.
- `tests/test_catalog_first_lookup.py` — Reflex picker without live fetch; indexed SKUs boom if fetch is called.
- `tests/test_richtech_vendor_lookup.py` — same contract for Richtech.
- FIND timeout copy: homepage of a known OEM is valid.

## Metrics

- `build_robot_profile("https://www.reflexrobotics.com/")` → 5ms, `home_fetch=skipped`, picker: Reflex Gen2, Reflex Humanoid.
- pytest: 19 passed (`test_catalog_first_lookup`, `test_richtech_vendor_lookup`, `test_vendor_robot_lookup`).
- vitest: `jobsWorkflow.test.ts` 28 passed.

## Follow-ups

Deploy `ready-2-robot` after merge so production FIND stops waiting on reflexrobotics.com.
