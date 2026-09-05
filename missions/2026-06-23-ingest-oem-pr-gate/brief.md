# Mission: Ingest-time OEM PR gate

**Date:** 2026-06-23
**Agent:** LeadQuality
**Status:** done
**Type:** build

## Goal

Reject vendor funding / OEM PR articles at ingest before company INSERT — close live-flow leak beyond name-only vendor blocklist.

## Acceptance criteria

- [x] `_buyer_opportunity_gate` in `evaluate_lead_candidate` article context pass
- [x] Test: funding-round vendor PR rejected
- [x] Deploy to Fly
