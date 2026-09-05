# Outcome — Jobs readable chrome

**Mission:** `missions/2026-08-22-jobs-readable-chrome`  
**Branch:** `cursor/jobs-readable-chrome-4bab`

## What changed

- Job cards put **robot name** and **job title** at display size. `Job ##### is for {SKU}` stays as secondary 14px meta, not 10px identity.
- Jobs process bar, rail links, and eyebrows use ≥14px mono.
- `ExperimentHeader` is taller (`h-14`), wordmark/nav are readable, and signed-in nav includes **CRM**. Pipeline is in the bar for everyone.
- `/pipeline` always uses Jobs chrome. Headline **Pipeline** plus next-step copy. No SIGNAL sales-intelligence eyebrow. Company names in the list are 20px.
- `/crm` uses Jobs chrome, headline **CRM**, and copy that tells the user to pick an account and send — or go back to Pipeline. Admin nav label is CRM, not Outreach editor.
- Login / signup / auth callback use the same header.

## Verify

`npx vitest run client/src/lib/jobsWorkflow.test.ts` — 23 passed.

## Follow-ups

Email-on-job-change watch loop. Do not restyle leftover SIGNAL marketing pages in this mission.
