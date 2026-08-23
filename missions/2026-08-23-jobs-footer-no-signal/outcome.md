# Outcome — Jobs footer matches header (no Pipeline / SIGNAL)

**Date:** 2026-08-23  
**Type:** build  
**Status:** shipped (PR)

## Diff

- `jobsWorkflow.ts` — `showJobsSiteChrome({ pathname, search })` for footer + Signal FAB.
- `SiteFooter.tsx` — Jobs kicker/copy/links (Jobs / CRM / About); SIGNAL footer unchanged on `/pipeline`.
- `ScoutChat.tsx` — hide Signal FAB when Jobs chrome is on (signup, About, Jobs CRM).
- `docs/EXPERIMENT_MODE.md` — footer lock.
- Vitest: helper matrix + file-read contracts.

## Verify

`pnpm exec vitest run client/src/lib/jobsWorkflow.test.ts` — 28 passed.

Local Vite (`localhost:3009`):

- `/signup?src=jobs_activate` — footer kicker JOBS; Product is Jobs / CRM / About; no Pipeline / Signals; no Signal FAB; copyright “Jobs for your robot.”
- `/intelligence` — same Jobs footer; no Signal FAB.
- `/signup?next=/pipeline` — SIGNAL footer keeps Pipeline / Signals and the Signal FAB.

## Follow-ups

Intelligence **body** is still SIGNAL copy (“Activate SIGNAL from live intelligence”). CRM “Pipeline lead #” hop stays SIGNAL-side for a later cycle.
