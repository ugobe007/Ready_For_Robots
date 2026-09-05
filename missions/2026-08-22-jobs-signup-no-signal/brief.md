# Jobs signup shows the 3 jobs, not SIGNAL buyers

**Date:** 2026-08-22  
**Type:** build  
**Agents:** ProductSurface

## Goal

After Next, signed-out users hit signup. That page still proves SIGNAL (Accor Hotels, HOT buyers). Jobs traffic must prove the 3 CRM job opportunities from the handoff.

## Acceptance

1. `src=jobs_activate` / `next=/crm` signup does not show a live HOT buyer or “HOT buyers live now”.
2. It lists up to 3 jobs from the Jobs handoff (title + company).
3. Bullets and magic-link copy land on CRM, not pipeline/SIGNAL.
4. Vitest asserts Signup source for the Jobs path.

## Out of scope

SIGNAL signup for `/pipeline` and `/results`. Matcher. Paid CRM unlocks.
