# Outcome: Contact gap backfill

**Date:** 2026-06-23  
**Status:** done

## Summary

Added `--require-gap` CLI flag and batch plumbing for targeted secondary passes. Ran contact-only batch (limit 25).

## Batch results

| Metric | Value |
|--------|-------|
| Candidates | 5 |
| Contact filled | 3 |
| Fields filled total | 7 |

Note: 3 filled rows were junk (quarantined by rectification). Real pipeline contact gap reduction needs Apollo (`APOLLO_API_KEY`) for verified outreach emails on clean buyer rows.

## Next

Re-run harness snapshot for `gap_frequency.contact` delta; prioritize contact gap on HOT/WARM surface leads with websites.
