# Outcome: Next on step 2 opens QUALIFY

**Date:** 2026-08-21
**Type:** build
**Status:** on branch

## What changed

Jobs is step 2. Next leaves it for step 3.

- Page-level **Next →** on the jobs list (expanded job). Not Qualify this job on the card.
- Rail: 01 Profile · 02 Jobs · 03 Qualify
- Qualify panel: pursue / needs evidence / not now from why, unknowns, blockers
- No hop to `/pipeline`

## Tests

`npx vitest run client/src/lib/jobsWorkflow.test.ts client/src/lib/jobsQualify.test.ts client/src/lib/jobsHandoffSnapshot.test.ts` — 24 passed
`npx tsc --noEmit` — pass
