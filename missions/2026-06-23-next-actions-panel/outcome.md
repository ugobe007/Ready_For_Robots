# Outcome: Next actions panel

**Date:** 2026-06-23  
**Status:** done

## What shipped

- **`app/services/pipeline_next_actions.py`** — rank HOT → WARM → COLD pipeline cards into top-N actions
- **`GET /api/leads/pipeline-next-actions?limit=3`** — public cache read; respects plan entitlements
- **`NextActionsPanel.tsx`** + **`usePipelineNextActions`** — dark editorial right-rail UI
- **Home hero** — live top-3 panel under `HeroLeadTicker`
- **Pipeline** — compact panel above deal list; click selects lead

## Tests

`tests/test_pipeline_next_actions.py` — **4/4** pass (plus existing pipeline_action_copy suite).

## Live API (post-deploy)

Verify: `GET /api/leads/pipeline-next-actions?limit=3` returns ranked actions with `pipeline_action` labels.

## Deploy

Fly deploy required for API + frontend bundle.

## Next

Rank 1: `humanoid-pilot-ranking` — tag + rank humanoid pilot language.
