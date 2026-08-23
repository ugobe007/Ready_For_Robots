# Outcome — Jobs footer matches header (no Pipeline / SIGNAL)

**Date:** 2026-08-23  
**Type:** build  
**Status:** in progress

## Diff

- `jobsWorkflow.ts` — `showJobsSiteChrome({ pathname, search })` for footer + Signal FAB.
- `SiteFooter.tsx` — Jobs kicker/copy/links (Jobs / CRM / About); SIGNAL footer unchanged on `/pipeline`.
- `ScoutChat.tsx` — hide Signal FAB when Jobs chrome is on (signup, About, Jobs CRM).
- `docs/EXPERIMENT_MODE.md` — footer lock.
- Vitest: helper matrix + file-read contracts.

## Verify

`pnpm exec vitest run client/src/lib/jobsWorkflow.test.ts` — 28 passed.

## Follow-ups

Intelligence **body** is still SIGNAL copy. CRM “Pipeline lead #” hop stays SIGNAL-side for a later cycle.
