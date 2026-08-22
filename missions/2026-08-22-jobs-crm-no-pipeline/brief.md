# Jobs CRM landing: 3 jobs, not SIGNAL pipeline

**Date:** 2026-08-22  
**Type:** build  
**Agents:** ProductSurface

## Goal

`/crm?src=jobs_activate` still shows Back to pipeline, HubSpot/path fork, empty accounts, and SIGNAL outreach. Jobs step 3 is the 3 unlocked jobs + watch. Do not hop onto pipeline.

## Acceptance

1. Jobs CRM src hides pipeline CTA, path fork, accounts table, and outreach editor.
2. Signed-out Sign in goes to signup with `next=/crm`, not a bare `/login`.
3. CrmHero (3 jobs + opt-in + new robot) stays the page.
4. Vitest covers Crm.tsx for the Jobs path.

## Out of scope

Paid unlocks, HubSpot sync, matcher, Cal digest 403.
