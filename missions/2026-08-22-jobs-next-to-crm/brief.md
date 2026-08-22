# Skip the Pipeline Activate confirmation; Next opens CRM

**Date:** 2026-08-22  
**Type:** build  
**Agents:** ProductSurface

## Goal

`/pipeline?src=jobs_activate` is a bounce: “5 checked · 12 in this list” then Save to CRM. CRM only unlocks 3 job opportunities. Next on Jobs should open CRM with those 3. No extra confirmation page.

## Acceptance

1. Next from the job list goes to `/crm?src=jobs_activate` (signup first if signed out).
2. Old `/pipeline?src=jobs_activate` links redirect to CRM. The save-confirmation board is gone.
3. CRM shows 3 unlocked jobs from the handoff, matching the free watch taste.
4. Vitest covers the href, the 3-job cap, and no second job list on pipeline.

## Out of scope

SIGNAL, matcher (M2), HubSpot, paid CRM unlocks.
