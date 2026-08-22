# Jobs list: Next / Start jobs, no flash

**Date:** 2026-08-21  
**Type:** build  
**Agents:** ProductSurface

## Goal

The job list must show a wizard advance: **Start jobs →** on FIND, **Next →** on the matched jobs list. The page must not remount/flash on first paint.

## Cause

FIND had no Start jobs on the tape. Matched jobs used "Activate job list" instead of Next. `/?new=1` remounted the workspace when stripped to `/`, and the live tape re-seeded + swapped the header to "● New Job" on arrive.

## Acceptance

1. FIND job tape has **Start jobs →** (and the URL form uses the same CTA).
2. Matched jobs list has **Next →** (page-level, not on the card).
3. Jobs page does not remount on `/?new=1` → `/`.
4. Tape does not flash the jobs-found header on load.
5. Vitest green.
