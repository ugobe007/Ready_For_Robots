# Mission: Contact gap backfill

**Date:** 2026-06-23
**Agent:** LeadQuality
**Status:** done
**Type:** build

## Goal

Backfill `contact` gaps on pipeline surface leads via secondary pass.

## Acceptance criteria

- [x] `--require-gap contact` on `run_lead_secondary_pass.py`
- [x] `require_gaps` wired through `run_secondary_pass_batch`
- [x] Batch run with contact-only filter
