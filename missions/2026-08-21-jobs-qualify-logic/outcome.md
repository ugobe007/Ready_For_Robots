# Outcome: Remove Qualify CTA from the jobs list

**Date:** 2026-08-21
**Type:** build
**Status:** on branch

## What changed

Step 2 is inspect jobs. There is no next step on that list.

- Removed **Qualify this job** (and the inner request / judgment slip)
- Removed “Qualify it — that is the next step, on this page.”
- Jobs heading is the selected robot (`Jobs for Servi`), not the company while a SKU is selected
- Cards still expand to why / unknowns / blockers. See All stays.

## Tests

`npx vitest run client/src/lib/jobsWorkflow.test.ts` 
`npx tsc --noEmit`
