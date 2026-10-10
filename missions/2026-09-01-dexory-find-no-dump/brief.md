# Dexory FIND: DexoryView is not a dump class

**Date:** 2026-09-01  
**Type:** build  
**Branch:** `cursor/dexory-find-no-dump-009b` from `origin/main` @ `3abc2b6e`

## Observe

Live `POST /api/robot-job-search` for `https://www.dexory.com/`:

- Listing overlay: DexoryView, `display_class` null (tests already require this)
- Fly FIND: DexoryView, `robot_class=service_robot`, 0 jobs, class picker
- Catalog skip: "skipped live manufacturer fetch". Impact is not in the product list on this path
- Dexory homepage still says Forrester "Total Economic Impact™". Chrome labels already treat `Impact` as nav, not a SKU

Tennant named robots and Dexmate Job Cards are healthy. Cal desk is 401 without auth, not a 500. Latest `deploy.yml` for #205 was cancelled, not a timeout that blocks this FIND dump.

## Goal

FIND for Dexory must match the listing. DexoryView stays the named product. It stays unclassified. Do not dump `service_robot`. Do not invent a scanner SKU. `Impact` stays chrome.

## Acceptance

- Mixed catalog and vendor seed: DexoryView `primary_class` is null. No `indexed class service_robot` claim
- `compile_vendor_seed` does not fill missing class with `service_robot`
- FIND profile does not restore generic `service_robot` via `prefer(...) or claimed`
- Discover on Dexory-like HTML with Impact™ does not put Impact in the picker
- Critic corpus still expects DexoryView and forbids Impact
- No Fly deploy unless the operator asks. This is a live FIND dump class

## Not

Cal-as-core, SIGNAL, #195, leftover #202, Alembic SSH, re-dispatch of the cancelled Fly push
