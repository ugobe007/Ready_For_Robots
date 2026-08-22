# Hide Pipeline on Jobs chrome

**Date:** 2026-08-22  
**Type:** build  
**Agents:** ProductSurface

## Goal

Jobs header Pipeline hops FIND users onto SIGNAL. Hide it on Jobs chrome and Jobs CRM. Header CRM on Jobs goes to `/crm?src=jobs_activate`.

## Acceptance

1. `/` and `/jobs` do not show Pipeline.
2. `/crm?src=jobs_activate` does not show Pipeline.
3. `/pipeline` and `/crm` without Jobs src still show Pipeline.
4. Vitest covers `showSignalPipelineNav` / `jobsHeaderCrmHref`.

## Out of scope

Deleting `/pipeline`, SIGNAL CRM, matcher, employer posting.
