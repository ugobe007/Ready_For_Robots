# Tune scrapers to the new parameters

**Date:** 2026-08-31  
**Type:** build  
**Agents:** ScraperOps + ProductSurface  
**Branch:** `cursor/tune-scrapers-new-params-009b`

## Goal

Job-board, venue, and OEM page extract use this cycle's ontology parameters: product range, named products, hardware-grounded capabilities, task models. Never company → category → jobs.

## Acceptance

1. Extracted jobs carry industry work language, required capabilities, product class (not OEM dump), task-model requirement, named employer.
2. Serving posting does not attach to a cleaner SKU class.
3. Drone-cleaning posting is not hard_floor_scrub-only.
4. Chrome is not a job employer. Empty and invented SKU names are rejected.
5. Venue coverage stays hotels / restaurants / casinos / airports / offices / malls / data centers.
6. Contacts stay page-only. REVIEW.md is the operator surface.

## Out of scope

Fly deploy. Merge #195, leftover #197, CRM-first #202.
