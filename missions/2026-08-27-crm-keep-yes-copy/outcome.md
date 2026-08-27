# Outcome — Keep N jobs? confirm, live nav, Apply sequence

**Date:** 2026-08-27
**Branch:** `cursor/crm-keep-yes-copy-009b`
**Type:** build
**Base:** `origin/main` includes #157 hold. Not reverted.

## Why Yes and nav were dead

**Yes.** Production already rendered a `<button type="button">` labeled **Yes**, but the prompt **Keep these N jobs?** was inert text and **Select all N** sat beside it asking the same question. Operators treated Yes as a link. The same class of bug as Next steps: a control that does not read as a confirm that POSTs keep. Confirm is now a `<form>` + `type="submit"` (**Yes, keep them**, `data-jobs-keep-confirm`) that calls `persistKeptJobs` (signed-in `POST /api/jobs-crm/keep`, then Apply). Unsigned still walls.

**Nav.** `onJobsFreshHomeClick` always `preventDefault()`’d, then `goJobsFreshHome()`. On `/pipeline?src=jobs_activate` that swallowed the real href (`/?new=1`, `/?restore=1`). Header Jobs used the same intercept. Process 03 CRM was a `<span>` with no href. About used wouter `Link` while Jobs used a neutralized `<a>`. Fix: intercept FIND only on Jobs home; CRM header Jobs → `/?restore=1`; 01/02/03 and About/CRM are native `<a href>`.

## What changed

- Prompt: `Keep ${n} jobs?` (N = selected count).
- Removed **Select all N**.
- Apply sequence next to Apply: apply to the job → we help schedule interviews with the customer → they close.
- Signup: **Keep jobs for your robot** (no “Keep these”).

## Files

- `readyforrobots-new/client/src/lib/jobsWorkflow.ts`
- `readyforrobots-new/client/src/lib/jobsCrmAccount.ts`
- `readyforrobots-new/client/src/components/JobsCrmDesk.tsx`
- `readyforrobots-new/client/src/components/JobsCrmNextSteps.tsx`
- `readyforrobots-new/client/src/components/JobsKeepStatusBar.tsx`
- `readyforrobots-new/client/src/components/JobsProcessChrome.tsx`
- `readyforrobots-new/client/src/components/ExperimentHeader.tsx`
- `readyforrobots-new/client/src/components/RobotJobsWorkspace.tsx`
- `readyforrobots-new/client/src/pages/Signup.tsx`
- `docs/jobs_crm.md`, `docs/feature_map.md`

## Tests

`pnpm exec vitest run` jobsCrmAccount + jobsWorkflow + jobsApply + pstackSite — **49 passed**.

Grep on desk/chrome/header: no `Keep these`, no `Select all 5`, no `href="#"` on Yes.

Local Vite `:3012` — `/` and `/pipeline?src=jobs_activate` 200. Module canaries: `Yes, keep them`, `data-jobs-keep-confirm`, apply sequence, `shouldInterceptJobsFreshHomeClick`. Unsigned desk still walls to signup.

## Follow-ups

Parent should open a **draft** PR to `main` (ManagePullRequest was not in this agent’s catalog). Do not merge until Vercel JS contains `Yes, keep them` / `Keep ${n} jobs?` and process hrefs. No Fly this cycle.
