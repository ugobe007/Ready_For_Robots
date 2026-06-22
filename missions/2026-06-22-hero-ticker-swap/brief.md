# Mission: Hero ticker swap

**Date:** 2026-06-22
**Agent:** ProductSurface
**Status:** done

## Goal

Replace the home hero typewriter spotlight (`HeroSpotlightLeads`) with the live sales-lead ticker that shows company name, tier, and robot types needed.

## Acceptance criteria

- [x] Home hero uses live ticker (8 visible rows, 6s tick)
- [x] Shows `robot_types_needed` from `/api/leads`
- [x] Visible on mobile (not `hidden lg:block` only)
- [x] Link to full pipeline in ticker footer
- [x] Experiment page `/experiment` unchanged (12 rows, 5s tick)
- [ ] Deploy to production and verify `built_at` + feed after release
- [ ] Baseline Activate SIGNAL CTR (optional 7-day compare)

## Context

User approved hero swap after `/experiment` ticker prototype. Harness mission follows Claude Agent SDK Phase 0.

Reference: `readyforrobots-new/client/src/components/HeroLeadTicker.tsx`, `ExperimentLeadTicker.tsx`.

## Out of scope

- Removing `HeroSpotlightLeads.tsx` (keep for rollback)
- Pipeline cache or lead quality rule changes
