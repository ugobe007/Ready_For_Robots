# Outcome — About page is Jobs, not SIGNAL

**Date:** 2026-08-23  
**Type:** build  
**Status:** shipped (PR)

## Diff

- `Intelligence.tsx` — About body is FIND → jobs → CRM. Primary CTA `Start jobs →` to `/?new=1`. Signup `src=jobs_activate`. No `/signals` hop, no product-name SIGNAL.
- `docs/EXPERIMENT_MODE.md` — About body lock.
- Vitest file-read on `Intelligence.tsx`.

## Verify

`pnpm exec vitest run client/src/lib/jobsWorkflow.test.ts` — 28 passed.

Local Vite `localhost:3009/intelligence`:

- Hero 01/02/03 process steps; description “Robots need jobs…”
- CTAs: Start jobs →, Keep jobs in CRM. No Activate SIGNAL. No /signals links.
- How Jobs works: Employer / Workplace / Work / Robot Job — not lead scoring.
- Footer kicker still JOBS.

## Follow-ups

CRM “Pipeline lead #” hop stays SIGNAL-side for a later cycle.
