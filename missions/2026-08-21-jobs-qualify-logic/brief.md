# Mission: Qualify is a judgment, not a request slip

**Date:** 2026-08-21
**Type:** build
**Agents:** ProductSurface
**Status:** in progress

## Goal

After FIND, **Qualify this job** must produce a pursuit judgment from evidence already on the card. It must not be a second empty click ("Request qualification") that only stores an analytics event.

## Why

PR #68 put QUALIFY on the job card so login no longer killed the workflow. The card still asked twice and then said "we'll investigate" without judging. That is the same wasted step, on the same page.

QUALIFY = determine whether this work is worth pursuing. FIND already produced `why` / `still_unknown` / `blockers`. Use those. Do not reopen the matcher. Do not hop to /pipeline.

## Acceptance

- [x] One click: Qualify this job → pursuit brief (pursue / needs evidence / not now)
- [x] Brief is grounded only in match evidence already on the job
- [x] No inner "Request qualification" dead click
- [x] Anonymous users still see the brief before any signup ask
- [x] Targeted tests pass
