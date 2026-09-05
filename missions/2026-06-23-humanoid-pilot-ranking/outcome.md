# Outcome: Humanoid pilot ranking

**Date:** 2026-06-23  
**Status:** done

## What shipped

- **`app/services/humanoid_pilot_ranking.py`** — tiers `ACTIVE_PILOT` / `PILOT_INTENT` / `HUMANOID_MENTION`; OEM PR downgraded
- **Pipeline cards** — `humanoid_pilot_tier`, `humanoid_pilot_score`, `humanoid_pilot_label`, `humanoid_pilot_action`; strong pilots override `pipeline_action` with `Humanoid · …`
- **Next actions** — humanoid pilot leads sort ahead of generic HOT rows
- **UI** — teal **Humanoid** badge on pipeline rows; chip in `NextActionsPanel`

## Tests

`tests/test_humanoid_pilot_ranking.py` — **6/6**; pipeline next-actions humanoid boost covered.

## Deploy

Fly deploy + `refresh_pipeline_cache.py` to populate new fields on cached cards.

## Next

Backlog rank 1 cleared — run harness snapshot + re-rank from live friction (Unknown industry **52**, buyer-intent historical cleanup).
