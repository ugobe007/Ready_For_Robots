# Outcome — Wire CRM into the Jobs workflow

**Date:** 2026-08-26  
**Status:** in PR

## Diff

- Canonical spec: `docs/jobs_crm.md` (signup wall, free 5 / 3×5 / 7-day, paid uncapped, export, agent rules).
- Process step 03 is **CRM**. Job-list CTA is **Open CRM →**.
- Checking a Keep row writes `rfr_jobs_handoff_v1` immediately (`jobsDumpedToCrm`).
- Open CRM / header CRM / unsigned desk use `jobsCrmOpenHref` — signup wall restored in front of the desk, not in front of Job Cards.
- Pipeline actions (kept from FIND, Place, apply) append to `rfr_pipeline_activity_v1` and show on the deal.
- Entitlement constants: `JOBS_CRM_FREE_BATCH=5`, `JOBS_CRM_FREE_MONTHLY_CAP=15`, `JOBS_CRM_FREE_TTL_DAYS=7`. Paid helpers return `None` (uncapped). UI does not show meters until the API enforces them.

## Tests

`pnpm exec vitest run` jobsWorkflow (+ related). `pytest tests/test_plan_entitlements.py`.

## Follow-ups

1. Persist dumped jobs + activity on the account.
2. Enforce 7-day TTL and 15/month on the API (free only).
3. Paid: all matching jobs, not only the last FIND dump.
4. Export Robot Jobs to HubSpot / CSV.
