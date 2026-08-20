# Outcome: All-robots submit lands on jobs + 5 buyer leads

**Date:** 2026-08-20
**Status:** done

## What changed

Clicking **Find jobs for all N robots** no longer dumps the user on a SKU catalog.

- One company-level `/api/robot-job-search` (first product), not N full rebuilds
- Lands on **JOBS** with a company heading
- Always-visible next step: **See 5 buyer leads →** (`/results?limit=5` anonymous, `/pipeline` signed-in)
- Catalog, if opened, has the same next-step CTAs
- Grounded company profile cache can overlay a SKU without rebuilding sources
- Identity-only picker cache is not used for matching

## Tests

- `venv/bin/python -m pytest tests/test_robot_job_search.py` — 9 passed
- `venv/bin/python -m pytest tests/test_lead_filter_junk.py tests/test_buyer_intent_gate.py` — 227 passed
- `pnpm exec vitest run client/src/lib/jobsWorkflow.test.ts` — 5 passed
- `pnpm exec tsc --noEmit` — clean

## Follow-ups

- First identity lookup can still be slow on a cold Unitree homepage fetch (separate from the all-robots N-search bug)
- Deploy via Fly after merge so production `/` picks up the workspace change
