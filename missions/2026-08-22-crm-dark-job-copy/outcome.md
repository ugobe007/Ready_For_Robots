# Outcome — Dark CRM + Intelligence; job copy

**Mission:** `missions/2026-08-22-crm-dark-job-copy`  
**Type:** build

## Shipped

- CRM: navy account table, job outreach checkpoint, sidebar cards. No light `admin-workspace`. Kicker is **Job outreach checkpoint**.
- `/intelligence`: Jobs header, Kare face, emerald About, explicit navy panels (not white remaps only).
- `/pipeline`: signed-in list capped at 15 (`JOBS_PIPELINE_CAP`) with a second slice on `displayedDeals`. Anonymous stays 5. Detail panel is **Job workspace**.
- Job cards use `jobExplanation()` — friction / workflow / job why. Sales templates (`Pitch`, `Open with`, `Lead with`, `discovery call`, `Why now signal not yet`) are skipped.

## Verify

- `npx vitest run client/src/lib/jobsWorkflow.test.ts` — 24 passed
