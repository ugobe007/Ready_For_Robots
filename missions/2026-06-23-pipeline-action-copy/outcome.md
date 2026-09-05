# Outcome: Pipeline action copy

**Date:** 2026-06-23  
**Status:** done

## What shipped

- **`app/services/pipeline_action_copy.py`** — canonical industry → `automation_type`, `pain_point`, `pipeline_action`; `pipeline_action_for_lead()` with HOT/WARM/COLD prefix and labor/capex signal tweaks.
- **`app/api/leads.py`** — `_automation_ctx()` delegates to canonical copy; `_fmt_pipeline_card()` emits `share_blurb` + `pipeline_action`.
- **`app/services/lead_sales_copy.py`** — `_industry_pain()` uses canonical pain points.
- **`app/services/plan_entitlements.py`** — anonymous teaser includes `pipeline_action`.
- **Frontend** — `pipelineLeadMap.ts` maps `pipeline_action`; `Pipeline.tsx` card subtitle prefers `pipelineAction` over raw signal.

## Tests

`tests/test_pipeline_action_copy.py` — **6/6** pass (unit + `_fmt_pipeline_card` integration).

## Cache rebuild

Ran `python3 scripts/refresh_pipeline_cache.py` (~59s):

| Surface | Count |
|---------|-------|
| `pipeline_feed_leads` | **35** |
| `homepage_hot_leads` | 46 |
| `leads_12_HOT` | 12 |
| Anonymous visible (API) | **9** |

Cards now carry industry-specific rep actions (e.g. Hospitality → housekeeping/runner robot pitch).

## Deploy

- **API/cache:** live immediately (Postgres cache + Fly API).
- **Frontend:** deploy `readyforrobots-new/` for UI card subtitle change.

## Next

Rank 1: `next-actions-panel` — home right rail top 3 autonomous actions.
