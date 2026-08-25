# Task-model contract + Cal jobs (not sales)

**Date:** 2026-08-25  
**Type:** build  
**Status:** done  
**PR:** https://github.com/ugobe007/ready_for_robots/pull/138

## Diff

- Ontology `task_model_ontology.v1.json` 1.2.0: model layers, time bands, data contract, no automatic field-data rebate
- Job Card “To place this job” (layer, who trains, typical time, data you provide)
- Practitioner doc: `docs/robot_task_model_contract.md`
- Cal: `CAL_BUYER_SALES_ENABLED` default off — skip buyer-sales drafts and new intros
- Digest: 0 robot-sales intros is expected; HOT queue is not a send list
- Seller brief / persona: jobs at a named employer, not robot sales

## Metrics

No pipeline cache / junk-score delta this cycle. QUALIFY honesty + Cal integrity.

Production after `fly deploy` (version **2822**, image `deployment-01M0X7ZJW5H50TPG0XWN5MAT6S`):
- `GET /api/leads/pipeline` — 200, `built_at` 2026-08-25T19:58:29Z, 5 leads
- `POST /api/robot-job-match` Vega/Dexmate profile — CNC jobs return `card_contract` (site-adapted, integrator, 4–12 weeks, no automatic rebate)
- Fly static bundle includes `To place this job` / `modelContract`. Canonical Vercel `readyforrobots.com` still serves the previous JS until that deploy catches up.

## Tests

- pytest task models + Cal digest/seller/autonomy/voice/ontology: 51 passed
- vitest `robotJobCard.test.ts`: 5 passed

## Follow-ups

- Do not invent dollar prices or dump pricing indexes on the Job Card
- Do not turn `CAL_BUYER_SALES_ENABLED` on
- Do not expand Cal into a new jobs-placement email product this cycle
- Production Cal still runs old code until this branch is deployed
- Canonical Vercel homepage may lag Fly static until frontend deploy
