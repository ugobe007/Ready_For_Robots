# Outcome: Drop Qualify loop; Place from jobs Next

**Date:** 2026-08-21
**Type:** build
**Status:** on branch

## What changed

Step 2 had two Next buttons (card + page bottom). Step 3 Qualify restated why/unknowns/blockers and the only CTA was ← Jobs, so 2→3 looped with no exit to buyers.

- Removed Next from the expanded job card
- Kept Next at the bottom of the jobs list
- Next opens Place (live buyer rows + See buyers → `/pipeline?src=place`)
- Rail: 01 Profile · 02 Jobs · 03 Place
- `src=place` is not a Jobs handoff, so pipeline shows sales leads instead of bouncing back to `/`

## Tests

`npx vitest run client/src/lib/jobsWorkflow.test.ts client/src/lib/jobsQualify.test.ts` — 22 passed
`npx tsc --noEmit` — clean
