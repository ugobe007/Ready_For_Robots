# Outcome — Jobs page scroll

**Mission:** `missions/2026-08-21-jobs-page-scroll`  
**Type:** build  
**Date:** 2026-08-21

## Cause

The Jobs workspace was a viewport-locked two-pane box (`h-[calc(100vh-76px)] overflow-hidden`). Chrome had no document to scroll. Step 03 sat below a fold the browser could not reach. Pinning Activate inside the pane was a patch on that architecture.

## What shipped

- Jobs is a three-step process on a normal page (`docs/EXPERIMENT_MODE.md` architecture lock).
- Process chrome at the top (under the site header) and at the bottom of the page.
- Workspace grows with content. The document scrolls.
- Activate stays in the jobs list (document flow), not in a clipped inner scroller.

## Tests

Vitest `jobsWorkflow.test.ts` — see this cycle's run.
