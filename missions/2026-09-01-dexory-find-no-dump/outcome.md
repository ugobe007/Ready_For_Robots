# Outcome. Dexory FIND dump class

**Date:** 2026-09-01
**Branch:** `cursor/dexory-find-no-dump-009b`
**Status:** complete (draft PR; not Fly-deployed)

Read [`REVIEW.md`](REVIEW.md).

## Observe

Live Dexory FIND dumped `service_robot` onto DexoryView (0 jobs, class picker) while listing left it unclassified. Catalog skip, so Impact was not in the picker. Tennant/Dexmate FIND were healthy. Cal 401 without auth.

## Shipped

- DexoryView unclassified in mixed catalog, vendor seed, known OEM lineup
- Seed compile no longer fills missing class with `service_robot`
- FIND does not restore generic `service_robot` from a catalog claim
- Impact / Total Economic Impact stay chrome

## Tests

`tests/test_dexory_find.py` plus mixed-OEM / critic / scrape-params. 110 passed. Vitest lineup passed.

## Follow-ups

- Operator deploy when they want production FIND to match listing
- Do not merge #195
- Alembic `jtm0a1b2c3d4` still not SSH-confirmed
