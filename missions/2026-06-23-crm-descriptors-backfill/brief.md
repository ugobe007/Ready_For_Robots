# Mission: CRM descriptors backfill

**Date:** 2026-06-23
**Agent:** LeadQuality
**Status:** done
**Type:** build

## Goal

Close `crm_descriptors` gaps on surface leads by inferring automation requirements when signal regex extraction finds nothing.

## Acceptance criteria

- [x] Robot-fit fallback in `crm_extractor.extract()`
- [x] Meaningful fill detection in `_run_crm_rescue` (not empty budget/timing shells)
- [x] Secondary pass batch with `--require-gap crm_descriptors`
- [x] Gap count reduced in harness snapshot
