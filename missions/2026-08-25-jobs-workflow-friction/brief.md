# Jobs workflow friction smoke (post PR #128)

**Date:** 2026-08-25  
**Type:** research  
**Agents:** ProductManager

## Goal

Walk production FIND → Job Cards → Next after the VLA-lookup merge. Identify weak points. Do not retune the matcher. Do not invent jobs.

## Acceptance

1. Production `/` has Jobs header (no Pipeline), Fourier N1 yields Conditional cards with OpenVLA / π0.5 / GR00T N1.5, Next goes to `/signup?next=/crm?src=jobs_activate`.
2. Ranked friction list with evidence (API timings + screenshots).
3. One recommended next build (Jobs-path only).

## Out of scope

SIGNAL ranking, matcher score tweaks, inventing hospitality SKUs or labor dollars.
