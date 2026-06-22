# Mission: RSS HTML strip and market-report filter

**Date:** 2026-06-23
**Agent:** LeadQuality
**Status:** done
**Type:** build

## Goal

Strip Google News RSS HTML from Unknown-industry signal text and quarantine market-report / display-junk rows polluting the largest industry bucket (~865 live).

## Acceptance criteria

- [ ] Enhanced HTML normalization in `lead_signal_display.strip_extraction_artifacts`
- [ ] Market-report name/signal patterns in `rss_noise_lead` + `is_junk`
- [ ] `scripts/quarantine_unknown_rss_noise.py` — dry-run + `--apply`
- [ ] `scripts/strip_unknown_industry_signal_html.py` — dry-run + `--apply`
- [ ] Tests; harness snapshot delta on Unknown-industry count
- [ ] Commit, push, notify

## Context

Rank-1 backlog after vendor-OEM mission. ~857 active Unknown-industry rows; signals dominated by Google RSS HTML blobs.

## Out of scope

- Hard deletes (use existing `cleanup_unknown_rss_noise.py` separately if needed)
- Industry ontology rescue (rank 3)

## Autonomous policy

Commit, push, notify when done. Quarantine after dry-run unless counts are unexpected.
