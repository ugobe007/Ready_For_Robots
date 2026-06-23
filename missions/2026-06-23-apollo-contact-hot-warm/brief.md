# Mission: Apollo contact HOT/WARM backfill

**Date:** 2026-06-23
**Agent:** LeadQuality
**Status:** done
**Type:** build

## Goal

Target contact gaps on HOT/WARM pipeline surface leads only.

## Acceptance criteria

- [x] `--priority-tier HOT|WARM` on secondary pass CLI
- [x] Batch run with `--require-gap contact`
- [ ] Apollo verified emails (blocked: `APOLLO_API_KEY` not in `.env`)
