# Outcome: Remove Qualify CTA from the jobs list

**Date:** 2026-08-21
**Type:** build
**Status:** on branch · smoke-tested

## What changed

Step 2 is inspect jobs. There is no next step on that list.

- Removed **Qualify this job** (and the inner request / judgment slip)
- Removed leftover CTA constants that still said "Qualify this job →"
- Removed “Qualify it — that is the next step, on this page.”
- Bounce screens no longer tell the user to qualify a job
- Jobs heading is the selected robot (`Jobs for Servi`), not the company while a SKU is selected
- Cards still expand to why / unknowns / blockers. See All stays.

## Tests

`npx vitest run client/src/lib/jobsWorkflow.test.ts client/src/lib/jobsHandoffSnapshot.test.ts` — 15 passed
`npx tsc --noEmit` — pass

## Smoke (local `/`, Bear Robotics → Servi)

- Heading: **Jobs for Servi** (not Jobs for Bear Robotics)
- Subtitle: expand a card for why, unknowns, and blockers — no “next step”
- Job 01 / Job 02 expanded: Why Servi + still unknown + no blocker; **no QUALIFY THIS JOB**
- See All 12 jobs stays on the same page; still no Qualify CTA
