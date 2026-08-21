# Outcome: Qualify is a judgment, not a request slip

**Date:** 2026-08-21
**Type:** build
**Status:** on branch

## What changed

`Qualify this job` now returns a pursuit brief from evidence FIND already produced (`why` / `still_unknown` / `blockers`):

- **Worth pursuing** — confirmed why, no blocker
- **Not enough to decide** — no confirmed why
- **Do not pursue this yet** — blocker or not a match

One click. No inner "Request qualification". No matcher reopen. No /pipeline hop. Anonymous users see the brief before signup.

## Tests

`npx vitest run client/src/lib/jobsQualify.test.ts client/src/lib/jobsWorkflow.test.ts` — 18 passed
`npx tsc --noEmit` — clean
