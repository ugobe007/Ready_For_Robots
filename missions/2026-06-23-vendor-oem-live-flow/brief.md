# Mission: Vendor OEM live flow

**Date:** 2026-06-23
**Agent:** LeadQuality
**Status:** done
**Type:** build

## Goal

Close live-flow OEM leak — broaden backlog quarantine beyond exact blocklist reason string.

## Acceptance criteria

- [x] `vendor_oem_junk_match()` — blocklist + pattern vendor reasons
- [x] `quarantine_vendor_oem_leaks.py` uses broad match
- [x] Dry-run → `--apply`
