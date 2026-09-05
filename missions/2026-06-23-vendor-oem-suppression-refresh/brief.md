# Mission: Vendor / OEM suppression refresh

**Date:** 2026-06-23
**Agent:** LeadQuality
**Status:** done
**Type:** build

## Goal

Extend the robotics OEM blocklist, exclude humanoid-catalog buyer deployers from false positives, and quarantine active `is_internal=true` rows already matching vendor junk.

## Acceptance criteria

- [ ] Expanded `KNOWN_ROBOTICS_VENDOR_NAMES` + catalog buyer denylist
- [ ] `scripts/quarantine_vendor_oem_leaks.py` — dry-run + `--apply`
- [ ] Tests in `tests/test_robot_vendor_names.py`
- [ ] Dry-run report; `--apply` quarantine on vendor/OEM matches
- [ ] Harness snapshot delta on `intelligence.junk_reasons`
- [ ] Commit, push, notify

## Context

Rank-1 backlog item in `docs/market_thesis.md`. Live junk sample ~6% vendor/OEM dominated on fresh ingest.

## Out of scope

- RSS HTML strip (rank 2)
- Hard deletes
- Parallel pipeline cache refresh

## Autonomous policy

Commit, push, notify when done. Run `--apply` after dry-run unless counts are unexpected.
