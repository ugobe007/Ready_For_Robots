# Rename process step 02 to Available jobs

**Date:** 2026-08-26  
**Type:** build  
**Agents:** ProductSurface

## Goal

In Jobs process chrome (FIND bar and CRM workflow), change step **02** from “Here are its jobs” to **Available jobs**. Step **03 stays CRM**. No href or behavior change.

Chrome uses `uppercase`, so the source string is sentence case like step 01 (`Show us your robot`). Users see **AVAILABLE JOBS**.

## Acceptance

1. `JOBS_PROCESS_STEPS[1].label` is `Available jobs`. Step 03 remains `CRM`.
2. FIND process bar, CRM desk process bar, and About all read the same constant.
3. verify-readyforrobots jobs-chrome canary and `agent_verify.py` expect `Available jobs`.
4. `docs/feature_map.md` and `docs/jobs_crm.md` name the new label.
5. vitest for jobsWorkflow / process chrome passes. No href or step-id changes.

## Out of scope

Rename step 03. Matcher retune. SIGNAL hop. Fly/Vercel deploy.
