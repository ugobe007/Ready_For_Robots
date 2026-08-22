# Outcome — Hide Pipeline on Jobs chrome

**Date:** 2026-08-22  
**Type:** build  
**Status:** shipped (awaiting merge)

## Diff

- `jobsWorkflow.ts`: `isJobsChromePath`, `showSignalPipelineNav`, `jobsHeaderCrmHref`
- `ExperimentHeader.tsx`: Pipeline only when SIGNAL nav is on; CRM href follows Jobs vs SIGNAL; `useSearch` so `/crm` → `/crm?src=jobs_activate` re-renders
- `Crm.tsx`: same `useSearch` for Jobs vs SIGNAL body
- `jobsWorkflow.test.ts`: covers hide/show + CRM href
- `docs/EXPERIMENT_MODE.md`: header is Jobs / About / Sign in; Pipeline is SIGNAL-only

## Metrics

No snapshot delta. This is a chrome leak, not ranking.

## Follow-ups

Header.tsx (legacy SIGNAL chrome) still lists Pipeline. Jobs pages use ExperimentHeader.
