# Outcome — home live tape height

**Mission:** `missions/2026-08-21-home-jobs-tape`  
**Type:** build  
**Date:** 2026-08-21

## Cause

LiveJobTape rows are absolutely positioned. Height used to come from the 100vh right pane (`h-full` + `flex-1`). The page-scroll change removed that pane height. `min-h-[28rem]` on a wrapper does not give percentage height to children, so the list clipped to 0px. Home looked like jobs were not loading.

## What shipped

- Tape viewport sets `height: TAPE_VIEWPORT_PX` (12 × 58px).
- FIND no longer wraps the tape in `min-h-[28rem]`.

## Tests

- Vitest: `jobsWorkflow.test.ts` 21 passed (tape viewport height contract).
- Manual FIND: Live Robot Jobs shows 12 classified rows and a jobs-found count.
