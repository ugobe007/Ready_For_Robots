# Mission: All-robots submit must land on jobs + 5 buyer leads

**Date:** 2026-08-20
**Type:** build
**Agents:** ProductSurface
**Status:** in progress

## Goal

The Jobs URL submit path must not strand a user on a robot catalog after they ask to find jobs for all robots. One company-level match. Reveal jobs. Offer 5 buyer leads as the next step.

## Why

Unitree (and other OEM homepages) resolve to several products. Clicking **All N robots** currently:

1. Runs a full job search per SKU (30s+)
2. Lands on PORTFOLIO with View matches / Review profile and no global next step

That breaks FIND → JOBS → 5 buyer leads.

## Acceptance

- [x] Confirming several/all robots lands on JOBS, not the catalog
- [x] One composed search (cached company profile when grounded), not N rebuilds
- [x] Jobs screen always shows a next-step CTA to 5 buyer leads (`/results?limit=5` anonymous, `/pipeline` signed-in)
- [x] Catalog, if opened, has the same next-step CTA so it is not a dead end
- [x] Targeted tests pass
