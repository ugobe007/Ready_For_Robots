# Outcome: Apollo contact HOT/WARM backfill

**Date:** 2026-06-23  
**Status:** done (partial — Apollo key missing)

## Summary

Added `--priority-tier` filter to gap audit + secondary pass. Ran HOT/WARM contact-only batch (limit 30).

## Results

| Metric | Value |
|--------|-------|
| HOT/WARM contact-gap candidates | **1** |
| Contact filled | **0** |

Most HOT/WARM surface leads already have contact signals or role-inbox fallback. **1** remaining row (`News Why`) is a junk headline stub — contact rescue correctly failed.

## Blocker

`APOLLO_API_KEY` not configured — add to `.env` for verified decision-maker lookup on real buyer rows.

## Harness

`contact` gap: **29** (down from 34); `crm_descriptors` now #1 at 30.
