# Outcome: Kill the post-login Jobs dead-end

**Date:** 2026-08-20
**Type:** build
**Status:** shipped to branch (frontend; Vercel preview on push)

## What changed

FIND and QUALIFY stay on `/`. The post-login "Jobs for ______ robot" board is gone.

- Job cards select + **Qualify this job** / **Request qualification** (`rdd_qualify_opened`, `rdd_qualify_requested`)
- Page-level "Next step: Jobs for your robot →" footer removed
- `/pipeline?src=jobs_*` and `/results?src=jobs_*` bounce to `/?restore=1`
- Header **Pipeline** is `/pipeline` (CRM), not a Jobs replay
- See All expands more jobs on the same page

## Tests

`npx vitest run client/src/lib/jobsWorkflow.test.ts client/src/lib/jobsHandoffSnapshot.test.ts client/src/lib/signupWorkflowPath.test.ts` — 20 passed
`npx tsc --noEmit` — clean

## Follow-ups

PLACE later still lives on `/pipeline` as CRM. Do not reopen SIGNAL/CRM as the Jobs next step.
