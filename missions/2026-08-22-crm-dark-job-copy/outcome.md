# Outcome — Dark CRM + Intelligence; job copy

**Mission:** `missions/2026-08-22-crm-dark-job-copy`  
**Type:** build

## Shipped

- CRM: removed light `admin-workspace`; `.sb-surface` / inputs / table rows are navy. Account list no longer sits on a white panel.
- `/intelligence`: Jobs header, Kare face, emerald About, navy page background.
- `/pipeline`: signed-in list capped at 15 (`JOBS_PIPELINE_CAP`). Anonymous stays 5.
- Job cards and pipeline rows use `jobExplanation()` — friction / workflow / job why, not “Pitch …” sales copy.

## Verify

- `npx vitest run client/src/lib/jobsWorkflow.test.ts` — 24 passed
