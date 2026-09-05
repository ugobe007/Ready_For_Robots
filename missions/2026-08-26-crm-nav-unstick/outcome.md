# Outcome — Unstick CRM nav

**Date:** 2026-08-26  
**Branch:** `cursor/crm-nav-unstick-009b`  
**Type:** build

## What was missing

Unsigned `/pipeline?src=jobs_activate` rendered only “Opening CRM…” and redirected with wouter `setLocation`. If that hop lagged or failed, there was no process bar, no signup CTA, and no way back to Job Cards or FIND. About was `max-sm:hidden`. After inspect/place the signed desk had 01/02 links but no explicit next to leave the desk.

Production JS `index-DNiSRZF_.js` still has the dead “Opening CRM…” desk and no `Sign up to open CRM` / `jobsCrmNextHref`.

## What changed

- Shared `JobsProcessChrome`: 01 FIND / 02 Job Cards / 03 CRM + next CTA.
- Unsigned wall keeps the signup redirect (`jobsCrmOpenHref`) and now shows process chrome + **Sign up to open CRM →** + leave (Job Cards or FIND). Auth must be ready before walling.
- Signed desk: same chrome top and bottom, empty-state FIND link, **CRM next** after inspect/place (`/?restore=1` or `/?new=1`). Place stays inside the egg. Step 03 stays CRM.
- Header About visible on all widths. Jobs CRM path gets `SiteFooter`. `/crm?src=jobs_*` hop shows the same chrome + next.
- Helpers: `jobsCrmNextHref`, `jobsCrmLeaveHref`, `jobsCrmNextLabel`.

## Tests

`pnpm exec vitest run client/src/lib/jobsWorkflow.test.ts client/src/lib/pstackSite.test.ts client/src/lib/jobsApply.test.ts` — 44 passed.

Local Vite (worktree `:3010`) `/pipeline?src=jobs_activate` 200; module canaries for process chrome, signup next, leave hrefs, About.

`python3 scripts/agent_verify.py doctor` — Fly + site JS canaries ok (`skip_green=false`). Drive `jobs-crm` / `jobs-chrome` ok on production (pre-deploy bundle).

## Follow-ups

Parent should open a **draft** PR to `main` (ManagePullRequest was not in this agent’s tool catalog). Do not merge until Vercel ships a JS hash that contains `Sign up to open CRM` / `jobsCrmNextHref`.
